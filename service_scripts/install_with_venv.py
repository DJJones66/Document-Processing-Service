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
import time
from pathlib import Path

from venv_utils import DEFAULT_VENV_DIR, REPO_ROOT, venv_exists, venv_python


def _pip_env() -> dict:
    env = os.environ.copy()
    env.setdefault("PIP_NO_INPUT", "1")
    return env


def _install_requirements(venv_py: Path, requirements: Path, torch_index: str) -> None:
    base_cmd = [
        str(venv_py),
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements),
        "--extra-index-url",
        torch_index,
    ]

    attempts = 2 if os.name == "nt" else 1
    env = _pip_env()
    for attempt in range(1, attempts + 1):
        try:
            subprocess.check_call(base_cmd, cwd=REPO_ROOT, env=env)
            return
        except subprocess.CalledProcessError:
            if attempt >= attempts:
                raise
            print("pip install failed; retrying once in 5s (Windows file locks can cause this).")
            time.sleep(5)
            base_cmd = [
                str(venv_py),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "-r",
                str(requirements),
                "--extra-index-url",
                torch_index,
            ]


def main() -> None:
    venv_dir = Path(os.environ.get("VENV_PATH", DEFAULT_VENV_DIR))
    if not venv_exists(venv_dir):
        sys.exit(f"Venv not found at {venv_dir}. Run tests/create_venv.py first.")

    requirements = REPO_ROOT / "requirements.txt"
    if not requirements.exists():
        sys.exit(f"requirements.txt not found at {requirements}")

    venv_py = venv_python(venv_dir)

    subprocess.check_call(
        [str(venv_py), "-m", "pip", "install", "--upgrade", "pip"],
        cwd=REPO_ROOT,
        env=_pip_env(),
    )

    # Use PyTorch CPU wheels index to avoid pulling CUDA dependencies by default.
    torch_index = "https://download.pytorch.org/whl/cpu"
    _install_requirements(venv_py, requirements, torch_index)

    print("\nDependencies installed into the venv.")


if __name__ == "__main__":
    main()
