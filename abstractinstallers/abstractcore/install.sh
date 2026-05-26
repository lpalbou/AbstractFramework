#!/usr/bin/env bash
# AbstractFramework AbstractCore Installer (test)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10+ is required to run the installer." >&2
  exit 1
fi

python3 "${SCRIPT_DIR}/installer.py" "$@"
