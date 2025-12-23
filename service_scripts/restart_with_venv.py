#!/usr/bin/env python3
"""
Restart the FastAPI service with the local venv after configuration or .env changes.

Usage:
  python service_scripts/restart_with_venv.py

Environment overrides:
  VENV_PATH         Path to venv directory (default: .venv at repo root)
  PIDFILE           Path to pidfile for shutdown (default: data/service.pid)
  PROCESS_MATCH     Comma-separated markers to identify the process (default: uvicorn,app.main:app)
  SHUTDOWN_TIMEOUT  Seconds to wait before force-killing the process (default: 15)
  RESTART_DELAY     Seconds to wait between stop and start (default: 1)
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from venv_utils import DEFAULT_VENV_DIR, REPO_ROOT, venv_exists

import shutdown_with_venv


def _load_env_file() -> None:
    """
    Load the .env file so host/port or other env-based settings are picked up on restart.
    """
    dotenv_path = REPO_ROOT / ".env"
    if not dotenv_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("python-dotenv is not installed; skipping .env reload.")
        return

    load_dotenv(dotenv_path, override=False)
    print(f"Loaded environment variables from {dotenv_path}")


def main() -> None:
    venv_dir = Path(os.environ.get("VENV_PATH", DEFAULT_VENV_DIR))
    if not venv_exists(venv_dir):
        sys.exit(f"Venv not found at {venv_dir}. Run service_scripts/create_venv.py first.")

    pidfile = shutdown_with_venv.pidfile_from_env()
    markers = shutdown_with_venv.parse_markers(os.environ.get("PROCESS_MATCH"))
    timeout = shutdown_with_venv.parse_timeout(os.environ.get("SHUTDOWN_TIMEOUT"), shutdown_with_venv.DEFAULT_SHUTDOWN_TIMEOUT)
    restart_delay = shutdown_with_venv.parse_timeout(os.environ.get("RESTART_DELAY"), 1.0)

    shutdown_with_venv.shutdown(pidfile=pidfile, process_markers=markers, timeout=timeout)

    if restart_delay:
        time.sleep(restart_delay)

    _load_env_file()

    # Ensure the start script reads the same venv path.
    os.environ["VENV_PATH"] = str(venv_dir)
    from start_with_venv import main as start_main

    print("Starting service...")
    start_main()


if __name__ == "__main__":
    main()
