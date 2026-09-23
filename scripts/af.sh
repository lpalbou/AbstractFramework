#!/usr/bin/env bash
# Launch the ENTIRE framework from PUBLISHED packages: the gateway (control
# plane) first, then flow, observer, code assistant, continuum console, and
# the summoned-entity app — one terminal, one Ctrl-C to stop everything.
#
# Composes the per-app launchers (gateway.sh, flow.sh, observer.sh, code.sh,
# console.sh, entity.sh); each keeps its own preflight + restart semantics.
# Every app is on npm (flow, observer, code, continuum, entity — versions in
# docs/installers/install-manifest.json); the gateway and the assistant come
# from the Python install (scripts/install.sh or pip install abstractframework).
#
# Ports: ONE canonical map, identical to start-local.sh/af-local.sh (two
# launchers must never disagree on ports — 2026-07-21 incident):
#   gateway 8080 · observer 3001 · console 3002 · code 3003 · entity 3004 · flow 3005
export ABSTRACTGATEWAY_PORT="${ABSTRACTGATEWAY_PORT:-8080}"
export ABSTRACTOBSERVER_PORT="${ABSTRACTOBSERVER_PORT:-3001}"
export ABSTRACTCONTINUUM_PORT="${ABSTRACTCONTINUUM_PORT:-3002}"
export ABSTRACTCODE_PORT="${ABSTRACTCODE_PORT:-3003}"
export ABSTRACTENTITY_PORT="${ABSTRACTENTITY_PORT:-3004}"
export ABSTRACTFLOW_PORT="${ABSTRACTFLOW_PORT:-3005}"
#
# Local-code twin: af-local.sh
AF_STACK_SUFFIX=""
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/af_stack.sh"
