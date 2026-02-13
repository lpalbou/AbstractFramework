#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — clone all project repositories
# =============================================================================
# Clones every sibling repository in the AbstractFramework ecosystem into a
# single root directory. AbstractFramework itself IS the root — all other repos
# are cloned as direct children alongside its own files.
#
# Usage modes:
#
#   1) From inside an existing AbstractFramework checkout:
#      ./scripts/clone.sh                     # clones siblings into repo root
#
#   2) Fresh setup into a new directory:
#      ./scripts/clone.sh ~/dev/abstract      # clones AF + siblings there
#
# If a repo already exists locally, the script pulls updates instead of
# re-cloning.
#
# Prerequisites:
#   - git
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# The AbstractFramework (meta-package) repository — cloned first as root.
AF_REPO="https://github.com/lpalbou/AbstractFramework.git"

# Sibling repositories — cloned INTO the AbstractFramework root.
# Python packages (PyPI)
SIBLING_REPOS=(
    "https://github.com/lpalbou/abstractcore.git"
    "https://github.com/lpalbou/abstractruntime.git"
    "https://github.com/lpalbou/abstractagent.git"
    "https://github.com/lpalbou/abstractflow.git"
    "https://github.com/lpalbou/abstractcode.git"
    "https://github.com/lpalbou/abstractgateway.git"
    "https://github.com/lpalbou/abstractmemory.git"
    "https://github.com/lpalbou/abstractsemantics.git"
    "https://github.com/lpalbou/abstractvoice.git"
    "https://github.com/lpalbou/abstractvision.git"
    "https://github.com/lpalbou/AbstractMusic.git"
    "https://github.com/lpalbou/abstractassistant.git"
    # Browser UIs & npm packages
    "https://github.com/lpalbou/abstractobserver.git"
    # UI component library (React monorepo)
    "https://github.com/lpalbou/abstractuic.git"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
banner() {
    printf "\n%s\n" "============================================================"
    printf "%s\n"   "  AbstractFramework — clone all repositories"
    printf "%s\n"   "============================================================"
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $1"
        exit 1
    fi
}

# Detect whether a directory IS the AbstractFramework repo
is_af_root() {
    local dir="$1"
    [[ -f "$dir/pyproject.toml" ]] && grep -q 'name = "abstractframework"' "$dir/pyproject.toml" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
banner
require_cmd git

# Determine the script's own location (reliable even via symlinks).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cloned=0
updated=0
failed=0

# ── Resolve the root directory ──────────────────────────────────────────────
if [[ -n "${1:-}" ]]; then
    # A target directory was supplied.
    TARGET_DIR="$1"
    if is_af_root "$TARGET_DIR"; then
        echo "✓ Target is already an AbstractFramework checkout."
    else
        echo "⬇  Cloning   AbstractFramework (root)"
        mkdir -p "$(dirname "$TARGET_DIR")"
        if git clone --quiet "$AF_REPO" "$TARGET_DIR" 2>/dev/null; then
            cloned=$((cloned + 1))
        else
            echo "   ERROR: git clone failed for AbstractFramework"
            exit 1
        fi
    fi
else
    # No target — detect repo root from script location.
    TARGET_DIR="$(dirname "$SCRIPT_DIR")"   # one level up from scripts/
    if ! is_af_root "$TARGET_DIR"; then
        echo "ERROR: cannot determine AbstractFramework root."
        echo "       Run from inside the repo or pass a target directory."
        exit 1
    fi
    echo "✓ Using repo root: $TARGET_DIR"
fi

echo ""
echo "Root directory:   $(cd "$TARGET_DIR" && pwd)"
echo "Sibling repos:    ${#SIBLING_REPOS[@]}"
echo ""

# ── Clone / update sibling repos ───────────────────────────────────────────
for repo_url in "${SIBLING_REPOS[@]}"; do
    repo_name=$(basename "$repo_url" .git)

    if [ -d "$TARGET_DIR/$repo_name/.git" ]; then
        echo "↻  Updating  $repo_name"
        if (cd "$TARGET_DIR/$repo_name" && git pull --rebase --quiet 2>/dev/null); then
            updated=$((updated + 1))
        else
            echo "   WARNING: git pull failed for $repo_name (resolve manually)"
            failed=$((failed + 1))
        fi
    else
        echo "⬇  Cloning   $repo_name"
        if git clone --quiet "$repo_url" "$TARGET_DIR/$repo_name" 2>/dev/null; then
            cloned=$((cloned + 1))
        else
            echo "   WARNING: git clone failed for $repo_name"
            failed=$((failed + 1))
        fi
    fi
done

echo ""
echo "============================================================"
echo "  Done."
echo "  Cloned:  $cloned"
echo "  Updated: $updated"
if [ "$failed" -gt 0 ]; then
    echo "  Failed:  $failed  (see warnings above)"
fi
echo "============================================================"
echo ""
echo "Root:     $(cd "$TARGET_DIR" && pwd)"
echo ""
echo "Next step — build everything from local repos:"
echo "  cd $(cd "$TARGET_DIR" && pwd)"
echo "  ./scripts/build.sh"
