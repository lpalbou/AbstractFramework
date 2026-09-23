#!/usr/bin/env bash
# Shared helpers for the per-app launchers (gateway.sh, flow.sh, observer.sh,
# entity.sh, console.sh, code.sh, assistant.sh and their -local.sh twins) and
# the whole-framework orchestrators (af.sh / af-local.sh).
#
# Design (maintainer directive 2026-07-08):
# - One script per app, each with a -local twin (source checkout vs published
#   packages). This file holds only what they share.
# - THE GATEWAY IS THE CONTROL PLANE. Every other app connects to it, so every
#   non-gateway launcher calls `require_gateway` first and refuses to start
#   until the gateway answers. Launch gateway.sh before anything else.
#
# Env knobs (all overridable): ABSTRACTGATEWAY_HOST/PORT, ABSTRACTFLOW_PORT,
# ABSTRACTOBSERVER_PORT, ABSTRACTENTITY_PORT, ABSTRACTCODE_PORT,
# ABSTRACTCONTINUUM_PORT, GATEWAY_URL, ABSTRACTGATEWAY_DATA_DIR.

set -euo pipefail

# --- paths ----------------------------------------------------------------
APPS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(dirname "$APPS_LIB_DIR")"
ROOT_DIR="$(dirname "$SCRIPTS_DIR")"

# --- host/port defaults ---------------------------------------------------
# The gateway binds 0.0.0.0 by default: entity handles are <name>@<LAN-ip>
# (ruled), so the control plane must be LAN-reachable — matching the
# historical gateway-flow[-local].sh posture. Loopback probing still goes
# through GATEWAY_CONNECT_HOST below.
GATEWAY_HOST="${GATEWAY_HOST:-${ABSTRACTGATEWAY_HOST:-0.0.0.0}}"
GATEWAY_PORT="${GATEWAY_PORT:-${ABSTRACTGATEWAY_PORT:-8080}}"
case "$GATEWAY_HOST" in
    0.0.0.0|::) GATEWAY_CONNECT_HOST="${GATEWAY_CONNECT_HOST:-127.0.0.1}" ;;
    *) GATEWAY_CONNECT_HOST="${GATEWAY_CONNECT_HOST:-$GATEWAY_HOST}" ;;
esac
GATEWAY_URL="${GATEWAY_URL:-http://${GATEWAY_CONNECT_HOST}:${GATEWAY_PORT}}"
GATEWAY_HEALTH_URL="${GATEWAY_URL}/api/health"

FLOW_HOST="${FLOW_HOST:-${ABSTRACTFLOW_HOST:-127.0.0.1}}"
FLOW_PORT="${FLOW_PORT:-${ABSTRACTFLOW_PORT:-3000}}"
OBSERVER_HOST="${OBSERVER_HOST:-${ABSTRACTOBSERVER_HOST:-127.0.0.1}}"
OBSERVER_PORT="${OBSERVER_PORT:-${ABSTRACTOBSERVER_PORT:-3001}}"
# The entity app (multi-entity manager + graph + chat) is its own package
# since 2026-07-12 (abstractentity/bin/cli.js), on its own port.
ENTITY_HOST="${ENTITY_HOST:-${ABSTRACTENTITY_HOST:-127.0.0.1}}"
ENTITY_PORT="${ENTITY_PORT:-${ABSTRACTENTITY_PORT:-3007}}"
# The browser coding assistant (abstractcode/web, @abstractframework/code).
CODE_HOST="${CODE_HOST:-${ABSTRACTCODE_HOST:-127.0.0.1}}"
CODE_PORT="${CODE_PORT:-${ABSTRACTCODE_PORT:-3002}}"
# The continuum console (abstractcontinuum, @abstractframework/continuum):
# backlog browsing + codex execution, inbox triage, managed process control.
# Its cli.js self-default is 3002, which collides with the code app's own
# default — the launchers always pass PORT explicitly, console on 3003.
CONTINUUM_HOST="${CONTINUUM_HOST:-${ABSTRACTCONTINUUM_HOST:-127.0.0.1}}"
CONTINUUM_PORT="${CONTINUUM_PORT:-${ABSTRACTCONTINUUM_PORT:-3003}}"

