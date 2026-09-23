#!/usr/bin/env bash
# Start AbstractFlow (published package). Requires the gateway (start it first).
# Local-code twin: flow-local.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

require_gateway

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$FLOW_PORT" "AbstractFlow"

export ABSTRACTFLOW_GATEWAY_URL="${ABSTRACTFLOW_GATEWAY_URL:-$GATEWAY_URL}"
FLOW_NPM_SPEC="${FLOW_NPM_SPEC:-@abstractframework/flow}"
info "Starting AbstractFlow (published) on http://${FLOW_HOST}:${FLOW_PORT}  (gateway ${GATEWAY_URL})"
exec env HOST="$FLOW_HOST" PORT="$FLOW_PORT" ABSTRACTFLOW_GATEWAY_URL="$ABSTRACTFLOW_GATEWAY_URL" \
    npx --yes "$FLOW_NPM_SPEC"
