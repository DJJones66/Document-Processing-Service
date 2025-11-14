# ADR-001: Use Docling Library for Multi-Format Document Processing

**Status:** Accepted
**Date:** 2024-10-22
**Deciders:** Development Team
**Related:** Supersedes spaCy-based approach (commented out in main.py)

---

## Context

BrainDrive Document AI needs to extract text and metadata from multiple document formats (PDF, DOCX, PPTX, HTML, MD) and convert them into structured chunks for downstream processing. The service must:

- Handle diverse document formats with consistent output
- Extract layout-aware content (preserving document structure)
- Support table extraction and optional OCR
- Run efficiently in containerized environments
- Work reliably on both Windows and Linux

Initial implementation used spaCy with custom layout processing, but this had limitations with format support and required separate handlers for each document type.

## Problem

The spaCy-based approach (`SimpleSpacyLayoutProcessor`) had several issues:

- **Limited format support:** Required custom parsers for each format (PDF, DOCX, etc.)
- **No layout understanding:** Simple text extraction without document structure
- **Table extraction:** Complex to implement reliably across formats
- **Maintenance burden:** Each document format needed separate implementation
- **Inconsistent output:** Different quality depending on document format
- **spaCy model dependency:** Required downloading/managing language models

## Decision

**We will:** Use the Docling library as the primary document processing engine

### Implementation Details

- **Primary processor:** `DoclingDocumentProcessor` in `app/adapters/document_processor/`
- **Document converter:** Uses `docling.DocumentConverter` with configurable pipeline
- **PDF backend:** `PyPdfiumDocumentBackend` for reliable PDF rendering
- **Output format:** Markdown export preserving document structure
- **Model:** `ds4sd/docling-layout-heron` from HuggingFace (configurable via `DOCLING_MODEL_NAME`)
- **Chunking:** Custom token-based recursive splitting after extraction

### Why This Approach

1. **Unified interface:** Single API handles PDF, DOCX, PPTX, HTML, MD
2. **Layout preservation:** Understands document structure (headings, tables, lists)
3. **Built-in features:** OCR, table extraction, image handling out-of-the-box
4. **Active development:** IBM Research maintains docling with regular updates
5. **Production-ready:** Designed for document processing pipelines
6. **Clean output:** Markdown export provides structured, consistent format

## Consequences

### Positive

- **Reduced code complexity:** Eliminated format-specific processors
- **Better extraction quality:** Layout-aware processing improves chunking
- **Feature-rich:** OCR and table extraction without custom implementation
- **Consistent output:** Same processing pipeline for all formats
- **Less maintenance:** Upstream library handles format edge cases

### Negative

- **Larger dependency:** Docling brings transformers, torch, and ML dependencies
- **Docker image size:** Increased from ~500MB to ~2GB with ML libraries
- **Model download:** First run downloads HuggingFace model (~100-200MB)
- **Windows complexity:** Symlink issues require special handling (see `DoclingModelManager`)
- **Processing time:** ML-based layout detection is slower than simple text extraction

### Neutral

- **Token-based chunking:** Still implemented separately (not using docling's chunking)
- **Authentication:** No change to auth layer
- **API interface:** Endpoint signatures remain the same

## Alternatives Considered

### Option 1: spaCy with Custom Layout Processing
**Description:** Continue with `SimpleSpacyLayoutProcessor`, add format-specific parsers
**Pros:**
- Smaller dependencies (no transformers/torch)
- Faster processing (no ML model inference)
- Already partially implemented

**Cons:**
- Complex maintenance (need parser per format)
- Limited layout understanding
- Custom table extraction needed
- Inconsistent quality across formats

**Key reason rejected:** Maintenance burden and quality issues outweighed size benefits

### Option 2: Apache Tika
**Description:** Use Apache Tika for format-agnostic text extraction
**Pros:**
- Mature, battle-tested solution
- Supports 1000+ formats
- Java-based with Python client

**Cons:**
- Requires Java runtime (deployment complexity)
- No layout-aware processing
- No ML-based understanding
- Additional service to manage

**Key reason rejected:** Java dependency and lack of layout awareness

### Option 3: PyMuPDF + python-docx + python-pptx
**Description:** Use format-specific libraries directly
**Pros:**
- Lightweight dependencies
- Direct control over extraction
- Fast processing

**Cons:**
- Manual layout reconstruction needed
- Format-specific code for each type
- No table structure preservation
- High maintenance burden

**Key reason rejected:** Same issues as spaCy approach - too much format-specific code

### Option 4: Commercial APIs (Adobe PDF Services, Google Document AI)
**Description:** Use cloud-based document processing
**Pros:**
- Excellent quality
- Zero infrastructure maintenance
- Advanced features (form detection, etc.)

**Cons:**
- Recurring costs per document
- Internet dependency
- Data privacy concerns (send docs to third party)
- Vendor lock-in

**Key reason rejected:** Cost and privacy requirements for on-premise deployment

## References

- Commit: 927689d - feat: add md, html and pptx file type support
- Docling GitHub: https://github.com/DS4SD/docling
- Docling Models: https://huggingface.co/ds4sd
- Implementation: `app/adapters/document_processor/docling_document_processor.py`
- Legacy code: `app/adapters/document_processor/simple_spacy_layout.py` (commented out)

## Validation Criteria

How will we know if this decision was correct?

- **Processing success rate:** >95% of documents successfully processed
- **Extraction quality:** Manual review of 100 sample documents shows good structure preservation
- **Performance:** Processing time <30s for typical documents (10-50 pages)
- **Stability:** No model download failures or crashes in production
- **Timeline:** Evaluate after 3 months of production use

## Rollback Plan

If Docling proves problematic:

1. **Detection signals:**
   - Success rate drops below 90%
   - Frequent model download failures
   - Processing time exceeds 60s consistently
   - Memory issues in production

2. **Rollback steps:**
   - Uncomment `SimpleSpacyLayoutProcessor` in `main.py:104-106`
   - Comment out `DoclingDocumentProcessor` initialization
   - Restart service
   - Remove heavy ML dependencies if needed

3. **Fallback alternative:**
   - Option 1: Return to spaCy-based processor
   - Option 2: Implement PyMuPDF + format-specific approach
   - Option 3: Consider Apache Tika if Java runtime acceptable

---

## Notes

### Windows Symlink Handling
Docling downloads HuggingFace models, which use symlinks by default. Windows requires admin rights for symlinks. Solution implemented in `DoclingModelManager`:
```python
if os.name == 'nt':  # Windows
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    constants.HF_HUB_DISABLE_SYMLINKS = True
```

### Model Preloading
The `preload_models` parameter (default: `True`) downloads models during startup to avoid first-request delays. Recommended for production.

### Markdown Output
Docling's `export_to_markdown()` provides structured output that preserves:
- Heading hierarchy
- Table structure
- List formatting
- Paragraph boundaries

This structure improves subsequent chunking quality compared to raw text extraction.
