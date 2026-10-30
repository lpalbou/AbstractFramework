# 1077 — Reactive session subscriptions across thin clients

> Package: abstractgateway, abstractruntime, abstractcode (terminal + web), abstractassistant (desktop + web + iPhone + watch), abstractuic (panel-chat transport)
> Type: investigation / implementation plan
> Created: 2026-10-30
> Priority: high
> Labels: sessions, subscriptions, replay, thin-client, lifecycle, security, multi-client

## Summary

Give every open session a continuing observer: discover new turns created by any
client, render their authoritative Gateway views, and detach on switch/close
without cancelling durable work. Reuse the existing account event stream, indexed
session roots and canonical run replay. This is not a new push service or broker.
This item is a proposed implementation plan; the investigation changed no
subscription code, Gateway process, operator session or approval.

## Why

Operator, 2026-10-30: a conversation started in Code TUI, continued in systray, then
remained stale in Code. Read-only verification found five completed Gateway root
turns in session acode-93fea9ec452a while Code's screenshot showed four. The newest
root input matched the systray follow-up. The requirement is automatic session
observation for every thin client, with proper cleanup and consistent replay.

## Current code reality — verified 2026-10-30

Inspected trees: Gateway 2d9f8b8f, Runtime d4f0069, Assistant de2c706,
AbstractUIC 4737470, Code ba76dfa. Four workers investigated Gateway, Code,
other clients and adversarial architecture. The Code live check was read-only;
65 existing Gateway event/replay tests passed. A real read_view() probe with a
saved initial prompt and zero ledger records returned that user message before
any inference. Reports: workspace `untracked/session-push-code-investigation.md`;
precise source evidence below. Do not infer Apple parity merely from APNs.

| Layer/client | Existing behavior | Gap |
|---|---|---|
| Gateway account stream | GET /me/events plus /me/events/stream, caller-scoped durable CloudEvent pointers with session_id/run_id | Discovery/invalidation, not a session projection; no retained-floor/store-generation reset contract |
| Canonical run replay | Runtime replay_view_v1, Gateway GET /runs/{id}/view and /view/stream, shared server fold/fan-out | A run stream ends when that run tree finishes; cannot discover the next root |
| Live tokens | llm.delta/llm.delta_end and call snapshots multiplexed on ledger/stream | Canonical view/stream currently lacks this transient overlay; migration must preserve it |
| Code TUI | Per-run ledger stream plus account events folded into EventAttention | No selected-session reconciler; terminal follow ends; events do not adopt external roots |
| Code web / Assistant web | Conversation list refreshes on events | Selected run ID can remain pinned to the old root |
| Systray | Matching lifecycle pointers coalesce a 50 ms active-session history refresh, then reconcile/reattach | Closest reusable pattern, still embedded in Qt application orchestration |
| iPhone/watch | Account attention/APNs plus known-run following/polling and explicit open-session history loading | Not complete ordinary selected-session observation |

Additional correctness issues to include:

- Code switch_session currently sends Cancel for an active old run. Unsubscribing
  a view must instead detach; explicit Stop remains the cancellation operation.
- Code Fold.begin_run/attach replace single-root state and clear followers/waits.
  Gateway currently permits concurrent roots. Repeated ProbeAttach or newest-wins
  can discard a different active run and its approval. Never fix discovery this way.
- Code account callbacks lack apply-time generation/principal guards; cursors and
  attention state are not fully scoped/reset across principal changes. The current
  five-minute input heuristic/60-second away catchup is not an open-session lifecycle.
- Swift userEventStream buffers 256 events but ignores continuation.yield drops;
  its existing run stream already throws/reconnects on overflow. Silent loss is
  incompatible with advancing a durable cursor.
- run.started is normally published after a runner tick. A blocked first effect
  can delay discovery even though the initial user message is already persisted.

## Boundaries and alternatives

| Alternative | Benefits | Risks / verdict |
|---|---|---|
| A — one account connection + reusable SessionObserver + canonical per-root views | Reuses working transport, store indexes and replay hubs; no new service or session wire schema | Recommended first implementation, provided observer logic lives once per language adapter and passes shared conformance fixtures |
| B — Gateway session view/stream composing existing hubs | Simplest clients and central ordering/multi-root composition | Keep as a bounded next step if A duplicates substantial semantics; requires a new snapshot/delta/cursor/pagination lifecycle contract |
| Full refresh on every event / newest-root attachment / new broker | Small initial patch or fashionable transport | Reject: repeated ledger reads, lost waits/drafts, duplicate history or a second infrastructure owner |

A SessionObserver owns subscriptions and presentation cache, not workflow
semantics. It consumes server-produced run views as part of existing [1065](../planned/1065_replay_view_client_migrations.md). It must
not become another raw-ledger reducer. Account events are invalidation hints;
indexed roots and canonical run views remain authoritative. Notifications and
APNs wake/delivery stay separate (1058); a transcript replay is not a fresh notice.

