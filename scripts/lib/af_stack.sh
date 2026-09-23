#!/usr/bin/env bash
# Whole-framework orchestrator shared by af.sh (published packages) and
# af-local.sh (source checkout). Composes the per-app launchers so each app
# keeps its own preflight + restart semantics:
#
#   gateway${SFX}.sh    control plane, started FIRST and awaited (health)
#   observer${SFX}.sh   observability UI      :3001
#   console${SFX}.sh    continuum console     :3002
#   code${SFX}.sh       abstractcode WEB UI   :3003  (abstractcode/web)
#   entity${SFX}.sh     summoned entities     :3004
#   flow${SFX}.sh       flow editor           :3005
#   assistant${SFX}.sh  desktop tray app      (no port — AF_STACK_ASSISTANT=0 to skip)
#
# (Ports are the canonical operator map set by the caller; the per-app
# defaults in apps_common.sh differ and lose.)
#
# The caller sets AF_STACK_SUFFIX ("" or "-local") and sources this file.
#
# RESILIENCE SEMANTICS (maintainer ruling 2026-07-21, dm#150 — supersedes the
# old all-or-nothing teardown): services run under scripts/lib/af_supervisor.sh
# with separated failure domains.
#   - The GATEWAY is critical: app failures never touch it; if it DIES it is
#     restarted with capped backoff, unlimited attempts, and a loud incident
#     banner naming the cause. A hung-but-alive gateway is WARNED ABOUT, never
#     killed (operator ruling 2026-08-20: restart on death only; an in-process
#     model call can starve /api/health while doing real work — SUP_HANG_KILL=1
#     restores hang-recycling). Every spawn repeats the proven preflight
#     (stop stray serves, free port, runner-lock probe).
#   - APPS self-restart with a bounded budget (default 5 restarts / 300s);
#     a crash-looping app converges to FAILED loudly while the rest of the
#     stack keeps serving. Apps are parked while the gateway is down and
#     return (budgets reset) when it recovers.
#   - Ctrl-C / TERM stops the whole stack: apps first, gateway last.
#
# Each app logs to $LOG_DIR/<app>.log (one .prev generation kept per respawn);
# supervisor events go to the terminal and $LOG_DIR/af-stack.log.

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/apps_common.sh"

# STARTUP_TIMEOUT_S is this stack's historical knob; map it onto the
# supervisor's readiness deadline BEFORE sourcing (the library defaults the
# variable at source time).
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-120}"
SUP_READY_TIMEOUT_S="${SUP_READY_TIMEOUT_S:-$STARTUP_TIMEOUT_S}"
source "$APPS_LIB_DIR/af_supervisor.sh"

SFX="${AF_STACK_SUFFIX:-}"

# Hosts bound to 0.0.0.0/:: are probed via loopback.
connect_host() {
    case "${1:-}" in
        0.0.0.0|::) echo "127.0.0.1" ;;
        *) echo "$1" ;;
    esac
}

GATEWAY_LOG="$LOG_DIR/gateway.log"
FLOW_LOG="$LOG_DIR/flow.log"
OBSERVER_LOG="$LOG_DIR/observer.log"
CODE_LOG="$LOG_DIR/code.log"
CONSOLE_LOG="$LOG_DIR/console.log"
ENTITY_LOG="$LOG_DIR/entity.log"
ASSISTANT_LOG="$LOG_DIR/assistant.log"

# The desktop assistant is part of the stack, but it is a GUI process: on a
# headless box, over SSH, or in CI there is no display to start it on. Opt out
# with AF_STACK_ASSISTANT=0 rather than watching it burn its restart budget.
AF_STACK_ASSISTANT="${AF_STACK_ASSISTANT:-1}"

mkdir_logs
SUP_LOG_FILE="$LOG_DIR/af-stack.log"
sup_rotate_log "$SUP_LOG_FILE"

# ONE supervisor per stack (per runtime dir): a second one would fight this
# one over the same services — each prestart kills the other's gateway,
# forever. Shadow stacks use their own RUNTIME_DIR and so their own pidfile.
if ! sup_acquire_singleton "$RUNTIME_DIR/af_stack.pid"; then
    exit 1
fi

resolve_stack_python() {
    if [[ -n "$SFX" ]]; then
        resolve_local_python
    else
        resolve_published_python
    fi
}

