#!/usr/bin/env bash
# Start AbstractFlow from the LOCAL checkout (serves abstractflow/dist via its
# bin/cli.js). Requires the gateway (start it first). Published twin: flow.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"
LOCAL_SUFFIX="-local"

require_gateway

NODE_BIN="${NODE_BIN:-node}"
FLOW_DIR="$ROOT_DIR/abstractflow"
[[ -f "$FLOW_DIR/bin/cli.js" ]] || die "no $FLOW_DIR/bin/cli.js — build AbstractFlow first (cd abstractflow && npm run build)."
[[ -f "$FLOW_DIR/dist/index.html" ]] || die "no $FLOW_DIR/dist/index.html — run: (cd abstractflow && npm ci && npm run build)."
clear_quarantine "$FLOW_DIR/node_modules"
clear_quarantine "$FLOW_DIR/dist"

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$FLOW_PORT" "AbstractFlow"

export ABSTRACTFLOW_GATEWAY_URL="${ABSTRACTFLOW_GATEWAY_URL:-$GATEWAY_URL}"
info "Starting AbstractFlow (local checkout) on http://${FLOW_HOST}:${FLOW_PORT}  (gateway ${GATEWAY_URL})"
exec env HOST="$FLOW_HOST" PORT="$FLOW_PORT" ABSTRACTFLOW_GATEWAY_URL="$ABSTRACTFLOW_GATEWAY_URL" \
    "$NODE_BIN" "$FLOW_DIR/bin/cli.js"
