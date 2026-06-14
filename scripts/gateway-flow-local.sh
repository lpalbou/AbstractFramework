#!/usr/bin/env bash
# Run AbstractGateway, AbstractFlow, and AbstractObserver from this source checkout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
BIN_DIR="$VENV_DIR/bin"
PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-$BIN_DIR/python}}"
NODE_BIN="${NODE_BIN:-node}"
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-90}"
VERBOSE="${VERBOSE:-0}"

GATEWAY_HOST="${GATEWAY_HOST:-${ABSTRACTGATEWAY_HOST:-0.0.0.0}}"
GATEWAY_PORT="${GATEWAY_PORT:-${ABSTRACTGATEWAY_PORT:-8080}}"
FLOW_HOST="${FLOW_HOST:-${ABSTRACTFLOW_HOST:-0.0.0.0}}"
FLOW_PORT="${FLOW_PORT:-${ABSTRACTFLOW_PORT:-${PORT:-3000}}}"
OBSERVER_HOST="${OBSERVER_HOST:-${ABSTRACTOBSERVER_HOST:-0.0.0.0}}"
OBSERVER_PORT="${OBSERVER_PORT:-${ABSTRACTOBSERVER_PORT:-3001}}"
case "$GATEWAY_HOST" in
    0.0.0.0|::) GATEWAY_CONNECT_HOST="${GATEWAY_CONNECT_HOST:-127.0.0.1}" ;;
    *) GATEWAY_CONNECT_HOST="${GATEWAY_CONNECT_HOST:-$GATEWAY_HOST}" ;;
esac
case "$FLOW_HOST" in
    0.0.0.0|::) FLOW_CONNECT_HOST="${FLOW_CONNECT_HOST:-127.0.0.1}" ;;
    *) FLOW_CONNECT_HOST="${FLOW_CONNECT_HOST:-$FLOW_HOST}" ;;
esac
case "$OBSERVER_HOST" in
    0.0.0.0|::) OBSERVER_CONNECT_HOST="${OBSERVER_CONNECT_HOST:-127.0.0.1}" ;;
    *) OBSERVER_CONNECT_HOST="${OBSERVER_CONNECT_HOST:-$OBSERVER_HOST}" ;;
esac
PUBLIC_HOST="${PUBLIC_HOST:-${LAN_HOST:-${ABSTRACTFRAMEWORK_PUBLIC_HOST:-}}}"
GATEWAY_PUBLIC_HOST="${GATEWAY_PUBLIC_HOST:-${ABSTRACTGATEWAY_PUBLIC_HOST:-$PUBLIC_HOST}}"
FLOW_PUBLIC_HOST="${FLOW_PUBLIC_HOST:-${ABSTRACTFLOW_PUBLIC_HOST:-$PUBLIC_HOST}}"
OBSERVER_PUBLIC_HOST="${OBSERVER_PUBLIC_HOST:-${ABSTRACTOBSERVER_PUBLIC_HOST:-$PUBLIC_HOST}}"
GATEWAY_URL="${GATEWAY_URL:-http://${GATEWAY_CONNECT_HOST}:${GATEWAY_PORT}}"
RUNTIME_DIR="${RUNTIME_DIR:-${ABSTRACTFRAMEWORK_RUNTIME_DIR:-$ROOT_DIR/runtime}}"
GATEWAY_RUNTIME_DIR="${GATEWAY_RUNTIME_DIR:-${ABSTRACTGATEWAY_DATA_DIR:-$RUNTIME_DIR}}"
GATEWAY_FLOWS_DIR="${GATEWAY_FLOWS_DIR:-${ABSTRACTGATEWAY_FLOWS_DIR:-$ROOT_DIR/abstractgateway/flows/bundles}}"
LOG_DIR="${LOG_DIR:-$RUNTIME_DIR/logs}"
DEFAULT_TOKEN_FILE="${DEFAULT_TOKEN_FILE:-$RUNTIME_DIR/dev/gateway-token}"
LOCAL_GATEWAY_USERS="${LOCAL_GATEWAY_USERS:-${ABSTRACTGATEWAY_LOCAL_USERS:-admin}}"
LOCAL_GATEWAY_USER_TENANT="${LOCAL_GATEWAY_USER_TENANT:-default}"
LOCAL_GATEWAY_USER_TOKENS_FILE="${LOCAL_GATEWAY_USER_TOKENS_FILE:-$RUNTIME_DIR/dev/gateway-user-tokens.json}"
LOCAL_GATEWAY_ROTATE_USER_TOKENS="${LOCAL_GATEWAY_ROTATE_USER_TOKENS:-0}"
SHOW_ALL_GATEWAY_USERS="${SHOW_ALL_GATEWAY_USERS:-0}"
SHOW_ADMIN_TOKEN="${SHOW_ADMIN_TOKEN:-0}"
STOP_EXISTING="${STOP_EXISTING:-1}"
FLOW_DIST_INDEX="$ROOT_DIR/abstractflow/dist/index.html"
OBSERVER_DIST_INDEX="$ROOT_DIR/abstractobserver/dist/index.html"
GATEWAY_HEALTH_URL="http://${GATEWAY_CONNECT_HOST}:${GATEWAY_PORT}/api/health"
GATEWAY_CAPABILITIES_URL="${GATEWAY_URL}/api/gateway/discovery/capabilities"
FLOW_HEALTH_URL="http://${FLOW_CONNECT_HOST}:${FLOW_PORT}/api/health"
FLOW_UI_URL="http://${FLOW_CONNECT_HOST}:${FLOW_PORT}/"
OBSERVER_UI_URL="http://${OBSERVER_CONNECT_HOST}:${OBSERVER_PORT}/"

