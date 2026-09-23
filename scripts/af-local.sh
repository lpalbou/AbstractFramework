#!/usr/bin/env bash
# Launch the ENTIRE framework from the LOCAL source checkout: the gateway
# (control plane) first, then flow, observer, code assistant, continuum
# console, and the summoned-entity app — one terminal, one Ctrl-C to stop
# everything.
#
# Composes the per-app launchers (gateway-local.sh, flow-local.sh,
# observer-local.sh, code-local.sh, console-local.sh, entity-local.sh); each
# keeps its own preflight (dist built? gateway up?) + restart semantics.
# Build first when needed: ./scripts/build.sh
#
# Ports: ONE canonical map, identical to start-local.sh (2026-07-21 incident:
# this launcher used the apps_common defaults — flow 3000, entity 3007 — so a
# stack it started looked "down" to every browser/bookmark expecting the
# deployed map; two launchers must never disagree on ports):
#   gateway 8080 · observer 3001 · console 3002 · code 3003 · entity 3004 · flow 3005
export ABSTRACTGATEWAY_PORT="${ABSTRACTGATEWAY_PORT:-8080}"
export ABSTRACTOBSERVER_PORT="${ABSTRACTOBSERVER_PORT:-3001}"
export ABSTRACTCONTINUUM_PORT="${ABSTRACTCONTINUUM_PORT:-3002}"
export ABSTRACTCODE_PORT="${ABSTRACTCODE_PORT:-3003}"
export ABSTRACTENTITY_PORT="${ABSTRACTENTITY_PORT:-3004}"
export ABSTRACTFLOW_PORT="${ABSTRACTFLOW_PORT:-3005}"
#
# Published twin: af.sh
AF_STACK_SUFFIX="-local"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/af_stack.sh"
