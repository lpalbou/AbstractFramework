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
#   source ./scripts/build.sh       # build AND stay in the .venv afterwards (recommended)
#   ./scripts/build.sh              # build (venv activates inside script only)
#   ./scripts/build.sh --python     # Python packages only
#   ./scripts/build.sh --npm        # npm packages only
#   ./scripts/build.sh --clean      # delete .venv first (avoids pollution from other projects)
#
# Prerequisites:
#   - Python 3.10+  (required)
#   - Node.js 18+   (optional; only needed for UI packages)
#   - git            (repos must already be cloned via scripts/clone.sh)
# =============================================================================

# Detect whether the script is being sourced or executed.
# IMPORTANT: the shebang is ignored when sourcing, so this must work in zsh/bash.
_AF_SOURCED=false
if (return 0 2>/dev/null); then
    _AF_SOURCED=true
fi

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
_AF_THIS_FILE=""
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
    _AF_THIS_FILE="${BASH_SOURCE[0]}"
elif [[ -n "${ZSH_VERSION:-}" ]]; then
    _AF_THIS_FILE="${(%):-%x}"
else
    _AF_THIS_FILE="$0"
fi

SCRIPT_DIR="$(cd "$(dirname "${_AF_THIS_FILE}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ROOT_DIR/.venv"

# If sourced, run the build in a real bash process (so bash-only syntax is safe),
# then activate the venv in the current shell and return.
if $_AF_SOURCED; then
    AF_BUILD_WRAPPER=1 bash "$SCRIPT_DIR/build.sh" "$@" || return 1
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "✓ Virtualenv is active in your shell."
    return 0
fi

set -euo pipefail

# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------
BUILD_PYTHON=true
BUILD_NPM=true
CLEAN_VENV=false

for arg in "$@"; do
    case "$arg" in
        --python) BUILD_NPM=false ;;
        --npm)    BUILD_PYTHON=false ;;
        --clean)  CLEAN_VENV=true ;;
    esac
done

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
        af_die "required command not found: $1"
    fi
}

af_die() {
    # Abort the build with a clear message.
    # IMPORTANT: when this script is sourced, `exit` would terminate the user's shell.
    local msg="$1"
    echo "ERROR: ${msg}"
    if $_AF_SOURCED; then
        return 1
    fi
    exit 1
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
        af_die "missing sibling repo: $name"
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
        af_die "Python 3.10+ is required. Detected: $(python3 --version 2>&1)"
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

    # --clean: remove existing venv to avoid pollution from other projects
    if $CLEAN_VENV && [[ -d "$VENV_DIR" ]]; then
        echo "  🗑️  Removing existing venv (--clean): $VENV_DIR"
        rm -rf "$VENV_DIR"
        # Also clear VIRTUAL_ENV so we don't skip venv creation below
        unset VIRTUAL_ENV 2>/dev/null || true
    fi

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
        if [[ "$VIRTUAL_ENV" != "$VENV_DIR" ]]; then
            echo ""
            echo "ERROR: Active venv ($VIRTUAL_ENV) differs from project venv ($VENV_DIR)"
            echo "       Refusing to continue to avoid polluting an unrelated environment."
            echo ""
            echo "       Fix:  deactivate && source ./scripts/build.sh --clean"
            echo ""
            echo "       Override (unsafe): AF_ALLOW_FOREIGN_VENV=1 source ./scripts/build.sh"
            if [[ "${AF_ALLOW_FOREIGN_VENV:-}" != "1" ]]; then
                af_die "foreign venv detected"
            fi
            echo "  ⚠️  WARNING: Proceeding due to AF_ALLOW_FOREIGN_VENV=1 (unsafe)."
        fi
        echo "  Using existing virtualenv: $VIRTUAL_ENV"
    fi

    echo ""
    echo "  Upgrading pip + build tools…"
    # hatchling is needed by abstractruntime, abstractgateway, abstractmemory
    pip install --quiet --upgrade pip setuptools wheel hatchling

    # ── Tier 0: No internal dependencies ────────────────────────────────
    section "Python — Tier 0  (no internal dependencies)"
    install_editable "abstractsemantics"
    install_editable "abstractmemory" "[lancedb]"
    install_editable "abstractvision"
    install_editable "abstractvoice"
    install_editable "abstractmusic"

    # ── Tier 1: Depends on Tier 0 ───────────────────────────────────────
    section "Python — Tier 1  (depends on Tier 0)"
    # Install AbstractCore with the full extras matching the umbrella pyproject.toml
    # + mlx on macOS (Apple Silicon local inference).
    _CORE_EXTRAS="openai,anthropic,huggingface,embeddings,tokens,tools,media,compression,server"
    if [[ "$(uname -s)" == "Darwin" ]]; then
        _CORE_EXTRAS="${_CORE_EXTRAS},mlx"
    fi
    install_editable "abstractcore" "[${_CORE_EXTRAS}]"
    install_editable "abstractruntime" "[abstractcore]"

    # ── Tier 2: Depends on Tier 0–1 ────────────────────────────────────
    section "Python — Tier 2  (depends on Tier 0–1)"
    install_editable "abstractagent"
    install_editable "abstractgateway" "[http]"

    # ── Tier 3: Depends on Tier 0–2 ────────────────────────────────────
    section "Python — Tier 3  (depends on Tier 0–2)"
    install_editable "abstractflow" "[editor]"
    install_editable "abstractcode" "[flow]"
    install_editable "abstractassistant"

    # ── Tier 4: Meta-package (AbstractFramework itself) ────────────────
    section "Python — Tier 4  (meta-package)"
    echo ""
    echo "  📦  pip install -e . (AbstractFramework)"
    pip install --quiet --no-deps -e "$ROOT_DIR"

    # ── Import safety: prevent workspace-root shadowing ─────────────────
    # Problem:
    # - In a multi-repo dev workspace, sibling repo directories like ./abstractcore/
    #   can be imported as *implicit namespace packages* when CWD is on sys.path.
    # - This shadows the editable-installed packages (e.g., abstractcore.create_llm)
    #   and yields "unknown location" / missing-symbol errors.
    #
    # SOTA fix (Python 3.11+):
    # - PYTHONSAFEPATH=1 (or `python -P`) prevents the CWD/script directory from being
    #   prepended to sys.path, eliminating this entire class of bugs.
    #
    # Fallback (Python <3.11): install a venv-local sitecustomize.py that mimics safe-path
    # by removing CWD from sys.path and printing a warning when it had to do so.
    section "Python — Dev import safety (safe-path)"

    _py_ver="$(python - <<'PY'
import sys
print(f"{sys.version_info[0]}.{sys.version_info[1]}")
PY
)"
    _py_safe_ok="$(python - <<'PY'
