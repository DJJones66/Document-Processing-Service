# Integration: Docling Document Processing Library

**Purpose:** Multi-format document text extraction and layout understanding
**Version:** 2.57.0
**Maintainer:** IBM Research (DS4SD)
**Repository:** https://github.com/DS4SD/docling

---

## Overview

Docling is IBM Research's document processing library that converts various document formats (PDF, DOCX, PPTX, HTML, MD) into structured formats while preserving layout information. It uses ML-based layout detection to understand document structure (headings, tables, lists, etc.).

**Why we use it:** Provides unified interface for multi-format processing with built-in table extraction and OCR support. See ADR-001 for decision rationale.

---

## Authentication & Setup

### Installation
```bash
poetry add docling[cpu]  # CPU-only version
# or
poetry add docling[gpu]  # GPU-accelerated (requires CUDA)
```

### Model Downloads
Docling downloads ML models from HuggingFace Hub on first use:
- **Primary model:** `ds4sd/docling-layout-heron` (configurable via `DOCLING_MODEL_NAME`)
- **Size:** ~100-200MB
- **Cache location:** `~/.cache/huggingface/hub/` (configurable via `HF_HOME`)

**⚠️ Windows Note:** See Data-Quirk-001 for symlink handling requirements.

### Configuration
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

# Configure PDF processing
pdf_options = PdfPipelineOptions()
pdf_options.do_ocr = False  # Enable for scanned documents
pdf_options.do_table_structure = True  # Extract table structure

# Create converter
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pdf_options,
            backend=PyPdfiumDocumentBackend
        )
    }
)
```

---

## Data Format & Schema

### Input
**Supported formats:**
- PDF (`.pdf`) - Best support, ML-based layout detection
- DOCX (`.docx`) - Native structure preserved
- PPTX (`.pptx`) - Slide-by-slide processing
- HTML (`.html`, `.htm`) - DOM structure parsed
- Markdown (`.md`) - Structure preserved

**File handling:**
```python
# From file path
result = converter.convert("/path/to/document.pdf")

# From file object
with open("/path/to/document.pdf", "rb") as f:
    result = converter.convert(f)
```

### Output Schema

#### Document Object
```python
result = converter.convert("document.pdf")

# Main document object
result.document
  ├── .pages          # List of Page objects
  ├── .tables         # List of extracted tables
  ├── .pictures       # List of extracted images
  ├── .text()         # Full text extraction (plain)
  └── .export_to_markdown()  # Structured markdown export
```

#### Page Object
```python
page = result.document.pages[0]
page.page_no          # Page number (1-indexed)
page.size             # Width x height
page.elements         # List of document elements (headings, paragraphs, etc.)
```

#### Element Types
- **Heading:** `element.element_type == "heading"`, `element.level` (1-6)
- **Paragraph:** `element.element_type == "paragraph"`
- **Table:** `element.element_type == "table"`, includes row/column structure
- **List:** `element.element_type == "list"`, includes list items
- **Image:** `element.element_type == "picture"`

### Markdown Export
```python
markdown = result.document.export_to_markdown()
```

**Format features:**
- Heading hierarchy preserved (`#`, `##`, `###`, etc.)
- Tables rendered as markdown tables
- Lists with proper indentation
- Code blocks preserved
- Image references included

**Example output:**
```markdown
# Document Title

This is a paragraph with **bold** and *italic* text.

## Section Heading

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |

- List item 1
- List item 2
  - Nested item
```

---

## Quirks and Gotchas

### 1. First-Run Model Download
**Quirk:** First document conversion triggers model download (100-200MB), causing 5-10 minute delay.

**Solution:** Pre-download during initialization:
```python
# In DoclingModelManager
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='ds4sd/docling-layout-heron',
    local_files_only=False,
    resume_download=True
)
```

### 2. Windows Symlink Issues
**Quirk:** Model downloads fail on Windows without admin rights.

**Solution:** Disable symlinks (see Data-Quirk-001):
```python
if os.name == 'nt':
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    constants.HF_HUB_DISABLE_SYMLINKS = True
```

### 3. Memory Usage with Large Documents
**Quirk:** Processing 100+ page PDFs can use 2-4GB RAM due to ML model inference.

**Solution:**
- Process in batches if handling multiple documents
- Set `OMP_NUM_THREADS=4` to limit parallelism
- Consider max document size limits

### 4. OCR Performance
**Quirk:** Enabling OCR (`do_ocr=True`) significantly increases processing time (10-20x slower).

**Solution:**
- Only enable for scanned documents
- Detect if OCR needed first (check if text extraction returns empty)
- Consider timeout limits

### 5. Table Structure Quality
**Quirk:** Complex tables (merged cells, nested tables) may not extract perfectly.

**Solution:**
- Test with representative sample documents
- Validate table extraction quality
- Consider fallback to simpler text extraction if needed

### 6. Format-Specific Behavior
**Quirk:** Different document formats have different processing paths:
- **PDF:** ML-based layout detection (slow, high quality)
- **DOCX:** Native structure parsing (fast, reliable)
- **HTML:** DOM-based extraction (fast, quality varies by HTML structure)

**Solution:** Set appropriate timeouts based on format.

### 7. Dependency Size
**Quirk:** Docling pulls in PyTorch, transformers, and other ML libraries (~1.5GB total).

**Impact:**
- Docker images grow from ~500MB to ~2GB
- Installation time increases
- Startup time includes model loading

**Mitigation:**
- Use multi-stage Docker builds
- Cache models in Docker layers
- Consider CPU-only PyTorch build

---

## Error Handling

### Common Errors

#### Model Download Failure
```python
# Error
HFValidationError: Repo not found

# Cause
Network issues, wrong model name, or HuggingFace Hub down

# Solution
try:
    snapshot_download(repo_id=model_name)
except Exception as e:
    logger.error(f"Model download failed: {e}")
    # Fall back to cached version or alternate model
```

