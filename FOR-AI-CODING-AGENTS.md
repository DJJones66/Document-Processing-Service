# FOR-AI-CODING-AGENTS.md

This file provides guidance to AI coding agents (Claude Code, GitHub Copilot, Cursor, Codeium, etc.) when working with code in this repository.

## Project Overview

BrainDrive Document AI is a standalone document processing API service built with FastAPI, following Clean Architecture principles. It processes documents (PDF, DOCX, DOC, PPTX, HTML, MD) and returns structured chunks with metadata using Docling for extraction and token-based chunking.

## Development Commands

### Installation (Python 3.11, venv)
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Running the Service
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or using the port from config (default 8000)
uvicorn app.main:app --reload
```

### Testing
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test types
python -m pytest tests/unit/
python -m pytest tests/integration/
```

### Docker
```bash
# Build image
docker build -t braindrive-document-ai .

# Run with Docker Compose
docker-compose up

# Production deployment
docker-compose -f docker-compose.prod.yml up
```

### Authentication Key Generation
```bash
# Windows (PowerShell)
.\generate_keys.ps1 -Both

# Linux/macOS
chmod +x generate_keys.sh
./generate_keys.sh --both
```

## Clean Architecture Structure

The project strictly follows Clean Architecture with clear separation of concerns:

### Core Domain Layer (`app/core/domain/`)
- **Entities**: Core business objects (Document, DocumentChunk, ProcessingResult, User, StructuredElement)
- **Value Objects**: Immutable types (ChunkMetadata, ProcessingStatus, DocumentType)
- **Exceptions**: Domain-specific errors (DocumentProcessingError, InvalidDocumentTypeError, AuthenticationError)
- No external dependencies - pure business logic

### Ports Layer (`app/core/ports/`)
Defines interfaces/contracts that external services must implement:
- `DocumentProcessor`: Contract for document processing implementations
- `TokenService`: Interface for token counting services
- `ChunkingStrategy`: Interface for different chunking approaches
- `AuthService`: Interface for authentication services
- `StorageService`: Interface for storage operations

### Use Cases Layer (`app/core/use_cases/`)
Application-specific business rules coordinating domain entities and ports:
- `ProcessDocumentUseCase`: Orchestrates document processing workflow
- `AuthenticateUserUseCase`: Handles authentication flow
- `ValidateDocumentUseCase`: Document validation logic
- `GetProcessingStatusUseCase`: Status retrieval logic

### Adapters Layer (`app/adapters/`)
Concrete implementations of port interfaces:
- **Document Processors**:
  - `DoclingDocumentProcessor`: Primary processor using Docling library (supports PDF, DOCX, PPTX, HTML, MD)
  - `SimpleSpacyLayoutProcessor`: Legacy spaCy-based processor (commented out in main.py)
  - `TextOnlyProcessor`: Fallback for plain text
- **Token Service**: `TikTokenService` - OpenAI tiktoken-based token counting
- **Auth Service**: `SimpleAuthService` - API key and JWT authentication
- **Chunking Strategies**: Multiple strategies in `adapters/document_processor/chunking_strategies/`
  - Hierarchical, Semantic, Token-based, Adaptive, Fixed-size, Recursive

### API Layer (`app/api/`)
- **Routes**: FastAPI endpoint definitions (`routes/documents.py`)
- **Dependencies**: Dependency injection setup (`deps.py`)
  - `get_document_processor()`: Retrieves processor from app.state
  - `get_document_processing_use_case()`: Creates use case with dependencies
  - `authenticate_user()`: Authentication middleware using header-based auth (X-API-Key or Bearer token)

### Infrastructure Layer (`app/infrastructure/`)
Cross-cutting concerns:
- `logging.py`: Structured JSON logging with RequestLoggingMiddleware
- `metrics.py`: Prometheus metrics with PrometheusMiddleware
- `multipart_limit_middleware.py`: File upload size enforcement

