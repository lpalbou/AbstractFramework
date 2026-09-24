#!/bin/sh
# AbstractFramework installer for macOS: double-click this file in Finder.
#
# It opens Terminal and runs install.sh (from next to this file, or the
# latest one from GitHub) with --interactive, which asks one question (start
# at login?) and then installs everything under your home folder: no admin
# password. When it finishes, your browser opens AbstractFramework.
# Every command it runs is printed and logged.

if [ -n "${ZSH_VERSION:-}" ]; then emulate sh; fi
AF_INSTALL_URL="https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh"

clear 2>/dev/null || true
cat <<'BANNER'

  ============================================================
     AbstractFramework installer
  ============================================================

  This window installs AbstractFramework on this Mac. It takes
  about 5 to 15 minutes, depending on your internet connection.

  - Everything goes into your home folder; no admin password.
  - Each step is shown below as it happens.
  - When it is done, your web browser opens AbstractFramework.

BANNER

_here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "")"
_rc=0
if [ -n "$_here" ] && [ -f "$_here/install.sh" ]; then
    sh "$_here/install.sh" --interactive "$@" || _rc=$?
elif command -v curl >/dev/null 2>&1; then
    echo "  \$ curl -LsSf $AF_INSTALL_URL | sh -s -- --interactive"
    _tmp="$(mktemp "${TMPDIR:-/tmp}/af-install.XXXXXX")"
    if curl -LsSf "$AF_INSTALL_URL" -o "$_tmp"; then
        sh "$_tmp" --interactive "$@" || _rc=$?
    else
        printf '\nERROR: no internet connection: the installer could not be downloaded.\n'
        printf 'What to do: connect to the internet, then double-click this file again.\n'
        _rc=1
    fi
    rm -f "$_tmp"
else
    printf '\nERROR: curl is missing, so nothing can be downloaded.\n'
    _rc=1
fi

echo ""
if [ "$_rc" = 0 ]; then
    echo "  All done. You can close this window."
else
    echo "  The installer stopped (exit code $_rc). The message just above says what to do;"
    echo "  after fixing it, double-click this file again: it continues where it stopped."
    printf '  Press Return to close this window. '
    { IFS= read -r _ans </dev/tty; } 2>/dev/null || true
fi
exit "$_rc"
