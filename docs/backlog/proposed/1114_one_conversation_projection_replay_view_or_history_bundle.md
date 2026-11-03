# 1114 — One conversation projection: the replay view or the history bundle

> Package: root (decision), AbstractRuntime, AbstractGateway, AbstractAssistant (watch, phone, desktop, web), AbstractUIC (panel-chat), AbstractCode, AbstractObserver, AbstractEntity
> Type: decision
> Created: 2026-11-03
> Priority: high
> Labels: replay-view, history-bundle, thin-clients, decision-gate
> Status: Proposed (operator decision gate)
> Split from: [1098](1098_typed_voice_block_in_replay_projection.md) (2026-11-03), which keeps the typed `voice` block

## Summary

Two backlog plans tell clients to render a conversation from different sources. 1098, as written on
2026-11-02, makes the **history bundle's session turns** "the ONE conversation projection every client
renders from" and moves panel-chat's earlier turns onto bundle rows. [0993](../planned/0993_one_ledger_replay_many_views.md)
and [1065](../planned/1065_replay_view_client_migrations.md) chose the **replay view** (`GET /runs/{id}/view`,
runtime `replay_view_v1`) and list every client's migration onto it. Neither item cited the other. This
item records the disagreement and the choice to make before either plan moves further.

## Why

- Today seven client lanes read three sources: bundle turns (watch, iPhone, desktop), the replay view
  (web, Entity, Observer) and ledger folds (Code TUI); the watch also mixes in the session listing and
  `run.output`.
- The "one replay, many views" ruling (2026-09-30, and 2026-10-01 "no logic in thin clients") was never
  written as an ADR; ADR 0018 only says "thin clients".
- Every 1065 migration built without the typed `voice` block of 1098 has to be revisited later.

Source: council B findings B1, B4 and B6 (`untracked/council-2026-11-02/council-B.md`) and decision 5 of
`untracked/release-2026-11-03/audit-decisions-site.md`.

## Options

- **A. The replay view is the conversation projection; the bundle is the export and archive** (the
  audit's recommendation): the replay view already carries status, waits, tools and messages for every
  web client. The `voice` block goes on replay-view messages, computed by the same runtime function
  that fills the bundle turn, and 1098 becomes a sub-item of 1065.
- **B. The bundle's session turns are the conversation projection** (1098 as written): the replay-view
  migrations in 1065 are re-planned onto bundle turns.

## Scope

### In scope

- The operator's choice between A and B.
- An ADR "one conversation projection" (root, next free number) that states it.
- Re-scoping 1098 and 1065 to the chosen projection, each citing the other and the ADR.

### Out of scope

- The typed `voice` block itself (1098).
- The voice-transport leak fixes that do not depend on this choice (council B A3, B2: the transcript
  tag and the replay-view voice predicate).

## Current code reality (2026-11-03, from the council B evidence)

- `abstractruntime/replay/view.py` builds the replay view; `abstractruntime/history_bundle.py`
  `_best_effort_session_turns` builds the bundle turns.
- Clients by source: see Why. The Assistant desktop and Code terminal lanes are rows 5 and 8 of 1065.

## Dependencies

- 1098 (typed voice block), 1065 (replay-view client migrations), 0993 (one ledger replay, many views),
  ADR 0018 (thin clients), ADR 0047 (voice transport).

## Acceptance criteria

- [ ] The operator chose A or B; the choice is recorded here with its date.
- [ ] The ADR is written and accepted.
- [ ] 1098 and 1065 are re-scoped to the chosen projection and cite each other and the ADR.
