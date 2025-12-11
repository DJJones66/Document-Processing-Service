$venvPath = ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv at $venvPath using Python..."
    python -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts/python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Error "Venv python not found at $venvPython. Ensure Python is installed."
    exit 1
}

# Start the service (install deps beforehand via tests/install_with_venv.py)
& $venvPython -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
