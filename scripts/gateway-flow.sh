#!/usr/bin/env bash
# Run AbstractGateway and AbstractFlow from published PyPI packages.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-gateway-flow-published}"
BIN_DIR="$VENV_DIR/bin"
PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-$BIN_DIR/python}}"
PYTHON_BOOTSTRAP="${PYTHON_BOOTSTRAP:-python3}"
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-90}"
INSTALL_FINGERPRINT_FILE="$VENV_DIR/.gateway-flow-published.fingerprint"

if [[ "$(uname -s)" == "Darwin" ]]; then
    DEFAULT_INSTALL_SPEC="abstractflow[apple]"
else
    DEFAULT_INSTALL_SPEC="abstractflow"
fi
PUBLISHED_INSTALL_SPEC="${PUBLISHED_INSTALL_SPEC:-$DEFAULT_INSTALL_SPEC}"
PUBLISHED_INSTALL_MODE="${PUBLISHED_INSTALL_MODE:-auto}"

GATEWAY_HOST="${GATEWAY_HOST:-${ABSTRACTGATEWAY_HOST:-127.0.0.1}}"
GATEWAY_PORT="${GATEWAY_PORT:-${ABSTRACTGATEWAY_PORT:-8080}}"
FLOW_HOST="${FLOW_HOST:-${ABSTRACTFLOW_HOST:-127.0.0.1}}"
FLOW_PORT="${FLOW_PORT:-${ABSTRACTFLOW_PORT:-${PORT:-3000}}}"
GATEWAY_URL="${GATEWAY_URL:-http://${GATEWAY_HOST}:${GATEWAY_PORT}}"
RUNTIME_DIR="${RUNTIME_DIR:-${ABSTRACTFRAMEWORK_RUNTIME_DIR:-$ROOT_DIR/runtime}}"
GATEWAY_RUNTIME_DIR="${GATEWAY_RUNTIME_DIR:-${ABSTRACTGATEWAY_DATA_DIR:-$RUNTIME_DIR}}"
FLOW_RUNTIME_DIR="${FLOW_RUNTIME_DIR:-${ABSTRACTFLOW_RUNTIME_DIR:-$RUNTIME_DIR/flow-published}}"
LOG_DIR="${LOG_DIR:-$RUNTIME_DIR/logs}"
DEFAULT_TOKEN_FILE="${DEFAULT_TOKEN_FILE:-$RUNTIME_DIR/dev/gateway-token}"
STOP_EXISTING="${STOP_EXISTING:-1}"
GATEWAY_HEALTH_URL="http://${GATEWAY_HOST}:${GATEWAY_PORT}/api/health"
GATEWAY_CAPABILITIES_URL="${GATEWAY_URL}/api/gateway/discovery/capabilities"
FLOW_HEALTH_URL="http://${FLOW_HOST}:${FLOW_PORT}/api/health"
FLOW_UI_URL="http://${FLOW_HOST}:${FLOW_PORT}/"

