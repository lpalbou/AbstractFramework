# 1099 — Active and recent first, a folded Paused section, in every app that lists automations or sessions

> Package: AbstractGateway (authority), AbstractAssistant (watch, iPhone, desktop, web), AbstractUIC, AbstractObserver, AbstractCode (web, terminal), AbstractEntity
> Type: task
> Created: 2026-11-02
> Priority: normal
> Labels: lists, automations, sessions, thin-clients, adr-0048
> Status: Planned — merged in every repo (gateway #90, UIC #50, Observer #17, Code #34, Assistant #41); release pending. It stays in `planned/` until root 0.12.1 publishes these merges, then moves to `completed/` with the published versions as evidence.

## Summary

Every app opens its automations list on what runs and what changed last, with paused automations
folded into their own "Paused" section (like Archived), and lists sessions by their latest
activity. The gateway serves the order and the grouping fields; every client draws them as served.
Durable rule: [ADR 0048](../../adr/0048-active-and-recent-first-paused-and-archived-sections.md).

## Why

Operator, 2026-11-02 20:37, with two Apple Watch screenshots of the Automations list opening on
paused automations ("Consolidate my notes", "Reflect on my notes", 0 runs): "for the watch, in terms
of visibility, i would first show the automation that are still active and the ones with the most
recent updates first. then i would have a section 'paused', like 'archived' where i can access those
automations that are paused. it allows to keep things clean and to first show what's important. this
behavior should be replicated across all thin clients / apps that shows sessions and automations".

## Scope

### In scope

- Gateway: `GET /automations` order (active by `last_activity_at`, then paused), `section`,
  `last_activity_at`, `paused_automations_count`; the tray menus; a test pinning the session order.
- Clients: watch, iPhone, desktop Assistant, Assistant web, Observer, Code web and terminal, Entity
  (where they list automations or sessions): the served order, a folded Paused section with its
  count, Archived unchanged, today's view when the gateway serves no `section`.

### Out of scope

- A separate "Ended" section for completed or failed automations (ADR 0048, Consequences).
- A session-level listing route (sessions stay folded from turn rows).

## Acceptance criteria

- [x] AbstractGateway PR merged on all-green CI (order, ties, paging, pause/resume moving a row).
- [x] Each client: served order drawn as-is, Paused folded with the gateway's count, Archived after
      it, older-gateway payload draws today's view; desktop and 400 px screenshots; watch in simulator.
- [ ] Packages released by the coordinator after the operator's go.

## Receipts

- ADR 0048: https://github.com/lpalbou/AbstractFramework/pull/35 (merge b0c56fb).
- Gateway: https://github.com/lpalbou/AbstractGateway/pull/90 (merge 92454d12): `automation_order.py`,
  `section`, `last_activity_at`, `paused_automations_count` / `archived_automations_count`, tray
  `Paused (N)` submenus. Tests: `test_automations_list_order.py` (15), `test_sessions_list_order.py`
  (1); reviewer's clean comparison 405 passed vs 389 on main, 0 failed. Scratch gateway over HTTP on a
  copy of the operator's 16 automations: 5 active then 5 paused, paged walk (limit 3) = unpaged order.
- AbstractUIC: https://github.com/lpalbou/AbstractUIC/pull/50 (merge 721150a): `AutomationSummary.section`,
  `last_activity_at`, `AutomationsPage` counts (types only).
- Observer: https://github.com/lpalbou/AbstractObserver/pull/17 (merge 0eec679): Paused disclosure,
  served count; 690 passed.
- Code web + terminal: https://github.com/lpalbou/AbstractCode/pull/34 (merge d79160d): `Paused · N`
  footer / line, served count; web 503 passed, terminal 1256 passed, clippy clean.
- Assistant watch + iPhone + desktop: https://github.com/lpalbou/AbstractAssistant/pull/41 (merge
  fcafee6): `AutomationSections` (shared Swift client), Paused screens, desktop switcher
  `Paused · N` / `Archived · N` sections (the filter finds folded rows; "Show archived" removed); Swift
  238 + AssistantKit 231, desktop 1558 passed, watch and iPhone Paused UI tests pass.
- Screenshots: `abstractassistant/untracked/w5-shots/` (watch, phone, desktop),
  `abstractobserver/untracked/w5-shots/`, `abstractcode/untracked/w5-shots/` (web PNGs, terminal text).

## Follow-ups

- Observer and Code web read `section` / `paused_automations_count` through a local cast until their
  next `@abstractframework/ui-kit` bump (types landed in AbstractUIC#50); drop the casts then.
- Assistant web lists sessions only (already newest first by the served `updated_at`); its
  automations surface is lane W10.
- `PhoneUITests.testAutomationFailureShowsCauseAttemptsTimesAndExpandableActivity` fails on main
  (`automation.run.occ-39` not found), unrelated to this item and outside CI's critical set.
