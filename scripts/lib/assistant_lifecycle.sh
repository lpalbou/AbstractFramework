#!/usr/bin/env bash
# Return true only for an Assistant owned by a still-running, pre-policy stack.
assistant_needs_legacy_guard() {
    [[ -z "${AF_SUPERVISOR_RESTART_POLICY:-}" ]] || return 1
    local owner
    owner="$(cat "$RUNTIME_DIR/af_stack.pid" 2>/dev/null)" || return 1
    [[ "$owner" == "$PPID" ]] && kill -0 "$PPID" 2>/dev/null
}
