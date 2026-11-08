# 1141 — An authorized tool never surfaces an approval request

> Package: AbstractGateway, AbstractRuntime (automations controller), AbstractAssistant (Watch/iPhone trust)
> Type: defect + policy reconciliation
> Created: 2026-11-07 (from the Codex investigation of 2026-11-05, never filed)
> Priority: high
> Labels: automations, permissions, watch

## Operator ruling (2026-11-05)

"IF the tool is authorized, the ledger should not surface a request for approval."

## Summary

On 2026-11-05 the pharma-news automation (`7734cbcb…`) waited 71 minutes for approval of `fetch_url` and two
`skim_websearch` calls the operator believed were authorized. Proven cause (read-only, `untracked/ui-fixes-2026-11-05/
approval-investigation.md`): its stored `policy.tool_approval` is `ask` (an old iPhone creation bug hard-coded `ask`),
so the gateway published a real wait; the Apple Watch client then approved it from its own device-local "Approve all"
trust, which is not a gateway grant. Nothing is auto-approved on the server; the desktop shows the wait truthfully.
Hiding the wait would conceal a real policy gap. Only an investigation was done; no code changed.

## Scope

### In scope

1. Gateway: a repair path for automations whose persisted `tool_approval` is `ask` while the person intends unattended
   runs: show the effective policy on the automation page and offer "run unattended (auto) for these tools" as an
   explicit, audited change of the definition (`controller.py` applies the definition's policy before dispatch;
   `grant_tool_approval` pre-authorizes scheduled auto-policy tools).
2. Client-local trust vs server grants: decide and record whether the Watch's "Approve all" should (a) become a session
   tool policy on the gateway (`/sessions/{id}/tool-policy`, the same Deny / Allow / Allow All, session scope as the
   web apps), or (b) stay device-local. Recommendation: (a), so every client sees the same truth and the ledger never
   shows a wait a trusted client will silently resolve.
3. Tests: an automation created with `ask` by an old client and later marked unattended runs without a wait; a wait
   that does exist is shown on desktop and Watch alike.

### Out of scope

- Changing the Deny / Allow / Allow All model or its session scope (settled 2026-11-07).
- The Watch/iPhone apps' code (another agent owns them this week); file the client half with them.

## Acceptance criteria

- [ ] An unattended automation never enters `tool_approval` waits for tools its definition authorizes.
- [ ] A genuine wait is visible on every client, and its approval is a gateway record (`POST /commands`), never a
      device-local shortcut.
- [ ] Evidence: the 2026-11-05 occurrence replayed against the fix shows no wait.