usage() {
    cat <<EOF
Usage: $0 [--light|--apple|--gpu]

Runs AbstractGateway from local Python sources and AbstractFlow/AbstractObserver
from local web package sources. The script prepends local Python package paths
to PYTHONPATH for Gateway and starts the web UIs with Node.

Environment overrides:
  VENV_DIR                         Local development venv (default: $ROOT_DIR/.venv)
  PYTHON_BIN / PYTHON              Python executable (default: VENV_DIR/bin/python)
  NODE_BIN                         Node executable for AbstractFlow/Observer (default: node)
  GATEWAY_HOST / GATEWAY_PORT      Gateway bind (default: 0.0.0.0:8080 for LAN access)
  GATEWAY_URL                      Gateway URL used by Flow/Observer proxies (default: loopback Gateway URL)
  PUBLIC_HOST / LAN_HOST           LAN hostname/IP to print for all services (default: auto-detect)
  GATEWAY_PUBLIC_HOST              LAN hostname/IP to print for Gateway (default: PUBLIC_HOST)
  FLOW_HOST / FLOW_PORT            Flow bind (default: 0.0.0.0:3000 for LAN access)
  FLOW_PUBLIC_HOST                 LAN hostname/IP to print for Flow (default: PUBLIC_HOST)
  OBSERVER_HOST / OBSERVER_PORT    Observer bind (default: 0.0.0.0:3001 for LAN access)
  OBSERVER_PUBLIC_HOST             LAN hostname/IP to print for Observer (default: PUBLIC_HOST)
  RUNTIME_DIR                      Shared runtime root (default: $ROOT_DIR/runtime)
  GATEWAY_FLOWS_DIR                Gateway bundle dir (default: abstractgateway/flows/bundles)
  LOCAL_GATEWAY_USERS              Comma-separated local dev users to ensure (default: admin)
  LOCAL_GATEWAY_USER_TENANT        Tenant for ensured local dev users (default: default)
  LOCAL_GATEWAY_USER_TOKENS_FILE   Local plaintext dev-token cache
  LOCAL_GATEWAY_ROTATE_USER_TOKENS Rotate non-local users missing cached tokens (default: 0)
  SHOW_ALL_GATEWAY_USERS           Also list non-local registry users (default: 0)
  SHOW_ADMIN_TOKEN                 Print the admin token in the final banner (default: 0)
  VERBOSE                          Print local import paths and commands (default: 0)
  STARTUP_TIMEOUT_S                Startup readiness timeout in seconds (default: 90)
  STOP_EXISTING                    Kill existing gateway/flow/observer first (default: 1)

Build local dependencies first when needed:
  ./scripts/build.sh          # light editable install
  ./scripts/build.sh --light  # explicit light editable install
  ./scripts/build.sh --apple  # Apple local engines
  ./scripts/build.sh --gpu    # GPU local engines

Passing --light / --apple / --gpu to this launcher triggers the matching
Python local editable install plus npm build before starting Gateway, Flow, and
Observer. --base is accepted as a legacy alias for --light.
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
        --light|--base|--apple|--gpu)
            normalized_arg="$arg"
            if [[ "$normalized_arg" == "--base" ]]; then
                normalized_arg="--light"
            fi
            if [[ -n "$BUILD_PROFILE_FLAG" && "$BUILD_PROFILE_FLAG" != "$normalized_arg" ]]; then
                die "conflicting profile flags: $BUILD_PROFILE_FLAG and $arg"
            fi
            BUILD_PROFILE_FLAG="$normalized_arg"
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

is_truthy() {
    case "${1:-}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
        *) return 1 ;;
    esac
}

is_wildcard_host() {
    case "${1:-}" in
        0.0.0.0|::) return 0 ;;
        *) return 1 ;;
    esac
}

