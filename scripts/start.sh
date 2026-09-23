#!/usr/bin/env bash
# =============================================================================
# AbstractFramework — start the WHOLE stack from PUBLISHED packages
# =============================================================================
# Operator port map (maintainer directive 2026-07-16):
#   gateway   8080   (control plane — started first, awaited on /api/health)
#   observer  3001
#   continuum 3002
#   code/web  3003
#   entity    3004
#   flow      3005
#
# Uses the packages as published (pip/npm registries) via the per-app
# launchers (gateway.sh, observer.sh, console.sh, code.sh, entity.sh,
# flow.sh). Each launcher keeps its own preflight + replace-a-running-
# instance semantics (a service already on its port is stopped and
# replaced, never refused). One terminal; Ctrl-C stops the whole stack
# (apps first, gateway last).
#
# Every port stays env-overridable (ABSTRACT<APP>_PORT); the values below
# are only defaults, so an operator export still wins.
#
# Local-development twin (builds the checkout first): start-local.sh
# =============================================================================
set -euo pipefail

export ABSTRACTGATEWAY_PORT="${ABSTRACTGATEWAY_PORT:-8080}"
export ABSTRACTOBSERVER_PORT="${ABSTRACTOBSERVER_PORT:-3001}"
export ABSTRACTCONTINUUM_PORT="${ABSTRACTCONTINUUM_PORT:-3002}"
export ABSTRACTCODE_PORT="${ABSTRACTCODE_PORT:-3003}"
export ABSTRACTENTITY_PORT="${ABSTRACTENTITY_PORT:-3004}"
export ABSTRACTFLOW_PORT="${ABSTRACTFLOW_PORT:-3005}"

AF_STACK_SUFFIX=""
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/af_stack.sh"
