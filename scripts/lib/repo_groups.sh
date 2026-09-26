#!/usr/bin/env bash
# Shared package/repository inventory for the AbstractFramework workspace
# scripts (status.sh, commit.sh, push.sh, pull.sh, clone.sh, build.sh).
#
# The DATA lives in scripts/lib/packages.txt (one row per published package:
# repo, GitHub name, kind, sub-path, registry name, tier, dependency edges).
# This file is only the bash loader: it parses the manifest into parallel
# indexed arrays and offers traversal helpers. scripts/lib/af_inventory.py
# reads the same file for the dependency / registry views (scripts/deps.sh).
#
# Compatibility: bash 3.2 (macOS /bin/bash) — no associative arrays, no
# mapfile, no ${var,,}. Callers set ROOT_DIR before sourcing. build.sh is
# zsh-sourceable because it re-executes itself in bash before it sources
# this file.

if [[ -z "${ROOT_DIR:-}" ]]; then
    echo "ERROR: ROOT_DIR must be set before sourcing scripts/lib/repo_groups.sh" >&2
    return 1 2>/dev/null || exit 1
fi

AF_PACKAGES_FILE="${AF_PACKAGES_FILE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/packages.txt}"

AF_PKG_COUNT=0
AF_PKG_ID=()
AF_PKG_REPO=()
AF_PKG_GITHUB=()
AF_PKG_KIND=()
AF_PKG_PATH=()
AF_PKG_REGISTRY=()
AF_PKG_NAME=()
AF_PKG_TIER=()
AF_PKG_DEPS=()
AF_MAX_TIER=0

af_inventory_load() {
    if [[ ! -f "$AF_PACKAGES_FILE" ]]; then
        echo "ERROR: package inventory not found: $AF_PACKAGES_FILE" >&2
        return 1
    fi
    AF_PKG_COUNT=0
    AF_MAX_TIER=0
    local line id repo github kind path registry name tier deps extra lineno=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        lineno=$((lineno + 1))
        line="${line//[[:space:]]/}"
        [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
        IFS='|' read -r id repo github kind path registry name tier deps extra <<<"$line"
        if [[ -z "$deps" || -n "$extra" ]]; then
            echo "ERROR: $AF_PACKAGES_FILE:$lineno: expected 9 '|'-separated columns" >&2
            return 1
        fi
        case "$tier" in
            ''|*[!0-9]*)
                echo "ERROR: $AF_PACKAGES_FILE:$lineno: tier must be an integer, got '$tier'" >&2
                return 1
                ;;
        esac
        AF_PKG_ID[$AF_PKG_COUNT]="$id"
        AF_PKG_REPO[$AF_PKG_COUNT]="$repo"
        AF_PKG_GITHUB[$AF_PKG_COUNT]="$github"
        AF_PKG_KIND[$AF_PKG_COUNT]="$kind"
        AF_PKG_PATH[$AF_PKG_COUNT]="$path"
        AF_PKG_REGISTRY[$AF_PKG_COUNT]="$registry"
        AF_PKG_NAME[$AF_PKG_COUNT]="$name"
        AF_PKG_TIER[$AF_PKG_COUNT]="$tier"
        AF_PKG_DEPS[$AF_PKG_COUNT]="$deps"
        [[ "$tier" -gt "$AF_MAX_TIER" ]] && AF_MAX_TIER="$tier"
        AF_PKG_COUNT=$((AF_PKG_COUNT + 1))
    done <"$AF_PACKAGES_FILE"
    if [[ "$AF_PKG_COUNT" -eq 0 ]]; then
        echo "ERROR: no packages in $AF_PACKAGES_FILE" >&2
        return 1
    fi
}

af_inventory_load || { return 1 2>/dev/null || exit 1; }

# --- package queries ----------------------------------------------------------

# Indices of the packages of one kind (or all when empty), in dependency order:
# tier ascending, then manifest order. Prints one index per line.
af_pkg_indices() {
    local kind="${1:-}" t i
    t=0
    while [[ "$t" -le "$AF_MAX_TIER" ]]; do
        i=0
        while [[ "$i" -lt "$AF_PKG_COUNT" ]]; do
            if [[ "${AF_PKG_TIER[$i]}" == "$t" && ( -z "$kind" || "${AF_PKG_KIND[$i]}" == "$kind" ) ]]; then
                echo "$i"
            fi
            i=$((i + 1))
        done
        t=$((t + 1))
    done
}

# Index of a package id (exit 1 when unknown).
af_pkg_index() {
    local i=0
    while [[ "$i" -lt "$AF_PKG_COUNT" ]]; do
        [[ "${AF_PKG_ID[$i]}" == "$1" ]] && { echo "$i"; return 0; }
        i=$((i + 1))
    done
    return 1
}

# Absolute directory of the package at index $1.
af_pkg_dir() {
    local repo="${AF_PKG_REPO[$1]}" path="${AF_PKG_PATH[$1]}" base
    if [[ "$repo" == "." ]]; then base="$ROOT_DIR"; else base="$ROOT_DIR/$repo"; fi
    if [[ "$path" == "." ]]; then echo "$base"; else echo "$base/$path"; fi
}

