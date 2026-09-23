#!/usr/bin/env bash
# Start AbstractObserver (published package) — the REGULAR observability UI
# (runs, ledgers, launch, mindmap). For the summoned-entity app, use entity.sh.
# Requires the gateway (start it first). Local-code twin: observer-local.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

require_gateway

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$OBSERVER_PORT" "AbstractObserver"

export ABSTRACTOBSERVER_GATEWAY_URL="${ABSTRACTOBSERVER_GATEWAY_URL:-$GATEWAY_URL}"
# Where the entity app lives (its own package since 2026-07-12) — drives
# the UI's "Entities ↗" links and the /entity.html bookmark redirect.
export ABSTRACTOBSERVER_ENTITY_APP_URL="${ABSTRACTOBSERVER_ENTITY_APP_URL:-http://${ENTITY_HOST}:${ENTITY_PORT}}"
OBSERVER_NPM_SPEC="${OBSERVER_NPM_SPEC:-@abstractframework/observer}"
info "Starting AbstractObserver (published) on http://${OBSERVER_HOST}:${OBSERVER_PORT}  (gateway ${GATEWAY_URL})"
info "  regular observability UI — index.html"
exec env HOST="$OBSERVER_HOST" PORT="$OBSERVER_PORT" ABSTRACTOBSERVER_GATEWAY_URL="$ABSTRACTOBSERVER_GATEWAY_URL" \
    ABSTRACTOBSERVER_ENTITY_APP_URL="$ABSTRACTOBSERVER_ENTITY_APP_URL" \
    npx --yes "$OBSERVER_NPM_SPEC"