Proposed logical flow (not a new endpoint):

```text
one authenticated account SSE connection
               |
      selected-session interest + generation
               |
      bounded/coalesced indexed-root reconciliation
               |
      root_id -> canonical view + durable cursor
               |                      |
           renderer          transient token overlay

switch/close -> drop interest + cancel reads/streams + reject queued callbacks
               (durable runs keep executing)
```

## Proposed lifecycle contract

1. Scope identity to Gateway/runtime plane/principal/session and allocate an
   observer generation. Auth/plane changes invalidate all old work and cursors.
2. Register interest/capture account head before the initial authoritative root
   snapshot. Retain invalidations during hydration; do not snapshot first then
   skip to a newer head. Existing loaded content stays visible during catchup.
3. Reconcile bounded recent history and every relevant active root. Page older
   history explicitly. Missing entries outside a page are not deletions. Use stable
   IDs and Gateway ordering; timestamps alone are not causal cursors.
4. Maintain a per-root projection map. Open existing canonical streams for active
   roots, fetch terminal final views once, release terminal streams, and retain a
   bounded presentation cache. Keep one metadata read in flight; dirty changes
   coalesce and request one follow-up pass. Unrelated-session events do no reads.
5. Observation and command targeting are separate. Preserve all active roots and
   interactions. Never retarget an approval/steer implicitly when another root
   appears. If sending is ambiguous, expose an explicit target choice. Do not
   impose one-active-root-per-session merely to hide the current Fold limitation.
6. Account sequence, per-run durable cursor and transient call positions remain
   separate. No token frame may advance a durable cursor. Duplicate/out-of-order
   delivery and own-start-response versus observed-start races must not duplicate
   optimistic prompts or finals; do not deduplicate by message text.
7. On reconnect/resume/gap, reconcile the authoritative session index and resume
   known run views. Overflow is explicit and forces replay. A cursor above head
   after store restore must reset, not silently follow forever. Specify additive
   stream generation/retained-floor/reset semantics before claiming lossless
   recovery across retention or store replacement.
8. Selected-session interest stays live while the connected view is open, even
   without keyboard input. Mobile suspend follows OS lifecycle; wake reconciles
   through the same contract. One account connection can still serve attention.
9. Switch/logout/quit drops the session listener and invalidates its generation
   immediately, aborts owned requests and closes streams within a tested bound.
   Shared account SSE stays only when another consumer needs it. Detach does not
   cancel a run, approve a gate, consume attention, or auto-play restored replies.
10. Keep drafts, scroll anchors and still-valid interaction identities. A historical
    replay cannot raise fresh notifications or read-aloud; new external live turns
    are distinguished from recovery. Expose syncing/offline/forbidden honestly.

## Implementation sequence and package/file map

| Phase | Tasks / files | Gate |
|---|---|---|
| 0: contract and fixtures | Shared run/session observation cases, existing replay conformance from 0993/1065; specify multiple-root targeting and cursor scopes | No latest-wins or second reducer; all origins/planes inventoried |
| 1: publication and transport safety | Gateway events_stream.py, hosts/bundle_host.py, runner.py; routes/me_events.py reset/retention behavior; Swift GatewayClient.swift overflow handling | Prompt discoverable before blocked inference; idempotent pointers; no auth/cursor/overflow loss |
| 2: Code observer + canonical-view adoption | tui/src/gateway/me_events.rs; proposed tui/src/gateway/session_observer.rs; runner.rs, store.rs, transcript.rs, ui/mod.rs, lib.rs; existing 1065 Code migration | Per-root state, exact waits/command targets, detach-not-cancel, no full ProbeAttach refresh loops |
| 3: other language adapters | Python abstractassistant/abstractassistant/gateway/session_observer.py (proposed), abstractassistant/abstractassistant/app.py; Swift AbstractGatewayClient/SessionObserver.swift (proposed), PhoneAssistantKit/AttentionFeed.swift + AssistantStore.swift, watch AskView.swift; TS shared transport beside panel-chat/workflow_runtime.ts and app selection bindings | Code↔systray↔phone↔watch↔web cross-client scenarios pass; generic UI widgets stay transport-free |
| 4: resilience/scale and docs | Reconnect/gap/retention/cancellation/authorization suites, listener/thread/byte/read-count benchmarks, api/architecture/SDK docs and 1065 tracking | No silent loss, unauthorized exposure, idle history polling or resource leaks |

Publication must occur after finalized identity/ownership/session metadata is
persisted, before execution. For ordinary API/bridge starts, the smallest host
point is BundleHost.start_run after its final session_id save and before listener
children are synchronously ticked. Keep runner publication/boot repair idempotent.
This host does not cover native automation discussions, Runtime subworkflow
occurrences or entity visits. Inventory and test those direct start paths, then
choose explicit shared publication calls or a generic post-create hook with
finalized metadata. Runtime._start_run has no such observer today. A host-only
fix must not claim universal origin coverage; never publish to a guessed owner.

