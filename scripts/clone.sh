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
#   3) Print the repository list (tier order) and exit:
#      ./scripts/clone.sh --list
#
# If a repo already exists locally, the script fast-forwards it instead of
# re-cloning (never rebases or merges local commits).
#
# The repository list is scripts/lib/packages.txt (21 repositories holding
# 30 packages); the clone order is the dependency tier order.
#
# Prerequisites:
#   - git
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The repository list comes from the shared package inventory
# (scripts/lib/packages.txt: `repo` + `github` columns), cloned tier by tier
# so the order matches build.sh / status.sh. ROOT_DIR here is only used by
# the loader; clone targets are resolved below.
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=./lib/repo_groups.sh
source "$SCRIPT_DIR/lib/repo_groups.sh"

AF_REPO="https://github.com/$(af_repo_github ".").git"

# "dir|owner/Name" per sibling repository, lowest tier first.
SIBLING_REPOS=()
_t=0
while [[ "$_t" -le "$AF_MAX_TIER" ]]; do
    while IFS= read -r _repo; do
        [[ "$_repo" == "." ]] && continue
        SIBLING_REPOS[${#SIBLING_REPOS[@]}]="${_repo}|$(af_repo_github "$_repo")"
    done < <(af_repos_in_tier "$_t")
    _t=$((_t + 1))
done

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
LIST_ONLY=false
TARGET_ARG=""
for arg in "$@"; do
    case "$arg" in
        --list) LIST_ONLY=true ;;
        -h|--help) sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) echo "ERROR: unknown argument: $arg" >&2; exit 2 ;;
        *) TARGET_ARG="$arg" ;;
    esac
done

if $LIST_ONLY; then
    echo "root  $AF_REPO"
    for entry in "${SIBLING_REPOS[@]}"; do
        printf "%-18s https://github.com/%s.git\n" "${entry%%|*}" "${entry#*|}"
    done
    exit 0
fi

banner
require_cmd git

cloned=0
updated=0
failed=0

# ── Resolve the root directory ──────────────────────────────────────────────
if [[ -n "$TARGET_ARG" ]]; then
    # A target directory was supplied.
    TARGET_DIR="$TARGET_ARG"
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
for entry in "${SIBLING_REPOS[@]}"; do
    # Checkout directories are lowercase (abstractmusic, abstractuic, ...) as
    # listed in packages.txt; the URL keeps GitHub's canonical casing.
    repo_name="${entry%%|*}"
    repo_url="https://github.com/${entry#*|}.git"

    if [ -d "$TARGET_DIR/$repo_name/.git" ]; then
        echo "↻  Updating  $repo_name"
        # Fast-forward only: local commits are never rebased or merged here
        # (./scripts/pull.sh reports diverged repos in detail).
        if git -C "$TARGET_DIR/$repo_name" pull --ff-only --quiet 2>/dev/null; then
            updated=$((updated + 1))
        else
            echo "   WARNING: git pull --ff-only failed for $repo_name (diverged or local changes; resolve manually)"
            failed=$((failed + 1))
        fi
    else
        echo "⬇  Cloning   $repo_name  ($repo_url)"
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
echo "Next steps:"
echo "  cd $(cd "$TARGET_DIR" && pwd)"
echo "  ./scripts/deps.sh            # tiers: what builds / installs first, and why"
echo "  source ./scripts/build.sh    # build everything from the local repos"
echo "  ./scripts/status.sh          # git overview per tier"
