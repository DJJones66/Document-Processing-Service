import logging
import os
from typing import List, Dict, Any, Tuple
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

from ...core.ports.document_processor import DocumentProcessor
from ...core.domain.entities.document import Document
from ...core.domain.entities.document_chunk import DocumentChunk
from ...core.domain.exceptions import DocumentProcessingError, InvalidDocumentTypeError
from ...core.ports.token_service import TokenService

from app.config import settings

class DoclingModelManager:
    """Manages Docling model downloads and caching"""
    
    # Default models used by Docling
    REQUIRED_MODELS = [
        settings.DOCLING_MODEL_NAME,
    ]
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def ensure_models_downloaded(self) -> None:
        """
        Pre-download required Hugging Face models to avoid runtime errors.
        This is especially important on Windows where symlink creation can fail.
        """
        try:
            # Disable symlinks on Windows to avoid permission errors
            if os.name == 'nt':  # Windows
                os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
                os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
                # Force huggingface_hub to not use symlinks
                try:
                    from huggingface_hub import constants
                    constants.HF_HUB_DISABLE_SYMLINKS = True
                except Exception as e:
                    self.logger.warning(f"Could not disable HF symlinks: {e}")
            
            self.logger.info("Checking Docling models...")
            
            # Import huggingface_hub for model downloading
            try:
                from huggingface_hub import snapshot_download
                
                for model_name in self.REQUIRED_MODELS:
                    try:
                        self.logger.info(f"Ensuring model is cached: {model_name}")
                        download_kwargs = {
                            "repo_id": model_name,
                            "local_files_only": False,  # Download if not cached
                            "resume_download": True,
                        }
                        if os.name == "nt":
                            download_kwargs["local_dir_use_symlinks"] = False
                        snapshot_download(**download_kwargs)
                        self.logger.info(f"Model ready: {model_name}")
                    except Exception as e:
                        self.logger.warning(
                            f"Could not pre-download model {model_name}: {e}. "
                            f"Will attempt to download on first use."
                        )
                
            except ImportError:
                self.logger.warning(
                    "huggingface_hub not available for pre-downloading models. "
                    "Models will be downloaded on first use."
                )
            
        except Exception as e:
            self.logger.warning(f"Model pre-download check failed: {e}")


