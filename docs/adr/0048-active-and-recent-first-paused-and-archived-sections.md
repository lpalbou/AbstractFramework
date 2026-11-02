# ADR 0048: Lists show what is active and recent first; paused and archived live behind their own sections

Status: Accepted — operator ruling 2026-11-02.

## Context

On 2026-11-02 the Apple Watch's Automations list opened on two automations the operator had paused
weeks earlier ("Consolidate my notes", "Reflect on my notes": "Paused", 0 runs), while the
automations that run every day sat below them. The gateway listed automations newest-created
first, so whatever was created last led the list whatever its state, and each app then drew the
rows in that order or applied an order of its own (the tray grouped by status, other apps did
not). The operator asked for one behaviour everywhere:

> "for the watch, in terms of visibility, i would first show the automation that are still active
> and the ones with the most recent updates first. then i would have a section 'paused', like
> 'archived' where i can access those automations that are paused. it allows to keep things clean
> and to first show what's important. this behavior should be replicated across all thin clients /
> apps that shows sessions and automations"

Two earlier rulings bound the answer: every client lists the SAME pool from the gateway and only
interprets it to draw its view, with no business logic in thin clients (2026-09-27, 2026-10-01);
and archive hides, it never deletes (round 5, 2026-10-04: `Archived · N` footer on both lists).

## Decision

1. **The gateway owns the order and the grouping.** Lists are served already ordered, and each row
   says which section it belongs to. Clients render the order as served; they never re-sort by a
   rule of their own and never infer a section from anything but the served fields. A client that
   merges pages or live updates into a list it holds may re-apply the served key
   (`last_activity_at` for automations, `updated_at` for sessions), newest first, and nothing else.
2. **Automations** (`GET /api/gateway/automations`, AbstractGateway `automation_order.py`):
   - Order: automations that are neither paused nor archived (status `active`, `completed` or
     `failed`) by `last_activity_at`, newest first; then paused automations the same way. Ties are
     broken by `automation_id`, descending, so the order is total and stable.
   - Every `AutomationSummary` (the listing and `GET /automations/{id}`) carries
     `section: "active" | "paused" | "archived"` and `last_activity_at`: the automation's last
     change as its controller run recorded it (`updated_at`: an occurrence admitted or finished, a
     pause or resume, a revision, an archive). It is defined once, in the gateway; widening it
     later (attention, waits) changes no client.
   - Every page carries `paused_automations` beside `archived_automations` (how many of the
     caller's automations are paused and archived, whatever the filter), so a folded section can
     show its count before its rows are read.
   - Archived automations stay their own listing (`archived_only=true`), in the same order.
   - The keyset cursor pages that same order. The key follows activity, so a row that changes
     between two page reads can move; a client that reads several pages keeps one row per id.
3. **Sessions** (`GET /api/gateway/runs?root_only=true`): turns come most recently updated first,
   so a client folding rows by `session_id` lists the session with the latest activity first, and a
   new turn moves its session to the top. Archived sessions stay their own listing
   (`archived_only=true`, counted by `archived_sessions`). Sessions are never paused.
4. **Clients draw three places, in this order:** the active rows; a **Paused** section (automations
   only), folded by default and labelled like Archived (the pause glyph, "Paused" and the count);
   the **Archived** section as each app has it today. A folded section opens on a tap and its
   rows are the same cards as the active rows. End-user copy is plain: "Paused", "Archived", no
   status codes or field names.
5. **Older gateways degrade to today's view.** A client that receives no `section` draws the list
   as it did before (no Paused section, the served order), so released apps and new apps both
   work against gateway 0.19.0 and earlier. It never reconstructs the rule from `status` and
   `updated_at` on its own.

## Consequences

- Positive: every app opens on what runs and what changed last; paused automations are one tap
  away, never lost; the rule lives in one gateway function and every client is a renderer of it.
- Positive: the gateway answers a listing with one controller load per automation (it already
  loaded them all for the archived count) and projects only the page's rows.
- Negative: the order is mutable, so keyset paging is exact only for a stable snapshot; a client
  that pages dedupes by id. Cursors issued before this change (`auto1:`) are refused with 422
  `invalid_request`; the client restarts from the first page.
- Negative: an automation that completed or failed (it can never run again but nobody archived it)
  is drawn among the active rows, where its status pill says what it is. A separate "Ended"
  section is a later decision, not part of this rule.
- Neutral: `status` keeps its meaning; `section` is the drawing contract.

## Enforcement

- Code review: a client list of sessions or automations that sorts the served rows by anything but
  the served key, or derives a section from `status`, is rejected; a client that needs another
  order asks the gateway for it.
- The gateway's order lives only in `abstractgateway/automation_order.py` (`automation_section`,
  `order_key`, `ordered`, `page`); the tray and every in-repo consumer import it.
- Search `section`, `paused_automations`, `last_activity_at` and `ADR 0048` to find the
  enforcement points in each client.

## Validation

- AbstractGateway: `tests/test_automations_list_order.py` (the rule, ties, paging at several
  limits, cursor refusals; live: run now moves a row up, pause moves it to the paused section,
  resume brings it back, a paged walk equals the unpaged order, archived rows carry their section)
  and `tests/test_sessions_list_order.py` (a new turn moves its session to the top; archived
  sessions leave the listing). Mutations: removing the sort or the paused section turns them red.
- Each client: a test or screenshot proving the served order is drawn as-is, the Paused section is
  folded with its count, Archived is unchanged, and a payload without `section` draws today's view.
- Manual: each UI at desktop width and at 400 px; the watch in the simulator.

## Scope

Packages: AbstractGateway (authority), AbstractAssistant (watch, iPhone, desktop, web), AbstractUIC
(shared web pieces), AbstractObserver, AbstractCode (web and terminal), AbstractEntity.

## Backlog links

- Originating work: [1099](../backlog/planned/1099_active_first_paused_section_all_clients.md).
- Related: [ADR 0047](0047-voice-transport-is-never-an-attachment.md) (same thin-client principle:
  the producer tags, clients render).
