# BrainDrive Document AI - Owner's Manual

**Version:** 0.1.0
**Last Updated:** 2024-11-14
**Audience:** Project owners, maintainers, team leads

---

## 📖 Table of Contents

1. [What This Service Does](#what-this-service-does)
2. [Quick Start Guide](#quick-start-guide)
3. [Architecture Overview](#architecture-overview)
4. [Day-to-Day Operations](#day-to-day-operations)
5. [Configuration Management](#configuration-management)
6. [Deployment Guide](#deployment-guide)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance Tasks](#maintenance-tasks)
10. [Security Considerations](#security-considerations)
11. [Scaling Guidelines](#scaling-guidelines)
12. [Cost Optimization](#cost-optimization)
13. [Knowledge Management](#knowledge-management)
14. [Team Onboarding](#team-onboarding)
15. [Disaster Recovery](#disaster-recovery)
16. [Support & Resources](#support--resources)

---

## What This Service Does

### Purpose

BrainDrive Document AI is a **standalone document processing API service** that:
- Accepts document uploads (PDF, DOCX, PPTX, HTML, MD)
- Extracts text while preserving document structure
- Chunks content into token-based segments
- Returns structured data ready for RAG/LLM applications

### Key Features

✅ **Multi-format support:** PDF, DOCX, DOC, PPTX, HTML, MD
✅ **Layout-aware extraction:** Preserves headings, tables, lists
✅ **Token-based chunking:** Configurable chunk sizes with overlap
✅ **Built-in authentication:** API key and JWT support
✅ **Production-ready:** Docker, Prometheus metrics, structured logging
✅ **Clean Architecture:** Easy to extend and maintain

### What It's NOT

❌ Not a full RAG system (no vector storage or retrieval)
❌ Not a document storage service (files deleted after processing)
❌ Not a document converter (output is text chunks, not files)
❌ Not a general-purpose ML service (specialized for document processing)

---

## Quick Start Guide

### For Local Development

```bash
# 1. Clone repository
git clone https://github.com/BrainDriveAI/Document-Processing-Service.git
cd Document-Processing-Service

# 2. Install dependencies
poetry install

# 3. Configure environment
cp .env.local .env
# Edit .env: Set DISABLE_AUTH=true for local dev

# 4. Generate keys (optional, for testing auth)
.\generate_keys.ps1 -Both  # Windows
./generate_keys.sh --both  # Linux/macOS

# 5. Run service
poetry run uvicorn app.main:app --reload --port 8000

# 6. Test
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.pdf"
```

**Access points:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### For Production Deployment

```bash
# 1. Configure production environment
cp .env.production .env
# Edit .env with production values

# 2. Generate secure keys
.\generate_keys.ps1 -Both -Length 128

# 3. Build Docker image
docker build -t braindrive-document-ai:latest .

# 4. Run container
docker run -d \
  --name braindrive-doc-ai \
  -p 8080:8080 \
  --env-file .env \
  -v /data/uploads:/app/data/uploads \
  braindrive-document-ai:latest

# 5. Verify health
curl http://localhost:8080/health
```

**See:** [Deployment Guide](#deployment-guide) for detailed production setup.

---

## Architecture Overview

### High-Level Design

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP POST /documents/upload
       ↓
┌─────────────────────────────────────────┐
│          FastAPI Application            │
├─────────────────────────────────────────┤
│  Middleware Layer                       │
│  - CORS                                 │
│  - Authentication (API Key / JWT)      │
│  - Request Logging                     │
│  - Prometheus Metrics                  │
├─────────────────────────────────────────┤
│  API Layer (routes/documents.py)       │
│  - Upload handling                     │
│  - File validation                     │
│  - Response formatting                 │
├─────────────────────────────────────────┤
│  Use Case Layer                         │
│  - ProcessDocumentUseCase              │
│  - AuthenticateUserUseCase             │
├─────────────────────────────────────────┤
│  Adapters Layer                         │
│  - DoclingDocumentProcessor            │
│  - TikTokenService                     │
│  - SimpleAuthService                   │
├─────────────────────────────────────────┤
│  Domain Layer                           │
│  - Document entities                   │
│  - Business logic                      │
│  - Value objects                       │
└─────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  External Dependencies                  │
│  - Docling (document extraction)       │
│  - HuggingFace (ML models)             │
│  - tiktoken (token counting)           │
└─────────────────────────────────────────┘
```

### Technology Stack

**Core Framework:**
- Python 3.12+
- FastAPI 0.115+
- Uvicorn (ASGI server)
- Pydantic (validation & settings)

**Document Processing:**
- Docling 2.57+ (extraction)
- pypdfium2 (PDF rendering)
- tiktoken (token counting)

**Infrastructure:**
- Docker (containerization)
- Prometheus (metrics)
- Poetry (dependency management)

**Key Design Patterns:**
- **Clean Architecture:** Separation of concerns across layers
- **Dependency Injection:** Services injected via FastAPI dependencies
- **Port-Adapter Pattern:** Interfaces define contracts, adapters implement

**See:** `FOR-AI-CODING-AGENTS.md` for detailed architecture documentation.

---

## Day-to-Day Operations

### Starting the Service

**Development:**
```bash
poetry run uvicorn app.main:app --reload --port 8000
```

**Production (Docker):**
```bash
docker-compose up -d
```

**Production (Kubernetes):**
```bash
kubectl apply -f k8s/deployment.yaml
```

### Stopping the Service

**Development:**
- Press `Ctrl+C` in terminal

**Docker:**
```bash
docker-compose down
```

**Kubernetes:**
```bash
kubectl delete -f k8s/deployment.yaml
```

### Checking Service Status

**Health check:**
```bash
curl http://localhost:8080/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "BrainDrive Document AI",
  "version": "0.1.0"
}
```

**Metrics:**
```bash
curl http://localhost:8080/metrics
```

### Processing a Document

**With authentication:**
```bash
curl -X POST http://localhost:8080/documents/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf"
```

**Response format:**
```json
{
  "chunks": [
    {
      "id": "chunk-0",
      "content": "Document text...",
      "metadata": {
        "chunk_index": 0,
        "chunk_token_count": 150,
        "document_type": "pdf"
      }
    }
  ],
  "complete_text": "Full document text..."
}
```

### Viewing Logs

**Docker:**
```bash
docker logs braindrive-doc-ai -f
```

**Local file:**
```bash
tail -f logs/app.log
```

**Kubernetes:**
```bash
kubectl logs -f deployment/braindrive-doc-ai
```

---

## Configuration Management

### Environment Variables

**Location:** `.env` file (never commit to git)

**Templates:**
- `.env.local` - Local development template
- `.env.production` - Production template

### Critical Configuration

#### Authentication (Required in Production)

```env
# Enable/disable authentication
DISABLE_AUTH=false

# Authentication method
AUTH_METHOD=api_key  # Options: api_key, jwt, disabled

# API Key (generate with generate_keys script)
AUTH_API_KEY=sk-your-generated-key-here

# JWT Secret (for JWT auth method)
JWT_SECRET=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

**⚠️ NEVER set `DISABLE_AUTH=true` in production!**

#### Application Settings

```env
# Debug mode (NEVER enable in production)
DEBUG=false

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log

# Server
API_HOST=0.0.0.0
API_PORT=8080
```

#### File Processing

```env
# Upload directory (must be writable)
UPLOADS_DIR=data/uploads

# File size limits
UPLOAD_MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_MAX_PART_SIZE=52428800   # 50MB
```

#### Document Processing

```env
# Docling model
DOCLING_MODEL_NAME=ds4sd/docling-layout-heron

# Chunking strategy
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200

# Performance
MAX_CONCURRENT_PROCESSES=4
PROCESSING_TIMEOUT=300  # 5 minutes
```

### Configuration by Environment

#### Local Development
```env
DISABLE_AUTH=true
DEBUG=true
LOG_LEVEL=DEBUG
UPLOADS_DIR=data/uploads
```

#### Staging
```env
DISABLE_AUTH=false
AUTH_METHOD=api_key
DEBUG=false
LOG_LEVEL=INFO
UPLOADS_DIR=/app/data/uploads
```

#### Production
```env
DISABLE_AUTH=false
AUTH_METHOD=api_key
AUTH_API_KEY=sk-prod-secure-key-here
DEBUG=false
LOG_LEVEL=WARNING
UPLOADS_DIR=/app/data/uploads
MAX_CONCURRENT_PROCESSES=8
PROCESSING_TIMEOUT=180
```

### Generating API Keys

**Windows:**
```powershell
.\generate_keys.ps1 -Both -Length 128
```

**Linux/macOS:**
```bash
./generate_keys.sh --both --length 128
```

**What it does:**
- Generates cryptographically secure API key
- Generates JWT secret
- Updates `.env` file automatically
- Creates backup of existing `.env`

**Manual generation (if scripts unavailable):**
```python
import secrets
api_key = f"sk-{secrets.token_urlsafe(32)}"
jwt_secret = secrets.token_urlsafe(64)
print(f"AUTH_API_KEY={api_key}")
print(f"JWT_SECRET={jwt_secret}")
```

---

## Deployment Guide

### Docker Deployment

#### Building the Image

```bash
# Standard build
docker build -t braindrive-document-ai:latest .

# With cache optimization
docker build --cache-from braindrive-document-ai:latest \
  -t braindrive-document-ai:latest .

# For specific platform
docker build --platform linux/amd64 \
  -t braindrive-document-ai:latest .
```

**Build time:** ~10-15 minutes (first time), ~2-5 minutes (with cache)
**Image size:** ~2GB (includes ML dependencies)

#### Running the Container

**Simple run:**
```bash
docker run -d \
  --name braindrive-doc-ai \
  -p 8080:8080 \
  -e DISABLE_AUTH=false \
  -e AUTH_API_KEY=your-key \
  braindrive-document-ai:latest
```

**With volume mounts:**
```bash
docker run -d \
  --name braindrive-doc-ai \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  braindrive-document-ai:latest
```

**With resource limits:**
```bash
docker run -d \
  --name braindrive-doc-ai \
  -p 8080:8080 \
  --env-file .env \
  --memory=4g \
  --cpus=2 \
  braindrive-document-ai:latest
```

#### Docker Compose

**File:** `docker-compose.yml`

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

**Production compose:** Use `docker-compose.prod.yml` with Nginx, Prometheus, etc.

### Cloud Platform Deployment

#### Google Cloud Run

```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/YOUR-PROJECT/braindrive-document-ai

# 2. Deploy
gcloud run deploy braindrive-document-ai \
  --image gcr.io/YOUR-PROJECT/braindrive-document-ai \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars DISABLE_AUTH=false \
  --set-secrets AUTH_API_KEY=api-key:latest \
  --allow-unauthenticated
```

**Cost estimate:** ~$50-200/month (depends on usage)

#### AWS ECS/Fargate

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name braindrive-document-ai

# 2. Build and push
aws ecr get-login-password | docker login --username AWS --password-stdin YOUR-ECR-URI
docker build -t braindrive-document-ai .
docker tag braindrive-document-ai:latest YOUR-ECR-URI/braindrive-document-ai:latest
docker push YOUR-ECR-URI/braindrive-document-ai:latest

# 3. Create task definition and service (see AWS console or Terraform)
```

#### Azure Container Instances

```bash
# 1. Create container registry
az acr create --resource-group myResourceGroup \
  --name braindrivedocai --sku Basic

# 2. Build and push
az acr build --registry braindrivedocai \
  --image braindrive-document-ai:latest .

# 3. Deploy
az container create \
  --resource-group myResourceGroup \
  --name braindrive-doc-ai \
  --image braindrivedocai.azurecr.io/braindrive-document-ai:latest \
  --cpu 2 --memory 4 \
  --port 8080 \
  --environment-variables \
    DISABLE_AUTH=false \
    AUTH_API_KEY=your-key
```

### Kubernetes Deployment

**Deployment manifest:** `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: braindrive-document-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: braindrive-document-ai
  template:
    metadata:
      labels:
        app: braindrive-document-ai
    spec:
      containers:
      - name: api
        image: braindrive-document-ai:latest
        ports:
        - containerPort: 8080
        env:
        - name: DISABLE_AUTH
          value: "false"
        - name: AUTH_API_KEY
          valueFrom:
            secretKeyRef:
              name: braindrive-secrets
              key: api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Deploy:**
```bash
# Create secret
kubectl create secret generic braindrive-secrets \
  --from-literal=api-key=your-generated-key

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods
kubectl get svc
kubectl logs -f deployment/braindrive-document-ai
```

---

## Monitoring & Health Checks

### Health Check Endpoint

**URL:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "BrainDrive Document AI",
  "version": "0.1.0"
}
```

**Status codes:**
- `200 OK` - Service healthy
- `500 Internal Server Error` - Service unhealthy

**Use for:**
- Load balancer health checks
- Kubernetes liveness/readiness probes
- Uptime monitoring (Pingdom, UptimeRobot, etc.)

### Prometheus Metrics

**URL:** `GET /metrics`

**Available metrics:**
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Currently processing requests
- `python_info` - Python version and implementation
- `process_*` - CPU, memory, file descriptors

**Scrape configuration (prometheus.yml):**
```yaml
scrape_configs:
  - job_name: 'braindrive-document-ai'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: /metrics
```

### Application Logs

**Format:** Structured JSON logging

**Log levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARNING` - Warning messages (not errors, but attention needed)
- `ERROR` - Error messages
- `CRITICAL` - Critical failures

**Example log entry:**
```json
{
  "timestamp": "2024-11-14T19:30:45.123Z",
  "level": "INFO",
  "logger": "app.adapters.document_processor.docling_document_processor",
  "message": "Starting Docling extraction for document abc-123",
  "document_id": "abc-123",
  "request_id": "req-xyz-789"
}
```

**Log locations:**
- **Docker:** `docker logs braindrive-doc-ai`
- **Local:** `logs/app.log`
- **Kubernetes:** `kubectl logs -f pod/braindrive-doc-ai-xxx`

### Key Metrics to Monitor

#### Service Health
- **Uptime:** Should be >99.9%
- **Health check response time:** <100ms
- **Error rate:** <1% of requests

#### Processing Performance
- **Document processing time:** <30s for typical documents (10-50 pages)
- **Request latency (p95):** <35s
- **Request latency (p99):** <60s

#### Resource Usage
- **Memory:** 1-2GB baseline, 3-4GB under load
- **CPU:** 20-30% baseline, 60-80% under load
- **Disk:** Minimal (files deleted after processing)

#### Error Indicators
- **Authentication failures:** Monitor for brute force attempts
- **Document processing failures:** Check for format/size issues
- **Timeout errors:** May indicate documents too large or complex

### Alerting Rules

**Recommended alerts:**

```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate detected"

# Slow processing
- alert: SlowProcessing
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 60
  for: 10m
  annotations:
    summary: "95th percentile latency >60s"

# Service down
- alert: ServiceDown
  expr: up{job="braindrive-document-ai"} == 0
  for: 2m
  annotations:
    summary: "Service is down"

# High memory usage
- alert: HighMemoryUsage
  expr: process_resident_memory_bytes / 1024 / 1024 / 1024 > 3.5
  for: 5m
  annotations:
    summary: "Memory usage >3.5GB"
```

### Monitoring Tools Integration

#### Grafana Dashboard

**Recommended panels:**
1. Request rate (requests/sec)
2. Error rate (%)
3. Latency percentiles (p50, p95, p99)
4. Memory usage
5. CPU usage
6. Active requests

**Dashboard JSON:** See `monitoring/grafana-dashboard.json` (if provided)

#### DataDog

```python
# Add to requirements if using DataDog
# ddtrace>=1.0.0

# In app/main.py:
from ddtrace import patch_all
patch_all()
```

#### New Relic

```bash
# Add to requirements
# newrelic>=8.0.0

# Run with New Relic
NEW_RELIC_CONFIG_FILE=newrelic.ini \
  newrelic-admin run-program uvicorn app.main:app
```

---

## Troubleshooting

### Common Issues

#### Service Won't Start

**Symptom:** Container exits immediately or fails to start

**Possible causes:**
1. **Missing environment variables**
   ```bash
   # Check logs
   docker logs braindrive-doc-ai

   # Solution: Ensure .env file has required variables
   # Minimum required: UPLOADS_DIR
   ```

2. **Port already in use**
   ```bash
   # Check what's using port 8080
   lsof -i :8080

   # Solution: Stop conflicting service or change port
   docker run -p 8081:8080 ...
   ```

3. **Model download failure (Windows)**
   ```bash
   # Error: HuggingFace symlink creation failed

   # Solution: Check Data-Quirk-001 in docs/data-quirks/
   # Set environment variable:
   -e HF_HUB_DISABLE_SYMLINKS_WARNING=1
   ```

4. **Insufficient memory**
   ```bash
   # Error: OOM (Out of Memory)

   # Solution: Increase Docker memory limit
   docker run --memory=4g ...
   ```

#### Authentication Errors

**Symptom:** HTTP 401 Unauthorized

**Possible causes:**
1. **No API key provided**
   ```bash
   # Add header
   curl -H "X-API-Key: your-key" ...
   ```

2. **Wrong API key**
   ```bash
   # Verify key matches AUTH_API_KEY in .env
   docker exec braindrive-doc-ai env | grep AUTH_API_KEY
   ```

3. **Auth disabled in environment**
   ```bash
   # Check DISABLE_AUTH setting
   # Should be false in production
   docker exec braindrive-doc-ai env | grep DISABLE_AUTH
   ```

#### Document Processing Failures

**Symptom:** HTTP 500 or processing timeout

**Possible causes:**
1. **Unsupported file format**
   ```bash
   # Supported: pdf, docx, doc, pptx, html, md
   # Check file extension matches supported types
   ```

2. **File too large**
   ```bash
   # Check file size against UPLOAD_MAX_FILE_SIZE
   # Default: 100MB

   # Solution: Increase limit in .env
   UPLOAD_MAX_FILE_SIZE=209715200  # 200MB
   ```

3. **Corrupted document**
   ```bash
   # Try opening document in native application
   # If it doesn't open, document is corrupted
   ```

4. **Processing timeout**
   ```bash
   # Increase timeout in .env
   PROCESSING_TIMEOUT=600  # 10 minutes
   ```

5. **OCR documents (scanned PDFs)**
   ```bash
   # OCR is disabled by default
   # These documents may fail to extract text

   # Solution: Enable OCR in DoclingDocumentProcessor
   # (requires code change)
   ```

#### Slow Processing

**Symptom:** Requests taking >60s

**Possible causes:**
1. **Large documents**
   ```bash
   # 100+ page PDFs can take 30-60s
   # This is expected behavior

   # Solution: Set appropriate timeout expectations
   ```

2. **First request after startup**
   ```bash
   # First request downloads ML models (~5-10 min)

   # Solution: Enable preload_models=True (default)
   # Models download during startup, not first request
   ```

3. **Resource constraints**
   ```bash
   # Check CPU/memory usage
   docker stats braindrive-doc-ai

   # Solution: Increase resources
   docker run --cpus=4 --memory=8g ...
   ```

4. **Concurrent processing**
   ```bash
   # Multiple simultaneous requests share resources

   # Solution: Increase MAX_CONCURRENT_PROCESSES
   MAX_CONCURRENT_PROCESSES=8
   ```

#### Memory Issues

**Symptom:** OOM errors or container restarts

**Possible causes:**
1. **ML models not released**
   ```bash
   # Memory grows over time

   # Solution: Restart service periodically
   # Or implement memory monitoring + restart
   ```

2. **Too many concurrent requests**
   ```bash
   # Each document uses 1-2GB during processing

   # Solution: Limit concurrent requests
   # Use MAX_CONCURRENT_PROCESSES setting
   ```

3. **Memory leak**
   ```bash
   # Check memory trends over time

   # Solution: Report issue, restart service as workaround
   ```

### Debug Mode

**Enable debug logging:**
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

**⚠️ Never enable in production!** Debug logs contain sensitive information.

**Debug logs show:**
- Request/response bodies
- Detailed error traces
- Document processing steps
- Token counts and chunk details

### Getting Help

1. **Check documentation:**
   - `FOR-AI-CODING-AGENTS.md` - Architecture and patterns
   - `docs/AI-AGENT-GUIDE.md` - Complete guide
   - `docs/decisions/` - Architectural decisions
   - `docs/data-quirks/` - Known issues and workarounds

2. **Check logs:**
   ```bash
   docker logs braindrive-doc-ai --tail 100
   ```

3. **Check metrics:**
   ```bash
   curl http://localhost:8080/metrics
   ```

4. **Search existing issues:**
   - Check GitHub issues for similar problems
   - Check `docs/failures/` for documented mistakes

5. **Create new issue:**
   - Include error logs
   - Include configuration (sanitize secrets!)
   - Include steps to reproduce
   - Include expected vs actual behavior

---

## Maintenance Tasks

### Daily Tasks

**Check service health:**
```bash
curl http://localhost:8080/health
```

**Monitor metrics:**
```bash
# Check Prometheus/Grafana dashboards
# Look for anomalies in request rate, latency, errors
```

**Review error logs:**
```bash
docker logs braindrive-doc-ai --since 24h | grep ERROR
```

### Weekly Tasks

**Review resource usage:**
```bash
docker stats braindrive-doc-ai --no-stream
```

**Check disk usage:**
```bash
# Uploads directory should be empty (files deleted after processing)
du -sh data/uploads/

# If files present, investigate why cleanup failed
```

**Rotate API keys (if policy requires):**
```bash
.\generate_keys.ps1 -ApiKey
# Update clients with new key
# Update environment with new key
# Restart service
```

**Review security logs:**
```bash
# Check for authentication failures
docker logs braindrive-doc-ai | grep "401\|403"
```

### Monthly Tasks

**Update dependencies:**
```bash
# Check for security updates
poetry update

# Test in staging
poetry run pytest

# Deploy to production if tests pass
```

**Review and update documentation:**
```bash
# Check if any ADRs need updates
# Document any new quirks discovered
# Update integration docs if APIs changed
```

**Backup configuration:**
```bash
# Backup .env file (sanitized)
cp .env .env.backup.$(date +%Y%m%d)

# Backup documentation
tar -czf docs-backup-$(date +%Y%m%d).tar.gz docs/
```

**Performance review:**
```bash
# Analyze metrics trends
# Identify bottlenecks
# Plan optimizations
```

### Quarterly Tasks

**Security audit:**
- Review authentication implementation
- Check for dependency vulnerabilities
- Review API key management
- Check CORS configuration
- Review logging (ensure no secrets logged)

**Capacity planning:**
- Analyze growth trends
- Project future resource needs
- Plan scaling strategy
- Evaluate cost optimization opportunities

**Disaster recovery test:**
- Test backup restoration
- Verify recovery procedures
- Update DR documentation
- Train team on recovery process

**Documentation review:**
- Update OWNERS-MANUAL.md (this file)
- Update FOR-AI-CODING-AGENTS.md if architecture changed
- Review and update ADRs if decisions changed
- Archive deprecated documentation

### Yearly Tasks

**Major version upgrades:**
- Plan upgrade to latest FastAPI version
- Evaluate new Python version (3.13+)
- Consider Docling major version upgrade
- Test thoroughly in staging

**Architecture review:**
- Evaluate if Clean Architecture still serving needs
- Consider new patterns or technologies
- Plan refactoring if needed
- Document decisions in ADRs

**Team training:**
- Review onboarding documentation
- Train new team members
- Update team on architecture changes
- Share lessons learned

---

## Security Considerations

### Authentication Best Practices

**API Key Management:**
- ✅ Generate keys with cryptographically secure random generator
- ✅ Use minimum 32-byte keys (256 bits)
- ✅ Rotate keys regularly (quarterly recommended)
- ✅ Store keys in secrets management (AWS Secrets Manager, etc.)
- ❌ Never commit keys to git
- ❌ Never log keys
- ❌ Never send keys in URL parameters

**Environment-Specific Keys:**
```bash
# Development: Can use simple keys
AUTH_API_KEY=sk-dev-test-key

# Staging: Use generated keys
AUTH_API_KEY=sk-staging-abc123...

# Production: Use strong, managed keys
AUTH_API_KEY=sk-prod-[64-char-random-string]
```

**Key Rotation Process:**
1. Generate new key
2. Update secrets manager
3. Deploy new key to environment
4. Notify clients of key change
5. Provide grace period (keep old key valid)
6. Deprecate old key
7. Remove old key after grace period

### Secure Deployment

**Environment Variables:**
```bash
# ✅ Good: Use secrets management
kubectl create secret generic braindrive-secrets \
  --from-literal=api-key=$(cat /secure/location/key.txt)

# ❌ Bad: Hardcode in manifest
env:
- name: AUTH_API_KEY
  value: "sk-hardcoded-key"  # Never do this!
```

**Network Security:**
```yaml
# Use HTTPS in production
# Terminate SSL at load balancer or ingress controller

# Example Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: braindrive-ingress
spec:
  tls:
  - hosts:
    - api.braindrive.example.com
    secretName: tls-secret
  rules:
  - host: api.braindrive.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: braindrive-document-ai
            port:
              number: 8080
```

**CORS Configuration:**
```python
# In production, restrict CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.braindrive.com",
        "https://admin.braindrive.com"
    ],  # NOT ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Data Security

**File Handling:**
- ✅ Files deleted immediately after processing
- ✅ Temporary files stored in secure directory
- ✅ No persistent document storage
- ✅ File size limits enforced
- ❌ Never store uploaded documents long-term
- ❌ Never log document content

**Logging Security:**
```python
# ✅ Good: Sanitized logging
logger.info(f"Processing document {document.id}")

# ❌ Bad: Logging sensitive data
logger.info(f"API key: {api_key}")  # Never do this!
logger.debug(f"Document content: {content}")  # Never do this!
```

**Memory Security:**
- Documents processed in memory
- Memory cleared after processing
- No swap to disk (if possible)

### Dependency Security

**Regular Updates:**
```bash
# Check for vulnerabilities
poetry show --outdated

# Update packages
poetry update

# Or use automated tools
pip install safety
safety check
```

**Pin Versions:**
```toml
# pyproject.toml
[tool.poetry.dependencies]
fastapi = ">=0.115.13,<0.116.0"  # Pin major.minor
docling = ">=2.57.0,<3.0.0"      # Pin major version
```

**Audit Dependencies:**
```bash
# Check for known vulnerabilities
poetry export -f requirements.txt | safety check --stdin
```

### Infrastructure Security

**Docker Security:**
```dockerfile
# ✅ Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# ✅ Minimize attack surface
# Only install required packages

# ✅ Use official base images
FROM python:3.12-slim-bookworm
```

**Kubernetes Security:**
```yaml
# ✅ Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL

# ✅ Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: braindrive-netpol
spec:
  podSelector:
    matchLabels:
      app: braindrive-document-ai
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### Compliance Considerations

**GDPR (if applicable):**
- Documents processed transiently (not stored)
- No personal data retention
- Provide data processing agreement if needed

**HIPAA (if applicable):**
- Ensure documents don't contain PHI
- Or implement additional safeguards (encryption at rest, audit logs, etc.)

**SOC 2 (if applicable):**
- Implement access controls
- Enable audit logging
- Document security procedures
- Regular security reviews

---

## Scaling Guidelines

### Vertical Scaling

**Resource Requirements by Load:**

| Concurrent Requests | CPU  | Memory | Notes                          |
|---------------------|------|--------|--------------------------------|
| 1-2                 | 1    | 2GB    | Minimum viable                 |
| 3-5                 | 2    | 4GB    | Development/small production   |
| 6-10                | 4    | 8GB    | Medium production              |
| 11-20               | 8    | 16GB   | High production                |

**When to scale vertically:**
- CPU usage consistently >80%
- Memory usage consistently >85%
- Request latency increasing
- Single-instance deployment

**How to scale vertically:**

**Docker:**
```bash
docker run \
  --cpus=4 \
  --memory=8g \
  braindrive-document-ai:latest
```

**Kubernetes:**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2"
  limits:
    memory: "8Gi"
    cpu: "4"
```

### Horizontal Scaling

**When to scale horizontally:**
- Need to handle 20+ concurrent requests
- Need high availability (redundancy)
- Vertical scaling reaching limits
- Cost optimization (smaller instances cheaper)

**Load Balancing:**

**Nginx:**
```nginx
upstream braindrive_backend {
    least_conn;  # Use least connections algorithm
    server api1.example.com:8080;
    server api2.example.com:8080;
    server api3.example.com:8080;
}

server {
    listen 80;
    location / {
        proxy_pass http://braindrive_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: braindrive-document-ai
spec:
  replicas: 5  # Multiple instances
  # ... rest of deployment spec

---
apiVersion: v1
kind: Service
metadata:
  name: braindrive-service
spec:
  type: LoadBalancer
  selector:
    app: braindrive-document-ai
  ports:
  - port: 80
    targetPort: 8080
```

**Horizontal Pod Autoscaler (HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: braindrive-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: braindrive-document-ai
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Performance Optimization

**Configuration Tuning:**
```env
# Increase concurrent processing
MAX_CONCURRENT_PROCESSES=8

# Reduce timeout for smaller documents
PROCESSING_TIMEOUT=180

# Optimize chunk sizes
DEFAULT_CHUNK_SIZE=800
DEFAULT_CHUNK_OVERLAP=150
```

**Uvicorn Workers:**
```bash
# Multiple workers for CPU-bound tasks
uvicorn app.main:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8080
```

**⚠️ Note:** Docling uses ML models, so multiple workers share GPU/CPU. Too many workers can cause contention.

### Capacity Planning

**Estimate requests per second:**
```
Average processing time: 10s/document
Concurrent capacity: 10 documents
Max throughput: 10 / 10s = 1 request/second
Daily capacity: 1 req/s × 86400s = 86,400 documents/day
```

**Plan for growth:**
```
Current: 1,000 documents/day
Growth: 20% per quarter
Year 1 Q4: 1,000 × 1.2^4 ≈ 2,074 documents/day
Year 2 Q4: 1,000 × 1.2^8 ≈ 4,300 documents/day

Current capacity: 86,400 documents/day ✅ Sufficient
Monitor and scale when approaching 50% capacity (43,200 docs/day)
```

### Monitoring Scaling Effectiveness

**Key metrics:**
- Request latency (should stay constant or decrease)
- Error rate (should stay constant or decrease)
- CPU/memory utilization per instance (should decrease)
- Cost per request (should decrease or stay constant)

**Scaling is successful when:**
- Latency p95 < 30s
- Error rate < 1%
- No resource exhaustion
- Cost per request acceptable

---

## Cost Optimization

### Infrastructure Costs

**Typical cloud costs (monthly estimates):**

| Environment | CPU  | Memory | Instances | Cloud Run | ECS Fargate | GKE       |
|-------------|------|--------|-----------|-----------|-------------|-----------|
| Dev/Test    | 1    | 2GB    | 1         | $10-30    | $20-40      | $30-50    |
| Staging     | 2    | 4GB    | 2         | $40-80    | $80-120     | $100-150  |
| Production  | 4    | 8GB    | 3         | $150-300  | $300-500    | $400-600  |

**Notes:**
- Cloud Run: Pay per request (cheapest for low/variable traffic)
- ECS Fargate: Pay per hour (predictable pricing)
- GKE: Pay for nodes (best for high consistent traffic)

### Reducing Costs

**1. Right-size resources:**
```bash
# Monitor actual usage
docker stats braindrive-doc-ai

# If CPU consistently <50%, reduce allocation
# If memory consistently <50%, reduce allocation
```

**2. Use autoscaling:**
```yaml
# Scale to zero when idle (Cloud Run does this automatically)
# Or scale down to minimum replicas during off-hours

# Example: Kubernetes CronJob to scale down at night
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-nights
spec:
  schedule: "0 22 * * *"  # 10 PM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scaler
            image: bitnami/kubectl
            command:
            - kubectl
            - scale
            - deployment/braindrive-document-ai
            - --replicas=1
```

**3. Optimize processing:**
```env
# Disable OCR if not needed (20x faster)
# OCR disabled by default

# Use smaller chunk sizes for faster processing
DEFAULT_CHUNK_SIZE=500  # Faster but more chunks

# Reduce overlap
DEFAULT_CHUNK_OVERLAP=100  # Less redundancy
```

**4. Use spot/preemptible instances:**
```bash
# AWS Spot Instances: 70-90% discount
# GCP Preemptible VMs: 60-91% discount

# ⚠️ Only for non-critical workloads
# Instances can be terminated with 30s notice
```

**5. Cache ML models:**
```dockerfile
# Pre-download models in Docker image
# Avoids download time and bandwidth costs
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('ds4sd/docling-layout-heron')"
```

**6. Use reserved instances (if predictable load):**
- AWS Reserved Instances: 30-70% discount
- GCP Committed Use Discounts: 25-55% discount
- Azure Reserved VM Instances: 40-72% discount

### Monitoring Costs

**Set up billing alerts:**
```bash
# AWS CloudWatch Billing Alert
aws cloudwatch put-metric-alarm \
  --alarm-name high-cost-alert \
  --metric-name EstimatedCharges \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold

# GCP Budget Alert
gcloud billing budgets create \
  --billing-account=ACCOUNT_ID \
  --display-name="Monthly Budget" \
  --budget-amount=1000 \
  --threshold-rule=percent=80
```

**Cost allocation tags:**
```yaml
# Tag resources for cost tracking
labels:
  environment: production
  team: braindrive
  service: document-ai
  cost-center: engineering
```

---

## Knowledge Management

### Compounding Engineering System

This project uses **Compounding Engineering** - every development session leaves behind structured knowledge.

**Knowledge Base Location:** `docs/`

```
docs/
├── decisions/           # Architecture Decision Records (ADRs)
├── failures/            # Lessons learned (what NOT to do)
├── data-quirks/         # Non-obvious behavior
└── integrations/        # External system documentation
```

### For Maintainers

**When you make architectural decisions:**
```bash
cp docs/decisions/000-template.md docs/decisions/00X-your-decision.md
# Document: Context, Problem, Decision, Alternatives, Consequences
```

**When you encounter mistakes/failures:**
```bash
touch docs/failures/00X-failure-name.md
# Document: What happened, Root cause, Lessons, Prevention
```

**When you discover quirks:**
```bash
touch docs/data-quirks/00X-quirk-name.md
# Document: Behavior, Why it matters, Detection, Correct patterns
```

**When you integrate external services:**
```bash
touch docs/integrations/service-name.md
# Document: Purpose, Auth, Schema, Quirks, Error handling
```

**See:** `docs/AI-AGENT-GUIDE.md` for complete guidelines

### Current Knowledge Base

**Decisions:**
- ADR-001: Use Docling for multi-format document processing

**Data Quirks:**
- Quirk-001: Windows HuggingFace symlink permission issues

**Integrations:**
- Docling: Complete reference for document processing library

**Failures:**
- (None yet - first mistake will be documented here)

### Knowledge Review Cadence

**Weekly:**
- Review new documentation added
- Check for documentation gaps

**Monthly:**
- Update outdated documentation
- Archive deprecated decisions

**Quarterly:**
- Major documentation review
- Update this OWNERS-MANUAL.md
- Update FOR-AI-CODING-AGENTS.md if architecture changed

---

## Team Onboarding

### New Developer Checklist

**Day 1: Setup**
- [ ] Clone repository
- [ ] Read README.md
- [ ] Read FOR-AI-CODING-AGENTS.md (architecture overview)
- [ ] Setup local environment (Python, Poetry, Docker)
- [ ] Run service locally
- [ ] Test document upload

**Day 2: Architecture**
- [ ] Read docs/AI-AGENT-GUIDE.md (complete guide)
- [ ] Review Clean Architecture layers
- [ ] Browse `app/core/` (domain layer)
- [ ] Browse `app/adapters/` (implementations)
- [ ] Review dependency injection pattern

**Day 3: Knowledge Base**
- [ ] Read all ADRs in `docs/decisions/`
- [ ] Read all data quirks in `docs/data-quirks/`
- [ ] Read integration docs in `docs/integrations/`
- [ ] Understand compounding engineering philosophy

**Day 4: Hands-on**
- [ ] Make a small code change
- [ ] Run tests locally
- [ ] Submit pull request
- [ ] Go through code review process

**Day 5: Operations**
- [ ] Read this OWNERS-MANUAL.md
- [ ] Learn deployment process
- [ ] Review monitoring dashboards
- [ ] Understand troubleshooting procedures

**Week 2: Advanced**
- [ ] Implement a new feature
- [ ] Document architectural decision (ADR)
- [ ] Add tests
- [ ] Deploy to staging

### Key Concepts to Master

1. **Clean Architecture:**
   - Domain layer has no external dependencies
   - Use cases orchestrate domain entities and ports
   - Adapters implement port interfaces
   - Dependency injection connects everything

2. **Document Processing Pipeline:**
   - Upload → Validation → Extraction (Docling) → Chunking → Response
   - Files deleted after processing (no persistent storage)
   - Token-based chunking with configurable overlap

3. **Authentication:**
   - API Key (X-API-Key header) or JWT (Authorization: Bearer)
   - Can be disabled for local development
   - Never disabled in production

4. **Compounding Engineering:**
   - Document decisions, failures, quirks, integrations
   - Check docs/ before implementing
   - Leave knowledge for next developer

### Training Resources

**Internal:**
- `FOR-AI-CODING-AGENTS.md` - Architecture and patterns
- `docs/AI-AGENT-GUIDE.md` - Complete guide
- `docs/decisions/` - Architectural decisions
- `OWNERS-MANUAL.md` - This file

**External:**
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- FastAPI docs: https://fastapi.tiangolo.com/
- Docling docs: https://docling.github.io/docling/
- Pydantic docs: https://docs.pydantic.dev/

### Mentorship

**First PR:**
- Pair program with senior developer
- Review together before submitting
- Walk through code review feedback

**First Production Deployment:**
- Shadow experienced team member
- Review deployment checklist together
- Monitor deployment health together

**First On-Call Shift:**
- Shadow on-call engineer first
- Review runbooks together
- Practice incident response scenarios

---

## Disaster Recovery

### Backup Strategy

**What to backup:**
- ✅ Configuration files (`.env.production`, docker-compose files)
- ✅ Documentation (`docs/`, `FOR-AI-CODING-AGENTS.md`, etc.)
- ✅ Deployment manifests (Kubernetes YAML, Terraform, etc.)
- ✅ Secrets (API keys, JWT secrets) - in secure secrets manager
- ❌ Uploaded documents (deleted after processing, nothing to backup)
- ❌ Application code (in git repository)

**Backup locations:**
```bash
# Configuration backup
aws s3 sync .env.production s3://braindrive-backups/config/
aws s3 sync k8s/ s3://braindrive-backups/manifests/

# Documentation backup
aws s3 sync docs/ s3://braindrive-backups/docs/

# Or use git for documentation
git add docs/
git commit -m "docs: update documentation"
git push
```

**Backup frequency:**
- Configuration: After every change
- Documentation: Daily (or on every commit)
- Secrets: On generation/rotation
- Deployment manifests: On every change

### Recovery Procedures

#### Scenario 1: Service Crash/Unresponsive

**Detection:**
- Health check fails
- Alerts fire
- Users report service down

**Recovery steps:**
```bash
# 1. Check logs
docker logs braindrive-doc-ai --tail 100

# 2. Restart service
docker restart braindrive-doc-ai

# 3. Verify health
curl http://localhost:8080/health

# 4. If restart fails, check configuration
docker exec braindrive-doc-ai env | grep -E "AUTH|DISABLE|UPLOAD"

# 5. If configuration correct, redeploy from known good image
docker pull braindrive-document-ai:v0.1.0
docker stop braindrive-doc-ai
docker rm braindrive-doc-ai
docker run -d --name braindrive-doc-ai --env-file .env -p 8080:8080 braindrive-document-ai:v0.1.0

# 6. Verify health again
curl http://localhost:8080/health

# 7. Check metrics for normal operation
curl http://localhost:8080/metrics
```

**Time to recovery:** 2-5 minutes

#### Scenario 2: Lost Configuration

**Detection:**
- Deployment fails due to missing environment variables
- Service won't start after redeployment

**Recovery steps:**
```bash
# 1. Restore from backup
aws s3 cp s3://braindrive-backups/config/.env.production .env

# 2. If backup unavailable, recreate from template
cp .env.production .env

# 3. Generate new API keys
.\generate_keys.ps1 -Both -Length 128

# 4. Redeploy service
docker-compose up -d

# 5. Verify health
curl http://localhost:8080/health

# 6. Notify clients of new API key
```

**Time to recovery:** 10-15 minutes

#### Scenario 3: Complete Infrastructure Loss

**Detection:**
- Cloud region outage
- Entire cluster lost
- All infrastructure destroyed

**Recovery steps:**
```bash
# 1. Provision new infrastructure (example: GCP Cloud Run)
gcloud run deploy braindrive-document-ai \
  --image gcr.io/PROJECT/braindrive-document-ai:latest \
  --region us-east1 \
  --platform managed \
  --memory 4Gi \
  --cpu 2

# 2. Restore configuration from backup
gcloud secrets create api-key --data-file=<(aws s3 cp s3://braindrive-backups/secrets/api-key -)

# 3. Configure service
gcloud run services update braindrive-document-ai \
  --set-secrets=AUTH_API_KEY=api-key:latest

# 4. Verify health
curl https://braindrive-document-ai-xxx-uc.a.run.app/health

# 5. Update DNS (if needed)
# Point domain to new service URL

# 6. Notify stakeholders of new endpoint
```

**Time to recovery:** 30-60 minutes

#### Scenario 4: Data Corruption (Unlikely)

**Detection:**
- Service returns incorrect results
- Processing consistently fails

**Recovery steps:**
```bash
# 1. Since no persistent data, simply redeploy clean service
docker pull braindrive-document-ai:latest
docker-compose up -d --force-recreate

# 2. Clear any cached models
docker exec braindrive-doc-ai rm -rf /app/.cache/huggingface

# 3. Restart to re-download models
docker restart braindrive-doc-ai

# 4. Verify processing with test document
curl -X POST http://localhost:8080/documents/upload \
  -H "X-API-Key: $API_KEY" \
  -F "file=@test.pdf"

# 5. If still failing, rollback to previous known good version
docker pull braindrive-document-ai:v0.0.9
docker-compose up -d
```

**Time to recovery:** 10-20 minutes

### Recovery Testing

**Schedule regular DR drills:**
```bash
# Quarterly: Test service restart
# Semi-annually: Test configuration restore
# Annually: Test complete infrastructure rebuild
```

**Document each drill:**
```bash
# Create docs/failures/00X-dr-drill-YYYY-MM-DD.md
# Document:
# - What was tested
# - Actual time to recovery
# - Issues encountered
# - Process improvements needed
```

### Business Continuity

**RTO (Recovery Time Objective):** 30 minutes
- Time to restore service after incident

**RPO (Recovery Point Objective):** 0 minutes
- No data loss (no persistent data)

**Redundancy:**
```yaml
# Run multiple replicas for high availability
replicas: 3

# Spread across zones
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        topologyKey: topology.kubernetes.io/zone
```

**Fallback plan:**
- If service unavailable, queue documents for later processing
- Or direct users to alternative service (if available)
- Or provide degraded functionality (manual processing)

---

## Support & Resources

### Internal Resources

**Documentation:**
- `README.md` - Quick start and overview
- `FOR-AI-CODING-AGENTS.md` - Complete architecture guide
- `OWNERS-MANUAL.md` - This file (operations guide)
- `docs/AI-AGENT-GUIDE.md` - Development guide
- `docs/decisions/` - Architectural decisions
- `docs/data-quirks/` - Known issues and workarounds
- `docs/integrations/` - External service docs

**Code:**
- Repository: https://github.com/BrainDriveAI/Document-Processing-Service
- Issues: https://github.com/BrainDriveAI/Document-Processing-Service/issues
- Pull Requests: https://github.com/BrainDriveAI/Document-Processing-Service/pulls

### External Resources

**Dependencies:**
- FastAPI: https://fastapi.tiangolo.com/
- Docling: https://docling.github.io/docling/
- Docling GitHub: https://github.com/DS4SD/docling
- Pydantic: https://docs.pydantic.dev/
- HuggingFace Hub: https://huggingface.co/docs/hub/

**Related Projects:**
- BrainDrive Main Application: https://github.com/BrainDriveAI/BrainDrive-Core
- BrainDrive Chat Service: https://github.com/BrainDriveAI/Document-Chat-Service

### Getting Help

**For developers:**
1. Check documentation (especially FOR-AI-CODING-AGENTS.md and AI-AGENT-GUIDE.md)
2. Search existing GitHub issues
3. Ask in team chat/Slack
4. Create GitHub issue with details
5. Ping team lead if urgent

**For operations:**
1. Check troubleshooting section above
2. Review logs and metrics
3. Check monitoring dashboards
4. Follow runbooks for common issues
5. Escalate to on-call engineer if needed

**For users/clients:**
1. Check API documentation (/docs endpoint)
2. Verify authentication (API key correct)
3. Check service status (health endpoint)
4. Contact support with error details
5. Provide example document that fails (if applicable)

### Issue Reporting Template

```markdown
**Description:**
Brief description of the issue

**Environment:**
- Deployment type: (Docker / Kubernetes / Cloud Run / etc.)
- Version: (Image tag or commit hash)
- Configuration: (Sanitized relevant env vars)

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Logs:**
```
Relevant log entries (last 50 lines)
```

**Additional Context:**
Any other relevant information
```

### Contact Information

**Project Owner:** [Your name/email]
**Technical Lead:** [Tech lead name/email]
**Operations Team:** [Ops team email/Slack]
**Security Contact:** [Security team email]

---

## Appendix

### Glossary

- **ADR:** Architecture Decision Record - documents why architectural choices were made
- **Clean Architecture:** Software design approach separating concerns into layers
- **Docling:** IBM Research library for document processing and layout understanding
- **Port:** Interface defining a contract (in Clean Architecture)
- **Adapter:** Implementation of a port interface
- **Use Case:** Application-specific business rules orchestrating domain entities
- **Chunk:** Segment of text extracted from document
- **Token:** Unit of text for LLM processing (roughly 0.75 words)
- **RAG:** Retrieval Augmented Generation - LLM technique using external knowledge

### Version History

| Version | Date       | Changes                                  |
|---------|------------|------------------------------------------|
| 0.1.0   | 2024-11-14 | Initial OWNERS-MANUAL.md creation        |

### Change Log

**2024-11-14:**
- Created comprehensive OWNERS-MANUAL.md
- Documented all operational procedures
- Added troubleshooting guides
- Documented disaster recovery procedures

### Contributing to This Manual

**When updating this manual:**
1. Follow existing structure
2. Keep language clear and concise
3. Include code examples
4. Update version history
5. Test procedures before documenting
6. Get review from team

**This manual should be updated when:**
- Architecture changes significantly
- New deployment target added
- New operational procedures established
- Common issues discovered
- Recovery procedures change

---

**Document Owner:** Project Maintainer
**Last Reviewed:** 2024-11-14
**Next Review:** 2025-02-14 (Quarterly)

---

*This OWNERS-MANUAL.md is a living document. Keep it updated with operational changes.*
