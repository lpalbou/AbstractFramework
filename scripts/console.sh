#!/usr/bin/env bash
# Start the CONTINUUM CONSOLE (published package @abstractframework/continuum) —
# continuous iterative development and deployment: backlog browsing + codex
# execution, report/email inbox triage, managed process control.
# Requires the gateway (start it first). Local-code twin: console-local.sh
#
# NOTE: requires @abstractframework/continuum to be PUBLISHED; until that first
# release, the -local twin is authoritative.
#
# Port note: the cli.js self-default (3002) collides with the code app; this
# launcher always passes PORT explicitly (default 3003, ABSTRACTCONTINUUM_PORT).
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

require_gateway

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$CONTINUUM_PORT" "the continuum console"

export ABSTRACTCONTINUUM_GATEWAY_URL="${ABSTRACTCONTINUUM_GATEWAY_URL:-$GATEWAY_URL}"
CONTINUUM_NPM_SPEC="${CONTINUUM_NPM_SPEC:-@abstractframework/continuum}"
info "Starting the continuum console (published) on http://${CONTINUUM_HOST}:${CONTINUUM_PORT}  (gateway ${GATEWAY_URL})"
info "  open: http://${CONTINUUM_HOST}:${CONTINUUM_PORT}/"
exec env HOST="$CONTINUUM_HOST" PORT="$CONTINUUM_PORT" \
    ABSTRACTCONTINUUM_GATEWAY_URL="$ABSTRACTCONTINUUM_GATEWAY_URL" \
    npx --yes "$CONTINUUM_NPM_SPEC"
