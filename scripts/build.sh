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
#   source ./scripts/build.sh         # light editable build, then stay in the .venv
#   ./scripts/build.sh                # light editable build (venv activates inside script only)
#   ./scripts/build.sh --light        # explicit light editable build
#   ./scripts/build.sh --base         # legacy alias for --light
#   ./scripts/build.sh --apple        # heavy native Apple local-engine profile
#   ./scripts/build.sh --gpu          # heavy native GPU local-engine profile
#   ./scripts/build.sh --python       # Python packages only
#   ./scripts/build.sh --npm          # npm packages only
#   ./scripts/build.sh --clean        # delete .venv first (avoids pollution from other projects)
#   AF_BUILD_PROFILE=light|apple|gpu|auto ./scripts/build.sh
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
    if [[ -t 1 ]]; then
        printf "\033[32m✓\033[0m Virtualenv is active in your shell.\n"
    else
        printf "✓ Virtualenv is active in your shell.\n"
    fi
    return 0
fi

set -euo pipefail

# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------
BUILD_PYTHON=true
BUILD_NPM=true
CLEAN_VENV=false
BUILD_PROFILE="${AF_BUILD_PROFILE:-light}"

for arg in "$@"; do
    case "$arg" in
        --python) BUILD_NPM=false ;;
        --npm)    BUILD_PYTHON=false ;;
        --clean)  CLEAN_VENV=true ;;
        --apple)  BUILD_PROFILE="apple" ;;
        --gpu)    BUILD_PROFILE="gpu" ;;
        --light)  BUILD_PROFILE="light" ;;
        --base)   BUILD_PROFILE="light" ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# ANSI color codes (disabled when stdout is not a terminal)
if [[ -t 1 ]]; then
    C_RESET="\033[0m"
    C_BOLD="\033[1m"
    C_GREEN="\033[32m"
    C_YELLOW="\033[33m"
    C_RED="\033[31m"
    C_CYAN="\033[36m"
    C_DIM="\033[2m"
else
    C_RESET="" C_BOLD="" C_GREEN="" C_YELLOW="" C_RED="" C_CYAN="" C_DIM=""
fi

banner() {
    printf "\n${C_BOLD}%s${C_RESET}\n" "============================================================"
    printf "${C_BOLD}%s${C_RESET}\n"   "  AbstractFramework — build all packages (dev mode)"
    printf "${C_BOLD}%s${C_RESET}\n"   "============================================================"
    echo ""
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
    printf "${C_RED}ERROR:${C_RESET} %s\n" "$msg"
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
    printf "${C_BOLD}  %s${C_RESET}\n" "$1"
    printf "  %s\n" "────────────────────────────────────────────────────────"
}

ok_line() {
    printf "  ${C_GREEN}✓${C_RESET} %s\n" "$1"
}

warn_line() {
    printf "  ${C_YELLOW}WARNING:${C_RESET} %s\n" "$1"
}

warn_cont() {
    printf "         %s\n" "$1"
}

info_line() {
    printf "  %s\n" "$1"
}

dim_line() {
    printf "  ${C_DIM}%s${C_RESET}\n" "$1"
}

package_line() {
    local kind="$1"
    local detail="$2"
    printf "  ${C_BOLD}${C_YELLOW}%-10s${C_RESET}  ${C_CYAN}%s${C_RESET}\n" "$kind" "$detail"
}

is_macos() {
    [[ "$(uname -s)" == "Darwin" ]]
}

resolve_build_profile() {
    local requested
    requested="$(printf '%s' "${BUILD_PROFILE:-light}" | tr '[:upper:]' '[:lower:]')"
    case "$requested" in
        ""|"light"|"base")
            printf '%s' "light"
            ;;
        "auto")
            if is_macos; then
                printf '%s' "apple"
            elif command -v nvidia-smi >/dev/null 2>&1; then
                printf '%s' "gpu"
            else
                printf '%s' "light"
            fi
            ;;
        "apple"|"all-apple")
            printf '%s' "apple"
            ;;
        "gpu"|"all-gpu")
            printf '%s' "gpu"
            ;;
        *)
            af_die "unsupported AF_BUILD_PROFILE=${BUILD_PROFILE} (expected light, apple, gpu, all-apple, all-gpu, or auto)"
            ;;
    esac
}

