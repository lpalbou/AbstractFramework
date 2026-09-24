# 0859 — Launcher port defaults match the stack port map

> Package: abstractframework (scripts/lib/apps_common.sh, scripts/gateway-flow*.sh)
> Type: task
> Created: 2026-09-23
> Priority: low
> Labels: scripts, ports

## Summary

The standalone app launchers default to ports that differ from the stack map, which
`scripts/start-local.sh` and the gateway's `apps_manager.STACK_PORTS` table both use: gateway
8080, observer 3001, continuum 3002, code 3003, entity 3004, flow 3005. `apps_common.sh` uses
flow 3000, code 3002, continuum 3003, entity 3007, and `gateway-flow*.sh` uses flow 3000 and
points at entity 3007. They were left unchanged so a live setup does not shift. (The gateway
also probes the old launcher ports 3000 and 3007 after the stack ports, so an app started by an
older script is still found.) Also `local_pythonpath` still lists `abstractflow/src`
(TypeScript now) and omits voice/vision/semantics.

## Acceptance criteria

- [ ] One port table in `docs/workspace-scripts.md`, used by every launcher.
- [ ] Changed defaults announced in the CHANGELOG with the override variables.
- [ ] `local_pythonpath` matches the inventory.