# THE PRODUCTION DATA ROOT IS $ROOT_DIR/runtime — the same root
# gateway-flow[-local].sh always served (provider endpoint profiles under
# config/, entity homes under entities/, auth/, artifacts/, dev tokens).
# 2026-07-16 incident: this defaulted to $ROOT_DIR/runtime-data, so a
# start*.sh gateway booted into an EMPTY world (no 'endpoint:ovh-provider'
# profile -> WorkflowBundleError 500s, no entities, fresh auth). Never point
# this default anywhere but the real root; overrides stay env-driven.
RUNTIME_DIR="${RUNTIME_DIR:-${ABSTRACTFRAMEWORK_RUNTIME_DIR:-$ROOT_DIR/runtime}}"
GATEWAY_DATA_DIR="${ABSTRACTGATEWAY_DATA_DIR:-$RUNTIME_DIR}"
LOG_DIR="${LOG_DIR:-$RUNTIME_DIR/logs}"

# Backlog/triage browsing needs the checkout root; without it the whole
# /backlog + /reports family answers "not configured" and the continuum
# board has no data source (operator incidents 2026-07-13 + 2026-07-16).
# The exec worker default matches the production posture (continuum's
# backlog-execution pipeline; executions stay operator-triggered).
export ABSTRACTGATEWAY_TRIAGE_REPO_ROOT="${ABSTRACTGATEWAY_TRIAGE_REPO_ROOT:-$ROOT_DIR}"
export ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER="${ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER:-1}"

# Static admin bearer: honor the env first, else the dev token file the
# production launcher (gateway-flow[-local].sh) has always read/written.
GATEWAY_TOKEN_FILE="${GATEWAY_TOKEN_FILE:-$RUNTIME_DIR/dev/gateway-token}"
if [[ -z "${ABSTRACTGATEWAY_AUTH_TOKEN:-}" && -r "$GATEWAY_TOKEN_FILE" ]]; then
    export ABSTRACTGATEWAY_AUTH_TOKEN="$(tr -d '\r\n' < "$GATEWAY_TOKEN_FILE")"
fi

# --- output ---------------------------------------------------------------
die() { echo "error: $*" >&2; exit 1; }
info() { echo "$*"; }
is_truthy() { case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in 1|true|yes|y|on) return 0 ;; *) return 1 ;; esac; }

# --- python / node resolution --------------------------------------------
# LOCAL mode uses the source checkout: the repo .venv python and the checked-out
# node CLIs. PUBLISHED mode uses whatever python has the packages installed and
# npx for the JS apps.
resolve_local_python() {
    # AF_VENV_DIR: same override as scripts/build.sh (default <root>/.venv).
    local venv="${AF_VENV_DIR:-$ROOT_DIR/.venv}"
    local candidates=("$venv/bin/python" "$venv/bin/python3")
    for c in "${candidates[@]}"; do
        [[ -x "$c" ]] && { echo "$c"; return 0; }
    done
    command -v python3 || die "no python found (expected $venv/bin/python for -local)"
}

resolve_published_python() {
    echo "${PYTHON_BIN:-${PYTHON:-python3}}"
}

# The src-layout PYTHONPATH for running the gateway (and its entity/runtime deps)
# straight from the checkout without installing. abstractcamera rides along so
# camera-backed tools resolve when the gateway/runtime reach for them.
# abstractagent is required for native-loop bundle materialize
# (react|codeact|memact) when the venv editable install is absent.
local_pythonpath() {
    printf '%s' \
      "$ROOT_DIR/abstractgateway/src:$ROOT_DIR/abstractruntime/src:$ROOT_DIR/abstractmemory/src:$ROOT_DIR/abstractflow/src:$ROOT_DIR/abstractcamera/src:$ROOT_DIR/abstract3d/src:$ROOT_DIR/abstractagent/src:$ROOT_DIR/abstractcore"
}

# macOS: downloaded checkouts can carry com.apple.quarantine, which blocks
# native node addons (rollup, esbuild). Clear it on a dir before `node` runs it.
clear_quarantine() {
    [[ "$(uname -s)" == "Darwin" ]] || return 0
    local target="$1"
    [[ -e "$target" ]] || return 0
    xattr -dr com.apple.quarantine "$target" >/dev/null 2>&1 || true
}

