#!/bin/sh
# =============================================================================
# AbstractFramework uninstaller (macOS / Linux)
# =============================================================================
# Removes what install.sh set up: the login item (LaunchAgent / systemd user
# unit), the running gateway, the `abstractgateway` uv tool (and nodejs-wheel
# when the installer added it), and, only if you say so, your data.
#
#   sh uninstall.sh                 # asks before removing, and about your data
#   sh uninstall.sh --yes           # no questions; keeps your data
#   sh uninstall.sh --yes --purge   # no questions; deletes your data too
#   curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/uninstall.sh | sh
#
# It is a thin front end: the removal itself is `install.sh --uninstall`, run
# from next to this file or downloaded from the same place, so the two can
# never disagree about what was installed. Every command it runs is printed.
# uv, its Python and its download cache (about 2.5 GB after an Apple Silicon
# install) are removed only when the installer added uv and you agree (or
# pass --remove-uv): other tools may use them. Ollama and LM Studio are kept
# (they have their own uninstallers).
#
# Options: --yes/-y, --purge (delete data), --remove-uv, --data-dir DIR,
#          --print (show, change nothing), -h/--help
# =============================================================================

if [ -n "${ZSH_VERSION:-}" ]; then emulate sh; fi
set -eu

AF_INSTALL_URL="https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh"
YES=0
PASS=""
while [ $# -gt 0 ]; do
    case "$1" in
        -y|--yes) YES=1 ;;
        --purge) PASS="$PASS --purge" ;;
        --remove-uv) PASS="$PASS --remove-uv" ;;
        --print|--dry-run|-n) PASS="$PASS --print"; YES=1 ;;
        --data-dir) [ $# -ge 2 ] || { echo "ERROR: --data-dir needs a value" >&2; exit 2; }
            AF_DATA_DIR="$2"; export AF_DATA_DIR; shift ;;
        --data-dir=*) AF_DATA_DIR="${1#*=}"; export AF_DATA_DIR ;;
        -h|--help) sed -n '2,23p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "ERROR: unknown argument: $1 (see --help)" >&2; exit 2 ;;
    esac
    shift
done

if [ "$YES" = 0 ]; then
    if { : </dev/tty; } 2>/dev/null; then
        printf 'Remove AbstractFramework from this computer? It stops the gateway and removes its login item. [y/N] ' >/dev/tty
        IFS= read -r _ans </dev/tty || _ans=""
        case "$_ans" in [Yy]*) ;; *) echo "Nothing was removed."; exit 0 ;; esac
    else
        echo "ERROR: no terminal to ask for confirmation; re-run with --yes to remove AbstractFramework." >&2
        exit 2
    fi
fi

# Only a real uninstall.sh file uses the install.sh next to it: piped through
# `curl | sh`, $0 is "sh" and "next to it" would be whatever folder the user is in.
_here=""
if [ -f "$0" ] && head -n 3 "$0" 2>/dev/null | grep -q "AbstractFramework uninstaller"; then
    _here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "")"
fi
if [ -n "$_here" ] && [ -f "$_here/install.sh" ]; then
    INSTALL_SH="$_here/install.sh"
else
    # Piped (curl | sh) or copied alone: fetch the installer it fronts.
    INSTALL_SH="$(mktemp "${TMPDIR:-/tmp}/af-install.XXXXXX")"
    trap 'rm -f "$INSTALL_SH"' EXIT
    echo "  \$ curl -LsSf $AF_INSTALL_URL -o $INSTALL_SH"
    if ! curl -LsSf "$AF_INSTALL_URL" -o "$INSTALL_SH"; then
        echo "ERROR: could not download the installer that performs the removal (no internet connection?)." >&2
        echo "What to do: connect to the internet and run the uninstaller again." >&2
        exit 1
    fi
fi

# --interactive: install.sh then asks about your data (default: keep it), unless
# --yes, --purge or --print already decided.
_ask="--interactive"
[ "$YES" = 1 ] && _ask=""
# shellcheck disable=SC2086  # PASS is a list of fixed flags
_rc=0
sh "$INSTALL_SH" --uninstall $_ask $PASS || _rc=$?
exit "$_rc"
