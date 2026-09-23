#!/usr/bin/env bash
# Start AbstractObserver from the LOCAL checkout — the REGULAR observability UI
# (runs, ledgers, launch, mindmap). For the summoned-entity app, use
# entity-local.sh. Requires the gateway (start it first). Published twin: observer.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"
LOCAL_SUFFIX="-local"

require_gateway

NODE_BIN="${NODE_BIN:-node}"
OBS_DIR="$ROOT_DIR/abstractobserver"
[[ -f "$OBS_DIR/bin/cli.js" ]] || die "no $OBS_DIR/bin/cli.js — build AbstractObserver first (cd abstractobserver && npm run build)."
[[ -f "$OBS_DIR/dist/index.html" ]] || die "no $OBS_DIR/dist/index.html — run: (cd abstractobserver && npm ci && npm run build)."
clear_quarantine "$OBS_DIR/node_modules"
clear_quarantine "$OBS_DIR/dist"

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$OBSERVER_PORT" "AbstractObserver"

export ABSTRACTOBSERVER_GATEWAY_URL="${ABSTRACTOBSERVER_GATEWAY_URL:-$GATEWAY_URL}"
# Where the entity app lives (its own package since 2026-07-12) — drives
# the UI's "Entities ↗" links and the /entity.html bookmark redirect.
export ABSTRACTOBSERVER_ENTITY_APP_URL="${ABSTRACTOBSERVER_ENTITY_APP_URL:-http://${ENTITY_HOST}:${ENTITY_PORT}}"
info "Starting AbstractObserver (local checkout) on http://${OBSERVER_HOST}:${OBSERVER_PORT}  (gateway ${GATEWAY_URL})"
info "  regular observability UI — index.html"
exec env HOST="$OBSERVER_HOST" PORT="$OBSERVER_PORT" ABSTRACTOBSERVER_GATEWAY_URL="$ABSTRACTOBSERVER_GATEWAY_URL" \
    ABSTRACTOBSERVER_ENTITY_APP_URL="$ABSTRACTOBSERVER_ENTITY_APP_URL" \
    "$NODE_BIN" "$OBS_DIR/bin/cli.js"
