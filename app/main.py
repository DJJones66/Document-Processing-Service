import os
import logging
import asyncio
import uvicorn
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
# Import our middleware
from fastapi.middleware.cors import CORSMiddleware
from .infrastructure.multipart_limit_middleware import MultipartLimitMiddleware
from .infrastructure.logging import setup_logging, RequestLoggingMiddleware
from .infrastructure.metrics import PrometheusMiddleware, metrics_endpoint
from .config import settings
# Import adapter classes
from .adapters.token_service.tiktoken_service import TikTokenService
# from .adapters.document_processor.simple_spacy_layout import SimpleSpacyLayoutProcessor
from .adapters.document_processor.docling_document_processor import DoclingDocumentProcessor
from .adapters.auth_service.simple_auth_service import SimpleAuthService
# Imports for routers
from .api.routes.documents import router as documents_router

app = FastAPI(
    title="BrainDrive Document Processing AI",
    description="Standalone document processing service for BrainDrive",
    version="0.1.0",
    debug=settings.DEBUG
)

# Setup logging early
setup_logging()
logger = logging.getLogger(__name__)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

def build_cors_config():
    """Build CORS settings; default is wide open for local testing."""
    allow_any = os.getenv("CORS_ALLOW_ANY", "1").lower() in ("1", "true", "yes", "on")
    if allow_any:
        # Reflect any origin (no hardcoded hosts) while allowing credentials
        return [], ".*", True

    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3034",
        "http://localhost:5273",
        "http://127.0.0.1:5273",
        "http://10.1.2.149:5273",
    ]

    env_origins = os.getenv("CORS_ORIGINS")
    if env_origins:
        default_origins.extend(
            [origin.strip() for origin in env_origins.split(",") if origin.strip()]
        )

    origin_regex = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"https?://(localhost|127\\.0\\.0\\.1|10\\.\d+\\.\d+\\.\d+|192\\.168\\.\d+\\.\d+|172\\.(1[6-9]|2\\d|3[0-1])\\.\d+\\.\d+)(:\\d+)?$",
    )

    allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in ("1", "true", "yes", "on")

    unique_origins = list(dict.fromkeys(default_origins))
    return unique_origins, origin_regex, allow_credentials

# CORS (if frontend served separately)
cors_origins, cors_origin_regex, cors_allow_credentials = build_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud Run"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "BrainDrive Document AI",
            "version": "0.1.0"
        }
    )

# Include metrics endpoint
@app.get("/metrics")
async def metrics():
    return await metrics_endpoint()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "BrainDrive Document Processing AI",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "upload": "/documents/upload"
        }
    }

# On startup, instantiate and store singleton adapter instances in app.state
@app.on_event("startup")
async def on_startup():
    logger.info("Application startup: instantiating adapters...")
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    
    try:
        # Auth service
        app.state.auth_service = SimpleAuthService(
            api_key=settings.auth_api_key.get_secret_value(),
            jwt_secret=settings.jwt_secret.get_secret_value(),
        )
        # Token service
        token_service = TikTokenService()
        
        # Document processor - this will fail fast if spaCy model is not available
        # app.state.document_processor = SimpleSpacyLayoutProcessor(
        #     spacy_model=settings.spacy_model,
        #     token_service=token_service,
        # )
        app.state.document_processor = DoclingDocumentProcessor(
            token_service=token_service,
        )
        
        logger.info("Startup complete: adapters instantiated successfully")
    except Exception as e:
        logger.error(f"Failed to initialize adapters: {e}")
        raise  # This will prevent the application from starting

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown: closing resources...")
    logger.info("Shutdown complete.")

app.include_router(
    documents_router,
    prefix="/documents",
    tags=["documents"]
)
