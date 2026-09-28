# 0930 — Automations: AbstractCode (WUI + TUI) and gateway console surfaces

- **Status:** completed 2026-09-28 — AbstractCode half released (abstractcode 0.7.0 + @abstractframework/code 0.6.0 @ `227e000`); console half split to 0971
- **Moved:** `planned/0930_automations_code_and_console_surfaces.md` → `completed/0930_automations_code_and_console_surfaces.md` on 2026-09-28
- **Earlier status:** planned (phase after 0928; the operator chose Observer + Assistant first, "possibly abstractcode" later)
- **Created:** 2026-09-26
- **Area:** abstractcode (web, tui), abstractgateway (console WUI/TUI)
- **Design:** untracked/design/automations-PLAN.md §4 missions C and K

## Summary
Once 0928 ships, AbstractCode gets an "Automations" sidebar section (WUI, via ui-kit's `AutomationPanel` + client module) and minimal TUI
commands (`/automations` list/open/pause/resume/run-now/archive/discuss; `/schedule <when> | <prompt>`; `/task` is taken by the entity
desk); both session lists fold by the gateway's `session_kind` and hide automation/occurrence sessions by default. The gateway console
(web + terminal) gets an authorised inventory of automations with pause/archive and the legacy distinction.

## Current code reality
`abstractcode/tui/src/gateway/mod.rs:865` and `web/src/workspace/use_workspace_catalog.ts:87` list `/runs?root_only=true` (a scheduled
parent shows as a one-turn conversation; result children are hidden); `commands.rs:143-251` parser, `:260` completions; the console has
no schedule view (`grep is_scheduled console.py` → nothing).

## Validation
`web/src/workspace/automations.test.ts`, `tui/tests/automation_contracts.rs` (fixtures vendored from abstractuic, checksum-verified),
`abstractgateway/tests/test_console_automations.py`.

## Related
0928; abstractcode and abstractgateway (console) planned items written 2026-09-26.

## Completion (2026-09-28)

- **Shipped:** AbstractCode terminal client `/automations` (list, open, runs as chat pairs, waits, folder, pause/resume,
  run now, stop, revise, archive, Discuss) and `/schedule`; the browser client's **Automations** sidebar section on the
  shared ui-kit panel; both list the gateway's sessions without filtering by creating client. Released as crate
  `abstractcode` 0.7.0 (crates.io) and `@abstractframework/code` 0.6.0 (npm), tags `v0.7.0` / `web-v0.6.0` → `227e000`.
- **Evidence:** `tui/tests/automation_contracts.rs` and `tui/tests/automations_ui.rs` (fixtures vendored from abstractuic,
  checksum-verified; root `scripts/check_identity_sync.py` byte-compares them), `web/src/workspace/automations.test.tsx`,
  `web/e2e/automations.spec.ts` (20/20 e2e at the tag gate, `untracked/wave2/gate-code/`).
- **Not done here, split out:** the gateway consoles' automations inventory → [0971](../planned/0971_gateway_console_automations_inventory.md).
  A session-kind filter for AbstractCode's lists stays open (see the root automations guide).
