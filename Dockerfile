# ---- Base image ----
FROM python:3.11-slim-bookworm

# Avoid interactive prompts & speed up builds
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OMP_NUM_THREADS=4 \
    HF_HOME=/app/.cache/huggingface \
    TORCH_HOME=/app/.cache/torch \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Set working directory
WORKDIR /app

# ---- System dependencies ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        curl \
        gcc \
        g++ && \
    rm -rf /var/lib/apt/lists/*

# ---- Layer 1: Core web framework dependencies (most stable) ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    fastapi \
    fastapi-cli==0.0.13 \
    uvicorn[standard]==0.38.0 \
    starlette==0.48.0 \
    pydantic==2.12.3 \
    pydantic_core==2.41.4 \
    pydantic-settings==2.11.0 \
    python-dotenv==1.1.1 \
    python-multipart==0.0.20 \
    email-validator==2.3.0

# ---- Layer 2: HTTP and networking ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    httpx==0.28.1 \
    httpcore==1.0.9 \
    httptools==0.6.4 \
    h11==0.16.0 \
    h2==4.3.0 \
    hpack==4.1.0 \
    hyperframe==6.1.0 \
    requests \
    dnspython==2.8.0 \
    certifi==2025.6.15 \
    urllib3==2.5.0 \
    Brotli==1.1.0 \
    PySocks==1.7.1

# ---- Layer 3: Core utilities and CLI ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    click==8.2.1 \
    typer==0.19.2 \
    typer-slim==0.20.0 \
    rich==14.2.0 \
    rich-toolkit==0.15.1 \
    colorlog==6.10.1 \
    prometheus_client==0.22.1 \
    watchfiles==1.1.1 \
    websockets==15.0.1

# ---- Layer 4: Data processing libraries ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    pandas==2.3.0 \
    numpy==2.2.6 \
    scipy==1.16.2 \
    psutil==7.1.1 \
    tqdm==4.67.1

# ---- Layer 5: PyTorch (CPU-only, large but stable) ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    torch==2.9.0 \
    torchvision==0.24.0 \
    --extra-index-url https://download.pytorch.org/whl/cpu

# ---- Layer 6: ML/NLP core dependencies ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    transformers==4.57.1 \
    tokenizers==0.22.1 \
    huggingface-hub==0.35.3 \
    accelerate==1.11.0 \
    safetensors==0.6.2 \
    tiktoken==0.12.0

# ---- Layer 7: Document processing (docling ecosystem) ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    docling==2.57.0 \
    docling-core==2.49.0 \
    docling-ibm-models==3.10.0 \
    docling-parse==4.7.0

# ---- Layer 8: Document format handlers ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    pypdfium2==4.30.0 \
    python-docx==1.2.0 \
    python-pptx==1.0.2 \
    openpyxl==3.1.5 \
    xlsxwriter==3.2.9 \
    et_xmlfile==2.0.0

# ---- Layer 9: Image processing and OCR ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    opencv-python==4.12.0.88 \
    pillow==11.3.0 \
    rapidocr==3.4.2

# ---- Layer 10: Text and markup processing ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    beautifulsoup4==4.14.2 \
    soupsieve==2.8 \
    lxml==5.4.0 \
    markdown-it-py==3.0.0 \
    marko==2.2.1 \
    Jinja2==3.1.6 \
    MarkupSafe==3.0.2 \
    Pygments==2.19.2 \
    mdurl==0.1.2

# ---- Layer 11: JSON and schema handling ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    jsonlines==4.0.0 \
    jsonref==1.1.0 \
    jsonschema==4.25.1 \
    jsonschema-specifications==2025.9.1 \
    referencing==0.37.0 \
    rpds-py==0.27.1

# ---- Layer 12: Math and scientific computing ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    sympy==1.14.0 \
    mpmath==1.3.0 \
    latex2mathml==3.78.1 \
    pylatexenc==2.10

# ---- Layer 13: Geometry and spatial processing ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    shapely==2.1.2 \
    pyclipper==1.3.0.post6 \
    rtree==1.4.1 \
    networkx==3.5

# ---- Layer 14: Multiprocessing and utilities ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    mpire==2.10.2 \
    multiprocess==0.70.18 \
    dill==0.4.0

# ---- Layer 15: Remaining dependencies ----
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    PyYAML==6.0.3 \
    omegaconf==2.3.0 \
    semchunk==2.2.2 \
    Faker==37.11.0 \
    PyJWT==2.10.1 \
    python-dateutil==2.9.0.post0 \
    pytz==2025.2 \
    tzdata==2025.2 \
    regex==2025.10.23 \
    tabulate==0.9.0 \
    filetype==1.2.0 \
    fsspec==2025.9.0 \
    filelock==3.20.0 \
    packaging==25.0 \
    attrs==25.4.0 \
    annotated-types==0.7.0 \
    typing_extensions==4.15.0 \
    typing-inspection==0.4.2 \
    anyio==4.9.0 \
    sniffio==1.3.1 \
    idna==3.10 \
    charset-normalizer==3.4.2 \
    colorama==0.4.6 \
    six==1.17.0 \
    shellingham==1.5.4 \
    setuptools==80.9.0 \
    wheel==0.45.1 \
    zstandard==0.25.0 \
    antlr4-python3-runtime==4.9.3 \
    polyfactory==2.22.3 \
    pluggy==1.6.0 \
    exceptiongroup==1.3.0 \
    cffi==2.0.0 \
    pycparser

# ---- Copy application code (last, changes most frequently) ----
COPY . .

# ---- Create necessary directories and set permissions ----
RUN mkdir -p /app/data /app/logs /app/.cache && \
    chmod -R 755 /app/data /app/logs /app/.cache

# ---- Expose and healthcheck ----
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# ---- Run server ----
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
