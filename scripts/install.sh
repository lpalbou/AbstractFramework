#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — installer (published packages)
# =============================================================================
# Installs the pinned AbstractFramework release from the public registries
# (PyPI, npm, crates.io) — NOT from local checkouts (that is scripts/build.sh).
# The versions below mirror docs/installers/install-manifest.json;
# scripts/tests/test_inventory.sh fails when they drift.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | bash
#   curl -sSL .../install.sh | bash -s -- --profile apple --with-apps
#   ./scripts/install.sh [options]
#
# Options:
#   --profile light|apple|gpu   Python profile (default: light, or $AF_PROFILE)
#                                 light  remote-first: cloud APIs / endpoint servers
#                                 apple  + local MLX/Metal engines (macOS 14+, Apple Silicon)
#                                 gpu    + local CUDA/ROCm engines (Linux/Windows)
#   --with-apps                 also `npm install -g` the browser apps at their
#                               released versions (flow, code, observer,
#                               continuum, entity); needs Node.js 18+.
#                               Without it, run them on demand with `npx`.
#   --with-console              also `cargo install abstractgateway-console`
#                               (terminal console for the gateway; Rust 1.87+)
#   --with-code-cli             also `cargo install abstractcode` (terminal client)
#   --venv DIR                  virtualenv to create/use when none is active
#                               (default: ./.venv, or $AF_VENV_DIR)
#   --print, --dry-run          print the plan (tier order + commands), install nothing
#   --print-versions            print "<registry> <name> <version>" lines and exit
#   -h, --help                  this help
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Release pins — keep in sync with docs/installers/install-manifest.json
# (checked by scripts/tests/test_inventory.sh).
# ---------------------------------------------------------------------------
AF_VERSION="0.1.12"

# Python packages the root meta-package pins, in dependency-tier order
# ("tier|distribution|version"; tiers from scripts/lib/packages.txt).
PY_RELEASE=(
    "0|AbstractMemory|0.3.0"
    "0|abstractsemantics|0.0.5"
    "0|abstractvoice|0.11.3"
    "0|abstractvision|0.3.29"
    "0|abstractmusic|0.1.15"
    "2|abstractcore|2.13.42"
    "3|AbstractRuntime|0.4.32"
    "4|abstractagent|0.3.13"
    "4|abstractassistant|0.5.0"
    "5|abstractgateway|0.2.30"
    "6|abstractframework|${AF_VERSION}"
)

# Browser apps (npm), run with `npx <package>` or installed with --with-apps.
NPM_APPS=(
    "@abstractframework/flow|0.3.20"
    "@abstractframework/code|0.4.2"
    "@abstractframework/observer|0.1.12"
    "@abstractframework/continuum|0.2.0"
    "@abstractframework/entity|0.1.0"
)

# Optional Rust terminal tools (crates.io). The install manifest has no crate
# section yet; these follow the released crates (docs/install.md).
CRATE_CONSOLE="abstractgateway-console|0.6.0"
CRATE_CODE_CLI="abstractcode|0.5.1"

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
PROFILE="${AF_PROFILE:-light}"
WITH_APPS=false
WITH_CONSOLE=false
WITH_CODE_CLI=false
PRINT_ONLY=false
VENV_DIR="${AF_VENV_DIR:-.venv}"

usage() {
    local self="${BASH_SOURCE[0]:-}"
    if [[ -n "$self" && -f "$self" ]]; then
        sed -n '2,32p' "$self" | sed 's/^# \{0,1\}//'
    else
        echo "Usage: install.sh [--profile light|apple|gpu] [--with-apps] [--with-console] [--with-code-cli] [--venv DIR] [--print]"
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --profile) shift; PROFILE="${1:-}" ;;
        --profile=*) PROFILE="${1#--profile=}" ;;
        --light|--apple|--gpu) PROFILE="${1#--}" ;;
        --with-apps) WITH_APPS=true ;;
        --with-console) WITH_CONSOLE=true ;;
        --with-code-cli) WITH_CODE_CLI=true ;;
        --venv) shift; VENV_DIR="${1:-}" ;;
        --venv=*) VENV_DIR="${1#--venv=}" ;;
        --print|--dry-run|-n) PRINT_ONLY=true ;;
        --print-versions)
            echo "pypi abstractframework ${AF_VERSION}"
            for entry in "${PY_RELEASE[@]}"; do
                IFS='|' read -r _t dist ver <<<"$entry"
                [[ "$dist" == "abstractframework" ]] || echo "pypi $dist $ver"
            done
            for entry in "${NPM_APPS[@]}"; do echo "npm ${entry%%|*} ${entry#*|}"; done
            for entry in "$CRATE_CONSOLE" "$CRATE_CODE_CLI"; do echo "crates ${entry%%|*} ${entry#*|}"; done
            exit 0
            ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

case "$PROFILE" in
    light) PIP_REQUIREMENT="abstractframework==${AF_VERSION}" ;;
    apple) PIP_REQUIREMENT="abstractframework[apple]==${AF_VERSION}" ;;
    gpu)   PIP_REQUIREMENT="abstractframework[gpu]==${AF_VERSION}" ;;
    *) echo "ERROR: unknown profile '$PROFILE' (expected light, apple or gpu)" >&2; exit 2 ;;
