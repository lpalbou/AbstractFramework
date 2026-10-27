# 1061 — Session tool policy: "approve all" held server-side, no approval gate flash in any app

> Package: abstractruntime (decision + store, its 0853), abstractgateway (routes + clamp, its 0943), abstractuic (`@abstractframework/panel-chat`, its 0039), abstractassistant (desktop; iPhone/watch follow-up, its 1062), abstractcode (web + terminal, follow-up)
> Type: feature
> Created: 2026-10-27
> Priority: high
> Labels: tool-approval, sessions, ledger, replay, multi-client

## Summary

A person's "approve all tools" / "approve all tools of this kind" / "deny this" for a conversation
becomes a durable, server-side **session tool policy**. The runtime consults it before it decides
whether a tool batch waits: an approved call runs with no wait and no interaction in any client,
a denied call is refused with no wait, and each decision is an `abstract.tool_policy_decision`
record in the run's ledger, which every view shows as an activity, never as a question.

## Why

Operator, 2026-10-27, verbatim: "when a user gives permission to either all tools of a kind (e.g.
fetch url) OR all tools (all available/authorized for the user and authorized by the gateway), I
still see very quickly the gate approval showing up in apps and disappearing. Before sending the
gate approval, check whether the tool is already approved for the current session, and if so, do
not send the gate approval at all." Affects all apps and the replayable ledger.

Root cause: "approve all" lived in each client. AbstractCode web sends every enabled tool as
`require_approval_tools` and flips a local `permissions: "all"`; panel-chat's controller
auto-answers the wait after it arrives (`autoApproveCurrentWait`); the desktop Assistant keeps an
in-memory grant and answers the shown wait (`should_auto_approve_tool_batch`); the iPhone stores the
grant in UserDefaults and answers waits in `applyConversationTrust`. The runtime only knew the
start-time `_runtime.tool_policy`, so it emitted `approval_required`, the ledger recorded it, every
client rendered it, and the granting client answered a moment later.

## Contract (v1)

- Routes: `GET`/`PUT` (replace)/`POST` (merge)/`DELETE` (reset)
  `/api/gateway/sessions/{session_id}/tool-policy`; body
  `{approve: {tools, kinds, all, max_risk_rank}, deny: {tools, kinds}, ask, client, if_revision}`;
  `kinds` = the `toolset` of `GET /discovery/tools` rows.
- The gateway clamps: approve selectors expand at write time to the caller's enabled discovery
  rows; the rest is listed in `clamped`. The run's `allowed_tools` still applies.
- Storage: sqlite per data root (per account) beside the run store, keyed by `session_id`, read by
  every run of the session at decision time (turns, delegated children, resumes, restarts). Not in
  run vars (the tick-writer race the steer sidecar removed).
- Never consulted for untrusted-input runs, automation occurrences, sessionless runs.
- Ledger: `emit_event` `abstract.tool_policy_decision` `{decision: auto_approved|denied, source:
  session_policy, session_id, node_id, tool_calls: [{call_id, name, matched}], policy: {revision,
  set_by, set_at}}`.
- Capability: `capabilities.session_tool_policy.supported`; clients keep their local behaviour
  only as an explicit, reported fallback on older gateways.
- Client order for "approve all" on a shown wait: write the policy, then answer that wait once.

Full text: gateway `docs/api.md` (Session tool policy) and runtime `docs/tool-approval.md`.

## Work and status

| Repo | Item | Branch / PR | State |
|---|---|---|---|
| abstractruntime | 0853 | `feat/session-tool-policy` | implemented, tests, mutation-checked |
| abstractgateway | 0943 | `feat/session-tool-policy` | implemented, end-to-end tests through the app |
| abstractuic (panel-chat) | 0039 | `feat/session-tool-policy` | controller + transport + opt-in approve-all, decision record as activity |
| abstractassistant (desktop) | — | `feat/session-tool-policy` | grant/revoke through the route, decision record as activity |
| abstractassistant (iPhone/watch) | 1062 | — | follow-up: `AssistantStore.approveAll` / `applyConversationTrust` |
| abstractcode (web, terminal) | — | — | follow-up: stop sending every enabled tool as `require_approval_tools`; use the route through panel-chat's `sessionPolicy` option |

## Related

- [0993](0993_one_ledger_replay_many_views.md): the shared replay must render
  `abstract.tool_policy_decision` as an activity; this removes one of the client-held states the
  0993 inventory lists ("granted" sets).
- [1056](../proposed/1056_programmable_ai_systems_workflows_as_the_central_primitive.md):
  execution state lives in gateway/runtime, clients forward requests (the same principle).

## Acceptance criteria

- [x] No `approval_required` wait for a call the session approved, root or delegated child; an
      audit record instead (runtime + gateway tests).
- [x] A tool the gateway does not authorize for the account is never covered by "approve all".
- [ ] Runtime released; gateway floor raised; gateway, panel-chat and Assistant released.
- [ ] Live: approve a kind in one client, two other clients connected, no gate appears anywhere.
- [ ] iPhone/watch and AbstractCode moved to the route; their local grants removed.
