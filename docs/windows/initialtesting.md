 # Windows install and smoke test

Use this checklist to validate a clean Windows install of the Document Processing Service.

## Preconditions
- Windows 10 or 11
- Python 3.11 installed and on PATH, or a Conda environment with Python 3.11
- PowerShell
- Optional: Git installed (if cloning fresh)
- Test Path to clone ("C:\Users\david\TestArea")
- Conda session: BrainDriveDev

## Option A: Use the helper scripts (creates .venv)
Run from the repo root: `C:\Users\david\Projects\Document-Processing-Service`

```powershell
# Create and populate the local venv
python .\service_scripts\create_venv.py
python .\service_scripts\install_with_venv.py

# Optional: prevent HuggingFace symlink issues on Windows
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

# Start the service
python .\service_scripts\start_with_venv.py
```

Notes:
- `start_with_venv.py` defaults to port 18080 unless `API_PORT` is set.
- To override port/host:
  ```powershell
  $env:API_HOST = "0.0.0.0"
  $env:API_PORT = "8080"
  python .\service_scripts\start_with_venv.py
  ```

## Option B: Use a Conda env (no local .venv)
```powershell
conda create -n docproc python=3.11
conda activate docproc
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Start the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Smoke test
Open a new PowerShell window:
```powershell
# Use 18080 if you started via start_with_venv.py without API_PORT
Invoke-RestMethod http://localhost:18080/health
```

Expected: JSON response from the health endpoint.

## Windows-specific quirk: HuggingFace symlinks
Docling model downloads can fail on Windows due to symlink permissions.
If you see WinError 1314 or symlink warnings:
- Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` in the environment or `.env`.
- The code also attempts to disable symlinks at runtime in
  `app/adapters/document_processor/docling_document_processor.py`.

## Troubleshooting
- If `python` is not found, install Python 3.11 or set `PYTHON_BIN` to a full path.
- If `pip install` fails on a package, record the error and whether it is a wheel build issue.
- If the service starts but requests fail, check `docs/data-quirks/001-windows-huggingface-symlinks.md`.

## Test run notes (local, TestArea clone)
Repository clone and install test run from `C:\Users\david\TestArea\Document-Processing-Service` using the Conda env `BrainDriveDev`.

### Clone
```powershell
New-Item -ItemType Directory -Force -Path "C:\Users\david\TestArea"
git clone "C:\Users\david\Projects\Document-Processing-Service" "C:\Users\david\TestArea\Document-Processing-Service"
```
Result: clone completed successfully.

### create_venv.py
First attempt (failed):
```powershell
conda run -n BrainDriveDev python .\service_scripts\create_venv.py
```
Observed error:
- `python3` resolved to `C:\Users\david\AppData\Local\Microsoft\WindowsApps\python3.EXE`
- Error: `Python was not found ...` and `CalledProcessError` when running `-m venv`.

Second attempt (success) with explicit Python:
```powershell
$env:PYTHON_BIN="C:\Users\david\miniconda3\envs\BrainDriveDev\python.exe"
conda run -n BrainDriveDev python .\service_scripts\create_venv.py
```
Result: venv created at `C:\Users\david\TestArea\Document-Processing-Service\.venv` and pip/setuptools/wheel upgraded.

### install_with_venv.py
First attempt:
```powershell
conda run -n BrainDriveDev python .\service_scripts\install_with_venv.py
```
Result: timed out after ~124 seconds.

Second attempt (longer timeout) started installing but failed:
- `ERROR: Could not install packages due to an OSError: [WinError 32] The process cannot access the file because it is being used by another process: '...\.venv\Lib\site-packages\scipy\optimize\tests\test_milp.py'`
- `conda run` reported non-zero exit status due to the pip failure.

Notes:
- This looks like a Windows file lock during `scipy` install (often AV or indexer). A retry after closing any scanners may succeed.
- The install pulled CPU PyTorch wheels from `https://download.pytorch.org/whl/cpu` as expected.

### Test run notes (post-fix, win2 clone)
This run used a fresh clone at `C:\Users\david\TestArea\Document-Processing-Service-win2` and the updated helper scripts.

Script updates applied before re-test:
- `service_scripts/venv_utils.py`: prefer `sys.executable` and skip WindowsApps Python stubs.
- `service_scripts/install_with_venv.py`: set `PIP_NO_INPUT=1` and retry once on Windows after a short delay.

Because the repo changes were uncommitted, the files were copied into the clone before testing:
```powershell
Copy-Item -Force "C:\Users\david\Projects\Document-Processing-Service\service_scripts\venv_utils.py" "C:\Users\david\TestArea\Document-Processing-Service-win2\service_scripts\venv_utils.py"
Copy-Item -Force "C:\Users\david\Projects\Document-Processing-Service\service_scripts\install_with_venv.py" "C:\Users\david\TestArea\Document-Processing-Service-win2\service_scripts\install_with_venv.py"
```

#### create_venv.py
```powershell
conda run -n BrainDriveDev python .\service_scripts\create_venv.py
```
Result: success without setting `PYTHON_BIN`. The script picked `C:\Users\david\miniconda3\envs\BrainDriveDev\python.exe` automatically.

#### install_with_venv.py
```powershell
conda run -n BrainDriveDev python .\service_scripts\install_with_venv.py
```
Result: success. Total time ~4.5 minutes. No WinError 32 this run.

### Test run notes (start/health/stop, win2 clone)
This run validates `start_with_venv.py` + `/health` + `shutdown_with_venv.py` using the same win2 clone.

Observed issues and fixes applied before the final run:
- Startup failed when `.env` was missing (`NoneType` error from `settings.auth_api_key`). Fix: `start_with_venv.py` now auto-copies `.env.local.example` to `.env` if `.env` is missing.
- Port 18080 was already bound by VS Code (`Code` process). Fix: use `API_PORT=18081` for the test run.
- Pre-download of Docling model failed on Windows with WinError 1314. Fix: pass `local_dir_use_symlinks=False` on Windows and set `HF_HUB_DISABLE_SYMLINKS=1`.
- `shutdown_with_venv.py` previously terminated the shell and exited with code 15 because the default process markers matched the PowerShell command line. Fix: remove the repo-name marker; keep `uvicorn` + `app.main:app`.
- `start_with_venv.py` now treats SIGTERM/SIGINT (including Windows code 15) as a clean stop to avoid `CalledProcessError`.

Final run commands:
```powershell
$env:API_HOST="127.0.0.1"
$env:API_PORT="18081"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
python .\service_scripts\start_with_venv.py
```
Health check:
```powershell
Invoke-RestMethod http://127.0.0.1:18081/health
```
Shutdown:
```powershell
python .\service_scripts\shutdown_with_venv.py
```

Result: service started cleanly, model pre-download succeeded without symlink errors, health endpoint returned 200, and shutdown exited 0 without killing the shell.