Canonical-view migration must retain token streaming. Prefer multiplexing the
existing live hub into canonical view/stream, with separate transient identities
and reconnect snapshots; alternatively retain a clearly isolated live-only
transport during migration. Do not reintroduce durable workflow reduction in the
client just to display streaming tokens. This choice is a phase 0 design gate.

## Security, performance and operational gates

- Session/run reads and stream admission enforce principal/runtime-plane access;
  a session_id, event payload or origin/client hint never grants authorization.
  Reusing an account stream is not proof of cross-principal shared-session delivery.
- Recheck scope at UI callback application; isolate credential changes, sign-out
  and cursor namespaces. Preserve Swift redirect protection; do not follow an
  event-supplied arbitrary URL with credentials. Define revocation behavior for
  long-lived streams; 401/403 stops/reconciles rather than busy retries.
- Bounded frames, queues, page sizes and stream fan-out. Slow consumers cannot
  silently skip events. Stream overflow disconnects with a recoverable contract.
- No per-token account-event publication, full-history scan per invalidation or
  new broker/daemon/model owner. Reuse canonical run hubs so replay is folded once.
- Existing same-process account append listeners wake immediately; cross-process
  account fallback checks at 1 second and canonical replay at 250 ms. Measure these
  separately; do not promise zero latency or increase polling globally without
  evidence. API/schema identity work 1063 can progress independently.
- Existing TypeScript transport duplication is tracked in AbstractUIC 0025. Use a
  shared nonvisual module now; do not force a new package extraction for this fix.

## Acceptance criteria

- [ ] Code starts a session, systray continues it, Code sees each request/reply without reopening; repeat with native/web clients, including a finished old root.
- [ ] A new root and its initial prompt appear before a deliberately blocked first inference returns; no first-tick discovery delay.
- [ ] Two concurrent roots retain both views, streams and exact approval identities; resolving one gate remotely leaves a subsequent/new gate visible everywhere.
- [ ] Snapshot/head, own-start-response and invalidation-during-read races do not lose or duplicate turns.
- [ ] Session A→B→A and signout/account/plane changes reject queued old callbacks; switching observes without cancelling durable work.
- [ ] Reconnect, sleep/wake, retained gaps, cursor beyond head/store replacement, malformed frames and slow-consumer overflow recover explicitly.
- [ ] Initial/history recovery does not resend consumed notifications or read historical replies aloud; attention acknowledgement remains explicit.
- [ ] Repeated switching/closing returns socket/listener/thread counts to baseline within a bound; no duplicate account connections for separate app consumers.
- [ ] Unauthorized session/run/plane access and revoked authorization cannot leak content or reuse a previous principal's cursor/state.
- [ ] Idle selected sessions perform no full-history polling; bursts coalesce, unrelated events do no reads, long sessions page and cache within measured limits.
- [ ] Same-process and split-process latency measured independently; original five-vs-four regression has a red-before/green-after multi-client test.

## Decisions, dependencies and non-goals

ADR state: 0993 and existing replay ownership remain authoritative. Before new
public observer/reset schema or durable cursor spellings are implemented, record
and review their exact semantics in the relevant Gateway/SDK ADR. This proposal
is not a new standing policy or permission to change run admission semantics.

Depends on the scoped Code portion of 1065, not completion of every unrelated
migration. Coordinate 1063/1064 where type/concurrency contracts intersect; do not
block the ordinary-session repair on full taxonomy or queryable-runtime cleanup.
1058 remains notification delivery; this is foreground data synchronization.
Shared presentation identity (Code 0018), bounded side-history access (0019) and
comment ownership/global dedup (0020) remain separate. No new service, database,
provider, model pool, OS push dependency, release or Gateway restart in this pass.

## Receipts

- Four read-only worker reports in this session: Gateway 65-test contract audit and empty-ledger initial-prompt probe; Code live 5-vs-4 verification; Swift/Python/web inventory; adversarial A/B architecture review.
- Source anchors: Gateway events_stream.py398/406/445, routes/me_events.py116, runner.py3053, hosts/bundle_host.py3458–3544, replay_view.py104, routes/replay_view.py85; Runtime replay/view.py148/1102 and core/runtime.py1737/5044.
- Client anchors: Code gateway/me_events.rs98/106, runner.rs2409, transcript.rs824, ui/mod.rs2055; systray app.py6711/7950/8068; Swift GatewayClient.swift328/334/356, RunLedgerStream.swift51; phone AttentionFeed.swift203, AssistantStore.swift581/781; watch AskView.swift816/1011; Assistant web useConversations.ts77, App.tsx64/103; Code web workspace/app.tsx747.
