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
import signal
import shutil
import subprocess
import sys
from pathlib import Path

from venv_utils import DEFAULT_VENV_DIR, REPO_ROOT, venv_exists, venv_python

ENV_NAME = os.environ.get("VENV_PATH", DEFAULT_VENV_DIR)
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = os.environ.get("API_PORT", "18080")
RELOAD = os.environ.get("UVICORN_RELOAD", "").lower() in {"1", "true", "yes", "on"}


def _set_windows_symlink_defenses() -> None:
    if os.name != "nt":
        return
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")


def _ensure_home_dir_env() -> None:
    if os.name != "nt":
        return
    if os.environ.get("USERPROFILE") or os.environ.get("HOME"):
        return
    fallback = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or os.environ.get("TMP") or str(REPO_ROOT)
    os.environ.setdefault("USERPROFILE", fallback)
    os.environ.setdefault("HOME", fallback)


def _set_hf_home() -> None:
    if os.name != "nt":
        return
    if os.environ.get("HF_HOME"):
        return
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or os.environ.get("TMP")
    if not base:
        base = os.environ.get("USERPROFILE") or os.environ.get("HOME") or str(REPO_ROOT)
    hf_home = Path(base) / ".hf"
    os.environ.setdefault("HF_HOME", str(hf_home))
    os.environ.setdefault("HF_HUB_CACHE", str(hf_home / "hub"))


def main() -> None:
    venv_dir = Path(ENV_NAME)
    if not venv_exists(venv_dir):
        sys.exit(f"Venv not found at {venv_dir}. Run service_scripts/create_venv.py first.")

    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        example_env = REPO_ROOT / ".env.local.example"
        if example_env.exists():
            shutil.copyfile(example_env, env_path)
            print(f"Created {env_path} from {example_env} for local startup.")
        else:
            sys.exit(f"{env_path} not found and no .env.local.example present.")

    _set_windows_symlink_defenses()
    _ensure_home_dir_env()
    _set_hf_home()

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
    try:
        subprocess.check_call(cmd, cwd=REPO_ROOT)
    except subprocess.CalledProcessError as exc:
        if exc.returncode in (-signal.SIGTERM, -signal.SIGINT, signal.SIGTERM, signal.SIGINT):
            print("Service stopped.")
            return
        raise


if __name__ == "__main__":
    main()
