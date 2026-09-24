#!/bin/sh
# AbstractFramework uninstaller for macOS: double-click this file in Finder.
# It runs uninstall.sh (from next to this file, or from GitHub), which asks
# before removing anything and asks separately whether to delete your data.

if [ -n "${ZSH_VERSION:-}" ]; then emulate sh; fi
AF_UNINSTALL_URL="https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/uninstall.sh"

clear 2>/dev/null || true
printf '\n  AbstractFramework uninstaller\n  =============================\n\n'

_here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "")"
_rc=0
if [ -n "$_here" ] && [ -f "$_here/uninstall.sh" ]; then
    sh "$_here/uninstall.sh" "$@" || _rc=$?
else
    echo "  \$ curl -LsSf $AF_UNINSTALL_URL | sh"
    _tmp="$(mktemp "${TMPDIR:-/tmp}/af-uninstall.XXXXXX")"
    if curl -LsSf "$AF_UNINSTALL_URL" -o "$_tmp"; then
        sh "$_tmp" "$@" || _rc=$?
    else
        printf '\nERROR: no internet connection: the uninstaller could not be downloaded.\n'
        printf 'What to do: connect to the internet, then double-click this file again.\n'
        _rc=1
    fi
    rm -f "$_tmp"
fi

echo ""
if [ "$_rc" = 0 ]; then echo "  Done. You can close this window."
else echo "  The uninstaller stopped (exit code $_rc); the message above says why."; fi
printf '  Press Return to close this window. '
{ IFS= read -r _ans </dev/tty; } 2>/dev/null || true
exit "$_rc"
