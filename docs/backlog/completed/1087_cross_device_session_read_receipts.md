# 1087 — Cross-device session read receipts

> Package: AbstractGateway, AbstractUIC, AbstractTUI, AbstractAssistant, AbstractCode
> Type: task
> Created: 2026-10-31
> Status: Completed
> Completed: 2026-10-31
> Priority: normal
> Labels: sessions, thin-clients, unread

## Summary

Prepare account-scoped content read receipts across devices, building on shared session cards
and the browser-local implementation. Clarify per-device versus account-wide semantics with
the operator before implementing the server contract.

## Why

Unread content and pending human attention are distinct facts. The operator requested compact
Watch-style cards in Code and Assistant, with unread highlights and orange human attention.
The Watch currently tracks per-device read state. The new web clients share receipts on one
browser origin but do not synchronize them with Watch, iPhone or another browser.

## Current code reality

- AbstractUIC owns SessionCard, per-run request/outcome revisions, SessionReadStore,
  useSessionReads, sessionReadTarget and the visibility-gated SessionReadMarker.
- Code and Assistant web consume generated, provenance-checked snapshots pending a UI kit
  release. Root-run content is acknowledged only after a loaded visible outcome is consumed.
- Browser receipts are scoped by Gateway/tenant/user/runtime, bounded to 4096 revisions,
  with a first-use old-history baseline. They are not durable account receipts.
- Gateway attention.seen resolves questions/approvals or automation results. It must not be
  repurposed as a chat read acknowledgement.
- AbstractTUI supplies the equivalent controlled SessionCard presenter. Code TUI has not yet
  adopted unread receipt tracking or the new card presentation.

## Scope

### In scope

- Decide account-wide versus device-specific unread preference and first-use/migration policy.
- Versioned content cursors that preserve late older-turn outcomes and ignore metadata changes.
- Authenticated bounded receipt storage, tenant/account isolation and reconnect catch-up.
- Integrate Code TUI, native Assistant clients and web clients with a common transport contract.
- Replace compatibility snapshots with released UI kit dependency floors when available.
- Receipt retention/compaction that does not turn read old content unread on metadata changes.

### Out of scope

- Resolving human approvals or changing notification delivery when viewing messages.
- New general push transport; coordinate with 1077 and the existing per-user event feed.

## Acceptance criteria

- [x] Operator read-scope semantics recorded before server implementation.
- [x] Read receipt endpoints and event payloads enforce account/tenant isolation.
- [x] Reading on the chosen scope updates connected clients without clearing human attention.
- [x] Hidden, offscreen, covered, failed-load and late-concurrent-turn scenarios stay correct.
- [x] Offline reconnect and principal switching cannot consume another account's content.
- [x] Native and web integration passes with the same semantic fixtures.

## Receipts

- Shared API and consumption rules: abstractuic/docs/session-cards.md.
- Current tests: ui-kit/scripts/check_session_cards{,_browser}.mjs;
  abstractassistant/web/scripts/check_experience.mjs;
  abstractcode/web/scripts/check_session_cards.mjs.
- ADR state: follow-up proposal; no new server read-receipt policy adopted.

## Completion report — 2026-10-31

The operator explicitly requested durable account-wide consumption shared by clients. This
supersedes the proposal's clarification gate. Gateway owns an append-only per-principal
conversation read ledger and emits idempotent `session.read` projections to its existing personal
event stream. Execution ledgers and automation attention remain independent. Canonical receipts
survive stream retention and process restart. Request and final outcomes are distinct revisions;
no existing local baseline is uploaded as factual consumption.

AbstractUIC owns the authenticated client, remote read hook and visibility marker. Code and
Assistant web use it, retain unread state on failed/incomplete writes, and refresh on account
events and reconnect. Opening a latest answer acknowledges only loaded history; historical
views cannot clear newer or missing outcomes. Chat wake occurrences follow canonical turn-root
semantics. Watch and iPhone use the same typed API with visible-session/account/lifetime guards;
Watch refreshes on foreground and its 15-second poll. Native binaries require rebuild/install.

Scope refinement: Code TUI has no conversation unread consumer, Qt/tray has automation unread
only, and AbstractTUI already supplies a controlled SessionCard without receipt authority. No
new unread UI was introduced there. Registry publication and dependency-floor propagation remain
release work under 1079 rather than part of this requested local fix.

Validation: Gateway 30 focused/regression tests (14 new), independent-browser consumption/
failure/incomplete-ACK/stale-response/batch/account tests, Code 501 tests, web Assistant 63,
Swift client 203, iPhone logic 231, full panel-chat tests, and both native simulator builds.
Live Code consumption committed two revisions, cleared Assistant's badge and survived reload;
zero browser JavaScript errors. Adversarial review closed historical-batch and stale-view risks.
Also delivered 8px sidebar card gaps/12px Code insets and media-fitted, single-header attachment
modals with verified download/close/mobile behavior.

Docs: Gateway API; AbstractUIC API/session cards; Code web; Assistant API/web/native guides.
Evidence: untracked/shared-session-read-design.md, untracked/native-shared-reads-verification.json,
untracked/shared-reads-scope-note.txt and corresponding local build/test logs.
ADR impact: no new cross-task policy; applies accepted ADR 0018's Gateway ownership through a
feature-scoped documented read API. Follow-up: native device installation and package release
remain deployment/release operations, not claims of completed device rollout.