# --- networking -----------------------------------------------------------
port_in_use() {
    lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

# KILL RECEIPT (operator ruling 2026-08-20): every kill a framework script
# issues leaves a line in one machine-wide ledger, so a supervised service
# that dies by signal can NAME its killer in the incident banner instead of
# logging an anonymous "exited (status 143)". One day of af-stack.log showed
# 10 gateway restarts — all external signals, zero crashes, zero attribution.
# Best-effort by design: a failed append must never break a launcher.
af_kill_receipt() {
    local ledger="${AF_KILL_RECEIPTS:-$HOME/.abstractframework/kill-receipts.log}"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo '?')"
    echo "[af-kill ${ts}] by pid $$ (ppid ${PPID:-?}, script ${0##*/}): $*" >>"$ledger" 2>/dev/null || true
}

# Restart semantics (maintainer directive 2026-07-09: launchers must replace a
# service that is already running, never refuse). TERM the listener(s), wait
# briefly, KILL stragglers, and die only if the port is STILL bound (something
# unkillable owns it — that deserves a human). Mirrors the proven
# kill_port_listeners in gateway-flow.sh.
free_port() {
    local port="$1" label="${2:-service}"
    command -v lsof >/dev/null 2>&1 || { info "#FALLBACK lsof not found - cannot check port ${port}; bind may fail"; return 0; }
    local pids
    pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
    [[ -z "$pids" ]] && return 0
    info "port ${port} is in use - stopping existing ${label} listener(s): ${pids//$'\n'/ }"
    af_kill_receipt "free_port ${port} (${label}): TERM ${pids//$'\n'/ }"
    kill $pids >/dev/null 2>&1 || true
    local i
    for i in 1 2 3 4 5; do
        sleep 1
        pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
        [[ -z "$pids" ]] && return 0
    done
    info "force-stopping stubborn listener(s) on port ${port}: ${pids//$'\n'/ }"
    af_kill_receipt "free_port ${port} (${label}): KILL ${pids//$'\n'/ }"
    kill -9 $pids >/dev/null 2>&1 || true
    sleep 1
    if port_in_use "$port"; then
        die "port ${port} is still in use after kill - inspect: lsof -nP -iTCP:${port} -sTCP:LISTEN"
    fi
}

# Restart semantics for port-less apps (the tray assistant) and for processes
# that matter beyond their port (the gateway serve tree): stop processes whose
# command line matches a pattern, sparing this script's own process tree, and
# WAIT for them to actually die. The wait matters: a TERM'd process that is
# still shutting down can hold kernel resources (flock on gateway_runner.lock)
# past the moment its port frees up — starting the replacement before the old
# process exits is exactly how the runner-lock orphan incident happened.
stop_processes() {
    local label="$1"; shift
    local pids="" pattern found
    for pattern in "$@"; do
        found="$(pgrep -f "$pattern" 2>/dev/null || true)"
        [[ -n "$found" ]] && pids+=$'\n'"$found"
    done
    pids="$(printf '%s\n' "$pids" | awk 'NF' | sort -u \
        | awk -v self="$$" -v bashpid="${BASHPID:-$$}" '$1 != self && $1 != bashpid')"
    [[ -z "$pids" ]] && return 0
    info "stopping existing ${label} process(es): ${pids//$'\n'/ }"
    af_kill_receipt "stop_processes (${label}): TERM ${pids//$'\n'/ }"
    kill $pids >/dev/null 2>&1 || true
    local i alive pid
    for i in 1 2 3 4 5; do
        alive=""
        for pid in $pids; do
            kill -0 "$pid" >/dev/null 2>&1 && alive+="$pid "
        done
        [[ -z "$alive" ]] && return 0
        sleep 1
    done
    info "force-stopping stubborn ${label} process(es): $alive"
    af_kill_receipt "stop_processes (${label}): KILL $alive"
    kill -9 $alive >/dev/null 2>&1 || true
    for i in 1 2 3; do
        sleep 1
        alive=""
        for pid in $pids; do
            kill -0 "$pid" >/dev/null 2>&1 && alive+="$pid "
        done
        [[ -z "$alive" ]] && return 0
    done
    # KILL survivors are almost certainly unreaped zombies (no locks held), but
    # say so loudly instead of silently proceeding.
    info "#FALLBACK ${label} process(es) still visible after KILL: $alive (likely zombies; if the new service misbehaves, inspect: ps -p ${alive// /,})"
    return 0
}

