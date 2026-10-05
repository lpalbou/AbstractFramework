#!/bin/sh
# https://abstractframework.ai/uninstall.sh — forwards to the current AbstractFramework uninstaller on GitHub
# (scripts/uninstall.sh on main), so this address never goes stale. Flags pass through, e.g.
#   curl -LsSf https://abstractframework.ai/uninstall.sh | sh -s -- --print
set -eu
SRC="https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/uninstall.sh"
if command -v curl >/dev/null 2>&1; then
    curl -LsSf "$SRC" | sh -s -- "$@"
elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$SRC" | sh -s -- "$@"
else
    echo "install: neither curl nor wget is available; download $SRC and run it with sh." >&2
    exit 1
fi