is_loopback_host() {
    case "${1:-}" in
        localhost|127.*|::1) return 0 ;;
        *) return 1 ;;
    esac
}

detect_lan_host() {
    "$PYTHON_BIN" - <<'PY'
import socket
import sys


def emit(ip: str) -> None:
    ip = str(ip or "").strip()
    if ip and not ip.startswith("127.") and ip != "0.0.0.0":
        print(ip)
        raise SystemExit(0)


try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.2)
        sock.connect(("8.8.8.8", 80))
        emit(sock.getsockname()[0])
except Exception:
    pass

try:
    infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM)
except Exception:
    infos = []

seen: set[str] = set()
for info in infos:
    ip = str(info[4][0])
    if ip in seen:
        continue
    seen.add(ip)
    emit(ip)

sys.exit(1)
PY
}

append_default_gateway_origin() {
    local origin="$1"
    [[ -n "$origin" ]] || return 0
    case ",$DEFAULT_GATEWAY_ALLOWED_ORIGINS," in
        *,"$origin",*) return 0 ;;
    esac
    DEFAULT_GATEWAY_ALLOWED_ORIGINS="${DEFAULT_GATEWAY_ALLOWED_ORIGINS},${origin}"
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
    prompt_cache is None or isinstance(prompt_cache, dict),
    durable_blocs is None or isinstance(durable_blocs, dict),
    model_residency is None or isinstance(model_residency, dict),
)
raise SystemExit(0 if all(checks) else 1)
PY
}