# The gateway restart must stop EVERY `abstractgateway ... serve` process, not
# only the port binder. free_port kills the LISTENER; a duplicate serve process
# that lost the port race, was started twice, or is mid-graceful-shutdown with
# its listener already closed stays alive holding <data_dir>/gateway_runner.lock.
# The replacement gateway then serves HTTP but its GatewayRunner is refused the
# singleton lock and never ticks runs (runs hang on "On Flow Start" forever with
# zero ledger and no error). Match every spawn shape:
#   .../bin/abstractgateway serve         (console script)
#   python -m abstractgateway serve       (gateway[-local].sh)
#   python -m abstractgateway.cli serve   (gateway-flow[-local].sh)
stop_gateway_serve_processes() {
    # GATEWAY_STOP_EXISTING=0: a shadow/test stack running BESIDE a production
    # gateway (own port, own data dir) must not stop gateways machine-wide.
    # It still frees its own port via free_port. Default 1 = production
    # posture: replace any existing gateway (maintainer 2026-07-09 ruling).
    if ! is_truthy "${GATEWAY_STOP_EXISTING:-1}"; then
        info "skipping machine-wide gateway-serve stop (GATEWAY_STOP_EXISTING=0)"
        return 0
    fi
    stop_processes "${1:-AbstractGateway serve}" \
        'abstractgateway(\.cli)?[[:space:]]+serve'
}

# Belt-and-braces: prove the runner singleton lock is actually free before
# starting the replacement gateway. This probes the exact kernel resource whose
# silent refusal caused the stuck-runs incident — process-liveness checks can
# be fooled (zombies, unkillable states); the flock cannot. Dies naming the
# holder so a human deals with it instead of a runner-less gateway starting.
verify_gateway_runner_lock_free() {
    local py="${1:-}" lock_file="${2:-$GATEWAY_DATA_DIR/gateway_runner.lock}"
    [[ -e "$lock_file" ]] || return 0
    # Accept an executable path or a bare command name (published launchers
    # pass e.g. "python3"); fall back to whatever python3 is on PATH.
    if [[ -n "$py" && ! -x "$py" ]]; then
        py="$(command -v "$py" 2>/dev/null || true)"
    fi
    if [[ -z "$py" ]]; then
        py="$(command -v python3 2>/dev/null || true)"
    fi
    if [[ -z "$py" ]]; then
        info "#FALLBACK no python available to probe ${lock_file}; if runs hang after start, check for orphan gateway processes"
        return 0
    fi
    if "$py" - "$lock_file" <<'PY'
import fcntl, sys
try:
    fh = open(sys.argv[1], "a")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    sys.exit(1)
sys.exit(0)
PY
    then
        return 0
    fi
    local holders
    holders="$(lsof -t -- "$lock_file" 2>/dev/null | sort -u | tr '\n' ' ' || true)"
    die "gateway runner lock is still held: ${lock_file} (holder pid(s): ${holders:-unknown}).
       A gateway started now would serve HTTP but never tick runs (they hang on
       'On Flow Start' with zero ledger). Stop the holder first:
       kill ${holders:-<pid>}   # then re-run this launcher"
}

wait_for_url() {
    local url="$1" timeout_s="${2:-60}" pid="${3:-}"
    local deadline=$(( $(date +%s) + timeout_s ))
    while (( $(date +%s) < deadline )); do
        if [[ -n "$pid" ]] && ! kill -0 "$pid" >/dev/null 2>&1; then
            return 1
        fi
        if curl -s -m 3 -o /dev/null "$url" 2>/dev/null; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# The one invariant every non-gateway app depends on: the control plane is up.
# Bounded WAIT, not a single shot (2026-07-21 outage): during a gateway restart
# there is an unavoidable seconds-long kill-to-bind gap; a one-shot probe that
# lands in it kills the app, and under af_stack the linked teardown then kills
# the whole framework. Waiting briefly absorbs restarts; a truly absent gateway
# still dies loudly after the window.
require_gateway() {
    local wait_s="${REQUIRE_GATEWAY_WAIT_S:-30}"
    if ! wait_for_url "$GATEWAY_HEALTH_URL" "$wait_s"; then
        die "the gateway is not reachable at ${GATEWAY_URL} (checked ${GATEWAY_HEALTH_URL} for ${wait_s}s).
       The gateway is the control plane — every other app connects to it.
       Start it first:  scripts/gateway${LOCAL_SUFFIX:-}.sh
       (or set GATEWAY_URL if it runs elsewhere.)"
    fi
    info "gateway: reachable at ${GATEWAY_URL}"
}

mkdir_logs() { mkdir -p "$LOG_DIR" >/dev/null 2>&1 || true; }
