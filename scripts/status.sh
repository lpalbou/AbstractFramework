#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — git status overview for all repositories
# =============================================================================
# Displays a concise git status report for the root AbstractFramework repository
# and every sibling repository cloned by scripts/clone.sh, grouped in the same
# package order used by scripts/build.sh.
#
# For each repository the script shows:
#   • Current branch
#   • Pending changes (staged, unstaged, untracked)
#   • Unpushed commits (ahead of upstream)
#   • Unpulled commits (behind upstream)
#
# Usage:
#   ./scripts/status.sh            # show status for all repos
#   ./scripts/status.sh --short    # show only repos with pending work
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
# The group order mirrors scripts/build.sh:
#   Python Tier 0 -> Tier 4, then npm UI packages.
# abstractcode/web is an npm build target inside the abstractcode repository, so
# the abstractcode repo is listed once in Python Tier 3.
GROUP_PY_TIER0=(
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
# CLI flags
# ---------------------------------------------------------------------------
SHORT_MODE=false
for arg in "$@"; do
    case "$arg" in
        --short|-s) SHORT_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--short|-s] [--help|-h]"
            echo ""
            echo "  --short, -s   Only show repos with pending changes or unpushed commits"
            echo "  --help, -h    Show this help message"
            exit 0
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

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
    printf "${C_BOLD}%s${C_RESET}\n"   "  AbstractFramework — git status overview"
    printf "${C_BOLD}%s${C_RESET}\n"   "============================================================"
    echo ""
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $1"
        exit 1
    fi
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

# Print status for a single repository.
# Arguments: $1 = display name, $2 = absolute path to the repo
# Returns: 0 if repo is clean, 1 if it has pending work
report_repo() {
    local name="$1"
    local repo_dir="$2"

    # --- Guard: directory must exist and contain .git ----------------------
    if [[ ! -d "$repo_dir/.git" ]]; then
        if $SHORT_MODE; then
            return 0   # skip silently in short mode
        fi
        printf "  ${C_DIM}%-24s  (not cloned)${C_RESET}\n" "$name"
        return 0
    fi

    # --- Gather git info ---------------------------------------------------
    local branch staged unstaged untracked ahead behind
    branch="$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "???")"
    staged="$(git -C "$repo_dir" diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')"
    unstaged="$(git -C "$repo_dir" diff --name-only 2>/dev/null | wc -l | tr -d ' ')"
    untracked="$(git -C "$repo_dir" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')"

    # Upstream comparison (may fail if no upstream is configured)
    ahead=0
    behind=0
    if git -C "$repo_dir" rev-parse --abbrev-ref '@{upstream}' >/dev/null 2>&1; then
        ahead="$(git -C "$repo_dir" rev-list '@{upstream}..HEAD' --count 2>/dev/null || echo 0)"
        behind="$(git -C "$repo_dir" rev-list 'HEAD..@{upstream}' --count 2>/dev/null || echo 0)"
    fi

    local has_changes=false
    [[ "$staged" -gt 0 || "$unstaged" -gt 0 || "$untracked" -gt 0 || "$ahead" -gt 0 || "$behind" -gt 0 ]] && has_changes=true

    # --- Skip clean repos in short mode ------------------------------------
    if $SHORT_MODE && ! $has_changes; then
        return 0
    fi

    # --- Format output -----------------------------------------------------
    # Repo name + branch
    if $has_changes; then
        printf "  ${C_BOLD}${C_YELLOW}%-24s${C_RESET}  ${C_CYAN}%s${C_RESET}" "$name" "$branch"
    else
        printf "  ${C_BOLD}${C_GREEN}%-24s${C_RESET}  ${C_CYAN}%s${C_RESET}" "$name" "$branch"
    fi

    # Details (only when there is something to report)
    local details=()
    [[ "$staged"    -gt 0 ]] && details+=("${C_GREEN}${staged} staged${C_RESET}")
    [[ "$unstaged"  -gt 0 ]] && details+=("${C_RED}${unstaged} modified${C_RESET}")
    [[ "$untracked" -gt 0 ]] && details+=("${C_RED}${untracked} untracked${C_RESET}")
    [[ "$ahead"     -gt 0 ]] && details+=("${C_YELLOW}↑${ahead} unpushed${C_RESET}")
    [[ "$behind"    -gt 0 ]] && details+=("${C_YELLOW}↓${behind} behind${C_RESET}")

    if [[ ${#details[@]} -gt 0 ]]; then
        printf "  "
        local first=true
        for d in "${details[@]}"; do
            $first || printf ", "
            printf "%b" "$d"
            first=false
        done
    else
        printf "  ${C_GREEN}✓ clean${C_RESET}"
    fi
    echo ""

    # --- Show unpushed commit subjects for quick reference -----------------
    if [[ "$ahead" -gt 0 ]]; then
        git -C "$repo_dir" log '@{upstream}..HEAD' --oneline --format="      ${C_DIM}%h %s${C_RESET}" 2>/dev/null | while IFS= read -r line; do
            printf "%b\n" "$line"
        done
    fi

    $has_changes && return 1 || return 0
}

report_group() {
    local title="$1"
    shift

    local group_output=""
    local repo_spec repo_name repo_dir repo_output

    for repo_spec in "$@"; do
        repo_name="$(repo_display_name "$repo_spec")"
        repo_dir="$(repo_dir_for "$repo_spec")"

        if repo_output="$(report_repo "$repo_name" "$repo_dir")"; then
            :
        else
            dirty=$((dirty + 1))
        fi

        total=$((total + 1))

        if [[ -n "$repo_output" ]]; then
            group_output+="${repo_output}"$'\n'
        fi
    done

    if [[ -n "$group_output" ]]; then
        printf "${C_BOLD}  %s${C_RESET}\n" "$title"
        printf "  %s\n\n" "────────────────────────────────────────────────────────"
        printf "%b" "$group_output"
        echo ""
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
banner
require_cmd git

total=0
dirty=0

# ── Build order ──────────────────────────────────────────────────────────
report_group "Python Tier 0 — No internal dependencies" "${GROUP_PY_TIER0[@]}"
report_group "Python Tier 1 — Depends on Tier 0" "${GROUP_PY_TIER1[@]}"
report_group "Python Tier 2 — Depends on Tier 0-1" "${GROUP_PY_TIER2[@]}"
report_group "Python Tier 3 — Depends on Tier 0-2" "${GROUP_PY_TIER3[@]}"
report_group "Python Tier 4 — Meta-package" "${GROUP_PY_TIER4[@]}"
report_group "npm — UI package repositories" "${GROUP_NPM[@]}"

# ── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
clean=$((total - dirty))
if [[ "$dirty" -eq 0 ]]; then
    printf "  ${C_GREEN}${C_BOLD}All ${total} repositories are clean.${C_RESET}\n"
else
    printf "  ${C_BOLD}${total} repos scanned:${C_RESET}  "
    printf "${C_GREEN}${clean} clean${C_RESET}, ${C_YELLOW}${dirty} with pending work${C_RESET}\n"
fi
echo "============================================================"
echo ""
