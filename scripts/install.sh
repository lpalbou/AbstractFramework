#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — installer
# =============================================================================
# This installs the full pinned AbstractFramework release profile.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | bash
#
# Or download and run:
#   ./scripts/install.sh
# =============================================================================

set -euo pipefail

banner() {
  printf "\n%s\n" "============================================================"
  printf "%s\n" "  AbstractFramework — install"
  printf "%s\n" "============================================================"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1"
    exit 1
  fi
}

py_version_ok() {
  python3 - <<'PY'
import sys
ok = sys.version_info >= (3, 10)
print("ok" if ok else "bad")
PY
}

banner

require_cmd python3

if [[ "$(py_version_ok)" != "ok" ]]; then
  echo "ERROR: Python 3.10+ is required. Detected: $(python3 --version 2>&1)"
  exit 1
fi

echo "✓ Python: $(python3 --version 2>&1)"

if command -v node >/dev/null 2>&1; then
  echo "✓ Node.js: $(node --version) (optional; used for AbstractObserver UI)"
else
  echo "ℹ Node.js not found (optional). Install Node 18+ if you want the browser UI: npx @abstractframework/observer"
fi

# Create venv if not already in one
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo ""
  echo "Creating virtual environment: ./.venv"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "✓ Activated: $VIRTUAL_ENV"
else
  echo "✓ Using existing virtualenv: $VIRTUAL_ENV"
fi

echo ""
echo "Upgrading pip..."
python -m pip install -U pip

echo ""
echo "Installing AbstractFramework full release profile..."
python -m pip install "abstractframework==0.1.1"

echo ""
echo "✓ Done."
echo ""
echo "Next steps (pick one):"
echo ""
echo "1) Local terminal host (AbstractCode):"
echo "   abstractcode --provider ollama --model qwen3:1.7b-q4_K_M"
echo ""
echo "2) Deploy a run gateway + open the browser UI (AbstractGateway + AbstractObserver):"
echo "   export ABSTRACTGATEWAY_AUTH_TOKEN=\"\$(python -c 'import secrets; print(secrets.token_urlsafe(32))')\""
echo "   export ABSTRACTGATEWAY_ALLOWED_ORIGINS=\"http://localhost:*,http://127.0.0.1:*\""
echo "   export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle"
echo "   export ABSTRACTGATEWAY_FLOWS_DIR=\"/path/to/bundles\"   # directory of *.flow bundles (or upload later)"
echo "   export ABSTRACTGATEWAY_DATA_DIR=\"\$PWD/runtime/gateway\""
echo "   abstractgateway serve --host 127.0.0.1 --port 8080"
echo "   npx @abstractframework/observer"
echo ""
echo "Docs:"
echo "  - Getting started: https://github.com/lpalbou/AbstractFramework/blob/main/docs/getting-started.md"
echo "  - Ecosystem index: https://github.com/lpalbou/AbstractFramework#readme"
