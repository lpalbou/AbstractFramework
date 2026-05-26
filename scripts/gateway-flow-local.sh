#!/usr/bin/env bash
# Run AbstractGateway and AbstractFlow from this source checkout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
BIN_DIR="$VENV_DIR/bin"
PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-$BIN_DIR/python}}"
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-90}"

GATEWAY_HOST="${GATEWAY_HOST:-${ABSTRACTGATEWAY_HOST:-127.0.0.1}}"
GATEWAY_PORT="${GATEWAY_PORT:-${ABSTRACTGATEWAY_PORT:-8080}}"
FLOW_HOST="${FLOW_HOST:-${ABSTRACTFLOW_HOST:-127.0.0.1}}"
FLOW_PORT="${FLOW_PORT:-${ABSTRACTFLOW_PORT:-${PORT:-3000}}}"
GATEWAY_URL="${GATEWAY_URL:-http://${GATEWAY_HOST}:${GATEWAY_PORT}}"
RUNTIME_DIR="${RUNTIME_DIR:-${ABSTRACTFRAMEWORK_RUNTIME_DIR:-$ROOT_DIR/runtime}}"
GATEWAY_RUNTIME_DIR="${GATEWAY_RUNTIME_DIR:-${ABSTRACTGATEWAY_DATA_DIR:-$RUNTIME_DIR}}"
FLOW_RUNTIME_DIR="${FLOW_RUNTIME_DIR:-${ABSTRACTFLOW_RUNTIME_DIR:-$RUNTIME_DIR/flow-local}}"
LOG_DIR="${LOG_DIR:-$RUNTIME_DIR/logs}"
DEFAULT_TOKEN_FILE="${DEFAULT_TOKEN_FILE:-$RUNTIME_DIR/dev/gateway-token}"
STOP_EXISTING="${STOP_EXISTING:-1}"
FLOW_DIST_INDEX="$ROOT_DIR/abstractflow/web/frontend/dist/index.html"
GATEWAY_HEALTH_URL="http://${GATEWAY_HOST}:${GATEWAY_PORT}/api/health"
GATEWAY_CAPABILITIES_URL="${GATEWAY_URL}/api/gateway/discovery/capabilities"
FLOW_HEALTH_URL="http://${FLOW_HOST}:${FLOW_PORT}/api/health"
FLOW_UI_URL="http://${FLOW_HOST}:${FLOW_PORT}/"

usage() {
    cat <<EOF
Usage: $0 [--base|--apple|--gpu]

Runs AbstractGateway and AbstractFlow from the local sibling repositories, not
from published PyPI packages. The script prepends local package paths to
PYTHONPATH and starts gateway/flow with python -m.

Environment overrides:
  VENV_DIR                         Local development venv (default: $ROOT_DIR/.venv)
  PYTHON_BIN / PYTHON              Python executable (default: VENV_DIR/bin/python)
  GATEWAY_HOST / GATEWAY_PORT      Gateway bind (default: 127.0.0.1:8080)
  FLOW_HOST / FLOW_PORT            Flow bind (default: 127.0.0.1:3000)
  RUNTIME_DIR                      Shared runtime root (default: $ROOT_DIR/runtime)
  STARTUP_TIMEOUT_S                Startup readiness timeout in seconds (default: 90)
  STOP_EXISTING                    Kill existing gateway/flow first (default: 1)

Build local dependencies first when needed:
  ./scripts/build.sh          # light editable install
  ./scripts/build.sh --apple  # Apple local engines
  ./scripts/build.sh --gpu    # GPU local engines

Passing --base / --apple / --gpu to this launcher triggers the matching
Python-only local editable install before starting Gateway and Flow.
EOF
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

BUILD_PROFILE_FLAG=""
for arg in "$@"; do
    case "$arg" in
        -h|--help)
            usage
            exit 0
            ;;
        --base|--apple|--gpu)
            if [[ -n "$BUILD_PROFILE_FLAG" && "$BUILD_PROFILE_FLAG" != "$arg" ]]; then
                die "conflicting profile flags: $BUILD_PROFILE_FLAG and $arg"
            fi
            BUILD_PROFILE_FLAG="$arg"
            ;;
        *)
            die "unsupported argument: $arg"
            ;;
    esac
done

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

require_cmd lsof
require_cmd pgrep

