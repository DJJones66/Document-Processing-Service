#!/usr/bin/env python3
"""
Install project dependencies into the local venv.

Usage:
  python tests/install_with_venv.py

Environment overrides:
  VENV_PATH   Path to venv directory (default: .venv at repo root)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from venv_utils import DEFAULT_VENV_DIR, REPO_ROOT, venv_exists, venv_python


def main() -> None:
    venv_dir = Path(os.environ.get("VENV_PATH", DEFAULT_VENV_DIR))
    if not venv_exists(venv_dir):
        sys.exit(f"Venv not found at {venv_dir}. Run tests/create_venv.py first.")

    requirements = REPO_ROOT / "requirements.txt"
    if not requirements.exists():
        sys.exit(f"requirements.txt not found at {requirements}")

    venv_py = venv_python(venv_dir)

    subprocess.check_call([str(venv_py), "-m", "pip", "install", "--upgrade", "pip"], cwd=REPO_ROOT)

    # Use PyTorch CPU wheels index to avoid pulling CUDA dependencies by default.
    torch_index = "https://download.pytorch.org/whl/cpu"
    subprocess.check_call(
        [
            str(venv_py),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements),
            "--extra-index-url",
            torch_index,
        ],
        cwd=REPO_ROOT,
    )

    print("\nDependencies installed into the venv.")


if __name__ == "__main__":
    main()
