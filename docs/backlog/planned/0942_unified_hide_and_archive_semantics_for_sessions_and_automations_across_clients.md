# 0942 — One gateway-stored "archive / hide" semantic for sessions and automations, honoured by every thin client

- **Status:** planned
- **Created:** 2026-09-27
- **Area:** abstractruntime (session/automation lifecycle state), abstractgateway (routes, `/runs` and `/automations` filters), abstractassistant, abstractcode, abstractobserver, abstractuic (ui-kit `AutomationPanel`)
- **Parent:** [0928](../completed/0928_automations_v1_runtime_native_scheduled_and_triggered_tasks.md) (Automations v1, completed, UNRELEASED); related [0853](../completed/0853_sessions_are_gateway_first.md)
- **Operator rulings (2026-09-27):** "ALL CLIENTS … MUST have access to the same pool of sessions, all coming from gateway and runtime. THERE MUST BE NO EXCEPTION." · "there must be NO SUCH THING AS SESSION LEGACY." · on the Assistant's automation card Archive control: "we never discussed it, what is that? … a way to 'delete' from the view since we don't authorize deleting from the runtime? if so, the issue is that it is not unified across thin clients, so remove that and write a planned backlog item".

## Summary
Sessions and automations are runtime objects that every thin client lists from the gateway. Today the two have
different end-of-life semantics and neither is a client-independent "hide": an automation can be **archived**
(runtime lifecycle: no further occurrences, the current one finishes, history kept, only Discuss remains, not
reversible), while a session has **no** archive, hide or delete at all (the gateway has no session delete route; the
Assistant's local "remove from the list / sessions-legacy" was deleted on 2026-09-27 because it was a per-client
exception). This item defines ONE gateway-stored semantic for both kinds, so that what one client hides or archives,
every client hides or archives the same way, and so that nothing is ever deleted from the runtime.

## Why
- A per-client hide (a local list of hidden ids) breaks the one-pool rule: the same session is visible in Code and
  invisible in the Assistant.
- `automation.archive` exists and is shown in the Observer and the Assistant's automation view, but the operator did not
  ask for it and its meaning ("delete from the view" versus "stop forever") was not explained anywhere a user sees it.
- Users still need a way to get finished conversations and dead automations out of the default lists without losing
  them, and to bring them back.

## Current code reality (2026-09-27, local unreleased tips)
- Runtime: `automations/commands.py` accepts `automation.archive` (terminal state `archived`, ledger record
  `automation.archived`); no unarchive; sessions carry no lifecycle flag in the run index (`storage/*`).
- Gateway: `POST /api/gateway/automations/{id}/commands` with `archive`; `GET /automations` returns archived rows
  (clients hide them behind "Show archived": Observer `9c45a77`, Assistant `bea7359`); `/runs` has `session_kind`
  filters but no hidden/archived filter; no `DELETE` route for sessions or runs (only visualflows, bundles, admin
  objects).
- Assistant: the automation card has no Archive control (this item's ruling); the automation view still offers Archive
  (with the confirm); the session card has no remove/hide control at all (`bea7359`).
- Observer: Automations page offers Archive; hides archived by default.
- Code: lists every chat session; no hide.

## Scope
### In scope
1. **One state, stored by the gateway/runtime, for both kinds:** `archived` (no further runs for an automation; a
   session simply leaves the default lists) with `archived_at` and `archived_by`, and **unarchive** for both (an
   archived automation returns paused, never active). Nothing is deleted; history, ledger and workspace stay readable.
2. **Runtime:** a session-level flag in the run index (root/turn rows) and the automation state machine gaining
   `unarchive`; ledger records for both; `select_session_turns` unchanged (history is never filtered).
3. **Gateway:** `/runs?archived=false|true|all` (default `false` for chat lists), `/automations?archived=…` (default
   `false`), commands `session.archive|unarchive`, `automation.archive|unarchive`; attention records untouched.
4. **Clients (all of them, same words):** an **Archive** action in the object's own view (not on list cards), an
   **Archived** filter/toggle in every list, **Unarchive** from the archived view; one sentence in each app's docs
   stating that archiving hides and stops, never deletes.
5. **Docs/ADR:** a short ADR ("archive hides and stops; nothing is deleted from the runtime; one semantic for every
   client") referenced by every app's docs.

### Out of scope
- Deleting runs, sessions or automations from the runtime (explicitly refused by the operator).
- Retention/purge policies (separate: gateway maintenance).
- Per-client hidden lists of any kind (forbidden by the one-pool rule).

## Acceptance criteria
- [ ] Archiving a session in the Assistant hides it from the default list in Code and the Observer at the next poll, and
      the reverse; the session's history is still readable by id in every client.
- [ ] Archiving an automation stops future occurrences (as today) and unarchive returns it paused, in every client.
- [ ] `/runs` and `/automations` default lists exclude archived rows; `archived=all` includes them; the flag is in the
      run index (no per-row store read).
- [ ] No client keeps a local hidden list (grep-proven test in the Assistant; review note for Code and Observer).
- [ ] ADR written; each app's docs carry the one-sentence semantic.

## Receipts
- (none yet)
