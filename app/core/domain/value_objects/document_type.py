from enum import Enum
from pathlib import Path
from typing import ClassVar


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    MARKDOWN = "md"
    HTML = "html"
    PPTX = "pptx"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_filename(cls, filename: str) -> "DocumentType":
        """Determine document type from filename"""
        ext = Path(filename).suffix.lower().lstrip(".")
        return FILENAME_MAP.get(ext, cls.UNKNOWN)
    
    @classmethod
    def from_mime_type(cls, mime_type: str) -> "DocumentType":
        """Determine document type from MIME type"""
        return MIME_TYPE_MAP.get(mime_type.lower(), cls.UNKNOWN)
    
    def get_mime_type(self) -> str:
        """Get MIME type for document type"""
        # Default to octet-stream for UNKNOWN type
        return MIME_TYPE_INVERSE_MAP.get(self, "application/octet-stream")

# File type map objects
FILENAME_MAP: dict[str, DocumentType] = {
    "pdf": DocumentType.PDF,
    "docx": DocumentType.DOCX,
    "doc": DocumentType.DOC,
    "md": DocumentType.MARKDOWN,
    "html": DocumentType.HTML,
    "htm": DocumentType.HTML,
    "pptx": DocumentType.PPTX,
    "ppt": DocumentType.PPTX,
}

MIME_TYPE_MAP: dict[str, DocumentType] = {
    "application/pdf": DocumentType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
    "application/msword": DocumentType.DOC,
    "text/markdown": DocumentType.MARKDOWN,
    "text/html": DocumentType.HTML,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": DocumentType.PPTX,
    "application/vnd.ms-powerpoint": DocumentType.PPTX,
}

MIME_TYPE_INVERSE_MAP: dict[DocumentType, str] = {
    DocumentType.PDF: "application/pdf",
    DocumentType.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    DocumentType.DOC: "application/msword",
    DocumentType.MARKDOWN: "text/markdown",
    DocumentType.HTML: "text/html",
    DocumentType.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