## Key Configuration

Settings are managed through Pydantic in `app/config.py`:
- Loaded from `.env` file (use `.env.local` for dev, `.env.production` for prod)
- Authentication: `DISABLE_AUTH`, `AUTH_METHOD` (api_key/jwt/disabled), `AUTH_API_KEY`, `JWT_SECRET`
- Document processing: `DEFAULT_CHUNKING_STRATEGY`, `DEFAULT_CHUNK_SIZE`, `DEFAULT_CHUNK_OVERLAP`
- Supported types: `SUPPORTED_DOCUMENT_TYPES` = ["pdf", "docx", "doc", "pptx", "html", "md"]
- Docling model: `DOCLING_MODEL_NAME` (default: "ds4sd/docling-layout-heron")
- File limits: `UPLOAD_MAX_FILE_SIZE`, `UPLOAD_MAX_PART_SIZE`

## Application Lifecycle

### Startup (`app/main.py:on_startup()`)
1. Creates upload directory (`settings.UPLOADS_DIR`)
2. Instantiates singleton adapters stored in `app.state`:
   - `app.state.auth_service` = SimpleAuthService
   - `app.state.document_processor` = DoclingDocumentProcessor
3. Initializes TikTokenService passed to document processor
4. Pre-downloads Docling models (configurable via `preload_models` parameter)

### Request Flow
1. **Authentication**: `authenticate_user()` dependency checks X-API-Key or Bearer token
   - Skipped if `DISABLE_AUTH=true`
   - Uses `AuthenticateUserUseCase` with `SimpleAuthService`
2. **Upload**: File saved to `UPLOADS_DIR` with UUID filename
3. **Processing**:
   - `ProcessDocumentUseCase` calls `document_processor.process_document()`
   - DoclingDocumentProcessor extracts text via Docling and creates token-based chunks
   - Returns tuple of `(List[DocumentChunk], complete_text)`
4. **Cleanup**: Uploaded file deleted after processing (success or failure)
5. **Response**: Returns chunks with metadata directly (note: current implementation in routes/documents.py returns raw result, not wrapped in ProcessingResult)

## Document Processing Pipeline

The `DoclingDocumentProcessor` implements this workflow:

1. **Validation**: Check document type against `SUPPORTED_DOCUMENT_TYPES`
2. **Extraction**: Use Docling's `DocumentConverter` to extract text as markdown
   - Configurable OCR, table extraction, image extraction
   - Pipeline options in `PdfPipelineOptions`
   - Uses `PyPdfiumDocumentBackend` for PDF rendering
3. **Chunking**: Recursive token-based splitting
   - Split by paragraphs (`\n\n`) first
   - If paragraphs too large, split by sentences (regex: `(?<=[.!?])\s+`)
   - If sentences too large, split by words
   - Apply overlap between chunks (`chunk_overlap` tokens)
4. **Metadata**: Each chunk includes:
   - `document_filename`, `document_type`
   - `chunk_token_count`, `chunk_char_count`
   - `processing_method`, `page_count`, `has_tables`, `has_images`

## Important Implementation Details

### Docling Model Management
- `DoclingModelManager` pre-downloads Hugging Face models to avoid runtime errors
- Windows symlink handling: Sets `HF_HUB_DISABLE_SYMLINKS_WARNING=1` and `HF_HUB_DISABLE_SYMLINKS=True`
- Models cached in `HF_HOME` (set to `/app/.cache/huggingface` in Dockerfile)

### Token Counting
- Uses OpenAI's tiktoken library (`TikTokenService`)
- Token counts drive chunking decisions (target: `chunk_size` tokens, overlap: `chunk_overlap` tokens)
- Rough conversion: 1 token ≈ 4 characters (used in fallback character splitting)

