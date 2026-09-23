#!/usr/bin/env bash
# Shared repository inventory for AbstractFramework multi-repo scripts.
#
# Expects ROOT_DIR to be set by the caller before sourcing this file.

if [[ -z "${ROOT_DIR:-}" ]]; then
    echo "ERROR: ROOT_DIR must be set before sourcing scripts/lib/repo_groups.sh" >&2
    return 1 2>/dev/null || exit 1
fi

# Format:
#   display-name[:primary-relative-path[:fallback-relative-path...]]
#
# Most repositories use the same display name and directory name. AbstractMusic
# has historically appeared with mixed repository casing, so accept both the
# canonical lowercase local package path and the GitHub repository casing.
# The group order mirrors scripts/build.sh:
#   Python Tier 0 -> Tier 4, npm UI packages, then Rust Tier 0 crates.
# abstractcode holds two clients in one repository: a Rust terminal client
# (a cargo workspace whose member is tui/) and a browser client at
# abstractcode/web. It has no Python package, so it is listed in Rust Tier 0
# and its web build is driven directly by scripts/build.sh.
# abstracttui is a standalone Rust Tier 0 crate (terminal UI engine); it has no
# Python/npm build step and is consumed by Rust projects (e.g. abstractcoder)
# via a cargo path dependency.
GROUP_PY_TIER0=(
    abstractskill:abstractskill:AbstractSkill
    abstractsemantics
    abstractmemory
    abstractvision
    abstractvoice
    abstractmusic:abstractmusic:AbstractMusic
    abstractcamera
    abstract3d
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
    abstractassistant
)

GROUP_PY_TIER4=(
    abstractframework:.
)

GROUP_NPM=(
    abstractui:abstractuic:AbstractUIC
    abstractobserver
    abstractflow
    abstractentity
    abstractcontinuum
)

GROUP_RUST_TIER0=(
    abstracttui:abstracttui:AbstractTUI
    abstractcode:abstractcode:AbstractCode
)

repo_dir_for() {
    local spec="$1"
    local fields=()
    IFS=':' read -r -a fields <<< "$spec"

    if [[ ${#fields[@]} -eq 1 ]]; then
        printf "%s/%s\n" "$ROOT_DIR" "${fields[0]}"
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

# Current branch of a repository, robust to edge cases:
#   - unborn branch (fresh repo with no commits): `rev-parse --abbrev-ref HEAD`
#     fails there, but `branch --show-current` still reports the branch name.
#   - detached HEAD: `branch --show-current` is empty; fall back to rev-parse,
#     which prints "HEAD".
repo_branch_for() {
    local repo_dir="$1"
    local branch
    branch="$(git -C "$repo_dir" branch --show-current 2>/dev/null || true)"
    if [[ -z "$branch" ]]; then
        branch="$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '???')"
    fi
    printf "%s\n" "$branch"
}

run_repo_groups() {
    local callback="$1"

    "$callback" "Python Tier 0 — No internal dependencies" "${GROUP_PY_TIER0[@]}"
    "$callback" "Python Tier 1 — Depends on Tier 0" "${GROUP_PY_TIER1[@]}"
    "$callback" "Python Tier 2 — Depends on Tier 0-1" "${GROUP_PY_TIER2[@]}"
    "$callback" "Python Tier 3 — Depends on Tier 0-2" "${GROUP_PY_TIER3[@]}"
    "$callback" "Python Tier 4 — Meta-package" "${GROUP_PY_TIER4[@]}"
    "$callback" "npm — UI package repositories" "${GROUP_NPM[@]}"
    "$callback" "Rust Tier 0 — Standalone crate repositories (no internal deps)" "${GROUP_RUST_TIER0[@]}"
}
