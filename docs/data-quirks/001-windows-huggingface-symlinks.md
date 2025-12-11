# Data Quirk-001: HuggingFace Model Downloads Fail on Windows Without Admin Rights

**Discovered:** 2024-10
**Severity:** High (blocks first-time model download)
**Affected Systems:** Windows development environments, Windows containers
**Related:** ADR-001 (Docling integration)

---

## Behavior

When Docling attempts to download models from HuggingFace Hub on Windows, it fails with permission errors related to symlink creation:

```
OSError: [WinError 1314] A required privilege is not held by the client:
'C:\\Users\\...\\cache\\huggingface\\hub\\models--ds4sd--docling-layout-heron\\...'
```

This happens because:
1. HuggingFace Hub uses symlinks in its caching mechanism by default
2. Windows requires administrator privileges to create symlinks
3. Most development environments and containers run without admin rights

## Why It Matters

**Impact on features:**
- **Blocks initialization:** Service fails to start on first run
- **Production deployments:** Docker containers fail if models not pre-cached
- **Developer onboarding:** Local development setup fails
- **CI/CD pipelines:** Tests fail in Windows-based CI runners

**Symptoms:**
- Service crashes during startup with symlink errors
- `app.state.document_processor` never initializes
- `/documents/upload` endpoint returns 500 errors

## Root Cause

HuggingFace Hub's default caching strategy:
1. Downloads model files to `~/.cache/huggingface/hub/`
2. Creates symlinks pointing to actual files
3. Symlinks allow multiple model versions to share files efficiently

On Windows, symlink creation requires `SeCreateSymbolicLinkPrivilege`, which is:
- Not granted to regular users by default
- Not available in non-admin Docker containers
- Not available in many CI/CD environments

## Detection

### How to Identify This Issue

**Error patterns in logs:**
```
ERROR: Failed to initialize adapters: [WinError 1314]
ERROR: A required privilege is not held by the client
WARNING: Could not create symbolic link
```

**Pre-flight check:**
```python
import os
if os.name == 'nt':  # Windows
    print("⚠️  Windows detected - check symlink handling")
```

**Test command:**
```bash
# Try downloading a model
python -c "from huggingface_hub import snapshot_download; snapshot_download('ds4sd/docling-layout-heron')"
```

If this fails with symlink errors, the quirk is present.

## Correct Patterns

### Solution 1: Disable Symlinks (Recommended)

Implemented in `DoclingModelManager`:

```python
class DoclingModelManager:
    def ensure_models_downloaded(self) -> None:
        if os.name == 'nt':  # Windows
            # Disable symlink warnings
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

            # Force huggingface_hub to not use symlinks
            try:
                from huggingface_hub import constants
                constants.HF_HUB_DISABLE_SYMLINKS = True
            except Exception as e:
                self.logger.warning(f"Could not disable HF symlinks: {e}")

        # Now download models - will use copies instead of symlinks
        snapshot_download(
            repo_id=model_name,
            local_files_only=False,
            resume_download=True,
        )
```

**Trade-off:** Uses more disk space (full copies instead of symlinks) but works everywhere.

### Solution 2: Pre-cache Models in Docker Build

In `Dockerfile`:

```dockerfile
# Set environment variable to disable symlinks
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Pre-download models during build (runs as root, has permissions)
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('ds4sd/docling-layout-heron')"
```

**Benefit:** Runtime doesn't need to download, avoiding the issue entirely.

### Solution 3: Use Local Model Cache

For air-gapped or restricted environments:

```python
# Download models once with admin rights
snapshot_download(
    repo_id='ds4sd/docling-layout-heron',
    local_dir='/app/models/docling-layout-heron'
)

# Then use local path
converter = DocumentConverter(
    model_path='/app/models/docling-layout-heron'
)
```

### What NOT to Do

❌ **Don't run with admin privileges**
```bash
# BAD: Security risk
runas /user:Administrator "uvicorn app.main:app"
```

❌ **Don't ignore the error**
```python
# BAD: Service starts but fails on actual processing
try:
    model_manager.ensure_models_downloaded()
except Exception:
    pass  # Hope for the best
```

❌ **Don't use Developer Mode symlinks**
```powershell
# BAD: Requires Windows 10+ Developer Mode, not available in containers
# Settings → Update & Security → For Developers → Developer Mode
```

## Prevention Checklist

Before deploying on Windows:

- [ ] Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` in environment
- [ ] Set `constants.HF_HUB_DISABLE_SYMLINKS = True` in code
- [ ] Pre-download models during Docker build (if using containers)
- [ ] Test model download without admin rights
- [ ] Verify `DoclingModelManager.ensure_models_downloaded()` succeeds
- [ ] Check logs for symlink warnings during startup

Before local development setup:

- [ ] Document Windows-specific setup in README
- [ ] Add pre-flight check script for Windows
- [ ] Provide pre-cached model download option
- [ ] Test on fresh Windows machine without admin rights

## Related Issues

- **Issue:** Docker build fails on Windows
  - **Cause:** Build step tries to create symlinks
  - **Fix:** Set environment variable before model download

- **Issue:** Service works on Linux, fails on Windows
  - **Cause:** Different symlink behavior between OS
  - **Fix:** OS-specific handling in `DoclingModelManager`

- **Issue:** First request hangs for 5+ minutes
  - **Cause:** Model downloading during request processing
  - **Fix:** Enable `preload_models=True` in processor initialization

## References

- Implementation: `app/adapters/document_processor/docling_document_processor.py:17-73`
- HuggingFace Hub docs: https://huggingface.co/docs/huggingface_hub/guides/download#download-files-to-local-folder
- Windows symlinks: https://docs.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/create-symbolic-links
- Related ADR: ADR-001 (Docling for Document Processing)

---

## Additional Notes

### Alternative: Use `local_files_only=True`

If models are pre-cached elsewhere:

```python
snapshot_download(
    repo_id='ds4sd/docling-layout-heron',
    local_files_only=True,  # Don't download, use cache only
)
```

This avoids symlink issues but requires models to be cached beforehand (e.g., during Docker build with root privileges).

### Disk Space Impact

Disabling symlinks increases disk usage:
- **With symlinks:** ~200MB (shared files between model versions)
- **Without symlinks:** ~300-400MB (duplicate files)

For typical deployments, this trade-off is acceptable for Windows compatibility.

### Testing This Quirk

Create a test that verifies Windows handling:

```python
import os
import pytest

@pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
def test_windows_model_download_without_symlinks():
    """Verify model download works on Windows without admin rights"""
    manager = DoclingModelManager(logger)
    manager.ensure_models_downloaded()
    # Should succeed without symlink errors
```
