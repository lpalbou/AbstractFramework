#!/usr/bin/env bash
# Start AbstractGateway (published package) — the control plane. Launch this
# FIRST; every other app (flow, observer, entity, console, code, assistant)
# connects to it. To launch the whole framework in one go, use scripts/af.sh
#
# Local-code twin: gateway-local.sh
# Config via env: ABSTRACTGATEWAY_HOST/PORT, ABSTRACTGATEWAY_DATA_DIR,
#   ABSTRACTGATEWAY_AUTH_TOKEN, ABSTRACTGATEWAY_FLOWS_DIR, provider/model.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

PY="$(resolve_published_python)"
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
info "Starting AbstractGateway (published) on http://${GATEWAY_HOST}:${GATEWAY_PORT}"
info "  data dir: ${GATEWAY_DATA_DIR}"
info "  entity chat defaults: shelf 36 / context 65536 (code defaults; override with ABSTRACTGATEWAY_ENTITY_CHAT_*)"
info "  apps: flow.sh / observer.sh / entity.sh / console.sh / code.sh — or everything at once: af.sh"
# -P (safe path, Python 3.11+): never put the launch cwd on sys.path — a repo
# folder named like an installed package (abstractvoice/) otherwise shadows it
# as a namespace package and pkgutil.get_data returns None (2026-07-17 piper
# TTS incident: "Capability asset not found"). PYTHONPATH entries are kept.
exec "$PY" -P -m abstractgateway serve --host "$GATEWAY_HOST" --port "$GATEWAY_PORT"
