#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PATH="${VENV_PATH:-.venv}"
export VENV_PATH

if [[ -n "${PYTHON_BIN:-}" ]]; then
    PYTHON="${PYTHON_BIN}"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "Error: python3 or python is required on PATH."
    exit 1
fi

cd "$REPO_ROOT"
"$PYTHON" "service_scripts/create_venv.py" "$@"