if [[ -n "$BUILD_PROFILE_FLAG" ]]; then
    echo "Preparing local Python packages with ./scripts/build.sh --python $BUILD_PROFILE_FLAG"
    bash "$SCRIPT_DIR/build.sh" --python "$BUILD_PROFILE_FLAG"
fi

require_executable "$PYTHON_BIN"

LOCAL_PATHS=()
add_path() {
    local path="$1"
    [[ -d "$path" ]] || return 0
    local existing
    if (( ${#LOCAL_PATHS[@]} > 0 )); then
        for existing in "${LOCAL_PATHS[@]}"; do
            [[ "$existing" == "$path" ]] && return 0
        done
    fi
    LOCAL_PATHS+=("$path")
}
add_repo_paths() {
    local repo="$1"
    local repo_dir="$ROOT_DIR/$repo"
    [[ -d "$repo_dir" ]] || return 0
    add_path "$repo_dir/src"
    add_path "$repo_dir"
}

add_path "$ROOT_DIR"
add_repo_paths "abstractsemantics"
add_repo_paths "abstractmemory"
add_repo_paths "abstractvision"
add_repo_paths "abstractvoice"
add_repo_paths "abstractmusic"
add_repo_paths "abstractcore"
add_repo_paths "abstractruntime"
add_repo_paths "abstractagent"
add_repo_paths "abstractgateway"
add_repo_paths "abstractflow"
add_path "$ROOT_DIR/abstractflow/web"
add_repo_paths "abstractcode"
add_repo_paths "abstractassistant"
add_repo_paths "abstractobserver"
add_repo_paths "abstractuic"
add_repo_paths "smartnote"
add_path "$ROOT_DIR/ai-space/src"
add_path "$ROOT_DIR/ai-space"

PYTHONPATH_PREFIX=""
if (( ${#LOCAL_PATHS[@]} > 0 )); then
    for path in "${LOCAL_PATHS[@]}"; do
        if [[ -z "$PYTHONPATH_PREFIX" ]]; then
            PYTHONPATH_PREFIX="$path"
        else
            PYTHONPATH_PREFIX="$PYTHONPATH_PREFIX:$path"
        fi
    done
fi
if [[ -n "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PYTHONPATH_PREFIX:$PYTHONPATH"
else
    export PYTHONPATH="$PYTHONPATH_PREFIX"
fi

"$PYTHON_BIN" - <<'PY'
import importlib
import sys

required = ("abstractgateway", "abstractflow", "abstractruntime", "abstractcore")
for name in required:
    mod = importlib.import_module(name)
    path = getattr(mod, "__file__", None)
    if not path:
        raise SystemExit(f"{name} resolved without a source file; check PYTHONPATH")
print("Local source imports:")
for name in required:
    mod = importlib.import_module(name)
    print(f"  {name}: {getattr(mod, '__file__', '')}")
sys.stdout.flush()
PY

[[ -f "$FLOW_DIST_INDEX" ]] || die "AbstractFlow frontend dist is missing: $FLOW_DIST_INDEX. Run ./scripts/build.sh or npm --prefix abstractflow/web/frontend run build."

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
    kill_matching_processes "AbstractFlow" \
        "$BIN_DIR/abstractflow[[:space:]]+serve" \
        "abstractflow[[:space:]]+serve" \
        "python[^[:space:]]*[[:space:]].*-m[[:space:]]+abstractflow.cli[[:space:]]+serve"
    kill_matching_processes "AbstractGateway" \
        "$BIN_DIR/abstractgateway[[:space:]]+serve" \
        "abstractgateway[[:space:]]+serve" \
        "python[^[:space:]]*[[:space:]].*-m[[:space:]]+abstractgateway.cli[[:space:]]+serve"
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
echo "Gateway command: $PYTHON_BIN -m abstractgateway.cli serve"
echo "Gateway log: $GATEWAY_LOG"
"$PYTHON_BIN" -m abstractgateway.cli serve --host "$GATEWAY_HOST" --port "$GATEWAY_PORT" >"$GATEWAY_LOG" 2>&1 &
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
echo "Flow command: $PYTHON_BIN -m abstractflow.cli serve"
echo "Flow log: $FLOW_LOG"
"$PYTHON_BIN" -m abstractflow.cli serve \
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
Gateway caps:    $GATEWAY_CAPABILITIES_URL
AbstractFlow:    http://${FLOW_HOST}:${FLOW_PORT}
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
