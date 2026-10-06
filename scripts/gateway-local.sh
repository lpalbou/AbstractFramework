#!/usr/bin/env bash
# Start AbstractGateway from the LOCAL source checkout — the control plane.
# Launch this FIRST; every other app (flow, observer, entity, console, code,
# assistant) connects to it. To launch the whole framework in one go, use
# scripts/af-local.sh. Published twin: gateway.sh
# Usage: gateway-local.sh [--print]   (--print: show the serve command and exit)
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

PY="$(resolve_local_python)"
# The checkout's packages first (the version check below reads the checkout's gateway).
export PYTHONPATH="$(local_pythonpath)${PYTHONPATH:+:$PYTHONPATH}"
gateway_backlog_flags "$PY" "$ROOT_DIR"
# -P (safe path, Python 3.11+): never put the launch cwd on sys.path — a repo
# folder named like an installed package (abstractvoice/) otherwise shadows it
# as a namespace package and pkgutil.get_data returns None (2026-07-17 piper
# TTS incident: "Capability asset not found"). PYTHONPATH entries are kept.
SERVE_CMD=("$PY" -P -m abstractgateway serve --host "$GATEWAY_HOST" --port "$GATEWAY_PORT" ${GATEWAY_SERVE_FLAGS[@]+"${GATEWAY_SERVE_FLAGS[@]}"})
# --print: show the serve command this launcher would run, then exit — before
# anything is stopped, freed or created (tests, and "what would this start?").
if [[ "${1:-}" == "--print" ]]; then
    printf '%q ' "${SERVE_CMD[@]}"
    printf '\n'
    exit 0
fi
mkdir_logs
mkdir -p "$GATEWAY_DATA_DIR" >/dev/null 2>&1 || true

# Restart semantics (maintainer 2026-07-09): an already-running gateway is
# stopped and replaced, never a refusal. Stop by COMMAND LINE first (waits for
# process death, so gateway_runner.lock is released), then free the port as a
# safety net for non-gateway squatters, then prove the runner lock is free —
# an orphan serve process holding it would leave the new gateway serving HTTP
# while never ticking runs.
stop_gateway_serve_processes "AbstractGateway"
free_port "$GATEWAY_PORT" "AbstractGateway"
verify_gateway_runner_lock_free "$PY" "$GATEWAY_DATA_DIR/gateway_runner.lock"

export ABSTRACTGATEWAY_DATA_DIR="$GATEWAY_DATA_DIR"
info "Starting AbstractGateway (local checkout) on http://${GATEWAY_HOST}:${GATEWAY_PORT}"
info "  python:   ${PY}"
info "  data dir: ${GATEWAY_DATA_DIR}"
info "  PYTHONPATH: ${PYTHONPATH}"
info "  entity chat defaults: shelf 36 / context 65536 (code defaults)"
info "  apps: flow-local.sh / observer-local.sh / entity-local.sh / console-local.sh / code-local.sh — or everything at once: af-local.sh"
exec "${SERVE_CMD[@]}"
