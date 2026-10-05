#!/bin/sh
# https://abstractframework.ai/install.sh — forwards to the current AbstractFramework installer on GitHub
# (scripts/install.sh on main), so this address never goes stale. Flags pass through, e.g.
#   curl -LsSf https://abstractframework.ai/install.sh | sh -s -- --print
set -eu
SRC="https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh"
if command -v curl >/dev/null 2>&1; then
    curl -LsSf "$SRC" | sh -s -- "$@"
elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$SRC" | sh -s -- "$@"
else
    echo "install: neither curl nor wget is available; download $SRC and run it with sh." >&2
    exit 1
fi
