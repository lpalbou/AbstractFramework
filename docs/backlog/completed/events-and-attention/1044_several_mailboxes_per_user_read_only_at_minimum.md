# 1044 — Several mailboxes per user, read-only at minimum

> Package: core, gateway, runtime
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, email, accounts

## Summary

A user registers N email accounts; each has `can_read` and `can_send` (IMAP without SMTP = read-only). `account_id` becomes a parameter everywhere the plane assumed `default` (config file `email/accounts/<id>/abstractcore.json`, `account_store(plane, account_id)`, `EmailPlane.account_ref(account_id)`, one watcher loop over readable accounts), and `email.received@1` takes `account: <account_id>` validated by the host. The occurrence's `_runtime.email_account` is the bound account, so "send from" follows for accounts that can send.

## Why

The operator wants to listen to several mailboxes (v0: read for X configured emails). Today one account per plane is hard-wired in five places.

## Scope

### In scope

- Core mail store multi-account, gateway accounts API and console Accounts page listing N accounts with capabilities, migration keeping `default` as the id of the existing account.
- Watcher per readable account; inbox streams already keyed by `account_ref`.

### Out of scope

- Shared mailboxes across users.
- OAuth providers beyond what the current account model supports.

## Current code reality

- `mail/accounts.py:78` `ACCOUNT_ID = "default"`; `:150-157` single ref and file; abstractcore `store.py:205-222` `settings().account` single dict; `watcher.py:7` one watcher per plane; `email_received.py:231,274-278` `account` enum `["self"]`.
- `models.py:311-316` `can_read`/`can_send` already distinct; `feeder.py:61` streams keyed by `account_ref`.

## Acceptance criteria

- [ ] Two accounts registered for one user (the operator's `test@` and `lpalbou@`), both watched; an automation bound to the second fires on a mail sent from the first.
- [ ] A read-only account refuses sends with a clear error.
- [ ] Existing single-account installs migrate without action.

## Testing

- `cd abstractgateway && python -m pytest tests -q -k 'mail or account'`
- `cd abstractcore && python -m pytest tests -q -k 'mail'`

## References

- Round-2 finding 5.
- [0992](../0992_per_user_email_accounts_and_notifications.md)

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

## Completion report

> Completed: 2026-10-25 18:30:00 +0200
> Original path: `docs/backlog/planned/events-and-attention/1044_several_mailboxes_per_user_read_only_at_minimum.md`
> Final path: `docs/backlog/completed/events-and-attention/1044_several_mailboxes_per_user_read_only_at_minimum.md`

**Outcome.** Several mailboxes per user (read-only by default), Google/Microsoft sign-in for further mailboxes, address-first autodiscovery, folders routes, mailbox ids accepted by email.received@1, batched watcher on one IMAP connection, flags and Gmail labels kept; the operator's Gmail registered live. Tests: mailbox 14, email suites 176–254 per repo.

**Commits.** gateway b21d2345, 88b8fe35, d462c5b2, 9ed00ff0, 3a3d915a, 3c99b771; runtime d590c43, f88a216, a595ace; abstractcore 2142520c, df127af5, b888ccc2 (all local, unpushed, unpublished; per-repo receipts under `untracked/lanes/`).

**Validation.** Lane receipts with per-item mutation checks: `untracked/lanes/L1-runtime.md`, `L2-gateway-triggers.md`, `L3-gateway-events.md`, `L4-flow-console.md`, `L5-consumers-e2e.md`, `UX-A-flow.md`, `UX-O-observer.md`; UX reviews `untracked/ux-review/REPORT.md` and `REPORT-2.md`; live evidence `abstractgateway/untracked/live-email-2026-10-25/`.

**Follow-ups.** See proposed [1050](../../proposed/1050_events_and_attention_follow_ups.md).
