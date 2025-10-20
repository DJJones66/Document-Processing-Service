# syntax=docker/dockerfile:1.7-labs
# =======================
# Stage 1 - Builder
# =======================
FROM python:3.12-slim AS builder

ARG ENABLE_CUDA=false
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies required for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy only the dependency descriptors first (cache friendly)
COPY pyproject.toml poetry.lock* /app/

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install packages (use BuildKit cache mounts so subsequent builds are fast)
# This layer will be reused as long as pyproject/poetry.lock don't change.
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    if [ "$ENABLE_CUDA" = "true" ]; then \
        echo "Installing with CUDA support..."; \
        poetry install --without dev --no-interaction --no-ansi --no-root; \
    else \
        echo "Installing CPU-only packages..."; \
        # install declared dependencies
        poetry install --without dev --no-interaction --no-ansi --no-root; \
        # replace torch with CPU wheel (if on amd64), keep torch separate to avoid invalidation
        pip uninstall -y torch torchvision || true; \
        if [ "$TARGETARCH" = "amd64" ]; then \
            pip install --no-cache-dir \
                torch==2.7.1+cpu \
                torchvision==0.22.1+cpu \
                --index-url https://download.pytorch.org/whl/cpu; \
        else \
            pip install --no-cache-dir torch torchvision; \
        fi \
    fi

# Remove tests/caches from site-packages to reduce image size
RUN find /usr/local/lib/python3.12 -type d \( -name "tests" -o -name "test" -o -name "__pycache__" \) -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.12 -type f -name "*.pyc" -delete

# =======================
# Stage 2 - Runtime
# =======================
FROM python:3.12-slim AS runtime

ARG ENABLE_CUDA=false
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    ENABLE_CUDA=${ENABLE_CUDA}

WORKDIR /app

# Install small runtime system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages and runtime binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application source last so code changes do not bust earlier caches
COPY . /app

# Create runtime directories
RUN mkdir -p /app/data/uploads /app/data/temp /app/logs

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
