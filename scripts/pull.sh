#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — fetch + fast-forward `main` of every repository
# =============================================================================
# For the root repository and every sibling repository (tier by tier, the order
# of scripts/status.sh — scripts/lib/packages.txt): fetch the upstream of
# `main`, then fast-forward `main` when it is strictly behind.
#
# Never merges, never rebases, never touches a diverged branch: a repository
# with local commits AND new upstream commits is reported and left alone.
# When `main` is checked out the fast-forward runs `git merge --ff-only`
# (it refuses if a local uncommitted change would be overwritten); when
# another branch is checked out, only the `main` ref moves.
#
# Usage:
#   ./scripts/pull.sh                  # fetch + fast-forward main everywhere
#   ./scripts/pull.sh --dry-run        # fetch only; report what would move
#   ./scripts/pull.sh --dry-run --no-fetch   # offline: last fetched state
#   ./scripts/pull.sh --only abstractcore,abstractuic
#
# Missing repositories are reported (clone them with ./scripts/clone.sh).
# Exit status: 1 when a fetch or fast-forward failed or a repo diverged.
#
# Prerequisites:
#   - git
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=./lib/repo_groups.sh
source "$SCRIPT_DIR/lib/repo_groups.sh"

BRANCH="main"
DRY_RUN=false
DO_FETCH=true
ONLY=""

usage() {
    sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run|-n) DRY_RUN=true ;;
        --no-fetch) DO_FETCH=false ;;
        --only) shift; ONLY="${1:-}" ;;
        --only=*) ONLY="${1#--only=}" ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

if [[ -t 1 ]]; then
    C_RESET="\033[0m" C_BOLD="\033[1m" C_GREEN="\033[32m" C_YELLOW="\033[33m"
    C_RED="\033[31m" C_CYAN="\033[36m" C_DIM="\033[2m"
else
    C_RESET="" C_BOLD="" C_GREEN="" C_YELLOW="" C_RED="" C_CYAN="" C_DIM=""
fi

command -v git >/dev/null 2>&1 || { echo "ERROR: required command not found: git" >&2; exit 1; }

selected() {
    [[ -z "$ONLY" ]] && return 0
    case ",$ONLY," in
        *",$1,"*) return 0 ;;
    esac
    [[ "$1" == "." ]] && case ",$ONLY," in *",abstractframework,"*) return 0 ;; esac
    return 1
}

row() {
    printf "  ${C_BOLD}%b%-24s${C_RESET}  ${C_CYAN}%s${C_RESET}  %b\n" "$1" "$2" "$3" "$4"
}

pull_repo() {
    local spec="$1" name repo_dir current upstream remote ahead behind
    name="$(repo_display_name "$spec")"
    repo_dir="$(repo_dir_for "$spec")"
    total=$((total + 1))

    if [[ ! -d "$repo_dir/.git" ]]; then
        printf "  ${C_DIM}%-24s  (not cloned — ./scripts/clone.sh)${C_RESET}\n" "$name"
        missing=$((missing + 1))
        return 0
    fi
    current="$(repo_branch_for "$repo_dir")"
    if ! git -C "$repo_dir" rev-parse --verify --quiet "refs/heads/$BRANCH" >/dev/null; then
        row "$C_DIM" "$name" "$current" "${C_DIM}no local $BRANCH branch${C_RESET}"
        return 0
    fi
    if ! upstream="$(git -C "$repo_dir" rev-parse --abbrev-ref "$BRANCH@{upstream}" 2>/dev/null)"; then
        row "$C_RED" "$name" "$current" "${C_RED}no upstream for $BRANCH${C_RESET}"
        failed=$((failed + 1))
        return 0
    fi
    remote="${upstream%%/*}"

    if $DO_FETCH; then
        if ! git -C "$repo_dir" fetch --quiet --prune "$remote" 2>/dev/null; then
            row "$C_RED" "$name" "$current" "${C_RED}fetch from $remote failed${C_RESET}"
            failed=$((failed + 1))
            return 0
        fi
    fi

    ahead="$(git -C "$repo_dir" rev-list --count "$upstream..$BRANCH")"
    behind="$(git -C "$repo_dir" rev-list --count "$BRANCH..$upstream")"

    if [[ "$behind" -eq 0 ]]; then
        if [[ "$ahead" -gt 0 ]]; then
            row "$C_GREEN" "$name" "$current" "up to date  ${C_YELLOW}↑${ahead} unpushed (scripts/push.sh)${C_RESET}"
        else
            row "$C_GREEN" "$name" "$current" "${C_GREEN}✓ up to date${C_RESET}"
        fi
        return 0
    fi
    if [[ "$ahead" -gt 0 ]]; then
        row "$C_RED" "$name" "$current" "${C_RED}DIVERGED ↑${ahead} ↓${behind} vs $upstream — left alone (resolve by hand)${C_RESET}"
        failed=$((failed + 1))
        return 0
    fi
    if $DRY_RUN; then
        row "$C_YELLOW" "$name" "$current" "${C_YELLOW}would fast-forward $BRANCH ↓${behind} from $upstream${C_RESET}"
        would=$((would + 1))
    else
        local ok=true
        if [[ "$current" == "$BRANCH" ]]; then
            git -C "$repo_dir" merge --ff-only --quiet "$upstream" >/dev/null 2>&1 || ok=false
        else
            # Not checked out: move the ref only; git refuses non fast-forwards.
            git -C "$repo_dir" fetch --quiet . "refs/remotes/$upstream:refs/heads/$BRANCH" 2>/dev/null || ok=false
        fi
        if $ok; then
            row "$C_YELLOW" "$name" "$current" "${C_GREEN}✓ fast-forwarded $BRANCH ↓${behind}${C_RESET}"
            updated=$((updated + 1))
        else
            row "$C_RED" "$name" "$current" "${C_RED}fast-forward FAILED (local changes in the way?) — git -C $repo_dir merge --ff-only $upstream${C_RESET}"
            failed=$((failed + 1))
            return 0
        fi
    fi
    git -C "$repo_dir" log --format="      %h %s" "$BRANCH..$upstream" | head -10 | while IFS= read -r line; do
        printf "${C_DIM}%s${C_RESET}\n" "$line"
    done
}

pull_group() {
    local title="$1" spec any=false
    shift
    for spec in "$@"; do
        selected "$spec" && any=true
    done
    $any || return 0
    printf "${C_BOLD}  %s${C_RESET}\n" "$title"
    printf "  %s\n" "────────────────────────────────────────────────────────"
    for spec in "$@"; do
        selected "$spec" || continue
        pull_repo "$spec"
    done
    echo ""
}

echo ""
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
if $DRY_RUN; then
    printf "${C_BOLD}%s${C_RESET}\n" "  AbstractFramework — pull $BRANCH (DRY RUN: $($DO_FETCH && echo 'fetch only' || echo 'no fetch'))"
else
    printf "${C_BOLD}%s${C_RESET}\n" "  AbstractFramework — pull $BRANCH (fetch + fast-forward only)"
fi
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
echo ""

total=0 updated=0 would=0 missing=0 failed=0
run_repo_groups pull_group

printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
if $DRY_RUN; then
    printf "  %s repos: ${C_YELLOW}%s would fast-forward${C_RESET}, %s missing, %s need attention\n" \
        "$total" "$would" "$missing" "$failed"
else
    printf "  %s repos: ${C_GREEN}%s fast-forwarded${C_RESET}, %s missing, %s need attention\n" \
        "$total" "$updated" "$missing" "$failed"
fi
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"

[[ "$failed" -eq 0 ]]
