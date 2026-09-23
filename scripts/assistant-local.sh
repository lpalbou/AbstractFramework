#!/usr/bin/env bash
# Start AbstractAssistant from the LOCAL checkout — the desktop tray assistant.
# It connects to the gateway (start it first). Published twin: assistant.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"
LOCAL_SUFFIX="-local"

require_gateway

PY="$(resolve_local_python)"
ASSISTANT_DIR="$ROOT_DIR/abstractassistant"
[[ -d "$ASSISTANT_DIR/abstractassistant" ]] || die "no $ASSISTANT_DIR/abstractassistant package in the checkout."

# Restart semantics (maintainer 2026-07-09): the tray app has no port — stop
# an already-running assistant by its command line before starting this one.
# The installed .app bundle counts: it is the same assistant against the same
# gateway, and matching only `abstractassistant.cli` left it running, so the
# stack put a SECOND tray icon beside it instead of replacing it.
stop_processes "AbstractAssistant" "abstractassistant\.cli" "AbstractAssistant\.app/Contents/MacOS/"

export ABSTRACTGATEWAY_URL="${ABSTRACTGATEWAY_URL:-$GATEWAY_URL}"
# Run straight from the checkout: put the assistant (and its sibling src-layout
# deps) on PYTHONPATH so no install is needed.
export PYTHONPATH="$ASSISTANT_DIR:$(local_pythonpath)${PYTHONPATH:+:$PYTHONPATH}"
info "Starting AbstractAssistant (local checkout), gateway ${ABSTRACTGATEWAY_URL}"
info "  python: ${PY}"
exec "$PY" -m abstractassistant.cli "$@"
