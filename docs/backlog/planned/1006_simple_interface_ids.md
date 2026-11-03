# 1006 — Simple interface ids (runnable.v1, assistant.v1, ...) instead of app-named ones

> Package: abstractflow, abstractgateway, abstractcode, abstractcode-tui, abstractassistant, abstractuic, abstractobserver, abstractruntime, abstractagent, abstractskill
> Type: task
> Created: 2026-10-11
> Priority: normal
> Labels: interfaces, naming, migration, cross-repo

## Summary

Workflow interface ids name the app that first used them (`abstractcode.agent.v1` is the framework's
runnable agent contract, `abstractassistant.agent.v1` the assistant contract, `abstractcode.goal.v1`,
`abstractcode.coding.v1`, ...). Rename every interface id to a simple role name (`runnable.v1`,
`assistant.v1`, `goal.v1`, `coding.v1`, ...) in one wave, with a one-time data fix for what is already
stored, so no id names an application.

## Why

Operator, 2026-10-11: "for runnable, what's the name? i think ideally we would want runnable.v1,
assistant.v1, simple names." Also: "abstractflow does not know and must not know about other apps
reusing or not the workflows composed there." The operator chose to keep the ids for now and plan the
rename here ("Keep ids, backlog the rename").

## Current code reality (2026-10-11)

- `abstractcode.agent.v1` appears in 183 files across 10 repos (agent, assistant, code, code-tui, flow,
  gateway, observer, runtime, skill, uic), excluding changelogs and llms files.
- `abstractassistant.agent.v1`: 22 files (assistant, flow, gateway); `abstractcode.goal.v1`: 32;
  `abstractcode.coding.v1`: 36.
- Ids declared in published bundles of the operator's gateway (`runtime/`): 162 declarations over 11 ids,
  including `abstractautomation.monitor.v1` (not in AbstractFlow's vocabulary).
- Stored state keyed by interface id: the gateway's `agents.default_workflow` (runtime config) and each
  account's `default_workflow` preferences (`abstractgateway/src/abstractgateway/account_preferences.py`),
  automation targets `{flow_id: "@default", interface}`, run inputs that started with `@default`.
- AbstractFlow's vocabulary: `abstractflow/src/utils/flowFamilies.ts` `KNOWN_INTERFACES`; the gateway's:
  `abstractgateway/src/abstractgateway/agent_defaults.py` `INTERFACE_TABLE`.

## Scope

### In scope

- One mapping table old id → new id, applied in every repo's code, tests, fixtures and docs.
- Re-packed shipped bundles (`abstractgateway/flows/bundles/*.flow`) declaring the new ids.
- A one-time script under `untracked/` (never gateway code) that rewrites stored flows, bundles (with
  their recorded sha256 in `workflow_catalog.json`), runtime-config and account-preference keys and
  automation targets, run while the gateway is stopped, with a backup. A rehearsal of that shape exists
  (`untracked/interface-dedup/migrate.py`, written 2026-10-11 and not run).
- Release order bottom-up: runtime/agent → gateway → apps.

### Out of scope

- Changing any contract (pins): names only.
- A permanent alias layer for old ids (the data is fixed once instead).

## Acceptance criteria

- [ ] No source, test or doc references an old id except the mapping table, CHANGELOGs and the script.
- [ ] Every stored flow, bundle, default and automation on the operator's gateway uses the new ids.
- [ ] Every app lists, starts and defaults the same workflows as before the rename.

## Receipts

- (to fill)
