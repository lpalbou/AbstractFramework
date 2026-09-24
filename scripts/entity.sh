#!/usr/bin/env bash
# Start the SUMMONED-ENTITY app (published package) — the multi-entity manager:
# create/list entities, watch a mind's memory graph live, and talk with it.
# Served by AbstractEntity's own static server (its own package since the
# 2026-07-12 split; the observer no longer ships entity.html).
# Requires the gateway (start it first). Local-code twin: entity-local.sh
#
# Published on npm since @abstractframework/entity 0.1.0 (2026-09-23); pin a
# version with ENTITY_NPM_SPEC=@abstractframework/entity@0.2.0.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

require_gateway

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$ENTITY_PORT" "the summoned-entity app"

export ABSTRACTENTITY_GATEWAY_URL="${ABSTRACTENTITY_GATEWAY_URL:-$GATEWAY_URL}"
export ABSTRACTENTITY_OBSERVER_URL="${ABSTRACTENTITY_OBSERVER_URL:-http://${OBSERVER_HOST:-127.0.0.1}:${OBSERVER_PORT:-3001}}"
ENTITY_NPM_SPEC="${ENTITY_NPM_SPEC:-@abstractframework/entity}"
ENTITY_URL="http://${ENTITY_HOST}:${ENTITY_PORT}/"
info "Starting the summoned-entity app (published) on http://${ENTITY_HOST}:${ENTITY_PORT}  (gateway ${GATEWAY_URL})"
info "  open: ${ENTITY_URL}"
info "  (no ?entity= => the multi-entity index: create, list, pick a mind)"
exec env HOST="$ENTITY_HOST" PORT="$ENTITY_PORT" \
    ABSTRACTENTITY_GATEWAY_URL="$ABSTRACTENTITY_GATEWAY_URL" \
    ABSTRACTENTITY_OBSERVER_URL="$ABSTRACTENTITY_OBSERVER_URL" \
    npx --yes "$ENTITY_NPM_SPEC"