usage() {
    cat <<EOF
Usage: $0

Runs AbstractGateway and AbstractFlow from published PyPI packages in a venv
separate from the local source checkout.

Environment overrides:
  VENV_DIR                         Published-package venv (default: $ROOT_DIR/.venv-gateway-flow-published)
  PYTHON_BOOTSTRAP                 Python used to create the venv (default: python3)
  PUBLISHED_INSTALL_SPEC           Pip spec to install (default: $DEFAULT_INSTALL_SPEC)
  PUBLISHED_INSTALL_MODE           auto, always, or skip (default: auto)
  GATEWAY_HOST / GATEWAY_PORT      Gateway bind (default: 127.0.0.1:8080)
  FLOW_HOST / FLOW_PORT            Flow bind (default: 127.0.0.1:3000)
  RUNTIME_DIR                      Shared runtime root (default: $ROOT_DIR/runtime)
  STARTUP_TIMEOUT_S                Startup readiness timeout in seconds (default: 90)
  STOP_EXISTING                    Kill existing gateway/flow first (default: 1)

Use ./scripts/gateway-flow-local.sh for local source checkout code.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

die() {
    echo "ERROR: $*" >&2
    exit 1
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_executable() {
    [[ -x "$1" ]] || die "required executable not found: $1"
}

show_log_tail() {
    local label="$1"
    local log_file="$2"
    echo "${label}. Last log lines:" >&2
    tail -n 80 "$log_file" >&2 || true
}

published_install_fingerprint() {
    "$PYTHON_BIN" - "$PUBLISHED_INSTALL_SPEC" "$0" "$ROOT_DIR/abstractflow/pyproject.toml" "$ROOT_DIR/abstractgateway/pyproject.toml" <<'PY'
import hashlib
import pathlib
import sys

h = hashlib.sha256()
for item in sys.argv[1:]:
    path = pathlib.Path(item)
    h.update(f"== {item} ==\n".encode("utf-8"))
    if path.exists():
        h.update(path.read_bytes())
    else:
        h.update(b"<missing>\n")
print(h.hexdigest())
PY
}

install_fingerprint_matches() {
    [[ -f "$INSTALL_FINGERPRINT_FILE" ]] || return 1
    local expected actual
    expected="$(published_install_fingerprint)"
    actual="$(tr -d '\r\n' < "$INSTALL_FINGERPRINT_FILE")"
    [[ -n "$actual" && "$actual" == "$expected" ]]
}

install_needed() {
    case "$PUBLISHED_INSTALL_MODE" in
        always) return 0 ;;
        skip) return 1 ;;
        auto)
            [[ ! -x "$BIN_DIR/abstractgateway" || ! -x "$BIN_DIR/abstractflow" ]] && return 0
            install_fingerprint_matches || return 0
            return 1
            ;;
        *) die "PUBLISHED_INSTALL_MODE must be auto, always, or skip" ;;
    esac
}

url_ready() {
    local url="$1"
    "$PYTHON_BIN" - "$url" <<'PY'
import sys
import urllib.request

try:
    with urllib.request.urlopen(sys.argv[1], timeout=1.5) as response:
        sys.exit(0 if response.status < 500 else 1)
except Exception:
    sys.exit(1)
PY
}

gateway_contract_ready() {
    local url="$1"
    local token="${2:-}"
    "$PYTHON_BIN" - "$url" "$token" <<'PY'
import json
import sys
import urllib.request

url = sys.argv[1]
token = sys.argv[2]
headers = {}
if token:
    headers["Authorization"] = f"Bearer {token}"
request = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(request, timeout=2.0) as response:
        if response.status >= 500:
            raise RuntimeError(f"HTTP {response.status}")
        payload = json.load(response)
except Exception:
    raise SystemExit(1)

caps = payload.get("capabilities") if isinstance(payload, dict) else None
contracts = caps.get("contracts") if isinstance(caps, dict) else None
common = contracts.get("common") if isinstance(contracts, dict) else None
flow_editor = contracts.get("flow_editor") if isinstance(contracts, dict) else None
prompt_cache = common.get("prompt_cache") if isinstance(common, dict) else None
durable_blocs = prompt_cache.get("durable_blocs") if isinstance(prompt_cache, dict) else None
model_residency = common.get("model_residency") if isinstance(common, dict) else None
runs = flow_editor.get("runs") if isinstance(flow_editor, dict) else None
ledger = flow_editor.get("ledger") if isinstance(flow_editor, dict) else None

checks = (
    isinstance(contracts, dict),
    isinstance(common, dict),
    isinstance(flow_editor, dict) and bool(flow_editor.get("available", True)),
    bool((runs or {}).get("start", {}).get("endpoint")),
    bool((ledger or {}).get("stream", {}).get("endpoint")),
    isinstance(durable_blocs, dict) and bool(durable_blocs.get("available")),
    isinstance(model_residency, dict) and bool(model_residency.get("available")),
)
raise SystemExit(0 if all(checks) else 1)
PY
}

port_in_use() {
    local host="$1"
    local port="$2"
    "$PYTHON_BIN" - "$host" "$port" <<'PY'
import socket
import sys

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.5)
    sys.exit(0 if sock.connect_ex((sys.argv[1], int(sys.argv[2]))) == 0 else 1)
PY
}

kill_port_listeners() {
    local port="$1"
    local label="$2"
    local pids
    pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
    [[ -z "$pids" ]] && return 0
    echo "Stopping existing listener(s) on port ${port} for ${label}: ${pids//$'\n'/ }"
    kill $pids >/dev/null 2>&1 || true
    sleep 1
    pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
    if [[ -n "$pids" ]]; then
        echo "Force-stopping stubborn listener(s) on port ${port}: ${pids//$'\n'/ }"
        kill -9 $pids >/dev/null 2>&1 || true
    fi
}