# Gateway pre-start hook — runs before EVERY gateway spawn (first launch and
# every respawn), parent-side.
#
# RACE FIX (2026-07-21 outage): the gateway child stops any pre-existing
# gateway itself, but that kill runs AFTER the spawn — so an OLD gateway
# still serving :8080 could answer the readiness probe while the child was
# in its kill-to-bind gap, and dependent preflights then failed inside that
# window. Stopping existing gateways SYNCHRONOUSLY before the spawn means the
# first health answer can only come from the gateway THIS stack started.
#
# The body runs in a subshell: apps_common helpers (`free_port`,
# `verify_gateway_runner_lock_free`) call `die` on hard failures, and a hard
# failure here must fail THIS start attempt (the supervisor logs it and
# retries with backoff) — never kill the supervisor and the healthy apps.
#
# The machine-wide serve stop honors GATEWAY_STOP_EXISTING (=0 for shadow/test
# stacks beside a production gateway) inside stop_gateway_serve_processes.
gateway_prestart() {
    (
        set -e
        stop_gateway_serve_processes "AbstractGateway"
        free_port "$GATEWAY_PORT" "AbstractGateway"
        verify_gateway_runner_lock_free "$(resolve_stack_python)" "$GATEWAY_DATA_DIR/gateway_runner.lock"
    )
}

if [[ -n "$SFX" ]]; then
    STACK_MODE="local checkout"
else
    STACK_MODE="published packages"
fi

echo ""
echo "============================================================"
echo "  AbstractFramework — full stack (${STACK_MODE})"
echo "============================================================"
echo ""

# ── Service registry ────────────────────────────────────────────────────────
# Per-user sign-in tokens default ON (same default as gateway-flow[-local].sh)
# so the stack banner can print usable admin/user tokens. Override with
# ABSTRACTGATEWAY_USER_AUTH=0 for a token-less single-user gateway.
export ABSTRACTGATEWAY_USER_AUTH="${ABSTRACTGATEWAY_USER_AUTH:-1}"

FLOW_URL="http://$(connect_host "$FLOW_HOST"):${FLOW_PORT}/"
OBSERVER_URL="http://$(connect_host "$OBSERVER_HOST"):${OBSERVER_PORT}/"
CODE_URL="http://$(connect_host "$CODE_HOST"):${CODE_PORT}/"
CONSOLE_URL="http://$(connect_host "$CONTINUUM_HOST"):${CONTINUUM_PORT}/"
ENTITY_URL="http://$(connect_host "$ENTITY_HOST"):${ENTITY_PORT}/"

# Ambient-env sanitization (2026-07-22, laurent's env order + adversary B/C):
# the live gateway inherited a FOREIGN AGORA_API_KEY from the launching shell
# and minted agora tools posting under another seat's identity. Serving
# processes must never inherit ambient identity/behavior vars from whatever
# shell happened to launch the stack. Conservative denylist: agent-hub
# identity (AGORA_*) and the long-dead gateway provider/model pair. Cloud API
# keys are deliberately NOT stripped yet — configured cloud providers still
# authenticate via env until the config-key migration lands.
SANITIZE_ENV_VARS="${SANITIZE_ENV_VARS:-AGORA_API_KEY AGORA_AGENT_ID AGORA_HUB_URL ABSTRACTGATEWAY_PROVIDER ABSTRACTGATEWAY_MODEL}"

launcher_cmd() {
    local unsets="" v
    for v in $SANITIZE_ENV_VARS; do
        unsets="$unsets -u $v"
    done
    printf 'env%s bash %q' "$unsets" "$SCRIPTS_DIR/$1${SFX}.sh"
}

# The gateway: critical, actively health-probed, preflighted on every spawn.
sup_register "gateway" 1 "$(launcher_cmd gateway)" "$GATEWAY_LOG" \
    "$GATEWAY_HEALTH_URL" "$GATEWAY_HEALTH_URL" gateway_prestart
GATEWAY_IDX="$SUP_LAST_INDEX"