### Authentication
- Two methods: API Key (via `X-API-Key` header) or JWT (via `Authorization: Bearer` header)
- Credentials validated by `SimpleAuthService` against environment variables
- Can be fully disabled with `DISABLE_AUTH=true` for local development
- Endpoints `/health`, `/metrics`, `/docs` are always unauthenticated

### Dependency Injection
- Singleton adapters stored in `app.state` during startup
- Retrieved via FastAPI `Depends()` in route handlers
- Use cases instantiated per-request with injected adapters
- Pattern: `get_X_use_case(adapter=Depends(get_adapter))` → `ProcessXUseCase(adapter)`

## Docker Build Optimization

The Dockerfile uses a multi-layer strategy to maximize cache hits:
1. Core web framework (FastAPI, Uvicorn, Pydantic)
2. HTTP/networking libraries
3. CLI utilities and metrics
4. Data processing (pandas, numpy)
5. PyTorch CPU-only
6. ML/NLP (transformers, huggingface-hub, tiktoken)
7. Docling ecosystem
8. Document format handlers (pypdfium2, python-docx, python-pptx)
9. Image processing and OCR
10. Text/markup processing
11. JSON/schema handling
12. Math/scientific computing
13. Geometry/spatial processing
14. Multiprocessing utilities
15. Remaining dependencies

Application code copied last (changes most frequently).

## Common Patterns

### Adding a New Document Processor
1. Create class in `app/adapters/document_processor/` implementing `DocumentProcessor` port
2. Implement `async def process_document(document: Document) -> Tuple[List[DocumentChunk], str]`
3. Register in `app/main.py:on_startup()` by assigning to `app.state.document_processor`

### Adding a New Chunking Strategy
1. Create class in `app/adapters/document_processor/chunking_strategies/` implementing `ChunkingStrategy` port
2. Implement `async def chunk_text(text: str, metadata: Dict) -> List[DocumentChunk]`
3. Use factory pattern in `make_chunking_strategy.py` if needed

### Adding a New File Type
1. Add extension to `SUPPORTED_DOCUMENT_TYPES` in `config.py`
2. Add mapping in `DocumentType.FILENAME_MAP` value object
3. Ensure Docling supports the format (it handles PDF, DOCX, PPTX, HTML, MD natively)
4. Test extraction and chunking with sample files

### Testing

#### Test Structure
```
tests/
├── document-upload.py      # Manual API test client with authentication
├── document-upload.http    # HTTP test file for REST clients
└── file_samples/           # Sample documents for testing
```

#### Running Tests

**Note:** This project currently uses manual integration tests. Formal pytest unit/integration tests to be added.

**Manual API testing:**
```bash
# Using Python test client
python tests/document-upload.py

# Or using HTTP file (in VS Code with REST Client extension)
# Open tests/document-upload.http and click "Send Request"
```

**API smoke test:**
```bash
# Health check
curl http://localhost:8000/health

# Document upload (requires service running)
curl -X POST http://localhost:8000/documents/upload \
  -H "X-API-Key: your-key" \
  -F "file=@tests/file_samples/sample.pdf"
```

#### Test Samples
Sample test files available in `tests/file_samples/` for verifying document processing:
- PDF documents
- DOCX documents
- PPTX presentations
- HTML files
- Markdown files

## Environment Setup

For local development:
1. Copy `.env.local` to `.env`
2. Run `.\generate_keys.ps1 -Both` (Windows) or `./generate_keys.sh --both` (Linux/macOS)
3. Set `DISABLE_AUTH=true` to skip authentication during development
4. Ensure uploads directory exists: `mkdir -p data/uploads`

For production:
1. Copy `.env.production` to `.env`
2. Generate secure keys with key generation scripts
3. Set `DISABLE_AUTH=false` and `AUTH_METHOD=api_key`
4. Configure `UPLOADS_DIR` to appropriate path (e.g., `/app/data/uploads` in Docker)
5. Adjust `MAX_CONCURRENT_PROCESSES` and `PROCESSING_TIMEOUT` for your environment