kill_matching_processes() {
    local label="$1"
    shift
    local pids=""
    local pattern found
    for pattern in "$@"; do
        found="$(pgrep -f "$pattern" 2>/dev/null || true)"
        [[ -n "$found" ]] && pids+=$'\n'"$found"
    done
    pids="$(
        printf '%s\n' "$pids" \
            | awk 'NF' \
            | sort -u \
            | awk -v self="$$" -v bashpid="${BASHPID:-$$}" '$1 != self && $1 != bashpid'
    )"
    [[ -z "$pids" ]] && return 0
    echo "Stopping existing ${label} process(es): ${pids//$'\n'/ }"
    kill $pids >/dev/null 2>&1 || true
    sleep 1
    local stubborn=""
    local pid
    for pid in $pids; do
        kill -0 "$pid" >/dev/null 2>&1 && stubborn+="$pid "
    done
    if [[ -n "$stubborn" ]]; then
        echo "Force-stopping stubborn ${label} process(es): $stubborn"
        kill -9 $stubborn >/dev/null 2>&1 || true
    fi
}

wait_for_url() {
    local url="$1"
    local timeout_s="${2:-$STARTUP_TIMEOUT_S}"
    local started_at
    started_at="$(date +%s)"
    while true; do
        url_ready "$url" && return 0
        if (( "$(date +%s)" - started_at >= timeout_s )); then
            return 1
        fi
        sleep 1
    done
}

wait_for_gateway_contract() {
    local url="$1"
    local token="${2:-}"
    local timeout_s="${3:-$STARTUP_TIMEOUT_S}"
    local started_at
    started_at="$(date +%s)"
    while true; do
        gateway_contract_ready "$url" "$token" && return 0
        if (( "$(date +%s)" - started_at >= timeout_s )); then
            return 1
        fi
        sleep 1
    done
}

require_cmd "$PYTHON_BOOTSTRAP"
require_cmd lsof
require_cmd pgrep
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating published-package venv: $VENV_DIR"
    "$PYTHON_BOOTSTRAP" -m venv "$VENV_DIR"
fi
require_executable "$PYTHON_BIN"

if install_needed; then
    echo "Installing published package: $PUBLISHED_INSTALL_SPEC"
    "$PYTHON_BIN" -m pip install -U pip
    "$PYTHON_BIN" -m pip install -U "$PUBLISHED_INSTALL_SPEC"
    published_install_fingerprint >"$INSTALL_FINGERPRINT_FILE"
else
    echo "Using existing published-package venv: $VENV_DIR"
fi

require_executable "$BIN_DIR/abstractgateway"
require_executable "$BIN_DIR/abstractflow"

# Published mode must not import packages from this source checkout.
unset PYTHONPATH

if [[ -z "${ABSTRACTGATEWAY_AUTH_TOKEN:-}" && -r "$DEFAULT_TOKEN_FILE" ]]; then
    ABSTRACTGATEWAY_AUTH_TOKEN="$(tr -d '\r\n' < "$DEFAULT_TOKEN_FILE")"
fi

export ABSTRACTGATEWAY_AUTH_TOKEN="${ABSTRACTGATEWAY_AUTH_TOKEN:-local-dev-token}"
export ABSTRACTGATEWAY_HOST="$GATEWAY_HOST"
export ABSTRACTGATEWAY_PORT="$GATEWAY_PORT"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="${ABSTRACTGATEWAY_ALLOWED_ORIGINS:-http://localhost:*,http://127.0.0.1:*}"
export ABSTRACTGATEWAY_DATA_DIR="$GATEWAY_RUNTIME_DIR"
export ABSTRACTFLOW_HOST="$FLOW_HOST"
export ABSTRACTFLOW_PORT="$FLOW_PORT"
export PORT="$FLOW_PORT"
export ABSTRACTFLOW_GATEWAY_URL="$GATEWAY_URL"
export ABSTRACTFLOW_RUNTIME_DIR="$FLOW_RUNTIME_DIR"

mkdir -p "$ABSTRACTGATEWAY_DATA_DIR" "$ABSTRACTFLOW_RUNTIME_DIR" "$LOG_DIR"