import sys
print("1" if sys.version_info >= (3, 11) else "0")
PY
)"

    _activate_dir="${VIRTUAL_ENV:-$VENV_DIR}/bin"

    _patch_activate_sh() {
        local target="$1"
        if [[ ! -f "$target" ]]; then
            return 0
        fi
        if grep -q "AbstractFramework dev fix: safe-path" "$target" 2>/dev/null; then
            return 0
        fi
        {
            echo ""
            echo "# AbstractFramework dev fix: safe-path (prevents CWD shadowing editable installs)"
            echo "# AbstractFramework dev fix: safe-path"
            echo "export PYTHONSAFEPATH=1"
        } >> "$target"
    }

    _patch_activate_fish() {
        local target="$1"
        if [[ ! -f "$target" ]]; then
            return 0
        fi
        if grep -q "AbstractFramework dev fix: safe-path" "$target" 2>/dev/null; then
            return 0
        fi
        {
            echo ""
            echo "# AbstractFramework dev fix: safe-path (prevents CWD shadowing editable installs)"
            echo "# AbstractFramework dev fix: safe-path"
            echo "set -gx PYTHONSAFEPATH 1"
        } >> "$target"
    }

    _patch_activate_csh() {
        local target="$1"
        if [[ ! -f "$target" ]]; then
            return 0
        fi
        if grep -q "AbstractFramework dev fix: safe-path" "$target" 2>/dev/null; then
            return 0
        fi
        {
            echo ""
            echo "# AbstractFramework dev fix: safe-path (prevents CWD shadowing editable installs)"
            echo "# AbstractFramework dev fix: safe-path"
            echo "setenv PYTHONSAFEPATH 1"
        } >> "$target"
    }

    _patch_activate_ps1() {
        local target="$1"
        if [[ ! -f "$target" ]]; then
            return 0
        fi
        if grep -q "AbstractFramework dev fix: safe-path" "$target" 2>/dev/null; then
            return 0
        fi
        {
            echo ""
            echo "# AbstractFramework dev fix: safe-path (prevents CWD shadowing editable installs)"
            echo "# AbstractFramework dev fix: safe-path"
            echo "\$env:PYTHONSAFEPATH = \"1\""
        } >> "$target"
    }

    _patch_activate_sh "${_activate_dir}/activate"
    _patch_activate_fish "${_activate_dir}/activate.fish"
    _patch_activate_csh "${_activate_dir}/activate.csh"
    _patch_activate_ps1 "${_activate_dir}/Activate.ps1"

    if [[ "$_py_safe_ok" == "1" ]]; then
        export PYTHONSAFEPATH=1
        echo "  ✅ Enabled safe-path via PYTHONSAFEPATH=1 (Python ${_py_ver})"
    else
        echo "  ⚠️  WARNING: Python ${_py_ver} does not support PYTHONSAFEPATH / -P."
        echo "     Installing venv-local fallback via sitecustomize.py"
        echo "     #FALLBACK : Python < 3.11 (no safe-path flag)"

        _site_dir="$(python - <<'PY'
