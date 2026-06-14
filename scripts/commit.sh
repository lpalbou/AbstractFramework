#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — commit per repository
# =============================================================================
# Commits changes in the root AbstractFramework repo and each sibling repository
# with a shared commit message. Repositories are processed in the same grouped
# package order used by scripts/build.sh and scripts/status.sh. Clean repos are
# skipped; missing repos are reported. This does NOT push to remotes.
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
# Build/status groups.
#
# Format:
#   display-name[:primary-relative-path[:fallback-relative-path...]]
#
# Most repositories use the same display name and directory name. AbstractMusic
# has historically appeared with mixed repository casing, so accept both the
# canonical lowercase local package path and the GitHub repository casing.
# The group order mirrors scripts/build.sh and scripts/status.sh:
#   Python Tier 0 -> Tier 4, then npm UI packages.
# abstractcode/web is an npm build target inside the abstractcode repository, so
# the abstractcode repo is committed once in Python Tier 3.
GROUP_PY_TIER0=(
    abstractskill:abstractskill:AbstractSkill
    abstractsemantics
    abstractmemory
    abstractvision
    abstractvoice
    abstractmusic:abstractmusic:AbstractMusic
)

GROUP_PY_TIER1=(
    abstractcore
    abstractruntime
)

GROUP_PY_TIER2=(
    abstractagent
    abstractgateway
)

GROUP_PY_TIER3=(
    abstractcode
    abstractassistant
)

GROUP_PY_TIER4=(
    abstractframework:.
)

GROUP_NPM=(
    abstractuic
    abstractobserver
    abstractflow
)

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
    printf "${C_BOLD}%s${C_RESET}\n"   "  AbstractFramework — commit per repository"
    printf "${C_BOLD}%s${C_RESET}\n"   "============================================================"
    echo ""
}

section() {
    printf "${C_BOLD}  %s${C_RESET}\n" "$1"
    printf "  %s\n" "────────────────────────────────────────────────────────"
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
    echo "Commits all dirty AbstractFramework repositories in build/status order."
    echo ""
    echo "Example:"
    echo "  $0 \"Fix gateway timeout handling\""
}

repo_dir_for() {
    local spec="$1"
    local fields=()
    IFS=':' read -r -a fields <<< "$spec"
    local name="${fields[0]}"

    if [[ ${#fields[@]} -eq 1 ]]; then
        printf "%s/%s\n" "$ROOT_DIR" "$name"
        return 0
    fi

    local candidate
    for candidate in "${fields[@]:1}"; do
        if [[ -d "$ROOT_DIR/$candidate/.git" ]]; then
            printf "%s/%s\n" "$ROOT_DIR" "$candidate"
            return 0
        fi
    done

    printf "%s/%s\n" "$ROOT_DIR" "${fields[1]}"
}

repo_display_name() {
    local spec="$1"
    printf "%s\n" "${spec%%:*}"
}

count_paths() {
    local repo_dir="$1"
    local mode="$2"

    case "$mode" in
        staged)
            git -C "$repo_dir" diff --cached --name-only 2>/dev/null | wc -l | tr -d ' '
            ;;
        unstaged)
            git -C "$repo_dir" diff --name-only 2>/dev/null | wc -l | tr -d ' '
            ;;
        untracked)
            git -C "$repo_dir" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' '
            ;;
    esac
}

format_change_details() {
    local staged="$1"
    local unstaged="$2"
    local untracked="$3"

    local details=()
    [[ "$staged"    -gt 0 ]] && details+=("${C_GREEN}${staged} staged${C_RESET}")
    [[ "$unstaged"  -gt 0 ]] && details+=("${C_RED}${unstaged} modified${C_RESET}")
    [[ "$untracked" -gt 0 ]] && details+=("${C_RED}${untracked} untracked${C_RESET}")

    local first=true
    local d
    for d in "${details[@]}"; do
        $first || printf ", "
        printf "%b" "$d"
        first=false
    done
}

print_repo_row() {
    local color="$1"
    local name="$2"
    local branch="$3"
    local detail="$4"

    printf "  ${C_BOLD}%b%-24s${C_RESET}  ${C_CYAN}%s${C_RESET}  %b\n" "$color" "$name" "$branch" "$detail"
}

