#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — package tiers and dependency edges
# =============================================================================
# Answers "what must be installed / released first, and why" from the single
# package inventory scripts/lib/packages.txt (30 packages in 21 repositories:
# Python on PyPI, npm packages and apps, Rust crates on crates.io).
#
# Usage:
#   ./scripts/deps.sh                     # every tier, with the edges (the "why")
#   ./scripts/deps.sh --kind npm          # one ecosystem: python | npm | rust | meta
#   ./scripts/deps.sh --versions          # + local version of every package
#   ./scripts/deps.sh order [--kind K]    # flat order: tier, kind, id, name, path
#   ./scripts/deps.sh rdeps abstractcore  # who depends on it (what follows a bump)
#   ./scripts/deps.sh check               # verify packages.txt against the real
#                                         # pyproject / package.json / Cargo.toml /
#                                         # vite.config files and git origins
#   ./scripts/deps.sh json                # machine-readable inventory
#
# Tier = dependency depth: tier 0 has no internal dependency; a tier-N package
# needs something from tier N-1. Install, build and release tier by tier.
#
# Prerequisites: python3 (3.9+; `check` needs 3.11+ for tomllib)
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
fi
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required" >&2; exit 1; }

case "${1:-}" in
    tiers|order|rdeps|versions|check|json) exec python3 "$SCRIPT_DIR/lib/af_inventory.py" "$@" ;;
    *) exec python3 "$SCRIPT_DIR/lib/af_inventory.py" tiers "$@" ;;
esac
