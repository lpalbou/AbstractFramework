#!/bin/sh
# AbstractFramework installer for macOS: double-click this file in Finder.
#
# It opens Terminal and runs the latest install.sh from GitHub, the same script
# as the one-line install, with --interactive: it asks one question (start at
# login?) and installs everything under your home folder, no admin password.
# Double-clicking it again upgrades an existing install the same way. The copy
# of install.sh next to this file is used only when GitHub cannot be reached (or answers
# with something that is not the installer, such as a network sign-in page).
# When it finishes, your browser opens AbstractFramework. Every command it runs
# is printed and logged.

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
_tmp=""
if command -v curl >/dev/null 2>&1; then
    _tmp="$(mktemp "${TMPDIR:-/tmp}/af-install.XXXXXX")"
    echo "  \$ curl -LsSf $AF_INSTALL_URL | sh -s -- --interactive"
    curl -LsSf "$AF_INSTALL_URL" -o "$_tmp" 2>/dev/null || { rm -f "$_tmp"; _tmp=""; }
    # A captive portal or proxy can answer with a web page instead of the script: run only a
    # download that is the installer (it starts with #!/bin/sh), else use the copy next to this file.
    if [ -n "$_tmp" ] && [ "$(head -n 1 "$_tmp" 2>/dev/null)" != "#!/bin/sh" ]; then
        rm -f "$_tmp"; _tmp=""
        _not_script=1
    fi
fi
if [ -n "$_tmp" ]; then
    sh "$_tmp" --interactive "$@" || _rc=$?
    rm -f "$_tmp"
elif [ -n "$_here" ] && [ -f "$_here/install.sh" ]; then
    if [ "${_not_script:-0}" = 1 ]; then
        echo "  The download was not the installer (a network sign-in page?): running the copy of the installer next to this file."
    else
        echo "  GitHub could not be reached: running the copy of the installer next to this file."
    fi
    sh "$_here/install.sh" --interactive "$@" || _rc=$?
else
    printf '\nERROR: no internet connection: the installer could not be downloaded.\n'
    printf 'What to do: connect to the internet, then double-click this file again.\n'
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