# The apps: bounded self-restart on DEATH only — no active health probing
# (empty health URL). A loaded dev machine can answer slowly for a minute;
# recycling static UI servers on slow probes would burn their restart budgets
# on phantom failures (verifier note c4046). The gateway keeps active probing:
# it is the one service with a real wedge history.
sup_register "flow"     0 "$(launcher_cmd flow)"     "$FLOW_LOG"     "$FLOW_URL"     "" ""
sup_register "observer" 0 "$(launcher_cmd observer)" "$OBSERVER_LOG" "$OBSERVER_URL" "" ""
sup_register "code"     0 "$(launcher_cmd code)"     "$CODE_LOG"     "$CODE_URL"     "" ""
sup_register "console"  0 "$(launcher_cmd console)"  "$CONSOLE_LOG"  "$CONSOLE_URL"  "" ""
sup_register "entity"   0 "$(launcher_cmd entity)"   "$ENTITY_LOG"   "$ENTITY_URL"   "" ""

# The desktop assistant: same bounded self-restart as the other apps, but no
# ready URL — it serves no port, so the supervisor treats "process alive" as
# ready (see sup_probe_ready).
ASSISTANT_IDX=""
if [[ "$AF_STACK_ASSISTANT" != "0" ]]; then
    sup_register "assistant" 0 "$(launcher_cmd assistant)" "$ASSISTANT_LOG" "" "" ""
    ASSISTANT_IDX="$SUP_LAST_INDEX"
fi

# Report what the supervisor ACTUALLY holds, not that it was asked for: a GUI
# app is the likeliest service on this list to have no display to start on,
# and a banner that says "running" either way is worth nothing.
assistant_summary_line() {
    if [[ -z "$ASSISTANT_IDX" ]]; then
        echo "skipped (AF_STACK_ASSISTANT=0)"
        return 0
    fi
    echo "${SUP_STATE[$ASSISTANT_IDX]} (no port — see assistant.log)"
}

# ── Signals ─────────────────────────────────────────────────────────────────
on_operator_stop() {
    trap - EXIT INT TERM
    echo ""
    sup_log "operator stop — shutting down the stack (apps first, gateway last)"
    sup_shutdown
    exit 0
}
on_unexpected_exit() {
    local status=$?
    trap - EXIT INT TERM
    if [[ "$SUP_SHUTDOWN" != "1" ]]; then
        sup_log "ERROR: supervisor exiting unexpectedly (status ${status}) — tearing the stack down rather than orphaning it"
        sup_shutdown
    fi
    exit "$status"
}
trap on_operator_stop INT TERM
trap on_unexpected_exit EXIT

# ── 1. The control plane ────────────────────────────────────────────────────
echo "Starting AbstractGateway (control plane): http://${GATEWAY_HOST}:${GATEWAY_PORT}"
sup_start_service "$GATEWAY_IDX" || true
# LAUNCH-time gateway failure is fatal (an operator just ran this command and
# a gateway that cannot boot is a config problem, not a blip). ONGOING
# failures after a successful launch are the supervisor's to absorb.
# ALIVE-NOT-READY is neither: /api/health answering status="starting" means
# the listener is up and the heavy boot runs on a background thread (gateway
# fold 2026-07-21) — the launch keeps waiting up to the supervisor's wedged-
# boot cap instead of aborting a healthy-but-loading control plane.
# The abort is a DELIBERATE teardown (sup_shutdown before exit), so the EXIT
# trap does not misreport it as an unexpected supervisor error.
if ! sup_await_state "$GATEWAY_IDX" "running" "$STARTUP_TIMEOUT_S"; then
    GATEWAY_LAUNCH_OK=0
    if [[ "${SUP_STATE[$GATEWAY_IDX]}" == "starting" ]]; then
        sup_log "gateway: alive with boot in progress — extending the launch wait (cap ${SUP_STARTING_ALIVE_MAX_S}s)"
        if sup_await_state "$GATEWAY_IDX" "running" "$SUP_STARTING_ALIVE_MAX_S"; then
            GATEWAY_LAUNCH_OK=1
        fi
    fi
    if [[ "$GATEWAY_LAUNCH_OK" != "1" ]]; then
        sup_log_incident "Gateway did not become healthy at launch" "$GATEWAY_LOG" "" "failed launch"
        sup_log "launch aborted — stopping anything the launch sequence started"
        sup_shutdown
        exit 1
    fi
fi

