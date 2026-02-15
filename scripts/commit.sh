#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — commit per repository
# =============================================================================
# Commits changes in the root AbstractFramework repo and each sibling repository
# with a shared commit message. Clean repos are skipped; missing repos are
# reported. This does NOT push to remotes.
#
# Usage:
#   ./scripts/commit.sh "Your commit message"
#   ./scripts/commit.sh Your commit message without quotes
#
# Prerequisites:
#   - git
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Sibling repositories — must mirror the list in scripts/clone.sh.
SIBLING_REPOS=(
    abstractcore
    abstractruntime
    abstractagent
    abstractflow
    abstractcode
    abstractgateway
    abstractmemory
    abstractsemantics
    abstractvoice
    abstractvision
    abstractmusic
    abstractassistant
    abstractobserver
    abstractuic
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
banner() {
    printf "\n%s\n" "============================================================"
    printf "%s\n"   "  AbstractFramework — commit per repository"
    printf "%s\n"   "============================================================"
    echo ""
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $1"
        exit 1
    fi
}

# Detect whether a directory IS the AbstractFramework repo.
is_af_root() {
    local dir="$1"
    [[ -f "$dir/pyproject.toml" ]] && grep -q 'name = "abstractframework"' "$dir/pyproject.toml" 2>/dev/null
}

usage() {
    echo "Usage: $0 <commit message>"
    echo ""
    echo "Example:"
    echo "  $0 \"Fix gateway timeout handling\""
}

# Commit changes for a single repository.
# Arguments: $1 = display name, $2 = absolute path to repo
commit_repo() {
    local name="$1"
    local repo_dir="$2"

    if [[ ! -e "$repo_dir/.git" ]]; then
        echo "WARNING: repo not found (not cloned): $name"
        missing=$((missing + 1))
        return 0
    fi

    local status
    if ! status="$(git -C "$repo_dir" status --porcelain 2>/dev/null)"; then
        echo "ERROR: git status failed: $name"
        failed=$((failed + 1))
        return 0
    fi

    if [[ -z "$status" ]]; then
        echo "CLEAN: $name"
        clean=$((clean + 1))
        return 0
    fi

    echo "COMMIT: $name"

    if ! git -C "$repo_dir" add -A; then
        echo "ERROR: git add failed: $name"
        failed=$((failed + 1))
        return 0
    fi

    if git -C "$repo_dir" diff --cached --quiet; then
        echo "WARNING: nothing staged after add: $name"
        clean=$((clean + 1))
        return 0
    fi

    if git -C "$repo_dir" commit -m "$COMMIT_MESSAGE"; then
        committed=$((committed + 1))
    else
        echo "ERROR: git commit failed: $name"
        failed=$((failed + 1))
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

if [[ "$#" -lt 1 ]]; then
    usage
    exit 1
fi

COMMIT_MESSAGE="$*"

if [[ -z "${COMMIT_MESSAGE//[[:space:]]/}" ]]; then
    echo "ERROR: commit message cannot be empty."
    usage
    exit 1
fi

require_cmd git

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if ! is_af_root "$ROOT_DIR"; then
    echo "ERROR: cannot determine AbstractFramework root from: $ROOT_DIR"
    echo "       Run from inside the repo or check your checkout."
    exit 1
fi

banner
echo "Root: $ROOT_DIR"
echo "Message: $COMMIT_MESSAGE"
echo ""

total=0
committed=0
clean=0
missing=0
failed=0

commit_repo "abstractframework" "$ROOT_DIR"
total=$((total + 1))

for repo_name in "${SIBLING_REPOS[@]}"; do
    commit_repo "$repo_name" "$ROOT_DIR/$repo_name"
    total=$((total + 1))
done

echo ""
echo "============================================================"
echo "  Done."
echo "  Total:     $total"
echo "  Committed: $committed"
echo "  Clean:     $clean"
echo "  Missing:   $missing"
echo "  Failed:    $failed"
echo "============================================================"
echo ""

if [[ "$failed" -gt 0 ]]; then
    exit 1
fi