build_profile_extras() {
    local rel_dir="$1"
    local profile="$2"

    if [[ "$profile" == "light" || "$profile" == "base" ]]; then
        printf '%s' ""
        return 0
    fi

    case "$rel_dir" in
        abstractgateway|abstractassistant)
            case "$profile" in
                apple) printf '%s' "[apple]" ;;
                gpu) printf '%s' "[gpu]" ;;
                *) printf '%s' "" ;;
            esac
            ;;
        abstractsemantics|abstractmemory|abstractvision|abstractvoice|abstractmusic|abstractcore|abstractruntime|abstractagent)
            case "$profile" in
                apple) printf '%s' "[all-apple]" ;;
                gpu) printf '%s' "[all-gpu]" ;;
                *) printf '%s' "" ;;
            esac
            ;;
        *)
            printf '%s' ""
            ;;
    esac
}

macos_clear_quarantine() {
    local target="$1"

    if ! is_macos; then
        return 0
    fi
    if ! command -v xattr >/dev/null 2>&1; then
        return 0
    fi
    if [[ ! -e "$target" ]]; then
        return 0
    fi

    # Gatekeeper can quarantine native addons in downloaded workspaces on macOS.
    # Clearing only the quarantine xattr is safe and prevents dlopen failures.
    xattr -dr com.apple.quarantine "$target" >/dev/null 2>&1 || true
}

# Check that a sibling repo directory exists; abort with a clear message if not.
require_repo() {
    local name="$1"
    if [[ ! -d "$ROOT_DIR/$name" ]]; then
        echo ""
        printf "${C_RED}ERROR:${C_RESET} sibling repo not found: %s\n" "$ROOT_DIR/$name"
        echo "       Run ./scripts/clone.sh first to clone all repositories."
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
    package_line "pip" "install -e ${rel_dir}${extras}"
    pip install --quiet --no-build-isolation -e "${pkg_path}${extras}"
}

remove_existing_meta_package() {
    if python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

try:
    version("abstractframework")
except PackageNotFoundError:
    raise SystemExit(1)
PY
    then
        info_line "Removing existing abstractframework metadata before local package installs."
        dim_line "This prevents stale release pins from making pip report false conflicts."
        pip uninstall --quiet -y abstractframework
    else
        ok_line "No existing abstractframework metadata found."
    fi
}

remove_source_meta_egg_info() {
    local egg_info="$ROOT_DIR/abstractframework.egg-info"

    if [[ -d "$egg_info" ]]; then
        info_line "Removing stale source-tree abstractframework.egg-info metadata."
        rm -rf "$egg_info"
    fi
}

