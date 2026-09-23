#!/usr/bin/env bash
# Start the SUMMONED-ENTITY app from the LOCAL checkout — the multi-entity
# manager: create/list entities, watch a mind's memory graph live, and talk
# with it. Served by AbstractEntity's own bin/cli.js (its own package since
# the 2026-07-12 split; the observer no longer ships entity.html).
# Requires the gateway (start it first). Published twin: entity.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"
LOCAL_SUFFIX="-local"

require_gateway

NODE_BIN="${NODE_BIN:-node}"
ENT_DIR="$ROOT_DIR/abstractentity"
[[ -f "$ENT_DIR/bin/cli.js" ]] || die "no $ENT_DIR/bin/cli.js — checkout AbstractEntity first."
[[ -f "$ENT_DIR/dist/index.html" ]] || die "no $ENT_DIR/dist/index.html — run: (cd abstractentity && npm install && npm run build)."
clear_quarantine "$ENT_DIR/node_modules"
clear_quarantine "$ENT_DIR/dist"

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$ENTITY_PORT" "the summoned-entity app"

export ABSTRACTENTITY_GATEWAY_URL="${ABSTRACTENTITY_GATEWAY_URL:-$GATEWAY_URL}"
# The header backlink to the observer app (its own deployment).
export ABSTRACTENTITY_OBSERVER_URL="${ABSTRACTENTITY_OBSERVER_URL:-http://${OBSERVER_HOST:-127.0.0.1}:${OBSERVER_PORT:-3001}}"
ENTITY_URL="http://${ENTITY_HOST}:${ENTITY_PORT}/"
info "Starting the summoned-entity app (local checkout) on http://${ENTITY_HOST}:${ENTITY_PORT}  (gateway ${GATEWAY_URL})"
info "  open: ${ENTITY_URL}"
info "  (no ?entity= => the multi-entity index: create, list, pick a mind)"
exec env HOST="$ENTITY_HOST" PORT="$ENTITY_PORT" \
    ABSTRACTENTITY_GATEWAY_URL="$ABSTRACTENTITY_GATEWAY_URL" \
    ABSTRACTENTITY_OBSERVER_URL="$ABSTRACTENTITY_OBSERVER_URL" \
    "$NODE_BIN" "$ENT_DIR/bin/cli.js"