#### Processing Timeout
```python
# Error
TimeoutError: Document processing exceeded limit

# Cause
Large document or OCR enabled

# Solution
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Processing timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(300)  # 5 minute timeout
try:
    result = converter.convert(document_path)
finally:
    signal.alarm(0)  # Cancel timeout
```

#### Unsupported Format
```python
# Error
ValueError: Unsupported document format

# Cause
File extension not in supported list or corrupted file

# Solution
SUPPORTED_FORMATS = ['.pdf', '.docx', '.pptx', '.html', '.md']
ext = Path(file_path).suffix.lower()
if ext not in SUPPORTED_FORMATS:
    raise InvalidDocumentTypeError(f"Format {ext} not supported")
```

#### Empty Extraction
```python
# Error
No text extracted (blank document)

# Cause
Scanned PDF without OCR, corrupted file, or image-only document

# Solution
text = result.document.export_to_markdown()
if not text or len(text.strip()) < 10:
    # Try with OCR enabled
    pdf_options.do_ocr = True
    result = converter.convert(document_path)
```

---

## Rate Limits & Quotas

**No rate limits** - Docling runs locally, no API calls.

**Resource limits:**
- **Memory:** ~1-4GB per document (depends on size and OCR)
- **CPU:** Uses all available cores by default (set `OMP_NUM_THREADS` to limit)
- **Disk:** Model cache uses ~300-400MB

---

## Scope Boundaries

### What Docling Does
✅ Extract text from PDF, DOCX, PPTX, HTML, MD
✅ Preserve document structure (headings, tables, lists)
✅ Table structure extraction
✅ OCR for scanned documents
✅ Layout-aware processing
✅ Export to markdown, JSON, or plain text

### What Docling Doesn't Do
❌ **Chunking** - Extracts full document, doesn't split into semantic chunks
❌ **Token counting** - No built-in token management
❌ **Embeddings** - No vector generation
❌ **Semantic analysis** - Doesn't understand content meaning
❌ **Document classification** - No type/category detection
❌ **Language detection** - Assumes English (works with other languages but quality varies)

**Our implementation adds:**
- Token-based recursive chunking (see `DoclingDocumentProcessor._recursive_token_split()`)
- Token counting via tiktoken (`TikTokenService`)
- Chunk metadata enrichment

---

## Performance Benchmarks

Typical processing times (tested on 8-core CPU, 16GB RAM):

| Document Type | Pages | OCR | Time | Memory |
|---------------|-------|-----|------|--------|
| PDF (text)    | 10    | No  | 5s   | 800MB  |
| PDF (text)    | 50    | No  | 15s  | 1.2GB  |
| PDF (text)    | 100   | No  | 30s  | 2GB    |
| PDF (scanned) | 10    | Yes | 45s  | 1.5GB  |
| DOCX          | 20    | N/A | 3s   | 500MB  |
| PPTX          | 30    | N/A | 8s   | 600MB  |

**Optimization tips:**
- Disable OCR unless needed (20x speedup)
- Disable table extraction if not needed (2x speedup)
- Process documents sequentially to limit memory usage

---

## Example Usage in Our Codebase

### Basic Extraction
```python
# From: app/adapters/document_processor/docling_document_processor.py

async def _extract_with_docling(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
    # Convert document
    result = self.converter.convert(file_path)

    # Extract as markdown (preserves structure)
    complete_text = result.document.export_to_markdown()

    # Extract metadata
    metadata = {
        "page_count": len(result.document.pages),
        "has_tables": len(result.document.tables) > 0,
        "extraction_method": "docling"
    }

    return complete_text.strip(), metadata
```

### Full Processing Pipeline
```python
async def process_document(self, document: Document) -> Tuple[List[DocumentChunk], str]:
    # 1. Extract with Docling
    complete_text, doc_metadata = await self._extract_with_docling(document.file_path)

    # 2. Create token-based chunks
    doc_chunks = await self._create_token_chunks(
        document=document,
        text=complete_text,
        doc_metadata=doc_metadata
    )

    return doc_chunks, complete_text
```

---

## References

- **Documentation:** https://docling.github.io/docling/
- **GitHub:** https://github.com/DS4SD/docling
- **Models:** https://huggingface.co/ds4sd
- **Paper:** "Docling: A Foundation Model for Document Understanding"
- **Our ADR:** ADR-001 (Use Docling for Document Processing)
- **Our Implementation:** `app/adapters/document_processor/docling_document_processor.py`

---

## Troubleshooting

### Issue: Slow first request
**Cause:** Model downloading during initialization
**Fix:** Enable `preload_models=True` in `DoclingDocumentProcessor.__init__()`

### Issue: Out of memory on large documents
**Cause:** Processing 100+ pages loads entire document
**Fix:** Implement document size limits or page-by-page processing

### Issue: Poor table extraction
**Cause:** Complex table structure confuses layout detection
**Fix:** Test with sample documents, consider fallback extraction

### Issue: Service won't start on Windows
**Cause:** Symlink creation fails (see Data-Quirk-001)
**Fix:** Set `HF_HUB_DISABLE_SYMLINKS=True` before model download

---

## Version Notes

**Current version: 2.57.0**

Breaking changes from previous versions:
- 2.x → Pipeline options moved to `PdfPipelineOptions`
- 2.x → Backend must be explicitly specified (`PyPdfiumDocumentBackend`)

Monitor for updates:
```bash
poetry show docling
poetry update docling
```

Consider pinning major version to avoid breaking changes:
```toml
[tool.poetry.dependencies]
docling = "^2.57.0"  # Allow patch updates only
```