build_npm_project() {
    local rel_dir="$1"
    local label="$2"
    local pkg_dir="$ROOT_DIR/$rel_dir"

    if [[ ! -d "$pkg_dir" ]]; then
        warn_line "${rel_dir}/ not found — skipping"
        npm_ok=false
        return 0
    fi

    echo ""
    package_line "npm" "$label"
    (
        cd "$pkg_dir"
        if is_macos; then
            echo "       macOS: clearing Gatekeeper quarantine on project files"
            macos_clear_quarantine "$pkg_dir"
        fi
        npm install --no-audit --no-fund 2>&1 | tail -1
        if is_macos && [[ -d "$pkg_dir/node_modules" ]]; then
            echo "       macOS: clearing Gatekeeper quarantine on node_modules"
            macos_clear_quarantine "$pkg_dir/node_modules"
        fi
        npm run build 2>&1 | tail -1
    ) && printf "       ${C_GREEN}✓ built${C_RESET}\n" || { printf "       ${C_YELLOW}WARNING:${C_RESET} %s build failed\n" "$label"; npm_ok=false; }
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
    ok_line "Python:   $(python3 --version 2>&1)"
fi

if $BUILD_NPM; then
    if command -v node >/dev/null 2>&1; then
        ok_line "Node.js:  $(node --version)"
        ok_line "npm:      $(npm --version)"
    else
        echo ""
        warn_line "Node.js not found — skipping npm builds."
        warn_cont "Install Node 18+ to build the browser UI packages."
        BUILD_NPM=false
    fi
fi

ok_line "Root:     $ROOT_DIR"

# ═══════════════════════════════════════════════════════════════════════════
# PYTHON PACKAGES
# ═══════════════════════════════════════════════════════════════════════════
if $BUILD_PYTHON; then
    section "Python — Creating / activating virtual environment"

    # --clean: remove existing venv to avoid pollution from other projects
    if $CLEAN_VENV && [[ -d "$VENV_DIR" ]]; then
        info_line "Removing existing venv (--clean): $VENV_DIR"
        rm -rf "$VENV_DIR"
        # Also clear VIRTUAL_ENV so we don't skip venv creation below
        unset VIRTUAL_ENV 2>/dev/null || true
    fi

    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        if [[ ! -d "$VENV_DIR" ]]; then
            info_line "Creating:  $VENV_DIR"
            python3 -m venv "$VENV_DIR"
        else
            ok_line "Found:     $VENV_DIR"
        fi
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
        ok_line "Activated: $VIRTUAL_ENV"
    else
        if [[ "$VIRTUAL_ENV" != "$VENV_DIR" ]]; then
            echo ""
            printf "${C_RED}ERROR:${C_RESET} Active venv (%s) differs from project venv (%s)\n" "$VIRTUAL_ENV" "$VENV_DIR"
            echo "       Refusing to continue to avoid polluting an unrelated environment."
            echo ""
            echo "       Fix:  deactivate && source ./scripts/build.sh --clean"
            echo ""
            echo "       Override (unsafe): AF_ALLOW_FOREIGN_VENV=1 source ./scripts/build.sh"
            if [[ "${AF_ALLOW_FOREIGN_VENV:-}" != "1" ]]; then
                af_die "foreign venv detected"
            fi
            warn_line "Proceeding due to AF_ALLOW_FOREIGN_VENV=1 (unsafe)."
        fi
        ok_line "Using existing virtualenv: $VIRTUAL_ENV"
    fi

    echo ""
    _build_tools_status="$(python - <<'PY'
from importlib.metadata import PackageNotFoundError, version
import re


def parse(v: str) -> tuple[int, int, int]:
    parts = [int(p) for p in re.findall(r"\d+", v)[:3]]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


checks = [
    ("setuptools", (77, 0, 0), (81, 0, 0)),
    ("wheel", (0, 0, 1), None),
    ("hatchling", (1, 27, 0), None),
    ("editables", (0, 5, 0), None),
]

issues = []
for name, lower, upper in checks:
    try:
        current = parse(version(name))
    except PackageNotFoundError:
        issues.append(f"{name}=missing")
        continue
    if current < lower:
        issues.append(f"{name}<{'.'.join(str(x) for x in lower)}")
    if upper is not None and current >= upper:
        issues.append(f"{name}>={'.'.join(str(x) for x in upper)}")

print("ok" if not issues else "; ".join(issues))
PY
)"
    if [[ "$_build_tools_status" == "ok" ]]; then
        ok_line "Build tools already satisfy local editable-install requirements."
    else
        info_line "Syncing build tools for local editable installs…"
        echo "     ${_build_tools_status}"
        pip install --quiet --upgrade "setuptools>=77,<81" wheel "hatchling>=1.27.0" "editables>=0.5"
    fi

    # Existing dev venvs may still have an older abstractframework meta-package
    # installed. Since pip validates already-installed distributions after each
    # editable install, stale meta-package pins can make every local install look
    # conflicted even when the source packages are correct.
    section "Python — Meta-package metadata"
    remove_source_meta_egg_info
    remove_existing_meta_package

    section "Python — Dependency profile"
    PYTHON_BUILD_PROFILE="$(resolve_build_profile)"
    ok_line "Using Python dependency profile: ${PYTHON_BUILD_PROFILE}"

    # ── Tier 0: No internal dependencies ────────────────────────────────
    section "Python — Tier 0  (no internal dependencies)"
    install_editable "abstractskill"
    install_editable "abstractsemantics" "$(build_profile_extras "abstractsemantics" "$PYTHON_BUILD_PROFILE")"
    install_editable "abstractmemory" "$(build_profile_extras "abstractmemory" "$PYTHON_BUILD_PROFILE")"
    install_editable "abstractvision" "$(build_profile_extras "abstractvision" "$PYTHON_BUILD_PROFILE")"
    install_editable "abstractvoice" "$(build_profile_extras "abstractvoice" "$PYTHON_BUILD_PROFILE")"
    install_editable "abstractmusic" "$(build_profile_extras "abstractmusic" "$PYTHON_BUILD_PROFILE")"

    # ── Tier 1: Depends on Tier 0 ───────────────────────────────────────
    section "Python — Tier 1  (depends on Tier 0)"
    install_editable "abstractcore" "$(build_profile_extras "abstractcore" "$PYTHON_BUILD_PROFILE")"
    install_editable "abstractruntime" "$(build_profile_extras "abstractruntime" "$PYTHON_BUILD_PROFILE")"

    # ── Tier 2: Depends on Tier 0–1 ────────────────────────────────────
    section "Python — Tier 2  (depends on Tier 0–1)"
    install_editable "abstractagent" "$(build_profile_extras "abstractagent" "$PYTHON_BUILD_PROFILE")"
    install_editable "abstractgateway" "$(build_profile_extras "abstractgateway" "$PYTHON_BUILD_PROFILE")"

    # ── Tier 3: Depends on Tier 0–2 ────────────────────────────────────
    section "Python — Tier 3  (depends on Tier 0–2)"
    install_editable "abstractcode"
    install_editable "abstractassistant" "$(build_profile_extras "abstractassistant" "$PYTHON_BUILD_PROFILE")"

    # ── Tier 4: Meta-package (AbstractFramework itself) ────────────────
    section "Python — Tier 4  (meta-package)"
    echo ""
    package_line "pip" "install -e . (AbstractFramework)"
    pip install --quiet --no-build-isolation --no-deps -e "$ROOT_DIR"

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
        ok_line "Enabled safe-path via PYTHONSAFEPATH=1 (Python ${_py_ver})"
    else
        warn_line "Python ${_py_ver} does not support PYTHONSAFEPATH / -P."
        warn_cont "Installing venv-local fallback via sitecustomize.py"
        warn_cont "#FALLBACK : Python < 3.11 (no safe-path flag)"

        _site_dir="$(python - <<'PY'
