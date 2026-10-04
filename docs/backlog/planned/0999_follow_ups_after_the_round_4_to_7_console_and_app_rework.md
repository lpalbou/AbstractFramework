# 0999 — Follow-ups after the rounds 4–7 console and app rework (0.10.0 preparation)

> Package: abstractframework, abstractgateway, abstractcore, abstractcode, abstractuic, abstractruntime
> Type: task
> Created: 2026-10-04
> Priority: normal
> Labels: follow-up, release, console, tui, tests, voice

## Summary

Non-blocking findings recorded while rounds 4–7 (2026-10-03/04) rebuilt the gateway consoles (web +
terminal), the OpenAI API page, Models, Network, Code web and Code TUI, the shared kit components
(rail drawer, file viewer, audio player, About, Voice settings) and voice in every app. Every round
passed its adversary gate; these items were accepted as not blocking the local deploy. Numbering is
local to this item. Operator decisions raised in the same rounds are the gate
[1001](1001_operator_decisions_after_the_round_4_to_7_rework.md); the named per-user API keys design
is [1000](../proposed/1000_named_per_user_openai_api_keys.md).

## Current code reality (2026-10-04)

Nothing below is released. The work sits on `round4/2026-10-03` in abstractgateway (console + crate),
abstractcode, abstractobserver, abstractentity, abstractuic, abstractcore, abstractruntime,
abstractflow, abstractcontinuum, abstractvoice and abstractassistant, with planned versions prepared
on those branches (ui-kit 0.8.0, panel-chat 0.3.1, gateway 0.13.0, core 2.25.0, runtime 0.9.0, voice
0.14.0, code web 0.11.0 / tui 0.9.0, flow 0.8.0, observer 0.7.0, continuum 0.7.0, entity 0.7.0,
assistant 0.13.0) and root `release-prep/0.10.0` (pins prepared, not released). Evidence and
verdicts: `untracked/round4/ADVERSARY.md`, `untracked/round4/COORD.md`, `untracked/round4/CLOSE-R7.md`.

## Items

1. Code web e2e "list refreshes preserve sidebar rows" is racy (pre-existing, seen in rounds 4 and 5):
   bind the wait to the list refresh event, 3 consecutive green runs. Owner: code.
2. Gateway test fixture `email_automations`: `PUT /me/email` can hang the fixture; add a timeout and
   find the blocking call. Owner: gateway.
3. AbstractCore's own structured-output suite stays green with its schema validator disabled (only the
   gateway's `tests/test_openai_api_structured.py` goes red): add a core-level test that fails when the
   validator is removed. Owner: core.
4. Kit `ToolPolicyEditor`: the "camera" label renders at 12 px on touch layouts; use the kit's label
   size. Owner: kit.
5. Three Code web workspace-voice e2e tests need `abstractvoice` in the test environment; declare it in
   the e2e setup or skip with a stated reason. Owner: code.
6. Code TUI live tests (`r7w4_live`) are not idempotent on a reused fixture gateway (automation and
   conversation archive tests fail once the items are archived): each test creates its own items or
   unarchives first. Owner: code.
7. Gateway console Models at 390 px: the filter block is long before the first card; consider a
   collapsed **Filters** disclosure. Owner: gateway.
8. Code automation header: the workspace shows the folder id (`session-automation-<uuid>`); show a
   short label ("Automation workspace") with the id in the tooltip if the rail did not already cover
   it. At 1440 px the automation timing line wraps to three short lines beside the switch. Owner: code.
9. Gateway terminal console items declared not mirrored from the web console: Resources sub-tabs,
   Sandbox pickers on the configured route, Providers sections reached with `v` at 80×24, the retained
   runtimes link on Accounts. Mirror them or document the difference in the crate README. Owner:
   gateway.
10. Visual checks covered only by node tests: the Models delete refusal for a resident model ("Unload it
    first") and the Code settings labels; capture them once on a stack with a resident model. Owner:
    gateway, code.
11. Release prep (0994 item 90 still open): a pre-tag script per repo that greps every version source
    (package.json, pyproject, `_version.py`, Cargo.toml + Cargo.lock, About/app version strings,
    FastAPI app version, `ABSTRACTRUNTIME_FLOOR`, CHANGELOG heading). The 0.10.0 preparation did this
    by hand. Owner: release.
12. App lockfiles were not relocked: the apps declare `@abstractframework/ui-kit` `^0.8.0` and
    `@abstractframework/panel-chat` `^0.3.1`, which are unpublished; relock each app right after the
    kit is published and before its own tag (the local deploy overlays the packs in
    `untracked/round4/packs/`). Owner: release.
13. Supervisor restart of a hung gateway: root branch `fix/supervisor-restarts-hung-gateway` (625c36b,
    adversary PASS) restarts on death by default and kills a hung gateway only with
    `start-local.sh --restart-on-hang`; it is not on `release-prep/0.10.0`. Merge it with 0.10.0 or
    leave it out, per decision 1001 §6. Owner: root.
14. Console islands and AbstractCore's vendored kit theme CSS must be re-synced after every kit
    version (see 0994 items 55 and 81); confirm both carry ui-kit 0.8.0 before tagging the gateway
    and core. Owner: gateway, core.

## Acceptance criteria

- [ ] Items 1–6 fixed with a test that goes RED without the change.
- [ ] Items 11–14 checked off in the 0.10.0 release wave (or carried with a reason).
- [ ] Items 7–10 fixed or moved to their own item with a screenshot.

## Receipts

`untracked/round4/ADVERSARY.md` (lines on rounds 4–7 "Backlog" and "NOTE (non-blocking)"),
`untracked/round4/COORD.md`, `untracked/round4/BACKLOG-R5.md`, `untracked/round4/CLOSE-R7.md`.