class DoclingDocumentProcessor(DocumentProcessor):
    """Document processor using Docling for text extraction and token-based chunking"""
    
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_MIN_CHUNK_SIZE = 100
    
    def __init__(
        self,
        token_service: TokenService,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
        enable_ocr: bool = False,
        extract_tables: bool = True,
        extract_images: bool = False,
        preload_models: bool = True,
    ):
        """
        Initialize the Docling processor
        
        Args:
            token_service: Service for token management
            chunk_size: Maximum size of text chunks (in tokens)
            chunk_overlap: Overlap between consecutive chunks (in tokens)
            min_chunk_size: Minimum acceptable chunk size (in characters)
            enable_ocr: Enable OCR for scanned documents
            extract_tables: Extract tables from documents
            extract_images: Extract images from documents
            preload_models: Pre-download models during initialization
        """
        self.logger = logging.getLogger(__name__)
        self.token_service = token_service
        
        self._validate_chunk_parameters(chunk_size, chunk_overlap, min_chunk_size)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.enable_ocr = enable_ocr
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        
        # Pre-download models if requested (recommended for production)
        if preload_models:
            model_manager = DoclingModelManager(self.logger)
            model_manager.ensure_models_downloaded()
        
        # Initialize Docling converter with optimized settings
        self.converter = self._initialize_converter()
        
        self.supported_types = settings.SUPPORTED_DOCUMENT_TYPES
        
        self.logger.info(
            f"Initialized DoclingDocumentProcessor with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, min_chunk_size={min_chunk_size}, "
            f"ocr={enable_ocr}, tables={extract_tables}, images={extract_images}"
        )
    
    def _initialize_converter(self) -> DocumentConverter:
        """Initialize Docling DocumentConverter with optimized settings"""
        try:
            # Disable symlinks on Windows
            if os.name == 'nt':
                os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
            
            # Configure PDF pipeline options
            pdf_options = PdfPipelineOptions()
            pdf_options.do_ocr = self.enable_ocr
            pdf_options.do_table_structure = self.extract_tables
            
            # Create format options
            format_options = {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pdf_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
            
            # Initialize converter
            converter = DocumentConverter(
                format_options=format_options
            )
            
            self.logger.info("Successfully initialized Docling DocumentConverter")
            return converter
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Docling converter: {str(e)}")
            raise DocumentProcessingError(f"Converter initialization failed: {str(e)}")
    
    def _validate_chunk_parameters(
        self, 
        chunk_size: int, 
        chunk_overlap: int, 
        min_chunk_size: int
    ) -> None:
        """Validate chunking parameters"""
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
            )
        
        if min_chunk_size <= 0:
            raise ValueError(f"min_chunk_size must be positive, got {min_chunk_size}")
        
        if min_chunk_size > chunk_size * 4:  # Rough token-to-char conversion
            self.logger.warning(
                f"min_chunk_size ({min_chunk_size} chars) may be larger than "
                f"chunk_size ({chunk_size} tokens ≈ {chunk_size * 4} chars)"
            )
    
    async def process_document(self, document: Document) -> Tuple[List[DocumentChunk], str]:
        """Process a document and return token-based chunks and complete text"""
        try:
            if document.document_type.value not in self.supported_types:
                raise InvalidDocumentTypeError(
                    f"Document type {document.document_type.value} not supported"
                )
            
            self.logger.info(f"Starting Docling extraction for document {document.id}")
            
            # Extract text and metadata using Docling
            complete_text, doc_metadata = await self._extract_with_docling(document.file_path)
            
            if not complete_text or len(complete_text.strip()) == 0:
                raise DocumentProcessingError("No text content extracted from document")
            
            self.logger.info(
                f"Extracted {len(complete_text)} characters from document {document.id}"
            )
            
            # Create token-based chunks
            doc_chunks = await self._create_token_chunks(
                document=document,
                text=complete_text,
                doc_metadata=doc_metadata
            )
            
            self.logger.info(f"Created {len(doc_chunks)} chunks for document {document.id}")
            
            return doc_chunks, complete_text
            
        except Exception as e:
            self.logger.error(f"Failed to process document {document.filename}: {str(e)}")
            raise DocumentProcessingError(
                f"Failed to process document {document.filename}: {str(e)}"
            )
    
    async def _extract_with_docling(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from document using Docling"""
        try:
            # Convert document
            result = self.converter.convert(file_path)
            
            # Extract text content as markdown
            complete_text = result.document.export_to_markdown()
            
            # Extract metadata
            metadata = {
                "page_count": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
                "has_tables": False,
                "has_images": False,
                "extraction_method": "docling"
            }
            
            # Check for tables and images if enabled
            if self.extract_tables and hasattr(result.document, 'tables'):
                metadata["has_tables"] = len(result.document.tables) > 0
                metadata["table_count"] = len(result.document.tables)
            
            if self.extract_images and hasattr(result.document, 'pictures'):
                metadata["has_images"] = len(result.document.pictures) > 0
                metadata["image_count"] = len(result.document.pictures)
            
            self.logger.debug(
                f"Docling extraction complete: {len(complete_text)} chars, "
                f"{metadata.get('page_count', 0)} pages"
            )
            
            return complete_text.strip(), metadata
            
        except Exception as e:
            self.logger.error(f"Docling extraction failed for {file_path}: {str(e)}")
            raise DocumentProcessingError(f"Docling extraction failed: {str(e)}")
    
    async def _create_token_chunks(
        self,
        document: Document,
        text: str,
        doc_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Create chunks based on token count using recursive approach"""
        try:
            chunks = []
            
            # Split text into chunks using recursive token-based splitting
            text_chunks = await self._recursive_token_split(text)
            
            for i, chunk_text in enumerate(text_chunks):
                if len(chunk_text.strip()) < self.min_chunk_size:
                    self.logger.debug(f"Skipping chunk {i}: too small ({len(chunk_text)} chars)")
                    continue
                
                # Calculate token count for this chunk
                token_count = self.token_service.count_tokens(chunk_text)
                
                # Create chunk metadata
                chunk_metadata = {
                    "document_filename": document.original_filename,
                    "document_type": document.document_type.value,
                    "chunk_token_count": token_count,
                    "chunk_char_count": len(chunk_text),
                    "processing_method": "docling_token_chunking",
                    **doc_metadata  # Include document-level metadata
                }
                
                # Create chunk
                chunk = DocumentChunk.create(
                    document_id=document.id,
                    content=chunk_text.strip(),
                    chunk_index=i,
                    metadata=chunk_metadata
                )
                
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to create chunks: {str(e)}")
            raise DocumentProcessingError(f"Chunk creation failed: {str(e)}")
    
    async def _recursive_token_split(self, text: str) -> List[str]:
        """Recursively split text based on token count"""
        try:
            # Check if text fits in one chunk
            token_count = self.token_service.count_tokens(text)
            
            if token_count <= self.chunk_size:
                return [text]
            
            # Text is too large, need to split
            chunks = []
            
            # Try splitting by double newlines (paragraphs) first
            paragraphs = text.split('\n\n')
            
            if len(paragraphs) > 1:
                current_chunk = ""
                current_tokens = 0
                
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue
                    
                    para_tokens = self.token_service.count_tokens(paragraph)
                    
                    # If single paragraph is too large, split it further
                    if para_tokens > self.chunk_size:
                        # Save current chunk if it has content
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                            current_tokens = 0
                        
                        # Recursively split the large paragraph
                        para_chunks = await self._split_by_sentences(paragraph)
                        chunks.extend(para_chunks)
                    else:
                        # Check if adding this paragraph exceeds chunk size
                        if current_tokens + para_tokens > self.chunk_size and current_chunk:
                            # Save current chunk and start new one
                            chunks.append(current_chunk.strip())
                            current_chunk = paragraph
                            current_tokens = para_tokens
                        else:
                            # Add to current chunk
                            if current_chunk:
                                current_chunk += "\n\n" + paragraph
                                current_tokens += para_tokens
                            else:
                                current_chunk = paragraph
                                current_tokens = para_tokens
                
                # Add remaining chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            else:
                # Single paragraph, split by sentences
                chunks = await self._split_by_sentences(text)
            
            # Apply overlap if we have multiple chunks
            if len(chunks) > 1 and self.chunk_overlap > 0:
                chunks = await self._apply_overlap(chunks)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed in recursive token split: {str(e)}")
            # Fallback to simple character-based splitting
            return self._fallback_character_split(text)
    
    async def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences using simple sentence boundary detection"""
        try:
            # Simple sentence splitting by common punctuation
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return [text]
            
            chunks = []
            current_chunk = ""
            current_tokens = 0
            
            for sentence in sentences:
                sent_tokens = self.token_service.count_tokens(sentence)
                
                # If single sentence is too large, split by words
                if sent_tokens > self.chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                        current_tokens = 0
                    
                    # Split sentence by words
                    word_chunks = await self._split_by_words(sentence)
                    chunks.extend(word_chunks)
                else:
                    if current_tokens + sent_tokens > self.chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                        current_tokens = sent_tokens
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                            current_tokens += sent_tokens
                        else:
                            current_chunk = sentence
                            current_tokens = sent_tokens
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to split by sentences: {str(e)}")
            return [text]
    
    async def _split_by_words(self, text: str) -> List[str]:
        """Split text by words when sentences are too large"""
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            test_chunk = f"{current_chunk} {word}".strip()
            test_tokens = self.token_service.count_tokens(test_chunk)
            
            if test_tokens > self.chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """Apply overlap between chunks"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            
            # Get overlap from previous chunk
            prev_chunk = chunks[i - 1]
            overlap_text = await self._get_overlap_text(prev_chunk, self.chunk_overlap)
            
            # Combine overlap with current chunk
            if overlap_text:
                overlapped_chunk = f"{overlap_text} {chunk}"
                overlapped_chunks.append(overlapped_chunk)
            else:
                overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    async def _get_overlap_text(self, text: str, target_tokens: int) -> str:
        """Get the last N tokens worth of text for overlap"""
        try:
            # Split into words and work backwards
            words = text.split()
            overlap_words = []
            current_tokens = 0
            
            for word in reversed(words):
                test_text = " ".join([word] + overlap_words)
                test_tokens = self.token_service.count_tokens(test_text)
                
                if test_tokens > target_tokens:
                    break
                
                overlap_words.insert(0, word)
                current_tokens = test_tokens
            
            return " ".join(overlap_words)
            
        except Exception as e:
            self.logger.error(f"Failed to get overlap text: {str(e)}")
            return ""
    
    def _fallback_character_split(self, text: str) -> List[str]:
        """Fallback method for splitting text by characters"""
        chunk_size_chars = self.chunk_size * 4  # Rough estimate: 1 token ≈ 4 chars
        chunks = []
        
        for i in range(0, len(text), chunk_size_chars):
            chunk = text[i:i + chunk_size_chars]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported document types"""
        return self.supported_types.copy()
