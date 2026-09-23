#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — status overview for every repository and package
# =============================================================================
# Git status of the root AbstractFramework repository and every sibling
# repository, grouped by dependency TIER (scripts/lib/packages.txt: a
# repository sits in the tier of its highest package, so tier 0 is what has
# to be installed / released first).
#
# For each repository the script shows:
#   • Current branch
#   • Pending changes (staged, unstaged, untracked)
#   • Unpushed commits (ahead of upstream)   -> scripts/push.sh
#   • Unpulled commits (behind upstream)     -> scripts/pull.sh
#   • The packages it holds (kind + id)
#
# Usage:
#   ./scripts/status.sh              # git overview, grouped by tier
#   ./scripts/status.sh --short      # only repos with pending work
#   ./scripts/status.sh --versions   # + local version of every package
#   ./scripts/status.sh --registry   # + local vs latest on PyPI / npm / crates.io (network)
#   ./scripts/status.sh --tiers      # + install/release order per tier with dependency edges
#   ./scripts/status.sh --no-git --registry   # only the registry table
#
# "behind"/"unpushed" compare with the LAST FETCHED upstream; run
# ./scripts/pull.sh --dry-run first to refresh them (fetch only).
#
# Prerequisites:
#   - git; python3 for --versions / --registry / --tiers
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------
SHORT_MODE=false
SHOW_GIT=true
SHOW_VERSIONS=false
SHOW_REGISTRY=false
SHOW_TIERS=false
usage() {
    echo "Usage: $0 [--short|-s] [--versions] [--registry] [--tiers] [--no-git] [--help|-h]"
    echo ""
    echo "  --short, -s   Only show repos with pending changes or unpushed commits"
    echo "  --versions    Also print the local version of every package (no network)"
    echo "  --registry    Also compare local versions with PyPI / npm / crates.io (network)"
    echo "  --tiers       Also print the install/release order per tier with dependency edges"
    echo "  --no-git      Skip the git overview (use with --versions/--registry/--tiers)"
    echo "  --help, -h    Show this help message"
}
for arg in "$@"; do
    case "$arg" in
        --short|-s) SHORT_MODE=true ;;
        --versions) SHOW_VERSIONS=true ;;
        --registry) SHOW_REGISTRY=true ;;
        --tiers|--deps) SHOW_TIERS=true ;;
        --no-git) SHOW_GIT=false ;;
        --help|-h) usage; exit 0 ;;
        *) echo "ERROR: unknown argument: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Shared package inventory (scripts/lib/packages.txt) and tier traversal.
# shellcheck source=./lib/repo_groups.sh
source "$SCRIPT_DIR/lib/repo_groups.sh"

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
    printf "${C_BOLD}%s${C_RESET}\n"   "  AbstractFramework — status overview"
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
# Arguments: $1 = display name, $2 = absolute path to the repo,
#            $3 = packages summary (dim second line)
# Returns: 0 if repo is clean, 1 if it has pending work
report_repo() {
    local name="$1"
    local repo_dir="$2"
    local packages="${3:-}"

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
    branch="$(repo_branch_for "$repo_dir")"
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
    if [[ -n "$packages" ]]; then
        printf "      ${C_DIM}%s${C_RESET}\n" "$packages"
    fi

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

        if repo_output="$(report_repo "$repo_name" "$repo_dir" "$(af_repo_packages "$repo_spec")")"; then
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

total=0
dirty=0

if $SHOW_GIT; then
    require_cmd git
    # ── Tier order (scripts/lib/packages.txt) ──────────────────────────────
    run_repo_groups report_group

    # ── Summary ───────────────────────────────────────────────────────────
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
fi

extra_status=0
if $SHOW_VERSIONS || $SHOW_REGISTRY; then
    require_cmd python3
    if $SHOW_REGISTRY; then
        printf "${C_BOLD}  %s${C_RESET}\n" "Package versions — local checkout vs latest published (PyPI / npm / crates.io)"
        printf "  %s\n\n" "────────────────────────────────────────────────────────"
        python3 "$SCRIPT_DIR/lib/af_inventory.py" versions --registry || extra_status=1
    else
        printf "${C_BOLD}  %s${C_RESET}\n" "Package versions — local checkout"
        printf "  %s\n\n" "────────────────────────────────────────────────────────"
        python3 "$SCRIPT_DIR/lib/af_inventory.py" versions || extra_status=1
    fi
    echo ""
fi

if $SHOW_TIERS; then
    require_cmd python3
    printf "${C_BOLD}  %s${C_RESET}\n" "Install / release order — per tier, with the dependency edges (scripts/deps.sh)"
    printf "  %s\n" "────────────────────────────────────────────────────────"
    python3 "$SCRIPT_DIR/lib/af_inventory.py" tiers || extra_status=1
    echo ""
fi

exit "$extra_status"
