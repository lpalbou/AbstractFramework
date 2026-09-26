# 0930 — Automations: AbstractCode (WUI + TUI) and gateway console surfaces

- **Status:** planned (phase after 0928; the operator chose Observer + Assistant first, "possibly abstractcode" later)
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