import site
paths = site.getsitepackages() or []
print(paths[0] if paths else "")
PY
)"
        if [[ -z "$_site_dir" ]]; then
            echo "  ⚠️  WARNING: could not determine site-packages directory; imports may still shadow."
        else
            _sitecustomize="${_site_dir}/sitecustomize.py"
            if [[ ! -f "$_sitecustomize" ]] || ! grep -q "AbstractFramework dev fix: safe-path fallback" "$_sitecustomize" 2>/dev/null; then
                cat >"$_sitecustomize" <<'PY'
"""
AbstractFramework dev fix: safe-path fallback.

This virtual environment is used in a multi-repo workspace where sibling repo
directories (e.g. ./abstractcore/) can shadow editable-installed packages when
the current directory is on sys.path (implicit namespace packages, PEP 420).

#FALLBACK : Python < 3.11 (no PYTHONSAFEPATH / -P support)
"""

from __future__ import annotations

import os
import sys


def _remove_cwd_from_sys_path() -> bool:
    try:
        cwd = os.getcwd()
    except Exception:
        cwd = None

    new_path = []
    removed = False

    for p in list(sys.path):
        if p == "":
            removed = True
            continue
        if cwd and p == cwd:
            removed = True
            continue
        new_path.append(p)

    if removed:
        sys.path[:] = new_path
    return removed


if _remove_cwd_from_sys_path():
    try:
        sys.stderr.write(
            "WARNING: AbstractFramework dev venv removed CWD from sys.path to prevent sibling-repo shadowing "
            "(#FALLBACK : Python < 3.11)\\n"
        )
    except Exception:
        pass
PY
                echo "  ✅ Installed safe-path fallback: ${_sitecustomize}"
            else
                echo "  ✅ sitecustomize.py fallback already present"
            fi
        fi
    fi

    section "Python — Verification"
    echo ""
    echo "  Installed AbstractFramework packages:"
    pip list 2>/dev/null | grep -i "^abstract" || true

    echo ""
    echo "  Verifying imports (and detecting namespace shadowing)..."
    _import_ok=true
    for _pkg in abstractcore abstractruntime abstractagent abstractflow abstractcode abstractgateway abstractmemory abstractsemantics abstractvoice abstractvision abstractmusic abstractassistant; do
        if ! python -c "import importlib; m=importlib.import_module('${_pkg}'); assert getattr(m, '__file__', None) is not None" 2>/dev/null; then
            _import_ok=false
            echo "     ✗ ${_pkg}"
        fi
    done
    if ! python -c "import abstractcore; assert hasattr(abstractcore, 'create_llm')" 2>/dev/null; then
        _import_ok=false
        echo "     ✗ abstractcore (shadowed: missing create_llm)"
    fi
    if [ "$_import_ok" = true ]; then
        echo "  ✅ All packages import successfully"
    else
        echo "  ⚠️  Some imports failed or were shadowed (namespace package) — check the output above"
    fi

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
    if [[ "${AF_BUILD_WRAPPER:-}" == "1" ]]; then
        echo "Note: you ran this via: source ./scripts/build.sh"
        echo "      The venv will be activated in your current shell automatically."
        echo ""
    else
        echo "To activate in your shell (run the script with 'source' next time to skip this step):"
        echo "  source $VENV_DIR/bin/activate"
        echo ""
    fi
    echo "Quick verification:"
    echo "  python -c 'import abstractcore; print(abstractcore)'"
    echo "  python -c 'import abstractruntime; print(abstractruntime)'"
    echo "  python -c 'import abstractagent; print(abstractagent)'"
fi
