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

DEFAULT_DOCLING_MODEL = "ds4sd/docling-layout-heron"


def _parse_env_file(path: Path) -> dict:
    if not path.exists():
        return {}
    values: dict = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = value.strip().strip('"').strip("'")
    return values


def _resolve_docling_model_name() -> str:
    env_name = os.environ.get("DOCLING_MODEL_NAME")
    if env_name:
        return env_name
    env_path = REPO_ROOT / ".env"
    env_values = _parse_env_file(env_path)
    if env_values.get("DOCLING_MODEL_NAME"):
        return env_values["DOCLING_MODEL_NAME"]
    fallback_env = REPO_ROOT / ".env.local.example"
    env_values = _parse_env_file(fallback_env)
    if env_values.get("DOCLING_MODEL_NAME"):
        return env_values["DOCLING_MODEL_NAME"]
    return DEFAULT_DOCLING_MODEL


def _preload_docling_model_windows(venv_py: Path) -> None:
    if os.name != "nt":
        return
    model_name = _resolve_docling_model_name()
    if not model_name:
        return
    env = os.environ.copy()
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    env.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
    cmd = [
        str(venv_py),
        "-c",
        (
            "from huggingface_hub import snapshot_download;"
            "snapshot_download(%r, local_dir_use_symlinks=False)"
        )
        % model_name,
    ]
    try:
        print(f"Preloading Docling model on Windows: {model_name}")
        subprocess.check_call(cmd, cwd=REPO_ROOT, env=env)
    except subprocess.CalledProcessError as exc:
        print(f"Warning: Docling model preload failed (will retry at runtime): {exc}")

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

    _preload_docling_model_windows(venv_py)

    print("\nDependencies installed into the venv.")


if __name__ == "__main__":
    main()