# Commit changes for a single repository.
# Arguments: $1 = display name, $2 = absolute path to repo
commit_repo() {
    local name="$1"
    local repo_dir="$2"

    if [[ ! -d "$repo_dir/.git" ]]; then
        printf "  ${C_DIM}%-24s  (not cloned)${C_RESET}\n" "$name"
        missing=$((missing + 1))
        return 0
    fi

    local branch
    branch="$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "???")"

    local status
    if ! status="$(git -C "$repo_dir" status --porcelain 2>/dev/null)"; then
        print_repo_row "$C_RED" "$name" "$branch" "${C_RED}git status failed${C_RESET}"
        failed=$((failed + 1))
        return 0
    fi

    if [[ -z "$status" ]]; then
        print_repo_row "$C_GREEN" "$name" "$branch" "${C_GREEN}✓ clean${C_RESET}"
        clean=$((clean + 1))
        return 0
    fi

    local staged unstaged untracked details
    staged="$(count_paths "$repo_dir" staged)"
    unstaged="$(count_paths "$repo_dir" unstaged)"
    untracked="$(count_paths "$repo_dir" untracked)"
    details="$(format_change_details "$staged" "$unstaged" "$untracked")"

    if ! git -C "$repo_dir" add -A; then
        print_repo_row "$C_RED" "$name" "$branch" "${C_RED}git add failed${C_RESET}"
        failed=$((failed + 1))
        return 0
    fi

    if git -C "$repo_dir" diff --cached --quiet; then
        print_repo_row "$C_YELLOW" "$name" "$branch" "${C_YELLOW}nothing staged after add${C_RESET}"
        clean=$((clean + 1))
        return 0
    fi

    if git -C "$repo_dir" commit --quiet -m "$COMMIT_MESSAGE"; then
        local sha
        sha="$(git -C "$repo_dir" rev-parse --short HEAD 2>/dev/null || echo "???????")"
        if [[ -n "$details" ]]; then
            print_repo_row "$C_YELLOW" "$name" "$branch" "${C_GREEN}✓ committed ${sha}${C_RESET}  ${C_DIM}(${C_RESET}${details}${C_DIM})${C_RESET}"
        else
            print_repo_row "$C_YELLOW" "$name" "$branch" "${C_GREEN}✓ committed ${sha}${C_RESET}"
        fi
        committed=$((committed + 1))
    else
        print_repo_row "$C_RED" "$name" "$branch" "${C_RED}git commit failed${C_RESET}"
        failed=$((failed + 1))
    fi
}

commit_group() {
    local title="$1"
    shift

    local repo_spec repo_name repo_dir

    section "$title"
    for repo_spec in "$@"; do
        repo_name="$(repo_display_name "$repo_spec")"
        repo_dir="$(repo_dir_for "$repo_spec")"
        commit_repo "$repo_name" "$repo_dir"
        total=$((total + 1))
    done
    echo ""
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

commit_group "Python Tier 0 — No internal dependencies" "${GROUP_PY_TIER0[@]}"
commit_group "Python Tier 1 — Depends on Tier 0" "${GROUP_PY_TIER1[@]}"
commit_group "Python Tier 2 — Depends on Tier 0-1" "${GROUP_PY_TIER2[@]}"
commit_group "Python Tier 3 — Depends on Tier 0-2" "${GROUP_PY_TIER3[@]}"
commit_group "Python Tier 4 — Meta-package" "${GROUP_PY_TIER4[@]}"
commit_group "npm — UI package repositories" "${GROUP_NPM[@]}"

echo ""
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
printf "  ${C_BOLD}Commit complete.${C_RESET}\n"
printf "  ${C_BOLD}Total:${C_RESET}     %s\n" "$total"
printf "  ${C_GREEN}Committed:${C_RESET} %s\n" "$committed"
printf "  ${C_GREEN}Clean:${C_RESET}     %s\n" "$clean"
printf "  ${C_DIM}Missing:${C_RESET}   %s\n" "$missing"
if [[ "$failed" -gt 0 ]]; then
    printf "  ${C_RED}Failed:${C_RESET}    %s\n" "$failed"
else
    printf "  ${C_GREEN}Failed:${C_RESET}    %s\n" "$failed"
fi
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
echo ""

if [[ "$failed" -gt 0 ]]; then
    exit 1
fi
