# AI Agent Guide: BrainDrive Document AI

**Purpose:** Help AI assistants work effectively by learning from past decisions, failures, and discoveries.

---

## 🚀 Quick Start (Read This FIRST)

### Your Mission as AI Agent

**Not just:** Write working code
**But also:** Compound knowledge for future developers/agents

Think: *"Six months from now, someone (human or AI) will work on this. What do they need to know to avoid my mistakes and build on my success?"*

**That's compounding engineering.** 🚀

### Core Principle

> You don't just write code - you **compound knowledge** by documenting decisions, failures, and discoveries.

**Your workflow:**
1. ✅ **BEFORE coding:** Check `docs/` for existing knowledge
2. ✅ **WHILE coding:** Write working code (normal development)
3. ✅ **AFTER coding:** Document what you learned

---

## 📚 Knowledge Base Structure

```
docs/
├── decisions/           # Architecture Decision Records (ADRs)
├── failures/            # Lessons learned (what NOT to do)
├── data-quirks/         # Non-obvious data behavior
└── integrations/        # External system gotchas
```

---

## Before Starting Any Task

### 1. Check Relevant Documentation (MANDATORY)

```bash
# Search for related decisions
grep -r "keyword" docs/decisions/

# Check for known failures
grep -r "keyword" docs/failures/

# Look for data quirks
grep -r "keyword" docs/data-quirks/

# Review integrations
ls docs/integrations/
```

**Example:** Before modifying document processing:
- Check `docs/decisions/` for chunking strategy decisions
- Check `docs/failures/` for past processing mistakes
- Check `docs/data-quirks/` for known document format issues

### 2. Read Architecture Overview
- Review `CLAUDE.md` for architecture patterns
- Understand Clean Architecture layers (core → ports → adapters → api)
- Follow established dependency injection patterns

---

## Required Documentation Actions

### When to Create ADR (Architecture Decision Record)

**Trigger:** Making an architectural choice between 2+ approaches

**Examples:**
- Choosing between Docling vs spaCy for document processing
- Selecting chunking strategy (token-based vs semantic)
- Deciding authentication method (API key vs JWT)
- Picking storage approach (file system vs object storage)

**Process:**
```bash
# Copy template
cp docs/decisions/000-template.md docs/decisions/00X-decision-name.md

# Fill out:
# - Context: Why decision needed
# - Problem: Pain points
# - Decision: Exact approach
# - Alternatives: What rejected and why
# - Consequences: Pros/cons/risks
```

**Don't create ADR for:**
- Obvious implementation details
- Following existing patterns
- Minor refactoring

### When to Create Failure Log

**Trigger:** Made mistake or wrong assumption that wasted >1 hour

**Examples:**
- Chose wrong library and had to rewrite
- Made incorrect assumption about data format
- Implemented feature that broke existing functionality
- Performance issue from poor architecture choice

**Process:**
```bash
touch docs/failures/00X-failure-name.md

# Document:
# - What happened (the mistake)
# - Root cause (why)
# - Impact (consequences)
# - Lessons learned (what NOT to do)
# - Resolution (how fixed)
# - Prevention (checklist for future)
```

**Template:**
```markdown
# Failure-XXX: [Brief Description]

**Date:** YYYY-MM-DD
**Impact:** [High/Medium/Low]
**Time Lost:** X hours

## What Happened
Detailed description of the mistake/failure.

## Root Cause
Why this happened. Don't blame, explain.

## Impact
- Broken features
- Time wasted
- Data corruption
- Production issues

## Lessons Learned
Key takeaways. What NOT to do.

## Resolution
Step-by-step how it was fixed.

## Prevention Checklist
- [ ] Check X before Y
- [ ] Verify Z assumption
- [ ] Test edge case W

## Related
- Commit: [hash]
- ADR: ADR-XXX (if created solution decision)
```

### When to Create Data Quirk Document

**Trigger:** Discovered non-obvious data behavior

**Examples:**
- Document format edge cases (e.g., scanned PDFs need OCR)
- Token counting doesn't match character count expectations
- Docling model behaves differently on Windows vs Linux
- Certain file types require special handling
- HuggingFace model download issues on Windows (symlinks)

**Process:**
```bash
touch docs/data-quirks/00X-quirk-name.md

# Document:
# - Behavior (what's weird)
# - Why it matters (impact)
# - Root cause (why it happens)
# - Detection (how to find it)
# - Correct patterns (how to handle)
```

### When to Create Integration Document

**Trigger:** Connected external API/service

**Examples:**
- Docling library integration
- OpenAI tiktoken service
- HuggingFace model hub
- External authentication provider
- File storage service