## Compounding Engineering

This project uses **Compounding Engineering** - a documentation philosophy where every development session leaves behind structured knowledge for future developers and AI agents.

### 🤖 For AI Agents: AUTO-COMPOUND KNOWLEDGE

**Your mission:** Don't just write code - **leave knowledge** for the next developer/agent.

### Auto-Documentation Triggers

**When to create documents:**

#### 1. Architecture Decision Record (ADR)
**Triggers:**
- Chose between 2+ implementation approaches
- Selected a library/framework
- Decided on data structure or pattern
- Changed core architecture

**Action:**
```bash
cp docs/decisions/000-template.md docs/decisions/00X-decision-name.md
# Fill: Context, Problem, Decision, Consequences, Alternatives
```

**Examples:**
- ✅ Chose Docling over spaCy → Created ADR-001
- ✅ Selected JWT over sessions → Create ADR
- ✅ Picked PostgreSQL over MongoDB → Create ADR

#### 2. Failure Log
**Triggers:**
- Assumed something that was wrong
- Built feature that didn't work
- Used wrong approach (later fixed)
- Wasted significant development time (>1 hour)

**Action:**
```bash
touch docs/failures/00X-failure-name.md
# Document: What happened, Root cause, Impact, Lessons, Prevention
```

**Examples:**
- ✅ Tried fuzzy name matching, got 15% errors → Document failure
- ✅ Assumed API returns UTC, actually local time → Document failure
- ✅ Used synchronous processing, caused timeout → Document failure

#### 3. Data Quirk
**Triggers:**
- Non-obvious data behavior
- Data format different than expected
- Field has NULL/invalid values
- Retention policies (purge, archival)
- Timezone/format inconsistencies

**Action:**
```bash
touch docs/data-quirks/00X-quirk-name.md
# Document: Behavior, Why it matters, Detection, Correct patterns
```

**Examples:**
- ✅ Windows HuggingFace symlinks fail → Created Data-Quirk-001
- ✅ Table purges nightly → Document quirk
- ✅ API returns mixed timezones → Document quirk

#### 4. Integration Doc
**Triggers:**
- Connected to new API/service
- Vendor-specific quirks discovered
- Authentication/authorization setup
- Scope boundaries defined

**Action:**
```bash
touch docs/integrations/service-name.md
# Document: Purpose, Auth, Schema, Quirks, Error handling
```

**Examples:**
- ✅ Integrated Docling → Created docs/integrations/docling.md
- ✅ Added Stripe payments → Create integration doc
- ✅ Connected to external API → Create integration doc

### Before Writing Code (MANDATORY)

**Step 1: Search existing knowledge**
```bash
grep -r "keyword" docs/decisions/   # Past architectural choices
grep -r "keyword" docs/failures/    # Known mistakes to avoid
grep -r "keyword" docs/data-quirks/ # Known gotchas
ls docs/integrations/               # External service docs
```

**Step 2: Ask user if uncertain**
- ✅ ASK the user before building
- ❌ DON'T assume and waste time

### After You're Done (AUTO-COMPOUND)

**Before committing, check:**
1. Did you make an architectural decision? → **Create ADR**
2. Did you discover data quirk? → **Document it**
3. Did you hit an error/mistake? → **Create failure log**
4. Did you integrate external service? → **Create integration doc**
5. Did you learn something non-obvious? → **Document it**

### Current Documentation

- **ADR-001:** Use Docling for multi-format document processing
- **Data-Quirk-001:** Windows HuggingFace symlink issues
- **Integration:** Docling library documentation

### Philosophy

> Every documented decision/failure saves 5-10 hours of future work.

**Your goal:** Six months from now, someone (human or AI) will work on this. Leave them knowledge to avoid your mistakes and build on your success.

**See:** `docs/AI-AGENT-GUIDE.md` for complete guidelines and self-test scenarios.
