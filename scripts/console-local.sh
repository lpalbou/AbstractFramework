#!/usr/bin/env bash
# Start the CONTINUUM CONSOLE from the LOCAL checkout (abstractcontinuum) —
# continuous iterative development and deployment: backlog browsing + codex
# execution, report/email inbox triage, managed process control.
# Requires the gateway (start it first). Published twin: console.sh
#
# Port note: the cli.js self-default (3002) collides with the code app; this
# launcher always passes PORT explicitly (default 3003, ABSTRACTCONTINUUM_PORT).
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"
LOCAL_SUFFIX="-local"

require_gateway

NODE_BIN="${NODE_BIN:-node}"
CONT_DIR="$ROOT_DIR/abstractcontinuum"
[[ -f "$CONT_DIR/bin/cli.js" ]] || die "no $CONT_DIR/bin/cli.js — checkout AbstractContinuum first."
[[ -f "$CONT_DIR/dist/index.html" ]] || die "no $CONT_DIR/dist/index.html — run: (cd abstractcontinuum && npm install && npm run build)."
clear_quarantine "$CONT_DIR/node_modules"
clear_quarantine "$CONT_DIR/dist"

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$CONTINUUM_PORT" "the continuum console"

export ABSTRACTCONTINUUM_GATEWAY_URL="${ABSTRACTCONTINUUM_GATEWAY_URL:-$GATEWAY_URL}"
info "Starting the continuum console (local checkout) on http://${CONTINUUM_HOST}:${CONTINUUM_PORT}  (gateway ${GATEWAY_URL})"
info "  open: http://${CONTINUUM_HOST}:${CONTINUUM_PORT}/"
exec env HOST="$CONTINUUM_HOST" PORT="$CONTINUUM_PORT" \
    ABSTRACTCONTINUUM_GATEWAY_URL="$ABSTRACTCONTINUUM_GATEWAY_URL" \
    "$NODE_BIN" "$CONT_DIR/bin/cli.js"
