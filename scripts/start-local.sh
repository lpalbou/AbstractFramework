#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — start the WHOLE stack from the local checkout
# =============================================================================
# Local-development twin of start.sh: serves the local packages so ongoing
# developments are what actually runs.
#
# Building is OPT-IN (maintainer directive 2026-09-21). Starting is the common
# case and a build is multi-minute, so the default starts what is already
# installed in .venv (or $AF_VENV_DIR) and touches nothing. Pass --build when you want the
# libraries rebuilt:
#
#   ./scripts/start-local.sh                 # start only — no build
#   ./scripts/start-local.sh --build         # build every local package, then start
#   ./scripts/start-local.sh --build=apple   # force a profile (light|apple|gpu|auto)
#
# --build defaults to the `auto` profile, which is `apple` on macOS: that is
# what installs the heavy local-engine extras ([all-apple] — mlx, mlx-lm,
# mlx-vlm at their pinned floors). build.sh's own default is `light`, which
# installs NO extras, so `bash build.sh` with no argument leaves the MLX
# provider unbuildable however many times you run it.
#
# Operator port map (same as start.sh):
#   gateway   8080   (control plane — started first, awaited on /api/health)
#   observer  3001
#   continuum 3002
#   code/web  3003
#   entity    3004
#   flow      3005
#
# Uses the per-app -local launchers (gateway-local.sh, observer-local.sh,
# console-local.sh, code-local.sh, entity-local.sh, flow-local.sh); each
# keeps its own preflight + replace-a-running-instance semantics. One
# terminal; Ctrl-C stops the whole stack (apps first, gateway last).
#
# Published twin: start.sh
# =============================================================================
set -euo pipefail
_START_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_START_ROOT_DIR="$(dirname "$_START_SCRIPT_DIR")"

START_DO_BUILD=false
START_BUILD_PROFILE="${AF_BUILD_PROFILE:-auto}"

usage() {
    cat <<'EOF'
Usage: ./scripts/start-local.sh [--build[=PROFILE]] [--no-build]

  (no flag)           start the stack from what is already installed in .venv
  --build             rebuild every local package first, then start
  --build=PROFILE     same, with an explicit profile: light | apple | gpu | auto
                      (default: auto — resolves to apple on macOS, i.e. the
                       [all-apple] extras that carry mlx / mlx-lm / mlx-vlm)
  --no-build          explicit form of the default
  -h, --help          this message
EOF
}

for arg in "$@"; do
    case "$arg" in
        --build)        START_DO_BUILD=true ;;
        --build=*)      START_DO_BUILD=true; START_BUILD_PROFILE="${arg#--build=}" ;;
        --no-build)     START_DO_BUILD=false ;;
        -h|--help)      usage; exit 0 ;;
        *)
            echo "error: unknown argument: $arg" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ -n "${START_SKIP_BUILD:-}" ]]; then
    echo "note: START_SKIP_BUILD is obsolete and ignored — not building is now the default; pass --build to build."
fi

if $START_DO_BUILD; then
    echo "Building local packages first (scripts/build.sh, profile=${START_BUILD_PROFILE}: editable Python + npm dists)..."
    if ! AF_BUILD_PROFILE="$START_BUILD_PROFILE" bash "$_START_SCRIPT_DIR/build.sh"; then
        echo "error: build failed — refusing to start a stale/partial stack" >&2
        exit 1
    fi
    echo "Build complete."
elif [[ ! -x "${AF_VENV_DIR:-$_START_ROOT_DIR/.venv}/bin/python" ]]; then
    # Nothing to serve: starting would fail later with a far less obvious error.
    echo "error: no build found at ${AF_VENV_DIR:-$_START_ROOT_DIR/.venv} — run ./scripts/start-local.sh --build first" >&2
    exit 1
fi

export ABSTRACTGATEWAY_PORT="${ABSTRACTGATEWAY_PORT:-8080}"
export ABSTRACTOBSERVER_PORT="${ABSTRACTOBSERVER_PORT:-3001}"
export ABSTRACTCONTINUUM_PORT="${ABSTRACTCONTINUUM_PORT:-3002}"
export ABSTRACTCODE_PORT="${ABSTRACTCODE_PORT:-3003}"
export ABSTRACTENTITY_PORT="${ABSTRACTENTITY_PORT:-3004}"
export ABSTRACTFLOW_PORT="${ABSTRACTFLOW_PORT:-3005}"

AF_STACK_SUFFIX="-local"
source "$_START_SCRIPT_DIR/lib/af_stack.sh"
