#!/usr/bin/env bash
# Gateway launch settings as `serve` FLAGS, never environment exports.
#
# Sourced by apps_common.sh (gateway.sh / gateway-local.sh and the af/start
# stacks that run them) and by gateway-flow[-local].sh. Operator rule: settings
# reach the gateway as launch flags. Gateway 0.13.0 takes the backlog folder
# and the backlog exec runner as `serve --backlog-root PATH --exec-runner on|off`
# (for this run; the saved setting stays untouched) and no longer reads the
# ABSTRACTGATEWAY_TRIAGE_REPO_ROOT / ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER
# variables except for a one-time import into the saved setting. An older
# gateway still reads the variables, so for it the launcher exports them and
# prints one line saying so.
#
# Inputs (launcher knobs, read here, never exported by this file):
#   ABSTRACTGATEWAY_TRIAGE_REPO_ROOT    backlog folder (default: the checkout root)
#   ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER 1/0 (default 1: continuum's backlog
#                                       execution pipeline; runs stay operator-triggered)
# Output: the array GATEWAY_SERVE_FLAGS (append it to the serve command line as
#   ${GATEWAY_SERVE_FLAGS[@]+"${GATEWAY_SERVE_FLAGS[@]}"} — bash 3.2 + set -u safe).

GATEWAY_FLAGS_MIN_VERSION="0.13.0"

# gateway_version PY: the X.Y.Z that `abstractgateway --version` prints, empty if none.
gateway_version() {
    local out
    out="$("$1" -P -m abstractgateway --version 2>/dev/null)" || return 0
    printf '%s\n' "$out" | sed -n 's/.*abstractgateway[[:space:]]\{1,\}v\{0,1\}\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -n 1
}

# version_at_least HAVE WANT: true when HAVE >= WANT (numeric X.Y.Z).
version_at_least() {
    awk -v have="$1" -v want="$2" 'BEGIN {
        n = split(have, h, "."); split(want, w, ".")
        for (i = 1; i <= 3; i++) { a = h[i] + 0; b = w[i] + 0
            if (a > b) exit 0; if (a < b) exit 1 }
        exit 0 }'
}

# gateway_backlog_flags PY ROOT [RUNNER_DEFAULT]: fills GATEWAY_SERVE_FLAGS for
# the gateway PY runs. RUNNER_DEFAULT (default 1) applies when the knob is unset;
# an EMPTY RUNNER_DEFAULT passes no exec-runner choice at all (the saved setting).
gateway_backlog_flags() {
    local py="$1" default_root="$2" runner_default="${3-1}" root runner="" ver
    root="${ABSTRACTGATEWAY_TRIAGE_REPO_ROOT:-$default_root}"
    case "$(printf '%s' "${ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER:-$runner_default}" | tr '[:upper:]' '[:lower:]')" in
        "") runner="" ;;
        1|true|yes|y|on) runner="on" ;;
        *) runner="off" ;;
    esac
    GATEWAY_SERVE_FLAGS=()
    ver="$(gateway_version "$py")"
    if [[ -n "$ver" ]] && version_at_least "$ver" "$GATEWAY_FLAGS_MIN_VERSION"; then
        # The flag wins for this run only; a stray variable from the launching
        # shell must not be imported into the saved setting behind it.
        unset ABSTRACTGATEWAY_TRIAGE_REPO_ROOT ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER
        [[ -n "$runner" ]] && GATEWAY_SERVE_FLAGS=(--exec-runner "$runner")
        # The gateway refuses to START on a --backlog-root without docs/backlog
        # (the old variable was not checked that strictly): skip the flag then,
        # and the gateway uses its saved setting or its own folder.
        if [[ -d "$root/docs/backlog" ]]; then
            GATEWAY_SERVE_FLAGS=(--backlog-root "$root" ${GATEWAY_SERVE_FLAGS[@]+"${GATEWAY_SERVE_FLAGS[@]}"})
        else
            echo "note: $root has no docs/backlog folder: no --backlog-root passed (the gateway keeps its saved backlog folder)" >&2
        fi
    else
        export ABSTRACTGATEWAY_TRIAGE_REPO_ROOT="$root"
        if [[ -n "$runner" ]]; then
            export ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER="$([[ "$runner" == on ]] && echo 1 || echo 0)"
        fi
        echo "note: abstractgateway ${ver:-(version unknown)} is older than ${GATEWAY_FLAGS_MIN_VERSION}: backlog folder and exec runner passed as environment variables (upgrade for --backlog-root / --exec-runner)" >&2
    fi
}
