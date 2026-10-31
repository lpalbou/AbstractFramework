# 1087 — Cross-device session read receipts

> Package: AbstractGateway, AbstractUIC, AbstractTUI, AbstractAssistant, AbstractCode
> Type: task
> Created: 2026-10-31
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

- [ ] Operator read-scope semantics recorded before server implementation.
- [ ] Read receipt endpoints and event payloads enforce account/tenant isolation.
- [ ] Reading on the chosen scope updates connected clients without clearing human attention.
- [ ] Hidden, offscreen, covered, failed-load and late-concurrent-turn scenarios stay correct.
- [ ] Offline reconnect and principal switching cannot consume another account's content.
- [ ] Native and web integration passes with the same semantic fixtures.

## Receipts

- Shared API and consumption rules: abstractuic/docs/session-cards.md.
- Current tests: ui-kit/scripts/check_session_cards{,_browser}.mjs;
  abstractassistant/web/scripts/check_experience.mjs;
  abstractcode/web/scripts/check_session_cards.mjs.
- ADR state: follow-up proposal; no new server read-receipt policy adopted.
