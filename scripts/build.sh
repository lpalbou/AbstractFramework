#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — build all packages from local repos
# =============================================================================
# Development-only script that installs every AbstractFramework Python package
# in editable mode (from local checkouts, NOT from PyPI) and builds every npm
# package from source (NOT from the npm registry).
#
# All Python packages are installed into an isolated .venv at the project root.
# Third-party dependencies (pydantic, react, torch, …) are resolved normally
# from PyPI / npm — only AbstractFramework packages come from local source.
#
# Usage:
#   ./scripts/build.sh              # full build (Python + npm)
#   ./scripts/build.sh --python     # Python packages only
#   ./scripts/build.sh --npm        # npm packages only
#
# Prerequisites:
#   - Python 3.10+  (required)
#   - Node.js 18+   (optional; only needed for UI packages)
#   - git            (repos must already be cloned via scripts/clone.sh)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ROOT_DIR/.venv"

# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------
BUILD_PYTHON=true
BUILD_NPM=true

if [[ "${1:-}" == "--python" ]]; then
    BUILD_NPM=false
elif [[ "${1:-}" == "--npm" ]]; then
    BUILD_PYTHON=false
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
banner() {
    printf "\n%s\n" "============================================================"
    printf "%s\n"   "  AbstractFramework — build all packages (dev mode)"
    printf "%s\n"   "============================================================"
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

section() {
    echo ""
    echo "────────────────────────────────────────────────────────────"
    echo "  $1"
    echo "────────────────────────────────────────────────────────────"
}

# Check that a sibling repo directory exists; abort with a clear message if not.
require_repo() {
    local name="$1"
    if [[ ! -d "$ROOT_DIR/$name" ]]; then
        echo ""
        echo "ERROR: sibling repo not found: $ROOT_DIR/$name"
        echo "       Run  ./scripts/clone.sh  first to clone all repositories."
        exit 1
    fi
}

# Editable-install a Python package from a local directory.
# Usage: install_editable <relative_dir> [pip_extras]
# Example: install_editable abstractcore "[tools,media]"
install_editable() {
    local rel_dir="$1"
    local extras="${2:-}"
    local pkg_path="$ROOT_DIR/$rel_dir"

    require_repo "$rel_dir"
    echo ""
    echo "  📦  pip install -e ${rel_dir}${extras}"
    pip install --quiet -e "${pkg_path}${extras}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
banner

# ── Preflight checks ───────────────────────────────────────────────────────
require_cmd git

if $BUILD_PYTHON; then
    require_cmd python3
    if [[ "$(py_version_ok)" != "ok" ]]; then
        echo "ERROR: Python 3.10+ is required.  Detected: $(python3 --version 2>&1)"
        exit 1
    fi
    echo "✓ Python:   $(python3 --version 2>&1)"
fi

if $BUILD_NPM; then
    if command -v node >/dev/null 2>&1; then
        echo "✓ Node.js:  $(node --version)"
        echo "✓ npm:      $(npm --version)"
    else
        echo ""
        echo "WARNING: Node.js not found — skipping npm builds."
        echo "         Install Node 18+ to build the browser UI packages."
        BUILD_NPM=false
    fi
fi

echo "✓ Root:     $ROOT_DIR"

# ═══════════════════════════════════════════════════════════════════════════
# PYTHON PACKAGES
# ═══════════════════════════════════════════════════════════════════════════
if $BUILD_PYTHON; then
    section "Python — Creating / activating virtual environment"

    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        if [[ ! -d "$VENV_DIR" ]]; then
            echo "  Creating:  $VENV_DIR"
            python3 -m venv "$VENV_DIR"
        else
            echo "  Found:     $VENV_DIR"
        fi
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
        echo "  Activated: $VIRTUAL_ENV"
    else
        echo "  Using existing virtualenv: $VIRTUAL_ENV"
    fi

    echo ""
    echo "  Upgrading pip + build tools…"
    # hatchling is needed by abstractruntime, abstractgateway, abstractmemory
    pip install --quiet --upgrade pip setuptools wheel hatchling

    # ── Tier 0: No internal dependencies ────────────────────────────────
    section "Python — Tier 0  (no internal dependencies)"
    install_editable "abstractsemantics"
    install_editable "abstractmemory"
    install_editable "abstractvision"
    install_editable "abstractvoice"

    # ── Tier 1: Depends on Tier 0 ───────────────────────────────────────
    section "Python — Tier 1  (depends on Tier 0)"
    install_editable "abstractcore"
    install_editable "abstractruntime"

    # ── Tier 2: Depends on Tier 0–1 ────────────────────────────────────
    section "Python — Tier 2  (depends on Tier 0–1)"
    install_editable "abstractagent"
    install_editable "abstractgateway"

    # ── Tier 3: Depends on Tier 0–2 ────────────────────────────────────
    section "Python — Tier 3  (depends on Tier 0–2)"
    install_editable "abstractflow"
    install_editable "abstractcode"
    install_editable "abstractassistant"

    # ── Tier 4: Meta-package (AbstractFramework itself) ────────────────
    section "Python — Tier 4  (meta-package)"
    echo ""
    echo "  📦  pip install -e . (AbstractFramework)"
    pip install --quiet --no-deps -e "$ROOT_DIR"

    section "Python — Verification"
    echo ""
    echo "  Installed AbstractFramework packages:"
    pip list 2>/dev/null | grep -i "^abstract" || true

    py_ok=true
fi

# ═══════════════════════════════════════════════════════════════════════════
# NPM PACKAGES
# ═══════════════════════════════════════════════════════════════════════════
if $BUILD_NPM; then
    section "npm — Building UI packages from local source"

    npm_ok=true

    # ── abstractuic (monorepo with npm workspaces) ──────────────────────
    if [[ -d "$ROOT_DIR/abstractuic" ]]; then
        echo ""
        echo "  📦  abstractuic  (monorepo: ui-kit, panel-chat, monitors)"
        (
            cd "$ROOT_DIR/abstractuic"
            npm install --no-audit --no-fund 2>&1 | tail -1
            npm run build 2>&1 | tail -1
        ) && echo "       ✓ built" || { echo "       WARNING: abstractuic build failed"; npm_ok=false; }
    else
        echo "  WARNING: abstractuic/ not found — skipping"
        npm_ok=false
    fi

    # ── abstractobserver ────────────────────────────────────────────────
    if [[ -d "$ROOT_DIR/abstractobserver" ]]; then
        echo ""
        echo "  📦  abstractobserver"
        (
            cd "$ROOT_DIR/abstractobserver"
            npm install --no-audit --no-fund 2>&1 | tail -1
            npm run build 2>&1 | tail -1
        ) && echo "       ✓ built" || { echo "       WARNING: abstractobserver build failed"; npm_ok=false; }
    else
        echo "  WARNING: abstractobserver/ not found — skipping"
        npm_ok=false
    fi

    # ── abstractcode/web (browser coding assistant) ─────────────────────
    if [[ -d "$ROOT_DIR/abstractcode/web" ]]; then
        echo ""
        echo "  📦  abstractcode/web  (@abstractframework/code)"
        (
            cd "$ROOT_DIR/abstractcode/web"
            npm install --no-audit --no-fund 2>&1 | tail -1
            npm run build 2>&1 | tail -1
        ) && echo "       ✓ built" || { echo "       WARNING: abstractcode/web build failed"; npm_ok=false; }
    else
        echo "  WARNING: abstractcode/web/ not found — skipping"
        npm_ok=false
    fi

    # ── abstractflow/web/frontend (visual workflow editor) ──────────────
    if [[ -d "$ROOT_DIR/abstractflow/web/frontend" ]]; then
        echo ""
        echo "  📦  abstractflow/web/frontend  (@abstractframework/flow)"
        (
            cd "$ROOT_DIR/abstractflow/web/frontend"
            npm install --no-audit --no-fund 2>&1 | tail -1
            npm run build 2>&1 | tail -1
        ) && echo "       ✓ built" || { echo "       WARNING: abstractflow/web/frontend build failed"; npm_ok=false; }
    else
        echo "  WARNING: abstractflow/web/frontend/ not found — skipping"
        npm_ok=false
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "  Build complete."
if $BUILD_PYTHON; then
    if ${py_ok:-false}; then
        echo "  ✓ Python:  all packages installed (editable mode)"
    else
        echo "  ⚠ Python:  some packages may have issues"
    fi
fi
if $BUILD_NPM; then
    if ${npm_ok:-false}; then
        echo "  ✓ npm:     all UI packages built"
    else
        echo "  ⚠ npm:     some UI packages had issues (see warnings above)"
    fi
fi
echo "============================================================"
echo ""
if $BUILD_PYTHON; then
    echo "Virtual environment: $VENV_DIR"
    echo ""
    echo "To activate in your shell:"
    echo "  source $VENV_DIR/bin/activate"
    echo ""
    echo "Quick verification:"
    echo "  python -c 'import abstractcore; print(abstractcore)'"
    echo "  python -c 'import abstractruntime; print(abstractruntime)'"
    echo "  python -c 'import abstractagent; print(abstractagent)'"
fi
