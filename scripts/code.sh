#!/usr/bin/env bash
# Start the browser CODE ASSISTANT (published package @abstractframework/code).
# Requires the gateway (start it first). Local-code twin: code-local.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"

require_gateway

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$CODE_PORT" "the code assistant"

export ABSTRACTCODE_GATEWAY_URL="${ABSTRACTCODE_GATEWAY_URL:-$GATEWAY_URL}"
CODE_NPM_SPEC="${CODE_NPM_SPEC:-@abstractframework/code}"
info "Starting the code assistant (published) on http://${CODE_HOST}:${CODE_PORT}  (gateway ${GATEWAY_URL})"
info "  open: http://${CODE_HOST}:${CODE_PORT}/"
exec env HOST="$CODE_HOST" PORT="$CODE_PORT" \
    ABSTRACTCODE_GATEWAY_URL="$ABSTRACTCODE_GATEWAY_URL" \
    npx --yes "$CODE_NPM_SPEC"
