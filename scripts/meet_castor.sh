#!/usr/bin/env bash
# DEPRECATED TWICE OVER — do not use.
#
# 2026-07-09 (maintainer consolidation): the standalone :8081 gateway this
# rig spun up is RETIRED; Castor is served by THE gateway (:8080).
# 2026-07-12 (repo split): the entity app moved out of abstractobserver
# into its own package (abstractentity, port 3007) — the landing knob and
# dist/entity.html this rig depended on no longer exist, so the legacy
# body below cannot function at all and has been removed.
#
# The current path:
#   ./scripts/gateway-flow-local.sh   # gateway + flow + observer, one login
#   ./scripts/entity-local.sh         # the entity app on :3007
#   open http://127.0.0.1:3007/?entity=castor&live=1
echo "DEPRECATED: this rig is dead (retired :8081 gateway + the entity app moved to abstractentity)." >&2
echo "Use: scripts/gateway-flow-local.sh + scripts/entity-local.sh, then open http://127.0.0.1:3007/?entity=castor&live=1" >&2
exit 1
