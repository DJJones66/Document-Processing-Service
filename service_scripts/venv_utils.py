#!/usr/bin/env python3
"""
Helpers for managing a local venv (cross-platform).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VENV_DIR = REPO_ROOT / os.environ.get("VENV_PATH", ".venv")
PYTHON_BIN = os.environ.get("PYTHON_BIN", "python3.11")


def _is_windowsapps_stub(path: str) -> bool:
    if os.name != "nt":
        return False
    try:
        parts = [part.lower() for part in Path(path).resolve().parts]
    except OSError:
        parts = [part.lower() for part in Path(path).parts]
    return "windowsapps" in parts


def find_python() -> str:
    """
    Resolve the Python executable to use for creating the venv.
    Falls back to python3/python if python3.11 is not found.
    """
    candidates = [
        PYTHON_BIN,
        sys.executable,
        "python3.11",
        "python3",
        "python",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(str(candidate))
        if resolved and not _is_windowsapps_stub(resolved):
            return resolved
    sys.exit("No suitable Python executable found. Set PYTHON_BIN to a Python 3.11 path.")


def venv_python(venv_dir: Path = DEFAULT_VENV_DIR) -> Path:
    """
    Return the python executable inside the venv.
    """
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_exists(venv_dir: Path = DEFAULT_VENV_DIR) -> bool:
    """
    Check whether the venv python exists.
    """
    return venv_python(venv_dir).exists()
