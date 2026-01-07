#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PATH="${VENV_PATH:-.venv}"
export VENV_PATH

PORT_START="${PORT_START:-18081}"
PORT_COUNT="${PORT_COUNT:-10}"

DATA_DIR="$REPO_ROOT/data"
mkdir -p "$DATA_DIR"

if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "Error: python3 or python is required on PATH."
    exit 1
fi

ENV_FILE="$REPO_ROOT/.env"
ENV_FALLBACK="$REPO_ROOT/.env.local.example"

get_env_value() {
    local file="$1"
    local key="$2"
    if [[ ! -f "$file" ]]; then
        return 0
    fi
    "$PYTHON" - "$file" "$key" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
if not path.exists():
    sys.exit(0)
for raw_line in path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    if k.strip() == key:
        value = v.strip().strip('"').strip("'")
        if value:
            print(value)
        break
PY
}

find_free_port() {
    "$PYTHON" - "$PORT_START" "$PORT_COUNT" <<'PY'
import socket
import sys

start = int(sys.argv[1])
count = int(sys.argv[2])

for port in range(start, start + count):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sock.close()
        continue
    sock.close()
    print(port)
    sys.exit(0)

sys.exit(1)
PY
}

wait_for_health() {
    local url="$1"
    local retries="${2:-12}"
    local delay="${3:-3}"
    local i
    for ((i = 0; i < retries; i++)); do
        if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep "$delay"
    done
    return 1
}

wait_for_exit() {
    local pid="$1"
    local timeout="${2:-10}"
    local waited=0
    while kill -0 "$pid" >/dev/null 2>&1; do
        if (( waited >= timeout * 2 )); then
            return 1
        fi
        sleep 0.5
        waited=$((waited + 1))
    done
    wait "$pid" >/dev/null 2>&1 || true
    return 0
}

VENV_PY="$REPO_ROOT/$VENV_PATH/bin/python"
cleanup() {
    set +e
    if [[ -x "$VENV_PY" ]]; then
        "$VENV_PY" "service_scripts/shutdown_with_venv.py" >/dev/null 2>&1 || true
    fi
    if [[ -n "${START_PID:-}" ]] && kill -0 "$START_PID" >/dev/null 2>&1; then
        kill "$START_PID" >/dev/null 2>&1 || true
    fi
    if [[ -n "${RESTART_PID:-}" ]] && kill -0 "$RESTART_PID" >/dev/null 2>&1; then
        kill "$RESTART_PID" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

if [[ -z "${API_HOST:-}" ]]; then
    API_HOST="$(get_env_value "$ENV_FILE" "API_HOST")"
    if [[ -z "$API_HOST" ]]; then
        API_HOST="$(get_env_value "$ENV_FALLBACK" "API_HOST")"
    fi
fi
API_HOST="${API_HOST:-127.0.0.1}"

if [[ -z "${API_PORT:-}" ]]; then
    API_PORT="$(get_env_value "$ENV_FILE" "API_PORT")"
    if [[ -z "$API_PORT" ]]; then
        API_PORT="$(get_env_value "$ENV_FALLBACK" "API_PORT")"
    fi
fi
if [[ -z "${API_PORT:-}" ]]; then
    API_PORT="$(find_free_port)"
fi

HEALTH_HOST="$API_HOST"
if [[ "$HEALTH_HOST" == "0.0.0.0" ]]; then
    HEALTH_HOST="127.0.0.1"
fi

export API_HOST
export API_PORT

cd "$REPO_ROOT"

"$SCRIPT_DIR/mac_create_venv.sh"
"$SCRIPT_DIR/mac_install.sh"

if [[ ! -x "$VENV_PY" ]]; then
    echo "Error: venv python not found at $VENV_PY."
    exit 1
fi

START_STDOUT="$DATA_DIR/test_start_stdout.log"
START_STDERR="$DATA_DIR/test_start_stderr.log"
RESTART_STDOUT="$DATA_DIR/test_restart_stdout.log"
RESTART_STDERR="$DATA_DIR/test_restart_stderr.log"

"$VENV_PY" "service_scripts/start_with_venv.py" >"$START_STDOUT" 2>"$START_STDERR" &
START_PID=$!

HEALTH_URL="http://$HEALTH_HOST:$API_PORT/health"
if ! wait_for_health "$HEALTH_URL"; then
    echo "Error: health check failed for $HEALTH_URL"
    exit 1
fi

"$VENV_PY" "service_scripts/restart_with_venv.py" >"$RESTART_STDOUT" 2>"$RESTART_STDERR" &
RESTART_PID=$!

if ! wait_for_health "$HEALTH_URL"; then
    echo "Error: health check failed after restart for $HEALTH_URL"
    exit 1
fi

"$VENV_PY" "service_scripts/shutdown_with_venv.py"

if [[ -n "${START_PID:-}" ]] && kill -0 "$START_PID" >/dev/null 2>&1; then
    if ! wait_for_exit "$START_PID" 10; then
        kill "$START_PID" >/dev/null 2>&1 || true
        wait "$START_PID" >/dev/null 2>&1 || true
    fi
fi
if [[ -n "${RESTART_PID:-}" ]] && kill -0 "$RESTART_PID" >/dev/null 2>&1; then
    if ! wait_for_exit "$RESTART_PID" 10; then
        kill "$RESTART_PID" >/dev/null 2>&1 || true
        wait "$RESTART_PID" >/dev/null 2>&1 || true
    fi
fi

echo "System test OK on $HEALTH_URL"
echo "Logs: $START_STDERR, $RESTART_STDERR"