esac

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
banner() {
  printf "\n%s\n" "============================================================"
  printf "%s\n" "  AbstractFramework ${AF_VERSION} — install (profile: ${PROFILE})"
  printf "%s\n" "============================================================"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1${2:+ ($2)}"
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

# Run (or, with --print, only show) a command.
run() {
  echo "  \$ $*"
  $PRINT_ONLY && return 0
  "$@"
}

print_plan() {
  echo ""
  echo "Install plan — dependency tiers (lowest first; pip resolves them in one step):"
  local entry tier dist ver next last="" idx=0
  while [[ "$idx" -lt "${#PY_RELEASE[@]}" ]]; do
    IFS='|' read -r tier dist ver <<<"${PY_RELEASE[$idx]}"
    if [[ "$tier" != "$last" ]]; then
      printf "  tier %s:" "$tier"
      last="$tier"
    fi
    printf " %s==%s" "$dist" "$ver"
    next="${PY_RELEASE[$((idx + 1))]:-}"
    [[ "${next%%|*}" != "$tier" ]] && echo ""
    idx=$((idx + 1))
  done
  echo "  python profile: ${PROFILE}  ->  pip install \"${PIP_REQUIREMENT}\""
  echo ""
  echo "Browser apps (npm; need a running gateway and Node.js 18+):"
  for entry in "${NPM_APPS[@]}"; do
    if $WITH_APPS; then
      printf "  %-32s %-8s npm install -g %s@%s\n" "${entry%%|*}" "${entry#*|}" "${entry%%|*}" "${entry#*|}"
    else
      printf "  %-32s %-8s run on demand: npx %s\n" "${entry%%|*}" "${entry#*|}" "${entry%%|*}"
    fi
  done
  echo ""
  echo "Terminal tools (crates.io, optional):"
  printf "  %-32s %-8s %s\n" "${CRATE_CONSOLE%%|*}" "${CRATE_CONSOLE#*|}" \
    "$($WITH_CONSOLE && echo "cargo install --locked ${CRATE_CONSOLE%%|*} --version ${CRATE_CONSOLE#*|}" || echo "not selected (add --with-console)")"
  printf "  %-32s %-8s %s\n" "${CRATE_CODE_CLI%%|*}" "${CRATE_CODE_CLI#*|}" \
    "$($WITH_CODE_CLI && echo "cargo install --locked ${CRATE_CODE_CLI%%|*} --version ${CRATE_CODE_CLI#*|}" || echo "not selected (add --with-code-cli)")"
  echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
banner
print_plan

if $PRINT_ONLY; then
  echo "Commands (--print: nothing is executed):"
fi

require_cmd python3 "Python 3.10+"
if [[ "$(py_version_ok)" != "ok" ]]; then
  echo "ERROR: Python 3.10+ is required. Detected: $(python3 --version 2>&1)"
  exit 1
fi
echo "✓ Python: $(python3 --version 2>&1)"

case "$PROFILE" in
  apple)
    if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
      echo "WARNING: the apple profile targets Apple Silicon macOS 14+; this is $(uname -s)/$(uname -m)."
    fi
    ;;
  gpu)
    if [[ "$(uname -s)" == "Darwin" ]]; then
      echo "WARNING: the gpu profile targets Linux/Windows CUDA/ROCm hosts; on a Mac use --profile apple."
    fi
    ;;
esac

if $WITH_APPS; then
  $PRINT_ONLY || require_cmd npm "Node.js 18+ for --with-apps"
elif command -v node >/dev/null 2>&1; then
  echo "✓ Node.js: $(node --version) (browser apps run with npx)"
else
  echo "ℹ Node.js not found (optional). Install Node 18+ to run the browser apps (npx @abstractframework/flow, ...)."
fi
if $WITH_CONSOLE || $WITH_CODE_CLI; then
  $PRINT_ONLY || require_cmd cargo "Rust toolchain from https://rustup.rs for the terminal tools"
fi

# Create a venv if none is active.
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo ""
  echo "Virtual environment: ${VENV_DIR}"
  run python3 -m venv "$VENV_DIR"
  if ! $PRINT_ONLY; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "✓ Activated: $VIRTUAL_ENV"
  else
    echo "  \$ source ${VENV_DIR}/bin/activate"
  fi
else
  echo "✓ Using existing virtualenv: $VIRTUAL_ENV"
fi

echo ""
echo "Python packages (profile ${PROFILE}):"
run python3 -m pip install -U pip
run python3 -m pip install "$PIP_REQUIREMENT"

if $WITH_APPS; then
  echo ""
  echo "Browser apps (npm, global):"
  for entry in "${NPM_APPS[@]}"; do
    run npm install -g "${entry%%|*}@${entry#*|}"
  done
fi

if $WITH_CONSOLE; then
  echo ""
  echo "Gateway terminal console (crates.io):"
  run cargo install --locked "${CRATE_CONSOLE%%|*}" --version "${CRATE_CONSOLE#*|}"
fi
if $WITH_CODE_CLI; then
  echo ""
  echo "AbstractCode terminal client (crates.io):"
  run cargo install --locked "${CRATE_CODE_CLI%%|*}" --version "${CRATE_CODE_CLI#*|}"
fi

echo ""
if $PRINT_ONLY; then
  echo "✓ Plan printed (--print): nothing was installed."
  exit 0
fi
echo "✓ Done."
echo ""
echo "Check the install, then configure providers:"
echo "   abstractframework doctor"
echo "   abstractcore --config"
echo ""
echo "Start the gateway (control plane), then a browser app against it:"
echo "   abstractgateway serve --host 127.0.0.1 --port 8080"
echo "   npx @abstractframework/flow        # or: code, observer, continuum, entity"
echo "   # built-in web console: http://127.0.0.1:8080/console"
echo ""
echo "Docs:"
echo "  - Install guide:   https://github.com/lpalbou/AbstractFramework/blob/main/docs/install.md"
echo "  - Getting started: https://github.com/lpalbou/AbstractFramework/blob/main/docs/getting-started.md"