prepare_gateway_local_users() {
    local users_csv="$1"
    local tenant_id="$2"
    local token_cache_file="$3"
    local rotate_tokens="$4"
    local gateway_url="$5"
    local show_all_users="$6"
    local verbose="$7"
    "$PYTHON_BIN" - "$users_csv" "$tenant_id" "$token_cache_file" "$rotate_tokens" "$gateway_url" "$show_all_users" "$verbose" <<'PY'
import datetime
import json
import stat
import sys
import urllib.request
from pathlib import Path
from typing import Any

from abstractgateway.security.principal import safe_principal_component
from abstractgateway.users import GatewayUserRegistry, gateway_user_auth_enabled


def _as_bool(raw: Any, default: bool = False) -> bool:
    if raw is None:
        return default
    value = str(raw).strip().lower()
    if not value:
        return default
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


users_csv, tenant_raw, cache_raw, rotate_raw, gateway_url, show_all_raw, verbose_raw = sys.argv[1:8]
rotate_missing = _as_bool(rotate_raw, False)
show_all = _as_bool(show_all_raw, False)
verbose = _as_bool(verbose_raw, False)

if not gateway_user_auth_enabled():
    print("Gateway user auth: disabled")
    print("Set ABSTRACTGATEWAY_USER_AUTH=1 to use per-user Flow sign-in tokens.")
    raise SystemExit(0)

tenant = safe_principal_component(tenant_raw, default="default")
configured_users: list[str] = []
for part in str(users_csv or "").replace("\n", ",").split(","):
    user_id = safe_principal_component(part, default="")
    if user_id and user_id not in configured_users:
        configured_users.append(user_id)

cache_path = Path(cache_raw).expanduser().resolve()
cache: dict[str, Any] = {"version": 1, "users": {}}
if cache_path.exists():
    try:
        loaded = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            cache = loaded
    except Exception as exc:
        raise SystemExit(f"Invalid local Gateway user token cache: {cache_path}: {exc}") from exc
cache["version"] = 1
cache_users = cache.setdefault("users", {})
if not isinstance(cache_users, dict):
    cache_users = {}
    cache["users"] = cache_users

registry = GatewayUserRegistry()
events: list[str] = []


def _cache_key(tenant_id: str, user_id: str) -> str:
    return f"{tenant_id}:{user_id}"


def _cached_token(tenant_id: str, user_id: str) -> str:
    entry = cache_users.get(_cache_key(tenant_id, user_id))
    if isinstance(entry, dict):
        return str(entry.get("token") or "").strip()
    if isinstance(entry, str):
        return entry.strip()
    return ""


def _remember_token(rec, token: str, reason: str) -> None:
    if not token:
        return
    cache_users[rec.key] = {
        "token": token,
        "tenant_id": rec.tenant_id,
        "user_id": rec.user_id,
        "runtime_id": rec.runtime_id or rec.user_id,
        "updated_at": _now(),
        "reason": reason,
    }


def _token_matches(rec, token: str) -> bool:
    if not token:
        return False
    principal = registry.authenticate(token)
    return bool(
        principal
        and principal.user_id == rec.user_id
        and principal.tenant_id == rec.tenant_id
        and principal.runtime_id == (rec.runtime_id or rec.user_id)
    )


configured_keys: set[str] = set()
for user_id in configured_users:
    configured_keys.add(_cache_key(tenant, user_id))
    desired_roles = ["admin", "user"] if user_id == "admin" else ["user"]
    desired_runtime_id = "default" if user_id == "admin" and tenant == "default" else user_id
    rec = registry.get_user(user_id, tenant_id=tenant)
    if rec is None:
        cached = _cached_token(tenant, user_id)
        rec, issued = registry.create_user(
            user_id=user_id,
            tenant_id=tenant,
            roles=desired_roles,
            runtime_id=desired_runtime_id,
            token=cached or None,
        )
        _remember_token(rec, issued, "created")
        events.append(f"created local Gateway user {rec.tenant_id}/{rec.user_id}")
        continue

    if user_id == "admin" and "admin" not in set(rec.roles):
        rec, _issued = registry.update_user(
            user_id=rec.user_id,
            tenant_id=rec.tenant_id,
            roles=desired_roles,
            enabled=True,
        )
        events.append(f"promoted local Gateway user {rec.tenant_id}/{rec.user_id} to admin")

    if rec.runtime_id != desired_runtime_id:
        previous_token = _cached_token(rec.tenant_id, rec.user_id)
        rec, _issued = registry.update_user(
            user_id=rec.user_id,
            tenant_id=rec.tenant_id,
            runtime_id=desired_runtime_id,
            enabled=True,
        )
        if previous_token:
            _remember_token(rec, previous_token, "runtime-moved")
        events.append(f"moved local Gateway user {rec.tenant_id}/{rec.user_id} to runtime {desired_runtime_id}")

    cached = _cached_token(rec.tenant_id, rec.user_id)
    if not _token_matches(rec, cached):
        rec, issued = registry.update_user(
            user_id=rec.user_id,
            tenant_id=rec.tenant_id,
            enabled=True,
            token="",
        )
        if issued:
            _remember_token(rec, issued, "rotated-local-user")
            events.append(f"rotated local Gateway user token for {rec.tenant_id}/{rec.user_id}")

rows: list[dict[str, str]] = []
for rec in registry.list_users():
    is_configured = rec.key in configured_keys
    if not is_configured and not show_all:
        continue
    token = _cached_token(rec.tenant_id, rec.user_id)
    if not _token_matches(rec, token):
        if rotate_missing and not is_configured:
            rec, issued = registry.update_user(
                user_id=rec.user_id,
                tenant_id=rec.tenant_id,
                token="",
            )
            token = issued or ""
            _remember_token(rec, token, "rotated-missing-cache")
            events.append(f"rotated Gateway user token for {rec.tenant_id}/{rec.user_id}")
        else:
            token = ""
    rows.append(
        {
            "tenant": rec.tenant_id,
            "user": rec.user_id,
            "runtime": rec.runtime_id or rec.user_id,
            "enabled": "yes" if rec.enabled else "no",
            "token": token,
            "configured": "yes" if is_configured else "no",
        }
    )

if cache_users:
    cache["updated_at"] = _now()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
    tmp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(cache_path)
    try:
        cache_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass

def _gateway_me(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    request = urllib.request.Request(
        gateway_url.rstrip("/") + "/api/gateway/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=2.0) as response:
            payload = json.load(response)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    principal = payload.get("principal")
    return principal if isinstance(principal, dict) else None


for row in rows:
    principal = _gateway_me(row["token"])
    row["verified"] = "no"
    if (
        principal
        and principal.get("tenant_id") == row["tenant"]
        and principal.get("user_id") == row["user"]
        and principal.get("runtime_id") == row["runtime"]
    ):
        row["verified"] = "yes"

configured_rows = [row for row in rows if row["configured"] == "yes"]
other_rows = [row for row in rows if row["configured"] != "yes"]

print("Use this in AbstractFlow:")
print(f"  Gateway URL: {gateway_url}")
if len(configured_rows) == 1:
    row = configured_rows[0]
    token = row["token"] if row["verified"] == "yes" else "<token unavailable>"
    print(f"  User:        {row['user']}")
    print(f"  Token:       {token}")
else:
    print("  Users:")
    user_w = max(4, *(len(row["user"]) for row in configured_rows)) if configured_rows else 4
    print(f"    {'user':<{user_w}}  token")
    if not configured_rows:
        print(f"    {'(none)':<{user_w}}  <none>")
    for row in configured_rows:
        token = row["token"] if row["verified"] == "yes" else "<token unavailable>"
        print(f"    {row['user']:<{user_w}}  {token}")

if other_rows:
    print()
    print("Other registered users:")
    user_w = max(4, *(len(row["user"]) for row in other_rows))
    print(f"  {'user':<{user_w}}  token")
    for row in other_rows:
        token = row["token"] if row["verified"] == "yes" else "<token unavailable>"
        print(f"  {row['user']:<{user_w}}  {token}")

if verbose:
    print()
    print(f"Token cache: {cache_path}")
if events and verbose:
    print("  Changes:")
    for event in events:
        print(f"    - {event}")
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
    local child_pid="${3:-}"
    local started_at
    started_at="$(date +%s)"
    while true; do
        url_ready "$url" && return 0
        if [[ -n "$child_pid" ]] && ! kill -0 "$child_pid" >/dev/null 2>&1; then
            return 1
        fi
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
    local child_pid="${4:-}"
    local started_at
    started_at="$(date +%s)"
    while true; do
        gateway_contract_ready "$url" "$token" && return 0
        if [[ -n "$child_pid" ]] && ! kill -0 "$child_pid" >/dev/null 2>&1; then
            return 1
        fi
        if (( "$(date +%s)" - started_at >= timeout_s )); then
            return 1
        fi
        sleep 1
    done
}

require_cmd lsof
require_cmd pgrep
require_cmd mktemp
require_cmd "$NODE_BIN"

if [[ -n "$BUILD_PROFILE_FLAG" ]]; then
    echo "Preparing local packages with ./scripts/build.sh $BUILD_PROFILE_FLAG"
    bash "$SCRIPT_DIR/build.sh" "$BUILD_PROFILE_FLAG"
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

"$PYTHON_BIN" - "$VERBOSE" <<'PY'
import importlib
import sys

def _truthy(raw: str) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}

verbose = _truthy(sys.argv[1] if len(sys.argv) > 1 else "")
required = ("abstractgateway", "abstractruntime", "abstractcore")
resolved = {}
for name in required:
    mod = importlib.import_module(name)
    path = getattr(mod, "__file__", None)
    if not path:
        raise SystemExit(f"{name} resolved without a source file; check PYTHONPATH")
    resolved[name] = path
if verbose:
    print("Local source imports:")
    for name in required:
        print(f"  {name}: {resolved[name]}")
sys.stdout.flush()
PY

[[ -f "$FLOW_DIST_INDEX" ]] || die "AbstractFlow dist is missing: $FLOW_DIST_INDEX. Run ./scripts/build.sh or npm --prefix abstractflow run build."
[[ -f "$OBSERVER_DIST_INDEX" ]] || die "AbstractObserver dist is missing: $OBSERVER_DIST_INDEX. Run ./scripts/build.sh or npm --prefix abstractobserver run build."
[[ -f "$GATEWAY_FLOWS_DIR/basic-agent.flow" ]] || die "Gateway bundle dir must contain basic-agent: $GATEWAY_FLOWS_DIR"

DETECTED_PUBLIC_HOST=""
if { [[ -z "$GATEWAY_PUBLIC_HOST" ]] && is_wildcard_host "$GATEWAY_HOST"; } || \
    { [[ -z "$FLOW_PUBLIC_HOST" ]] && is_wildcard_host "$FLOW_HOST"; } || \
    { [[ -z "$OBSERVER_PUBLIC_HOST" ]] && is_wildcard_host "$OBSERVER_HOST"; }; then
    DETECTED_PUBLIC_HOST="$(detect_lan_host 2>/dev/null || true)"
fi
if [[ -z "$GATEWAY_PUBLIC_HOST" ]] && is_wildcard_host "$GATEWAY_HOST"; then
    GATEWAY_PUBLIC_HOST="$DETECTED_PUBLIC_HOST"
fi
if [[ -z "$FLOW_PUBLIC_HOST" ]] && is_wildcard_host "$FLOW_HOST"; then
    FLOW_PUBLIC_HOST="$DETECTED_PUBLIC_HOST"
fi
if [[ -z "$OBSERVER_PUBLIC_HOST" ]] && is_wildcard_host "$OBSERVER_HOST"; then
    OBSERVER_PUBLIC_HOST="$DETECTED_PUBLIC_HOST"
fi

GATEWAY_LOCAL_URL="http://${GATEWAY_CONNECT_HOST}:${GATEWAY_PORT}"
GATEWAY_NETWORK_URL=""
if [[ -n "$GATEWAY_PUBLIC_HOST" ]]; then
    GATEWAY_NETWORK_URL="http://${GATEWAY_PUBLIC_HOST}:${GATEWAY_PORT}"
elif is_wildcard_host "$GATEWAY_HOST"; then
    GATEWAY_NETWORK_URL="http://<this-machine-LAN-IP>:${GATEWAY_PORT}"
elif ! is_loopback_host "$GATEWAY_HOST"; then
    GATEWAY_NETWORK_URL="http://${GATEWAY_HOST}:${GATEWAY_PORT}"
fi

FLOW_LOCAL_URL="http://${FLOW_CONNECT_HOST}:${FLOW_PORT}"
FLOW_NETWORK_URL=""
if [[ -n "$FLOW_PUBLIC_HOST" ]]; then
    FLOW_NETWORK_URL="http://${FLOW_PUBLIC_HOST}:${FLOW_PORT}"
elif is_wildcard_host "$FLOW_HOST"; then
    FLOW_NETWORK_URL="http://<this-machine-LAN-IP>:${FLOW_PORT}"
elif ! is_loopback_host "$FLOW_HOST"; then
    FLOW_NETWORK_URL="http://${FLOW_HOST}:${FLOW_PORT}"
fi

OBSERVER_LOCAL_URL="http://${OBSERVER_CONNECT_HOST}:${OBSERVER_PORT}"
OBSERVER_NETWORK_URL=""
if [[ -n "$OBSERVER_PUBLIC_HOST" ]]; then
    OBSERVER_NETWORK_URL="http://${OBSERVER_PUBLIC_HOST}:${OBSERVER_PORT}"
elif is_wildcard_host "$OBSERVER_HOST"; then
    OBSERVER_NETWORK_URL="http://<this-machine-LAN-IP>:${OBSERVER_PORT}"
elif ! is_loopback_host "$OBSERVER_HOST"; then
    OBSERVER_NETWORK_URL="http://${OBSERVER_HOST}:${OBSERVER_PORT}"
fi

DEFAULT_GATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
if [[ -n "$FLOW_PUBLIC_HOST" ]]; then
    append_default_gateway_origin "http://${FLOW_PUBLIC_HOST}:${FLOW_PORT}"
elif ! is_wildcard_host "$FLOW_HOST" && ! is_loopback_host "$FLOW_HOST"; then
    append_default_gateway_origin "http://${FLOW_HOST}:${FLOW_PORT}"
fi
if [[ -n "$OBSERVER_PUBLIC_HOST" ]]; then
    append_default_gateway_origin "http://${OBSERVER_PUBLIC_HOST}:${OBSERVER_PORT}"
elif ! is_wildcard_host "$OBSERVER_HOST" && ! is_loopback_host "$OBSERVER_HOST"; then
    append_default_gateway_origin "http://${OBSERVER_HOST}:${OBSERVER_PORT}"
fi
if [[ -n "$GATEWAY_PUBLIC_HOST" ]]; then
    append_default_gateway_origin "http://${GATEWAY_PUBLIC_HOST}:${GATEWAY_PORT}"
elif ! is_wildcard_host "$GATEWAY_HOST" && ! is_loopback_host "$GATEWAY_HOST"; then
    append_default_gateway_origin "http://${GATEWAY_HOST}:${GATEWAY_PORT}"
fi

if [[ -z "${ABSTRACTGATEWAY_AUTH_TOKEN:-}" && -r "$DEFAULT_TOKEN_FILE" ]]; then
    ABSTRACTGATEWAY_AUTH_TOKEN="$(tr -d '\r\n' < "$DEFAULT_TOKEN_FILE")"
fi

export ABSTRACTGATEWAY_AUTH_TOKEN="${ABSTRACTGATEWAY_AUTH_TOKEN:-local-dev-token}"
export ABSTRACTGATEWAY_HOST="$GATEWAY_HOST"
export ABSTRACTGATEWAY_PORT="$GATEWAY_PORT"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="${ABSTRACTGATEWAY_ALLOWED_ORIGINS:-$DEFAULT_GATEWAY_ALLOWED_ORIGINS}"
export ABSTRACTGATEWAY_DATA_DIR="$GATEWAY_RUNTIME_DIR"
export ABSTRACTGATEWAY_FLOWS_DIR="$GATEWAY_FLOWS_DIR"
export ABSTRACTGATEWAY_USER_AUTH="${ABSTRACTGATEWAY_USER_AUTH:-1}"
export ABSTRACTFLOW_HOST="$FLOW_HOST"
export ABSTRACTFLOW_PORT="$FLOW_PORT"
export PORT="$FLOW_PORT"
export ABSTRACTFLOW_GATEWAY_URL="$GATEWAY_URL"
export ABSTRACTOBSERVER_HOST="$OBSERVER_HOST"
export ABSTRACTOBSERVER_PORT="$OBSERVER_PORT"
export ABSTRACTOBSERVER_GATEWAY_URL="${ABSTRACTOBSERVER_GATEWAY_URL:-$GATEWAY_URL}"

mkdir -p "$ABSTRACTGATEWAY_DATA_DIR" "$LOG_DIR" "$(dirname "$LOCAL_GATEWAY_USER_TOKENS_FILE")"

if [[ "$STOP_EXISTING" != "0" && "$STOP_EXISTING" != "false" && "$STOP_EXISTING" != "False" ]]; then
    kill_matching_processes "AbstractObserver" \
        "node[[:space:]].*abstractobserver/bin/cli\\.js" \
        "@abstractframework/observer" \
        "abstractobserver"
    kill_matching_processes "AbstractFlow" \
        "node[[:space:]].*abstractflow/bin/cli\\.js" \
        "@abstractframework/flow" \
        "abstractflow-editor"
    kill_matching_processes "AbstractGateway" \
        "$BIN_DIR/abstractgateway[[:space:]]+serve" \
        "abstractgateway[[:space:]]+serve" \
        "python[^[:space:]]*[[:space:]].*-m[[:space:]]+abstractgateway.cli[[:space:]]+serve"
fi
kill_port_listeners "$GATEWAY_PORT" "AbstractGateway"
kill_port_listeners "$FLOW_PORT" "AbstractFlow"
kill_port_listeners "$OBSERVER_PORT" "AbstractObserver"

port_in_use "$GATEWAY_CONNECT_HOST" "$GATEWAY_PORT" && die "gateway port is already in use: ${GATEWAY_HOST}:${GATEWAY_PORT}"
port_in_use "$FLOW_CONNECT_HOST" "$FLOW_PORT" && die "flow port is already in use: ${FLOW_HOST}:${FLOW_PORT}"
port_in_use "$OBSERVER_CONNECT_HOST" "$OBSERVER_PORT" && die "observer port is already in use: ${OBSERVER_HOST}:${OBSERVER_PORT}"

GATEWAY_LOG="$LOG_DIR/gateway.log"
FLOW_LOG="$LOG_DIR/flow.log"
OBSERVER_LOG="$LOG_DIR/observer.log"
GATEWAY_USERS_REPORT=""
GATEWAY_PID=""
FLOW_PID=""
OBSERVER_PID=""

cleanup() {
    local status=$?
    trap - EXIT INT TERM
    [[ -n "$OBSERVER_PID" ]] && kill "$OBSERVER_PID" >/dev/null 2>&1 || true
    [[ -n "$FLOW_PID" ]] && kill "$FLOW_PID" >/dev/null 2>&1 || true
    [[ -n "$GATEWAY_PID" ]] && kill "$GATEWAY_PID" >/dev/null 2>&1 || true
    [[ -n "$OBSERVER_PID" ]] && wait "$OBSERVER_PID" >/dev/null 2>&1 || true
    [[ -n "$FLOW_PID" ]] && wait "$FLOW_PID" >/dev/null 2>&1 || true
    [[ -n "$GATEWAY_PID" ]] && wait "$GATEWAY_PID" >/dev/null 2>&1 || true
    [[ -n "$GATEWAY_USERS_REPORT" && -f "$GATEWAY_USERS_REPORT" ]] && rm -f "$GATEWAY_USERS_REPORT" >/dev/null 2>&1 || true
    exit "$status"
}
trap cleanup EXIT INT TERM

echo
echo "Starting AbstractGateway, AbstractFlow, and AbstractObserver from local checkout."
echo "Starting AbstractGateway: http://${GATEWAY_HOST}:${GATEWAY_PORT}"
is_truthy "$VERBOSE" && echo "  command: $PYTHON_BIN -m abstractgateway.cli serve"
"$PYTHON_BIN" -m abstractgateway.cli serve --host "$GATEWAY_HOST" --port "$GATEWAY_PORT" >"$GATEWAY_LOG" 2>&1 &
GATEWAY_PID=$!

if ! wait_for_url "$GATEWAY_HEALTH_URL" "$STARTUP_TIMEOUT_S" "$GATEWAY_PID"; then
    show_log_tail "Gateway did not become healthy" "$GATEWAY_LOG"
    exit 1
fi
echo "  health: ready"

if ! wait_for_gateway_contract "$GATEWAY_CAPABILITIES_URL" "$ABSTRACTGATEWAY_AUTH_TOKEN" "$STARTUP_TIMEOUT_S" "$GATEWAY_PID"; then
    show_log_tail "Gateway did not expose the Flow contract" "$GATEWAY_LOG"
    exit 1
fi
echo "  Flow contract: ready"

echo "Preparing Gateway users."
GATEWAY_USERS_REPORT="$(mktemp "${TMPDIR:-/tmp}/gateway-flow-users.XXXXXX")"
chmod 600 "$GATEWAY_USERS_REPORT" >/dev/null 2>&1 || true
prepare_gateway_local_users \
    "$LOCAL_GATEWAY_USERS" \
    "$LOCAL_GATEWAY_USER_TENANT" \
    "$LOCAL_GATEWAY_USER_TOKENS_FILE" \
    "$LOCAL_GATEWAY_ROTATE_USER_TOKENS" \
    "$GATEWAY_URL" \
    "$SHOW_ALL_GATEWAY_USERS" \
    "$VERBOSE" \
    >"$GATEWAY_USERS_REPORT"
echo "  users: ready"

echo "Starting AbstractFlow: http://${FLOW_HOST}:${FLOW_PORT}"
is_truthy "$VERBOSE" && echo "  command: $NODE_BIN $ROOT_DIR/abstractflow/bin/cli.js"
env -u ABSTRACTGATEWAY_AUTH_TOKEN "$NODE_BIN" "$ROOT_DIR/abstractflow/bin/cli.js" \
    --host "$FLOW_HOST" \
    --port "$FLOW_PORT" \
    --gateway-url "$GATEWAY_URL" \
    >"$FLOW_LOG" 2>&1 &
FLOW_PID=$!

if ! wait_for_url "$FLOW_HEALTH_URL" "$STARTUP_TIMEOUT_S" "$FLOW_PID"; then
    show_log_tail "Flow server did not become healthy" "$FLOW_LOG"
    exit 1
fi
echo "  health: ready"

if ! wait_for_url "$FLOW_UI_URL" "$STARTUP_TIMEOUT_S" "$FLOW_PID"; then
    show_log_tail "Flow UI did not become ready" "$FLOW_LOG"
    exit 1
fi
echo "  UI: ready"

echo "Starting AbstractObserver: http://${OBSERVER_HOST}:${OBSERVER_PORT}"
is_truthy "$VERBOSE" && echo "  command: HOST=$OBSERVER_HOST PORT=$OBSERVER_PORT ABSTRACTOBSERVER_GATEWAY_URL=$ABSTRACTOBSERVER_GATEWAY_URL $NODE_BIN $ROOT_DIR/abstractobserver/bin/cli.js"
env -u ABSTRACTGATEWAY_AUTH_TOKEN \
    HOST="$OBSERVER_HOST" \
    PORT="$OBSERVER_PORT" \
    ABSTRACTOBSERVER_GATEWAY_URL="$ABSTRACTOBSERVER_GATEWAY_URL" \
    "$NODE_BIN" "$ROOT_DIR/abstractobserver/bin/cli.js" \
    >"$OBSERVER_LOG" 2>&1 &
OBSERVER_PID=$!

if ! wait_for_url "$OBSERVER_UI_URL" "$STARTUP_TIMEOUT_S" "$OBSERVER_PID"; then
    show_log_tail "Observer UI did not become ready" "$OBSERVER_LOG"
    exit 1
fi
echo "  UI: ready"

echo
echo "Gateway local:   $GATEWAY_LOCAL_URL"
if [[ -n "$GATEWAY_NETWORK_URL" ]]; then
    echo "Gateway network: $GATEWAY_NETWORK_URL"
fi
echo "Flow local:      $FLOW_LOCAL_URL"
if [[ -n "$FLOW_NETWORK_URL" ]]; then
    echo "Flow network:    $FLOW_NETWORK_URL"
fi
echo "Observer local:  $OBSERVER_LOCAL_URL"
if [[ -n "$OBSERVER_NETWORK_URL" ]]; then
    echo "Observer network: $OBSERVER_NETWORK_URL"
fi
echo

sed -n '1,160p' "$GATEWAY_USERS_REPORT"

cat <<EOF

Logs:
  Gateway: $GATEWAY_LOG
  Flow:    $FLOW_LOG
  Observer: $OBSERVER_LOG
EOF

if is_truthy "$VERBOSE"; then
    cat <<EOF
Runtime:
  Root:    $RUNTIME_DIR
  Gateway: $ABSTRACTGATEWAY_DATA_DIR
  Bundles: $ABSTRACTGATEWAY_FLOWS_DIR
  Caps:    $GATEWAY_CAPABILITIES_URL
EOF
fi

if is_truthy "$SHOW_ADMIN_TOKEN"; then
    cat <<EOF
Admin token: $ABSTRACTGATEWAY_AUTH_TOKEN
EOF
fi

cat <<EOF

Gateway, Flow, and Observer are running. Leave this terminal open; press Ctrl-C to stop all three.
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
    if ! kill -0 "$OBSERVER_PID" >/dev/null 2>&1; then
        show_log_tail "Observer exited" "$OBSERVER_LOG"
        exit 1
    fi
    sleep 2
done
