#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PATH="${VENV_PATH:-.venv}"
export VENV_PATH

VENV_PY="$REPO_ROOT/$VENV_PATH/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    echo "Error: venv python not found at $VENV_PY. Run service_scripts/mac_create_venv.sh first."
    exit 1
fi

cd "$REPO_ROOT"
"$VENV_PY" "service_scripts/shutdown_with_venv.py" "$@"
