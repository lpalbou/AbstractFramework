#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — git status overview for all repositories
# =============================================================================
# Displays a concise git status report for the root AbstractFramework repository
# and every sibling repository cloned by scripts/clone.sh.
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

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
banner
require_cmd git

total=0
dirty=0

# ── Root repository (AbstractFramework) ───────────────────────────────────
printf "${C_BOLD}  Root repository${C_RESET}\n"
printf "  %s\n\n" "────────────────────────────────────────────────────────"

report_repo "abstractframework" "$ROOT_DIR" || dirty=$((dirty + 1))
total=$((total + 1))
echo ""

# ── Sibling repositories ─────────────────────────────────────────────────
printf "${C_BOLD}  Sibling repositories${C_RESET}\n"
printf "  %s\n\n" "────────────────────────────────────────────────────────"

for repo_name in "${SIBLING_REPOS[@]}"; do
    report_repo "$repo_name" "$ROOT_DIR/$repo_name" || dirty=$((dirty + 1))
    total=$((total + 1))
done

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
