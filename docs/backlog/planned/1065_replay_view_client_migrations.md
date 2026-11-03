# 1065 — Replay view client migrations: every client renders the served view

> Package: abstractuic (panel-chat), abstractcode (web + terminal), abstractassistant (web, desktop, iPhone, watch), abstractobserver, abstractflow, abstractentity, abstractcontinuum, abstractnote (web), abstractgateway (consoles)
> Type: tracking (cross-package migration)
> Created: 2026-10-28
> Priority: high
> Labels: replay, ledger, multi-client, thin-client
> Links: [0993](0993_one_ledger_replay_many_views.md) (one ledger, many views); AbstractRuntime 0854 (`abstractruntime/docs/backlog/planned/0854_replay_view.md`, the inventory of every client's reconstruction path and the migration order); AbstractGateway 0947 (completed: `/runs/{id}/view`, `/view/stream`, cache)

## Summary

The runtime reducer (`replay_view_v1`, AbstractRuntime 0.14.0) and the gateway routes
(`GET /runs/{id}/view` with ETag, `GET /runs/{id}/view/stream` with `Last-Event-ID`) are released.
What remains is the client half: each client replaces its private ledger fold with the served view
and deletes the reconstruction code once it passes the conformance fixtures. This item lists every
client and its state; the per-client code inventory (file and line of each fold) is runtime 0854
§"Client-side reconstruction paths", and its order is 0854 §"In (clients...)".

## Clients and state (2026-10-28)

| # | Client | Renders through | State | Where tracked |
|---|---|---|---|---|
| 1 | panel-chat (`@abstractframework/panel-chat`) | itself | IN PROGRESS by a worker (branch `feat/panel-chat-replay-view`; `WorkflowSessionController` renders the view; `ingestHistory`, `foldRecord`, `adoptDurableWait`, `resolvedWaits`, `foldWorkflowTools` and the 2 s poll go) | AbstractUIC 0040 (on that branch) |
| 2 | AbstractCode web | panel-chat | waits on 1; then `activity_rows` reads `activities[]`; delete `wait_resolution.ts`, `history_bundle_seed.ts`, `subworkflow_follow.ts` | 0854 step 1 |
| 3 | Assistant web | panel-chat (since the UI-kit adoption, AbstractAssistant PR #5) | follows 1 by a version bump | 0854 step 1 |
| 4 | Observer, Entity, Continuum, Note web | panel-chat where they embed the chat; Observer's own run steps view separately (row 9) | follows 1 by a version bump; each app's own run pages listed in 0854 | 0854 |
| 5 | Assistant desktop (Python/Qt) | own (`GatewayRunController`, `GatewayWorker`) | not started; closes assistant 0008's replay findings | 0854 step 2; AbstractAssistant 0008 |
| 6 | iPhone and watch (Swift `AbstractGatewayClient`) | own | not started; the watch's per-key resolution is the closest to the reducer | 0854 step 2 |
| 7 | AbstractFlow run views | own (`executionIdFor`, `ledgerEvents.ts`) | not started; `activities[].execution_id` replaces `executionIdFor` | 0854 step 3 |
| 8 | AbstractCode terminal (Rust) | own (`transcript.rs` fold, bundle merge in `runner.rs`) | not started | 0854 step 4 |
| 9 | AbstractObserver run steps | own | not started | 0854 step 3 |
| 10 | Gateway web console and terminal console | own | not started; status, interaction and run tree only | 0854 step 5 |

## Chosen route

The order of 0854 (server-side projection, option a): panel-chat first because it carries rows 2-4 by a
version bump; then the native clients (5, 6) that need no reducer port, only the stream; then Flow and
Observer; then the terminal and the consoles. A client keeps only what it decides to show and how it
forwards a request; nothing derives status, waits or tool rows on the client.

## Open decision

- The conversation list and its counts are out (gateway 0939); 1063 (typed runs) adds `run.type` /
  `run.origin` to the view, which the clients read once both land.

## Acceptance criteria

- [ ] Each row above: the client renders `replay_view_v1`, passes the runtime's conformance fixtures, and its private fold is deleted (a grep proves it).
- [ ] Two clients of different kinds open the same delegated run tree and show the same status, interaction and tool rows (0854's incident table replayed).
