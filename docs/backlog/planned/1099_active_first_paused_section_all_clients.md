# 1099 — Active and recent first, a folded Paused section, in every app that lists automations or sessions

> Package: AbstractGateway (authority), AbstractAssistant (watch, iPhone, desktop, web), AbstractUIC, AbstractObserver, AbstractCode (web, terminal), AbstractEntity
> Type: task
> Created: 2026-11-02
> Priority: normal
> Labels: lists, automations, sessions, thin-clients, adr-0048

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

- [ ] AbstractGateway PR merged on all-green CI (order, ties, paging, pause/resume moving a row).
- [ ] Each client: served order drawn as-is, Paused folded with its count, Archived unchanged,
      older-gateway payload draws today's view; desktop and 400 px screenshots; watch in simulator.
- [ ] Packages released by the coordinator after the operator's go.

## Receipts

- Gateway PR: https://github.com/lpalbou/AbstractGateway/pull/90