**Process:**
```bash
touch docs/integrations/service-name.md

# Document:
# - Purpose and capabilities
# - Authentication/setup
# - Data format/schema
# - Known quirks and gotchas
# - Error handling patterns
# - Rate limits/quotas
# - Scope boundaries (what it does/doesn't do)
```

---

## Technology Stack Context

### Core Framework
- **FastAPI** (0.115+): ASGI web framework
- **Pydantic** (2.x): Settings and validation
- **Uvicorn**: ASGI server

### Document Processing
- **Docling** (2.57+): Primary document extraction library
  - Handles: PDF, DOCX, PPTX, HTML, MD
  - Uses HuggingFace transformers for layout detection
  - Model: `ds4sd/docling-layout-heron`
- **pypdfium2**: PDF rendering backend
- **tiktoken**: OpenAI token counting

### Authentication
- **PyJWT**: JWT token handling
- Custom API key validation
- Optional: Can be disabled for local dev

### Infrastructure
- **Prometheus**: Metrics collection
- **Docker**: Containerization
- **Poetry**: Dependency management

---

## Common Patterns in This Codebase

### Dependency Injection Pattern
```python
# 1. Store singleton in app.state during startup
@app.on_event("startup")
async def on_startup():
    app.state.document_processor = DoclingDocumentProcessor(...)

# 2. Retrieve via dependency function
def get_document_processor(request: Request) -> DocumentProcessor:
    return request.app.state.document_processor

# 3. Inject into use case
def get_use_case(processor = Depends(get_document_processor)):
    return ProcessDocumentUseCase(processor)

# 4. Use in route
@router.post("/upload")
async def upload(use_case = Depends(get_use_case)):
    return await use_case.execute(...)
```

### Clean Architecture Layer Boundaries
```python
# ✅ CORRECT: Use case depends on port interface
class ProcessDocumentUseCase:
    def __init__(self, document_processor: DocumentProcessor):
        self.processor = document_processor  # Port, not adapter

# ❌ WRONG: Use case depends on concrete adapter
class ProcessDocumentUseCase:
    def __init__(self, processor: DoclingDocumentProcessor):
        self.processor = processor  # Violates clean architecture
```

### Async Processing Pattern
```python
# All processing is async
async def process_document(self, document: Document) -> Tuple[List[DocumentChunk], str]:
    # Extract
    text, metadata = await self._extract_with_docling(document.file_path)

    # Chunk
    chunks = await self._create_token_chunks(document, text, metadata)

    return chunks, text
```

### Error Handling Pattern
```python
try:
    result = await self.processor.process_document(document)
except InvalidDocumentTypeError as e:
    raise HTTPException(status_code=400, detail=str(e))
except DocumentProcessingError as e:
    raise HTTPException(status_code=500, detail=str(e))
finally:
    # Always cleanup uploaded files
    if file_path.exists():
        file_path.unlink()
```

---

## Known Issues and Gotchas

### 1. Windows Symlink Issues
**Problem:** HuggingFace hub creates symlinks by default, fails on Windows without admin
**Solution:** Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` and pre-download models
**Reference:** `DoclingModelManager` in `docling_document_processor.py`

### 2. Token Count ≠ Character Count
**Problem:** 1 token ≈ 4 characters (rough estimate), varies by content
**Solution:** Always use `token_service.count_tokens()`, don't estimate
**Impact:** Chunking, cost calculation, model limits

### 3. Uploaded Files Must Be Cleaned Up
**Problem:** Files saved to disk during upload aren't auto-deleted
**Solution:** Always use try/finally to delete files after processing
**Reference:** `routes/documents.py:upload_document()`

### 4. ProcessingResult vs Direct Return
**Problem:** Use case creates `ProcessingResult` but route returns raw tuple
**Solution:** Current implementation returns tuple `(chunks, text)` directly
**Note:** May need alignment between use case and route expectations

---

## Development Workflow

### Before Implementing a Feature

1. **Search documentation:**
   ```bash
   grep -r "feature_keyword" docs/
   ```

2. **Check CLAUDE.md** for:
   - Architecture patterns to follow
   - Similar implementations
   - Configuration requirements

3. **Review related code:**
   - Find similar features
   - Check how they handle errors
   - Follow established patterns

### During Implementation

1. **Follow Clean Architecture:**
   - Domain entities have no external deps
   - Use cases depend on port interfaces
   - Adapters implement ports
   - API layer uses dependency injection

2. **Add proper logging:**
   ```python
   self.logger.info(f"Processing document {document.id}")
   self.logger.error(f"Failed to process: {str(e)}")
   ```

3. **Handle errors gracefully:**
   - Domain exceptions for business logic errors
   - HTTP exceptions at API layer
   - Always clean up resources (files, connections)

### After Implementation

1. **Document decisions:**
   - Made architectural choice? → Create ADR
   - Hit a gotcha? → Document in failures or data-quirks
   - Integrated external service? → Create integration doc

2. **Update CLAUDE.md if needed:**
   - Added new pattern?
   - Changed workflow?
   - New configuration option?

---

## Testing Patterns

### Running Tests
```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=app