# Workspace-relative location of the package at index $1 (for messages).
af_pkg_location() {
    local repo="${AF_PKG_REPO[$1]}" path="${AF_PKG_PATH[$1]}"
    if [[ "$path" == "." ]]; then echo "$repo"; else echo "$repo/$path"; fi
}

# "a, b, c" list of the dependency ids of the package at index $1 ("" = none).
af_pkg_dep_ids() {
    local deps="${AF_PKG_DEPS[$1]}"
    [[ "$deps" == "-" ]] && return 0
    local out="" item
    local IFS=','
    for item in $deps; do
        out="${out:+$out, }${item%%:*}"
    done
    echo "$out"
}

# Dependency ids of the package at index $1 that are taken from a REGISTRY
# (edge kinds dep / dev), one per line. Source aliases (kind alias) and peers
# (kind peer) are not installed by the consumer and are left out. The dev
# build installs these from local packs so a sibling that is not published yet
# (or is ahead of the registry) still builds.
af_pkg_registry_dep_ids() {
    local deps="${AF_PKG_DEPS[$1]}"
    [[ "$deps" == "-" ]] && return 0
    local item
    local IFS=','
    for item in $deps; do
        case "${item#*:}" in
            dep|dev) echo "${item%%:*}" ;;
        esac
    done
}

# --- repository queries ---------------------------------------------------------

# Tier of a repository = the highest tier among its packages (the repo is
# "complete" once everything any of its packages needs is in place).
af_repo_tier() {
    local repo="$1" i=0 tier=-1
    while [[ "$i" -lt "$AF_PKG_COUNT" ]]; do
        if [[ "${AF_PKG_REPO[$i]}" == "$repo" && "${AF_PKG_TIER[$i]}" -gt "$tier" ]]; then
            tier="${AF_PKG_TIER[$i]}"
        fi
        i=$((i + 1))
    done
    echo "$tier"
}

# Unique repositories in manifest order (one per line).
af_repos() {
    local i=0 seen=" "
    while [[ "$i" -lt "$AF_PKG_COUNT" ]]; do
        case "$seen" in
            *" ${AF_PKG_REPO[$i]} "*) ;;
            *) echo "${AF_PKG_REPO[$i]}"; seen="$seen${AF_PKG_REPO[$i]} " ;;
        esac
        i=$((i + 1))
    done
}

# Repositories whose tier is $1, in manifest order.
af_repos_in_tier() {
    local want="$1" repo
    while IFS= read -r repo; do
        [[ "$(af_repo_tier "$repo")" == "$want" ]] && echo "$repo"
    done < <(af_repos)
}

af_repo_github() {
    local i=0
    while [[ "$i" -lt "$AF_PKG_COUNT" ]]; do
        [[ "${AF_PKG_REPO[$i]}" == "$1" ]] && { echo "${AF_PKG_GITHUB[$i]}"; return 0; }
        i=$((i + 1))
    done
    return 1
}

# Short "kind:id kind:id" summary of the packages a repository holds.
af_repo_packages() {
    local repo="$1" i=0 out=""
    while [[ "$i" -lt "$AF_PKG_COUNT" ]]; do
        if [[ "${AF_PKG_REPO[$i]}" == "$repo" ]]; then
            out="${out:+$out, }${AF_PKG_KIND[$i]} ${AF_PKG_ID[$i]}"
        fi
        i=$((i + 1))
    done
    echo "$out"
}

# --- compatibility helpers (status.sh / commit.sh / push.sh / pull.sh) ----------
# A repo "spec" is now simply the repo directory from packages.txt ("." = root).

repo_dir_for() {
    if [[ "$1" == "." ]]; then echo "$ROOT_DIR"; else echo "$ROOT_DIR/$1"; fi
}

repo_display_name() {
    if [[ "$1" == "." ]]; then echo "abstractframework"; else echo "$1"; fi
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

af_tier_title() {
    local t="$1"
    if [[ "$t" == "0" ]]; then
        echo "Tier 0 — no internal dependencies (first)"
    elif [[ "$t" == "1" ]]; then
        echo "Tier 1 — needs tier 0"
    else
        echo "Tier $t — needs tiers 0-$((t - 1))"
    fi
}

# Call "$callback" "<tier title>" repo... once per tier, lowest tier first.
# A repository appears once, in the tier of its highest package.
run_repo_groups() {
    local callback="$1" t repo
    local repos=()
    t=0
    while [[ "$t" -le "$AF_MAX_TIER" ]]; do
        repos=()
        while IFS= read -r repo; do
            repos[${#repos[@]}]="$repo"
        done < <(af_repos_in_tier "$t")
        if [[ "${#repos[@]}" -gt 0 ]]; then
            "$callback" "$(af_tier_title "$t")" "${repos[@]}"
        fi
        t=$((t + 1))
    done
}
