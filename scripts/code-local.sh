#!/usr/bin/env bash
# Start the browser CODE ASSISTANT from the LOCAL checkout (abstractcode/web,
# @abstractframework/code). Requires the gateway (start it first).
# Published twin: code.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/apps_common.sh"
LOCAL_SUFFIX="-local"

require_gateway

NODE_BIN="${NODE_BIN:-node}"
CODE_DIR="$ROOT_DIR/abstractcode/web"
[[ -f "$CODE_DIR/bin/cli.js" ]] || die "no $CODE_DIR/bin/cli.js — checkout abstractcode first."
[[ -f "$CODE_DIR/dist/index.html" ]] || die "no $CODE_DIR/dist/index.html — run: (cd abstractcode/web && npm install && npm run build)."
clear_quarantine "$CODE_DIR/node_modules"
clear_quarantine "$CODE_DIR/dist"

# Restart semantics (maintainer 2026-07-09): replace a running instance.
free_port "$CODE_PORT" "the code assistant"

export ABSTRACTCODE_GATEWAY_URL="${ABSTRACTCODE_GATEWAY_URL:-$GATEWAY_URL}"
info "Starting the code assistant (local checkout) on http://${CODE_HOST}:${CODE_PORT}  (gateway ${GATEWAY_URL})"
info "  open: http://${CODE_HOST}:${CODE_PORT}/"
exec env HOST="$CODE_HOST" PORT="$CODE_PORT" \
    ABSTRACTCODE_GATEWAY_URL="$ABSTRACTCODE_GATEWAY_URL" \
    "$NODE_BIN" "$CODE_DIR/bin/cli.js"
