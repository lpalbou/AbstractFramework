#!/usr/bin/env bash
# Start AbstractAssistant (published package) — the desktop tray assistant.
# It connects to the gateway (start it first). Local-code twin: assistant-local.sh
#
# The assistant reads its gateway target from its own config/env; we export
# ABSTRACTGATEWAY_URL so a fresh setup points at the right control plane.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

require_gateway

PY="$(resolve_published_python)"

# Restart semantics (maintainer 2026-07-09): the tray app has no port — stop
# an already-running assistant (module or console-script form) first.
stop_processes "AbstractAssistant" "abstractassistant\.cli" "bin/assistant($| )" \
    "AbstractAssistant\.app/Contents/MacOS/"

export ABSTRACTGATEWAY_URL="${ABSTRACTGATEWAY_URL:-$GATEWAY_URL}"
# Older supervisors already running in memory do not understand clean Quit.
# Only that exact parent needs the compatibility guard; standalone launches
# and current supervisors exec the app directly as usual.
source "$APPS_LIB_DIR/assistant_lifecycle.sh"
if assistant_needs_legacy_guard; then
    exec "$PY" "$APPS_LIB_DIR/assistant_legacy_supervisor.py" "$@"
fi

info "Starting AbstractAssistant (published), gateway ${ABSTRACTGATEWAY_URL}"
# The console entry point is `assistant` (pyproject [project.scripts]); fall
# back to the module if the script shim is not on PATH.
if command -v assistant >/dev/null 2>&1; then
    exec assistant "$@"
fi
exec "$PY" -m abstractassistant.cli "$@"
