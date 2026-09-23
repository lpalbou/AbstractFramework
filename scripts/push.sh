#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — push `main` of every repository that is ahead
# =============================================================================
# For the root repository and every sibling repository (tier by tier, the order
# of scripts/status.sh — scripts/lib/packages.txt), compare the local `main`
# with its upstream and push the commits that are ahead.
#
# SAFE BY DEFAULT: without --yes nothing is pushed — the script prints what it
# would push (commit list per repository). It never force-pushes, never pushes
# tags and never pushes a branch other than `main`. A repository whose `main`
# has DIVERGED from its upstream (commits on both sides) is skipped: run
# ./scripts/pull.sh first and resolve it by hand.
#
# Usage:
#   ./scripts/push.sh                  # dry-run: what would be pushed
#   ./scripts/push.sh --yes            # push every repo whose main is ahead
#   ./scripts/push.sh --fetch          # fetch first so ahead/behind are current
#   ./scripts/push.sh --only abstractcore,abstractuic [--yes]
#
# Exit status: 0 when every push succeeded (or nothing to do), 1 when a push
# failed or a repository with commits to push was skipped (diverged / no
# upstream / fetch failed).
#
# Prerequisites:
#   - git (with push access to the remotes when using --yes)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=./lib/repo_groups.sh
source "$SCRIPT_DIR/lib/repo_groups.sh"

BRANCH="main"
DO_PUSH=false
DO_FETCH=false
ONLY=""

usage() {
    sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes|-y) DO_PUSH=true ;;
        --dry-run|-n) DO_PUSH=false ;;
        --fetch) DO_FETCH=true ;;
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
    # row <color> <name> <detail>
    printf "  ${C_BOLD}%b%-24s${C_RESET}  ${C_CYAN}%s${C_RESET}  %b\n" "$1" "$2" "$BRANCH" "$3"
}

push_repo() {
    local spec="$1" name repo_dir upstream remote remote_branch ahead behind dirty=""
    name="$(repo_display_name "$spec")"
    repo_dir="$(repo_dir_for "$spec")"
    total=$((total + 1))

    if [[ ! -d "$repo_dir/.git" ]]; then
        printf "  ${C_DIM}%-24s  (not cloned)${C_RESET}\n" "$name"
        return 0
    fi
    if ! git -C "$repo_dir" rev-parse --verify --quiet "refs/heads/$BRANCH" >/dev/null; then
        row "$C_DIM" "$name" "${C_DIM}no local $BRANCH branch${C_RESET}"
        return 0
    fi
    if ! upstream="$(git -C "$repo_dir" rev-parse --abbrev-ref "$BRANCH@{upstream}" 2>/dev/null)"; then
        row "$C_RED" "$name" "${C_RED}no upstream for $BRANCH — set it: git -C $repo_dir branch -u origin/$BRANCH${C_RESET}"
        skipped=$((skipped + 1))
        return 0
    fi
    remote="${upstream%%/*}"
    remote_branch="${upstream#*/}"

    if $DO_FETCH; then
        if ! git -C "$repo_dir" fetch --quiet "$remote" 2>/dev/null; then
            row "$C_RED" "$name" "${C_RED}fetch from $remote failed — not pushing${C_RESET}"
            skipped=$((skipped + 1))
            return 0
        fi
    fi

    ahead="$(git -C "$repo_dir" rev-list --count "$upstream..$BRANCH")"
    behind="$(git -C "$repo_dir" rev-list --count "$BRANCH..$upstream")"
    if [[ -n "$(git -C "$repo_dir" status --porcelain 2>/dev/null)" ]]; then
        dirty="  ${C_DIM}(uncommitted changes stay local — scripts/commit.sh)${C_RESET}"
    fi

    if [[ "$ahead" -eq 0 ]]; then
        if [[ "$behind" -gt 0 ]]; then
            row "$C_GREEN" "$name" "nothing to push  ${C_YELLOW}↓${behind} behind (scripts/pull.sh)${C_RESET}${dirty}"
        else
            row "$C_GREEN" "$name" "${C_GREEN}✓ up to date with $upstream${C_RESET}${dirty}"
        fi
        return 0
    fi

    if [[ "$behind" -gt 0 ]]; then
        row "$C_RED" "$name" "${C_RED}DIVERGED: ↑${ahead} ↓${behind} vs $upstream — skipped (pull and resolve; never forced)${C_RESET}"
        skipped=$((skipped + 1))
        return 0
    fi

    if $DO_PUSH; then
        if git -C "$repo_dir" push --quiet "$remote" "refs/heads/$BRANCH:refs/heads/$remote_branch"; then
            row "$C_YELLOW" "$name" "${C_GREEN}✓ pushed ↑${ahead} to $upstream${C_RESET}${dirty}"
            pushed=$((pushed + 1))
        else
            row "$C_RED" "$name" "${C_RED}push to $upstream FAILED${C_RESET}"
            failed=$((failed + 1))
        fi
    else
        row "$C_YELLOW" "$name" "${C_YELLOW}would push ↑${ahead} to $upstream${C_RESET}${dirty}"
        would=$((would + 1))
    fi
    git -C "$repo_dir" log --format="      %h %s" "$upstream..$BRANCH" | while IFS= read -r line; do
        printf "${C_DIM}%s${C_RESET}\n" "$line"
    done
}

push_group() {
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
        push_repo "$spec"
    done
    echo ""
}

echo ""
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
if $DO_PUSH; then
    printf "${C_BOLD}%s${C_RESET}\n" "  AbstractFramework — push $BRANCH (for real: --yes)"
else
    printf "${C_BOLD}%s${C_RESET}\n" "  AbstractFramework — push $BRANCH (DRY RUN — add --yes to push)"
fi
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
$DO_FETCH || printf "  ${C_DIM}%s${C_RESET}\n" "ahead/behind use the last fetched upstream (--fetch to refresh)"
echo ""

total=0 pushed=0 would=0 skipped=0 failed=0
run_repo_groups push_group

printf "${C_BOLD}%s${C_RESET}\n" "============================================================"
if $DO_PUSH; then
    printf "  %s repos: ${C_GREEN}%s pushed${C_RESET}, %s skipped, %s failed\n" "$total" "$pushed" "$skipped" "$failed"
else
    printf "  %s repos: ${C_YELLOW}%s would be pushed${C_RESET}, %s skipped — dry run, nothing pushed\n" \
        "$total" "$would" "$skipped"
    [[ "$would" -gt 0 ]] && printf "  Push them with: %s --yes\n" "$0"
fi
printf "${C_BOLD}%s${C_RESET}\n" "============================================================"

[[ "$failed" -eq 0 && "$skipped" -eq 0 ]]