import site
paths = site.getsitepackages() or []
print(paths[0] if paths else "")
PY
)"
        if [[ -z "$_site_dir" ]]; then
            warn_line "could not determine site-packages directory; imports may still shadow."
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
                ok_line "Installed safe-path fallback: ${_sitecustomize}"
            else
                ok_line "sitecustomize.py fallback already present"
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
    for _pkg in abstractcore abstractruntime abstractagent abstractcode abstractgateway abstractmemory abstractsemantics abstractvoice abstractvision abstractmusic abstractassistant; do
        if ! python -c "import importlib; m=importlib.import_module('${_pkg}'); assert getattr(m, '__file__', None) is not None" 2>/dev/null; then
            _import_ok=false
            printf "     ${C_RED}✗${C_RESET} %s\n" "$_pkg"
        fi
    done
    if ! python -c "import abstractcore; assert hasattr(abstractcore, 'create_llm')" 2>/dev/null; then
        _import_ok=false
        printf "     ${C_RED}✗${C_RESET} abstractcore (shadowed: missing create_llm)\n"
    fi
    if [ "$_import_ok" = true ]; then
        ok_line "All packages import successfully"
    else
        warn_line "Some imports failed or were shadowed (namespace package) — check the output above"
    fi

    py_ok=true
fi

# ═══════════════════════════════════════════════════════════════════════════
# NPM PACKAGES
# ═══════════════════════════════════════════════════════════════════════════
if $BUILD_NPM; then
    section "npm — Building UI packages from local source"

    npm_ok=true

    build_npm_project "abstractuic" "abstractuic  (monorepo: ui-kit, panel-chat, monitors)"
    build_npm_project "abstractobserver" "abstractobserver"
    build_npm_project "abstractcode/web" "abstractcode/web  (@abstractframework/code)"
    build_npm_project "abstractflow" "abstractflow  (@abstractframework/flow)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════
echo ""
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
printf "  ${C_BOLD}Build complete.${C_RESET}\n"
if $BUILD_PYTHON; then
    if ${py_ok:-false}; then
        printf "  ${C_GREEN}✓ Python:${C_RESET}  all packages installed (editable mode)\n"
    else
        printf "  ${C_YELLOW}WARNING:${C_RESET} Python packages may have issues\n"
    fi
fi
if $BUILD_NPM; then
    if ${npm_ok:-false}; then
        printf "  ${C_GREEN}✓ npm:${C_RESET}     all UI packages built\n"
    else
        printf "  ${C_YELLOW}WARNING:${C_RESET} npm packages had issues (see warnings above)\n"
    fi
fi
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
echo ""
if $BUILD_PYTHON; then
    printf "${C_BOLD}%s${C_RESET} %s\n" "Virtual environment:" "$VENV_DIR"
    echo ""
    if [[ "${AF_BUILD_WRAPPER:-}" == "1" ]]; then
        printf "${C_BOLD}%s${C_RESET} %s\n" "Note:" "you ran this via: source ./scripts/build.sh"
        echo "      The venv will be activated in your current shell automatically."
        echo ""
    else
        printf "${C_BOLD}%s${C_RESET}\n" "To activate in your shell (run the script with 'source' next time to skip this step):"
        echo "  source $VENV_DIR/bin/activate"
        echo ""
    fi
    printf "${C_BOLD}%s${C_RESET}\n" "Quick verification:"
    echo "  python -c 'import abstractcore; print(abstractcore)'"
    echo "  python -c 'import abstractruntime; print(abstractruntime)'"
    echo "  python -c 'import abstractagent; print(abstractagent)'"
fi
