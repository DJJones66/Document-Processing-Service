#!/usr/bin/env python3
"""
Start the FastAPI service using the local venv.

Usage:
  python tests/start_with_venv.py

Environment overrides:
  VENV_PATH       Path to venv directory (default: .venv at repo root)
  API_HOST        Host for uvicorn (default: 0.0.0.0)
  API_PORT        Port for uvicorn (default: 8080)
  UVICORN_RELOAD  Set to '1'/'true' to enable reload
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from venv_utils import DEFAULT_VENV_DIR, REPO_ROOT, venv_exists, venv_python

ENV_NAME = os.environ.get("VENV_PATH", DEFAULT_VENV_DIR)
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = os.environ.get("API_PORT", "18080")
RELOAD = os.environ.get("UVICORN_RELOAD", "").lower() in {"1", "true", "yes", "on"}


def main() -> None:
    venv_dir = Path(ENV_NAME)
    if not venv_exists(venv_dir):
        sys.exit(f"Venv not found at {venv_dir}. Run tests/create_venv.py first.")

    venv_py = venv_python(venv_dir)
    cmd = [
        str(venv_py),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        API_HOST,
        "--port",
        API_PORT,
    ]
    if RELOAD:
        cmd.append("--reload")

    print("Starting service with:\n ", " ".join(cmd))
    subprocess.check_call(cmd, cwd=REPO_ROOT)


if __name__ == "__main__":
    main()