if [[ "$STOP_EXISTING" != "0" && "$STOP_EXISTING" != "false" && "$STOP_EXISTING" != "False" ]]; then
    kill_matching_processes "AbstractFlow" "$BIN_DIR/abstractflow[[:space:]]+serve" "abstractflow[[:space:]]+serve"
    kill_matching_processes "AbstractGateway" "$BIN_DIR/abstractgateway[[:space:]]+serve" "abstractgateway[[:space:]]+serve"
fi
kill_port_listeners "$GATEWAY_PORT" "AbstractGateway"
kill_port_listeners "$FLOW_PORT" "AbstractFlow"

port_in_use "$GATEWAY_HOST" "$GATEWAY_PORT" && die "gateway port is already in use: ${GATEWAY_HOST}:${GATEWAY_PORT}"
port_in_use "$FLOW_HOST" "$FLOW_PORT" && die "flow port is already in use: ${FLOW_HOST}:${FLOW_PORT}"

GATEWAY_LOG="$LOG_DIR/gateway.log"
FLOW_LOG="$LOG_DIR/flow.log"
GATEWAY_PID=""
FLOW_PID=""

cleanup() {
    local status=$?
    trap - EXIT INT TERM
    [[ -n "$FLOW_PID" ]] && kill "$FLOW_PID" >/dev/null 2>&1 || true
    [[ -n "$GATEWAY_PID" ]] && kill "$GATEWAY_PID" >/dev/null 2>&1 || true
    [[ -n "$FLOW_PID" ]] && wait "$FLOW_PID" >/dev/null 2>&1 || true
    [[ -n "$GATEWAY_PID" ]] && wait "$GATEWAY_PID" >/dev/null 2>&1 || true
    exit "$status"
}
trap cleanup EXIT INT TERM

echo "Starting AbstractGateway on http://${GATEWAY_HOST}:${GATEWAY_PORT}"
echo "Gateway command: $BIN_DIR/abstractgateway serve"
echo "Gateway log: $GATEWAY_LOG"
"$BIN_DIR/abstractgateway" serve --host "$GATEWAY_HOST" --port "$GATEWAY_PORT" >"$GATEWAY_LOG" 2>&1 &
GATEWAY_PID=$!

if ! wait_for_url "$GATEWAY_HEALTH_URL"; then
    show_log_tail "Gateway did not become healthy" "$GATEWAY_LOG"
    exit 1
fi

if ! wait_for_gateway_contract "$GATEWAY_CAPABILITIES_URL" "$ABSTRACTGATEWAY_AUTH_TOKEN"; then
    show_log_tail "Gateway did not expose the Flow contract" "$GATEWAY_LOG"
    exit 1
fi

echo "Starting AbstractFlow on http://${FLOW_HOST}:${FLOW_PORT}"
echo "Flow command: $BIN_DIR/abstractflow serve"
echo "Flow log: $FLOW_LOG"
"$BIN_DIR/abstractflow" serve \
    --host "$FLOW_HOST" \
    --port "$FLOW_PORT" \
    --gateway-url "$GATEWAY_URL" \
    --gateway-token "$ABSTRACTGATEWAY_AUTH_TOKEN" \
    >"$FLOW_LOG" 2>&1 &
FLOW_PID=$!

if ! wait_for_url "$FLOW_HEALTH_URL"; then
    show_log_tail "Flow backend did not become healthy" "$FLOW_LOG"
    exit 1
fi

if ! wait_for_url "$FLOW_UI_URL"; then
    show_log_tail "Flow UI did not become ready" "$FLOW_LOG"
    exit 1
fi

cat <<EOF

AbstractGateway: http://${GATEWAY_HOST}:${GATEWAY_PORT}
Gateway caps:   $GATEWAY_CAPABILITIES_URL
AbstractFlow:   http://${FLOW_HOST}:${FLOW_PORT}
Runtime root:    $RUNTIME_DIR
Gateway runtime: $ABSTRACTGATEWAY_DATA_DIR
Flow runtime:    $ABSTRACTFLOW_RUNTIME_DIR
Gateway token:   $ABSTRACTGATEWAY_AUTH_TOKEN

Press Ctrl-C to stop both processes.
EOF

while true; do
    if ! kill -0 "$GATEWAY_PID" >/dev/null 2>&1; then
        show_log_tail "Gateway exited" "$GATEWAY_LOG"
        exit 1
    fi
    if ! kill -0 "$FLOW_PID" >/dev/null 2>&1; then
        show_log_tail "Flow exited" "$FLOW_LOG"
        exit 1
    fi
    sleep 2
done