# Specific test
poetry run pytest tests/unit/test_processor.py::test_name
```

### Test File Location
```
tests/
├── unit/              # Unit tests (domain, use cases)
├── integration/       # Integration tests (adapters, API)
└── file_samples/      # Sample documents for testing
```

### Manual Testing
```bash
# Start server
poetry run uvicorn app.main:app --reload

# Test upload (see tests/document-upload.py for full example)
curl -X POST http://localhost:8000/documents/upload \
  -H "X-API-Key: your-key" \
  -F "file=@test.pdf"
```

---

## Environment Configuration

### Local Development
```env
DISABLE_AUTH=true
DEBUG=true
LOG_LEVEL=DEBUG
UPLOADS_DIR=data/uploads
```

### Production
```env
DISABLE_AUTH=false
AUTH_METHOD=api_key
AUTH_API_KEY=sk-generated-key
DEBUG=false
LOG_LEVEL=INFO
UPLOADS_DIR=/app/data/uploads
```

### Key Generation
```bash
# Windows
.\generate_keys.ps1 -Both

# Linux/macOS
./generate_keys.sh --both
```

---

## Quick Reference: File Locations

- **Main app:** `app/main.py`
- **Config:** `app/config.py`
- **Routes:** `app/api/routes/`
- **Use cases:** `app/core/use_cases/`
- **Domain entities:** `app/core/domain/entities/`
- **Ports (interfaces):** `app/core/ports/`
- **Adapters (implementations):** `app/adapters/`
- **Current processor:** `app/adapters/document_processor/docling_document_processor.py`

---

## 🔄 After You're Done - Auto-Compounding Checklist

### Before Committing (MANDATORY CHECKS)

**Code Quality:**
- [ ] Searched docs/ for related decisions/failures
- [ ] Followed Clean Architecture patterns
- [ ] Added proper error handling
- [ ] Cleaned up resources (files, connections)
- [ ] Added logging for debugging
- [ ] Tested manually or with pytest

**Knowledge Compounding (AUTO-DOCUMENT):**
- [ ] **Made architectural decision?** → Created ADR
- [ ] **Discovered data quirk?** → Documented it
- [ ] **Hit error/mistake (>1 hour)?** → Created failure log
- [ ] **Integrated external service?** → Created integration doc
- [ ] **Changed workflows?** → Updated CLAUDE.md

**If you answered YES to any "Knowledge Compounding" item but DIDN'T create documentation:**
⚠️ **STOP. Go back and document it now.**

---

## 🎯 Your Goal as AI Agent

**Success criteria:**
1. ✅ Code works correctly
2. ✅ Tests pass
3. ✅ **Knowledge documented for next developer/agent**

**Questions to ask yourself:**

**Before implementing:**
- "Has someone tried this before?" → Check `docs/failures/`
- "Why was it done this way?" → Check `docs/decisions/`
- "What are the gotchas?" → Check `docs/data-quirks/`
- "Is there an existing integration?" → Check `docs/integrations/`

**After implementing:**
- "Would this decision help future developers?" → **Create ADR**
- "Did I waste time on something avoidable?" → **Create failure log**
- "Did I discover something non-obvious?" → **Create data-quirk doc**
- "Did I integrate an external system?" → **Create integration doc**

**Remember:** Every documented decision/failure saves 5-10 hours of future work.

---

## 🧪 Self-Test: Are You Auto-Compounding?

**Scenario 1:** You chose Pydantic over attrs for validation.
- ❌ Wrong: Just implement and move on
- ✅ Right: Create ADR-00X documenting why Pydantic (pros/cons, alternatives rejected)

**Scenario 2:** You assumed document types were lowercase, but found mixed case.
- ❌ Wrong: Fix it and continue
- ✅ Right: Document in data-quirks (behavior, detection, correct pattern)

**Scenario 3:** You tried semantic chunking but quality was poor.
- ❌ Wrong: Switch to token-based and forget about it
- ✅ Right: Create failure log (what happened, why, lessons, prevention)

**Scenario 4:** You integrated Stripe payment API.
- ❌ Wrong: Just write the code
- ✅ Right: Create integration doc (auth, schema, quirks, error handling)

**If you're doing the ✅ Right actions automatically, you're successfully compounding!**
