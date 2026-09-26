#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — build all packages from local repos
# =============================================================================
# Development-only script that builds EVERY package of the workspace from the
# local checkouts, tier by tier, in dependency order (scripts/lib/packages.txt;
# see ./scripts/deps.sh for the tiers and the edges):
#
#   Python  editable installs (NOT from PyPI) of the 13 Python packages and the
#           root meta-package, into one isolated virtualenv
#   npm     the 7 AbstractUIC packages (ui-kit, app-server, monitor-*,
#           panel-chat) then the apps flow, observer, continuum, entity and
#           code/web — built from source, NOT from the npm registry
#   Rust    abstracttui, abstractcore-console (abstractcore/console-tui),
#           abstractcode (abstractcode/tui) and abstractgateway-console
#           (abstractgateway/console-tui), `cargo build`
#
# Third-party dependencies (pydantic, react, torch, crates, …) are resolved
# normally from PyPI / npm / crates.io — only AbstractFramework Python
# packages and the AbstractUIC sources come from the local checkouts.
#
# Usage:
#   source ./scripts/build.sh         # light editable build, then stay in the venv
#   ./scripts/build.sh                # light editable build (venv activates inside script only)
#   ./scripts/build.sh --light        # explicit light editable build
#   ./scripts/build.sh --base         # legacy alias for --light
#   ./scripts/build.sh --apple        # heavy native Apple local-engine profile
#   ./scripts/build.sh --gpu          # heavy native GPU local-engine profile
#   ./scripts/build.sh --python       # Python packages only
#   ./scripts/build.sh --npm          # npm packages only
#   ./scripts/build.sh --rust         # Rust crates only
#   ./scripts/build.sh --npm --rust   # selections combine
#   ./scripts/build.sh --plan         # print the tier-ordered build plan, build nothing
#   ./scripts/build.sh --clean        # delete the venv first (avoids pollution from other projects)
#   AF_BUILD_PROFILE=light|apple|gpu|auto ./scripts/build.sh
#   AF_VENV_DIR=/path/to/venv ./scripts/build.sh   # venv location (default: <root>/.venv)
#
# Prerequisites:
#   - Python 3.10+  (required for the Python packages)
#   - Node.js 18+   (optional; only needed for the npm packages)
#   - cargo         (optional; only needed for the Rust crates)
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
# AF_VENV_DIR overrides the virtualenv location (a relative path is taken from
# the current directory). Default: the workspace .venv.
VENV_DIR="${AF_VENV_DIR:-$ROOT_DIR/.venv}"
case "$VENV_DIR" in
    /*) ;;
    *) VENV_DIR="$PWD/$VENV_DIR" ;;
esac

# If sourced, run the build in a real bash process (so bash-only syntax is safe),
# then activate the venv in the current shell and return.
if $_AF_SOURCED; then
    AF_BUILD_WRAPPER=1 AF_VENV_DIR="$VENV_DIR" bash "$SCRIPT_DIR/build.sh" "$@" || return 1
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

# pip's "new release available" notice after every editable install is noise.
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Shared package inventory (scripts/lib/packages.txt): kinds, paths, tiers.
# shellcheck source=./lib/repo_groups.sh
source "$SCRIPT_DIR/lib/repo_groups.sh"

# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------
# --python / --npm / --rust SELECT ecosystems and combine; none = all three.
SELECT_PYTHON=false
SELECT_NPM=false
SELECT_RUST=false
CLEAN_VENV=false
PLAN_ONLY=false
BUILD_PROFILE="${AF_BUILD_PROFILE:-light}"

for arg in "$@"; do
    case "$arg" in
        --python) SELECT_PYTHON=true ;;
        --npm)    SELECT_NPM=true ;;
        --rust)   SELECT_RUST=true ;;
        --clean)  CLEAN_VENV=true ;;
        --apple)  BUILD_PROFILE="apple" ;;
        --gpu)    BUILD_PROFILE="gpu" ;;
        --light)  BUILD_PROFILE="light" ;;
        --base)   BUILD_PROFILE="light" ;;
        --plan|--dry-run) PLAN_ONLY=true ;;
        -h|--help)
            sed -n '2,41p' "$SCRIPT_DIR/build.sh" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $arg (see --help)" >&2
            exit 2
            ;;
    esac
done
if ! $SELECT_PYTHON && ! $SELECT_NPM && ! $SELECT_RUST; then
    SELECT_PYTHON=true; SELECT_NPM=true; SELECT_RUST=true
fi
BUILD_PYTHON=$SELECT_PYTHON
BUILD_NPM=$SELECT_NPM
BUILD_RUST=$SELECT_RUST

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

    # abstractruntime and abstractagent publish `apple`/`gpu`, NOT `all-apple`,
    # so the line below asks them for an extra they do not define: pip warns
    # ("does not provide the extra 'all-apple'") and installs them bare. That
    # looks like a bug and is deliberately left alone. Their `apple` extra is
    # only `abstractcore[all-apple]`, which this script installs directly one
    # line below -- so nothing is missed -- while ASKING for it re-resolves the
    # environment, and the root meta-package (installed editable, with exact
    # `==` pins) then drags every local editable install back to the pinned
    # PyPI builds whenever a sibling checkout is ahead of the root pins. With
    # the 0.1.11 pins (`abstractcore==2.13.38`, `abstractvision==0.3.26`) a
    # dry-run showed [apple] here would downgrade abstractcore, abstractvision,
    # abstractruntime, abstractgateway and abstractassistant at once. 0.2.0
    # pins the released checkouts (core 2.14.0, runtime 0.4.33, agent 0.3.13,
    # gateway 0.3.0, assistant 0.5.0), but the hazard returns with the next
    # sibling bump, so the mapping stays as it is.
    case "$rel_dir" in
        abstractgateway|abstractassistant)
            case "$profile" in
                apple) printf '%s' "[apple]" ;;
                gpu) printf '%s' "[gpu]" ;;
                *) printf '%s' "" ;;
            esac
            ;;
        abstractsemantics|abstractmemory|abstractvision|abstractvoice|abstractmusic|abstract3d|abstractcore|abstractruntime|abstractagent)
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

# Name the conflict pip could not name.
#
# pip answers an UNSATISFIABLE graph with `resolution-too-deep`: it spends its
# whole backtracking budget before it can prove which two requirements are
# irreconcilable, so the operator is told the graph is "too complex" and
# advised to add lower bounds — for what is really package A wanting X>=n and
# package B wanting X<n. uv's resolver reports that pair in seconds. This is
# DIAGNOSIS ONLY: the build still fails, it just stops lying about why.
explain_resolution_failure() {
    local rel_dir="$1" extras="$2" pkg_path="$3"

    if ! command -v uv >/dev/null 2>&1; then
        echo ""
        printf "${C_YELLOW}hint:${C_RESET} install uv (https://docs.astral.sh/uv/) and re-run — its resolver\n"
        echo "      names the conflicting requirement pair that pip's depth limit hides."
        return 0
    fi

    echo ""
    printf "${C_YELLOW}Re-resolving %s%s with uv to name the actual conflict...${C_RESET}\n" "$rel_dir" "$extras"
    echo ""
    # --dry-run: resolve and report, install nothing. A uv failure here is the
    # POINT (it prints the conflict), so it must not abort this handler.
    uv pip install --dry-run --no-build-isolation \
        --python "$VENV_DIR/bin/python" -e "${pkg_path}${extras}" 2>&1 | tail -40 || true
}

# Editable-install a Python package from a local directory.
# Usage: install_editable <relative_dir> [pip_extras] [label] [needs]
# Example: install_editable abstractcore "[tools,media]" "pip t2" "abstractvision"
install_editable() {
    local rel_dir="$1"
    local extras="${2:-}"
    local label="${3:-pip}"
    local needs="${4:-}"
    local pkg_path="$ROOT_DIR/$rel_dir"

    require_repo "$rel_dir"
    echo ""
    package_line "$label" "install -e ${rel_dir}${extras}"
    [[ -n "$needs" ]] && dim_line "     needs: ${needs}"
    if ! pip install --quiet --no-build-isolation -e "${pkg_path}${extras}"; then
        explain_resolution_failure "$rel_dir" "$extras" "$pkg_path"
        af_die "pip install -e ${rel_dir}${extras} failed"
    fi
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

# Log directory for npm / cargo output: the terminal shows one line per
# package; the full log is printed (tail) only when a step fails.
BUILD_LOG_DIR="${AF_BUILD_LOG_DIR:-${TMPDIR:-/tmp}/af-build-logs.$$}"

run_logged() {
    # run_logged <log-file> <dir> <command...>: run in <dir>, keep the output in
    # <log-file>, print its tail on failure. Returns the command status.
    local log="$1" dir="$2"
    shift 2
    mkdir -p "$BUILD_LOG_DIR"
    local status=0
    (cd "$dir" && "$@") >"$log" 2>&1 || status=$?
    if [[ "$status" -eq 0 ]]; then
        return 0
    fi
    printf "       ${C_RED}failed (exit %s):${C_RESET} %s  (in %s)\n" "$status" "$*" "$dir"
    tail -25 "$log" | sed 's/^/       | /'
    printf "       ${C_DIM}full log: %s${C_RESET}\n" "$log"
    return "$status"
}

# Does <repo_dir>/package.json declare npm workspaces (AbstractUIC)?
is_npm_workspace_root() {
    [[ -f "$1/package.json" ]] && grep -q '"workspaces"' "$1/package.json"
}

package_has_npm_script() {
    node -e 'const p = require(process.argv[1]); process.exit(p.scripts && p.scripts[process.argv[2]] ? 0 : 1)' \
        "$1/package.json" "$2"
}

NPM_INSTALLED_ROOTS=" "

# Pack every sibling kit the package at index $1 takes from the registry
# (packages.txt edge kinds dep/dev) into $NPM_PACKS_DIR and print the tarball
# paths, space-separated. The sibling must already be built (it is: the tiers
# order the kits before their consumers). Fails loudly when a sibling is
# missing or `npm pack` fails.
NPM_PACKS_DIR="${AF_NPM_PACKS_DIR:-$ROOT_DIR/untracked/npm-packs}"
pack_sibling_kits() {
    local i="$1" dep_id dep_idx dep_dir tgz specs=""
    for dep_id in $(af_pkg_registry_dep_ids "$i"); do
        dep_idx="$(af_pkg_index "$dep_id")" || { printf "       ${C_RED}unknown sibling:${C_RESET} %s\n" "$dep_id"; return 1; }
        dep_dir="$(af_pkg_dir "$dep_idx")"
        [[ -f "$dep_dir/package.json" ]] || { printf "       ${C_RED}missing sibling:${C_RESET} %s (run ./scripts/clone.sh)\n" "$dep_dir"; return 1; }
        mkdir -p "$NPM_PACKS_DIR"
        tgz="$( (cd "$dep_dir" && npm pack --silent --pack-destination "$NPM_PACKS_DIR" 2>/dev/null) | tail -1)"
        [[ -n "$tgz" && -f "$NPM_PACKS_DIR/$tgz" ]] || { printf "       ${C_RED}npm pack failed:${C_RESET} %s\n" "$dep_dir"; return 1; }
        specs="${specs:+$specs }$NPM_PACKS_DIR/$tgz"
    done
    echo "$specs"
}

# Build one npm package from packages.txt (index $1).
# - A package inside an npm WORKSPACE repo (AbstractUIC) is installed once at
#   the workspace root and built with `npm run build --workspace <path>`.
# - Any other package (flow, observer, continuum, entity, abstractcode/web) is
#   installed and built in its own directory.
build_npm_package() {
    local i="$1"
    local id="${AF_PKG_ID[$i]}" name="${AF_PKG_NAME[$i]}" rel_path="${AF_PKG_PATH[$i]}"
    local pkg_dir repo_dir install_root location deps
    pkg_dir="$(af_pkg_dir "$i")"
    repo_dir="$(repo_dir_for "${AF_PKG_REPO[$i]}")"
    location="$(af_pkg_location "$i")"
    deps="$(af_pkg_dep_ids "$i")"

    echo ""
    package_line "npm t${AF_PKG_TIER[$i]}" "${location}  (${name})"
    [[ -n "$deps" ]] && dim_line "     needs: ${deps}"
    if [[ ! -f "$pkg_dir/package.json" ]]; then
        printf "       ${C_RED}missing:${C_RESET} %s/package.json — run ./scripts/clone.sh\n" "$pkg_dir"
        npm_ok=false
        return 0
    fi

    if [[ "$rel_path" != "." ]] && is_npm_workspace_root "$repo_dir"; then
        install_root="$repo_dir"
    else
        install_root="$pkg_dir"
    fi

    case "$NPM_INSTALLED_ROOTS" in
        *" $install_root "*) ;;
        *)
            if is_macos; then
                macos_clear_quarantine "$install_root"
            fi
            # Sibling kits the manifest takes from the registry (app-server,
            # ui-kit, panel-chat, monitors) are installed from LOCAL packs of the
            # checkouts built in the lower tiers, so a sibling that is not
            # published yet — or is ahead of the registry — still builds. The
            # manifest and its lockfile are left untouched (--no-save).
            local sibling_specs=""
            if [[ "$install_root" == "$pkg_dir" ]]; then
                sibling_specs="$(pack_sibling_kits "$i")" || { npm_ok=false; return 0; }
            fi
            if [[ -n "$sibling_specs" ]]; then
                echo "       npm install  (${install_root#"$ROOT_DIR"/}; siblings from local packs: $(echo "$sibling_specs" | xargs -n1 basename | tr '\n' ' '))"
                # shellcheck disable=SC2086
                if ! run_logged "$BUILD_LOG_DIR/npm-install-${AF_PKG_REPO[$i]}.log" "$install_root" \
                        npm install --no-audit --no-fund --no-save $sibling_specs; then
                    npm_ok=false
                    return 0
                fi
            else
                echo "       npm install  (${install_root#"$ROOT_DIR"/})"
                if ! run_logged "$BUILD_LOG_DIR/npm-install-${AF_PKG_REPO[$i]}.log" "$install_root" \
                        npm install --no-audit --no-fund; then
                    npm_ok=false
                    return 0
                fi
            fi
            if is_macos && [[ -d "$install_root/node_modules" ]]; then
                macos_clear_quarantine "$install_root/node_modules"
            fi
            NPM_INSTALLED_ROOTS="${NPM_INSTALLED_ROOTS}${install_root} "
            ;;
    esac

    if ! package_has_npm_script "$pkg_dir" build; then
        printf "       ${C_GREEN}✓ no build step${C_RESET} ${C_DIM}(ships its sources)${C_RESET}\n"
        npm_built=$((npm_built + 1))
        return 0
    fi
    if [[ "$install_root" != "$pkg_dir" ]]; then
        run_logged "$BUILD_LOG_DIR/npm-build-${id}.log" "$install_root" \
            npm run build --workspace "$rel_path" || { npm_ok=false; return 0; }
    else
        run_logged "$BUILD_LOG_DIR/npm-build-${id}.log" "$pkg_dir" \
            npm run build || { npm_ok=false; return 0; }
    fi
    printf "       ${C_GREEN}✓ built${C_RESET}\n"
    npm_built=$((npm_built + 1))
}

# Build one Rust crate from packages.txt (index $1) with `cargo build`.
# The default (debug) profile is used: it is incremental and serves as the
# "does it still compile" gate. The crates consume abstracttui from crates.io
# (see Cargo.toml), so the local abstracttui build is a check of that crate,
# not an input of the others.
build_rust_package() {
    local i="$1"
    local id="${AF_PKG_ID[$i]}" pkg_dir location deps
    pkg_dir="$(af_pkg_dir "$i")"
    location="$(af_pkg_location "$i")"
    deps="$(af_pkg_dep_ids "$i")"

    echo ""
    package_line "cargo t${AF_PKG_TIER[$i]}" "${location}  (crate ${AF_PKG_NAME[$i]})"
    [[ -n "$deps" ]] && dim_line "     needs: ${deps}"
    if [[ ! -f "$pkg_dir/Cargo.toml" ]]; then
        printf "       ${C_RED}missing:${C_RESET} %s/Cargo.toml — run ./scripts/clone.sh\n" "$pkg_dir"
        rust_ok=false
        return 0
    fi
    run_logged "$BUILD_LOG_DIR/cargo-${id}.log" "$pkg_dir" cargo build || { rust_ok=false; return 0; }
    printf "       ${C_GREEN}✓ built${C_RESET}\n"
    rust_built=$((rust_built + 1))
}

# Print the tier-ordered plan (--plan) without building anything.
print_build_plan() {
    local kind i last_tier
    for kind in python npm rust; do
        case "$kind" in
            python) $BUILD_PYTHON || continue ;;
            npm) $BUILD_NPM || continue ;;
            rust) $BUILD_RUST || continue ;;
        esac
        section "Plan — ${kind}"
        last_tier=""
        while IFS= read -r i; do
            if [[ "${AF_PKG_TIER[$i]}" != "$last_tier" ]]; then
                last_tier="${AF_PKG_TIER[$i]}"
                info_line "$(af_tier_title "$last_tier")"
            fi
            printf "    %-22s %-30s %s\n" "${AF_PKG_ID[$i]}" "$(af_pkg_location "$i")" \
                "$( [[ -n "$(af_pkg_dep_ids "$i")" ]] && echo "needs: $(af_pkg_dep_ids "$i")" )"
        done < <( { af_pkg_indices "$kind"; [[ "$kind" == "python" ]] && af_pkg_indices meta; } )
    done
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

if $BUILD_RUST; then
    if command -v cargo >/dev/null 2>&1; then
        ok_line "cargo:    $(cargo --version)"
    else
        echo ""
        warn_line "cargo not found — skipping Rust builds."
        warn_cont "Install Rust (https://rustup.rs) to build the Rust crates."
        BUILD_RUST=false
    fi
fi

ok_line "Root:     $ROOT_DIR"
ok_line "Packages: $AF_PKG_COUNT in scripts/lib/packages.txt (tiers 0-$AF_MAX_TIER; ./scripts/deps.sh shows the edges)"
if $BUILD_PYTHON; then
    ok_line "Venv:     $VENV_DIR"
fi

if $PLAN_ONLY; then
    print_build_plan
    echo ""
    info_line "--plan: nothing was built."
    exit 0
fi

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

    # ── Every Python package, tier by tier (scripts/lib/packages.txt) ──
    # A package is installed only after everything it depends on (tier =
    # dependency depth; ./scripts/deps.sh --kind python shows the edges).
    _last_tier=""
    while IFS= read -r _i; do
        if [[ "${AF_PKG_TIER[$_i]}" != "$_last_tier" ]]; then
            _last_tier="${AF_PKG_TIER[$_i]}"
            section "Python — $(af_tier_title "$_last_tier")"
        fi
        _deps="$(af_pkg_dep_ids "$_i")"
        if [[ "${AF_PKG_KIND[$_i]}" == "meta" ]]; then
            # The meta-package pins released versions with `==`; installing its
            # dependencies would drag the editable checkouts back to PyPI builds.
            echo ""
            package_line "pip t${_last_tier}" "install --no-deps -e . (AbstractFramework meta-package)"
            pip install --quiet --no-build-isolation --no-deps -e "$ROOT_DIR"
            continue
        fi
        install_editable "$(af_pkg_location "$_i")" \
            "$(build_profile_extras "${AF_PKG_ID[$_i]}" "$PYTHON_BUILD_PROFILE")" \
            "pip t${_last_tier}" "$_deps"
    done < <(af_pkg_indices python; af_pkg_indices meta)

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
    # Import names are the package ids of the Python rows of packages.txt.
    for _pkg in $(af_pkg_indices python | while IFS= read -r _i; do echo "${AF_PKG_ID[$_i]}"; done); do
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

    py_ok="$_import_ok"
fi

# ═══════════════════════════════════════════════════════════════════════════
# NPM PACKAGES
# ═══════════════════════════════════════════════════════════════════════════
if $BUILD_NPM; then
    section "npm — Building every npm package from local source, tier by tier"

    npm_ok=true
    npm_built=0
    while IFS= read -r _i; do
        build_npm_package "$_i"
    done < <(af_pkg_indices npm)
fi

# ═══════════════════════════════════════════════════════════════════════════
# RUST CRATES
# ═══════════════════════════════════════════════════════════════════════════
if $BUILD_RUST; then
    section "Rust — Building every crate from local source, tier by tier"

    rust_ok=true
    rust_built=0
    while IFS= read -r _i; do
        build_rust_package "$_i"
    done < <(af_pkg_indices rust)
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
        printf "  ${C_RED}FAILED:${C_RESET}  Python imports failed or were shadowed (see above)\n"
    fi
fi
if $BUILD_NPM; then
    if ${npm_ok:-false}; then
        printf "  ${C_GREEN}✓ npm:${C_RESET}     %s npm packages built\n" "$npm_built"
    else
        printf "  ${C_RED}FAILED:${C_RESET}  npm: %s built, some failed (see the logs above)\n" "$npm_built"
    fi
fi
if $BUILD_RUST; then
    if ${rust_ok:-false}; then
        printf "  ${C_GREEN}✓ Rust:${C_RESET}    %s crates built\n" "$rust_built"
    else
        printf "  ${C_RED}FAILED:${C_RESET}  Rust: %s built, some failed (see the logs above)\n" "$rust_built"
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

# Exit non-zero when any selected ecosystem failed, so callers (start-local.sh
# --build, CI) never proceed on a partial build.
if { $BUILD_PYTHON && ! ${py_ok:-false}; } || { $BUILD_NPM && ! ${npm_ok:-false}; } \
    || { $BUILD_RUST && ! ${rust_ok:-false}; }; then
    exit 1
fi