# Ensure the local dev users exist and print their sign-in tokens (maintainer
# ask 2026-07-16: the stack launchers must output the admin & user tokens).
# The helper writes through the SAME data dir the gateway serves from and
# rotates a token only when the plaintext dev cache is missing/stale, so the
# printed value always authenticates. Failure here never kills the stack.
STACK_GATEWAY_USERS="${STACK_GATEWAY_USERS:-${LOCAL_GATEWAY_USERS:-admin,user}}"
STACK_GATEWAY_USER_TENANT="${STACK_GATEWAY_USER_TENANT:-${LOCAL_GATEWAY_USER_TENANT:-default}}"
STACK_GATEWAY_USER_TOKENS_FILE="${STACK_GATEWAY_USER_TOKENS_FILE:-${LOCAL_GATEWAY_USER_TOKENS_FILE:-$GATEWAY_DATA_DIR/dev/gateway-user-tokens.json}}"

print_gateway_user_tokens() {
    local py
    py="$(resolve_stack_python)"
    local pythonpath="${PYTHONPATH:-}"
    if [[ -n "$SFX" ]]; then
        pythonpath="$(local_pythonpath)${pythonpath:+:$pythonpath}"
    fi
    echo "Gateway sign-in:"
    if ! ABSTRACTGATEWAY_DATA_DIR="$GATEWAY_DATA_DIR" PYTHONPATH="$pythonpath" \
        "$py" "$APPS_LIB_DIR/gateway_user_tokens.py" \
        "$STACK_GATEWAY_USERS" "$STACK_GATEWAY_USER_TENANT" \
        "$STACK_GATEWAY_USER_TOKENS_FILE" "$GATEWAY_URL"; then
        echo "  #FALLBACK could not resolve user tokens; inspect $STACK_GATEWAY_USER_TOKENS_FILE" >&2
    fi
}

# ── 2. The apps (parallel start, ordered readiness) ────────────────────────
# Every launcher re-checks the gateway itself (require_gateway) and frees its
# own port, so starting them together is safe — ports are disjoint.
echo "Starting AbstractFlow:      $FLOW_URL"
echo "Starting AbstractObserver:  $OBSERVER_URL"
echo "Starting AbstractCode web:  $CODE_URL"
echo "Starting Continuum console: $CONSOLE_URL"
echo "Starting Summoned entities: $ENTITY_URL"
if [[ "$AF_STACK_ASSISTANT" != "0" ]]; then
    echo "Starting AbstractAssistant: desktop tray app (no port)"
fi
i=1
while [[ "$i" -lt "$SUP_COUNT" ]]; do
    sup_start_service "$i" || true
    i=$((i + 1))
done

# An app that misses its launch window is NOT fatal (new semantics): the
# supervisor keeps recycling it within its budget; it either recovers or
# converges to FAILED while the rest of the stack serves.
i=1
while [[ "$i" -lt "$SUP_COUNT" ]]; do
    if ! sup_await_state "$i" "running" "$STARTUP_TIMEOUT_S"; then
        sup_log "${SUP_NAME[$i]}: not ready at launch (state: ${SUP_STATE[$i]}) — supervision continues"
    fi
    i=$((i + 1))
done

# ── 3. Summary ──────────────────────────────────────────────────────────────
cat <<EOF

============================================================
  The framework is up.  ($(sup_status_line))
============================================================
  Gateway (control plane):  ${GATEWAY_URL}
  Flow (editor):            ${FLOW_URL}
  Observer (runs, ledgers): ${OBSERVER_URL}
  Code (web UI):            ${CODE_URL}
  Console (continuum):      ${CONSOLE_URL}
  Entities (summoned):      ${ENTITY_URL}
  Assistant (desktop tray): $(assistant_summary_line)

Logs (${LOG_DIR}):
  gateway.log  flow.log  observer.log  code.log  console.log  entity.log  assistant.log
  af-stack.log (supervisor events: restarts, health, failures)
EOF

print_gateway_user_tokens

cat <<EOF

Resilience: apps self-restart (budget $SUP_APP_RESTART_MAX/${SUP_APP_RESTART_WINDOW_S}s, then FAILED with a
${SUP_FAILED_RETRY_S}s cooldown retry — the stack stays up); the gateway self-restarts
indefinitely and is health-probed. Leave this terminal open; press
Ctrl-C to stop the whole stack.
EOF

# ── 4. Supervise ─────────────────────────────────────────────────────────────
sup_monitor
