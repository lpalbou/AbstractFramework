# 1020 — Admins are read-only outside their own runtime: account parameters and unlocks, never data

> Package: abstractgateway
> Type: task
> Created: 2026-10-15
> Priority: high
> Labels: governance, security, rbac, decision-gate, adversarial-review-required
> Track: governance (README rows 6–12)

## Summary

OPERATOR DECISION GATE (never assignable) for Q1, Q2, Q11; the P0 rows are buildable now.
Today an admin can act AS any user and can WRITE into any user's plane: `PATCH /admin/users/{id}`
with `rotate_token`/`token` returns another account's token (row 6, P0); a plane on disk with no
reservation can be adopted by a new account and a plane can be rebound or transferred with its runs,
sessions and memory (rows 7–8, P0); turning a workflow's availability off writes pause commands and
a reasons file into every user's plane (row 9, P0); `PUT /sessions/{id}/workspaces?account=`
rewrites another account's session workspace setting (row 10, P0); an admin can purge any plane's
data homes (row 12). Meanwhile there is NO admin path to do what the operator calls "unlock" on a
run in another plane (cancel/resume a stuck run, answer its wait) and admin reads of other planes are
summaries only, with no plane in `observer_path` (row 11).

## Why

Operator, 2026-10-15: "no admin should probably be able to run something on any other runtime, but
they should be able to have read-only access, as well as the possibility to change account
parameters, and unlock certain situations. but i do not think an admin should be allowed to alter
anyone's data, for traceability and auditability reasons."

## Scope

### In scope
- Three admin verbs over other planes, and nothing else: READ (summaries and, per Q11, run content
  and ledgers, read-only), ACCOUNT PARAMETERS (registry fields, quotas, grants, defaults — stored in
  the gateway home, never inside the user's plane), UNLOCK (a closed, audited list per Q1).
- Row 6: never return another account's token; token rotation delivers to the user (mail/recovery
  path) or requires `_same_account`; email changes are audited and notify the old address.
- Rows 7–8: every existing `users/<t>/<rid>` folder counts as reserved (backfill reservations for the
  two live unowned planes); refuse `runtime_id` edits on accounts whose plane exists; `transfer`
  becomes an archive MOUNT (read-only) or is gated on a ruling.
- Row 9: workflow availability is enforced when an occurrence is ADMITTED (refused with a reason the
  owner sees), never by writing into the user's command store.
- Row 10: `?account=` is read-only for admins; admins change account DEFAULTS only
  (`/workspace/policy/{account}`).
- Row 11: a read-only `/host/runs/{plane}/{id}/ledger` (if Q11 says content) and the unlock verbs,
  each one audit line naming admin, plane, run and verb.
- Row 12: purge limited to the gateway home's own data homes.

### Out of scope
- Tool/workspace ceilings (1023); entity ownership (1022).

## Rulings taken (2026-10-15)
- Rows 7–8: a runtime folder is bound to its account forever — never adoptable, never re-bindable; archive read-only only. Buildable now.
- Row 6: ADOPTED — the claim-code design (`evidence/TOKEN-RESET-best-practices.md`): admins only invalidate or regenerate; a one-time, short-TTL, hashed claim code (mailed, else shown once to the admin) is exchanged by the user at sign-in for the real token; audited; claimed-at/from visible to the user; re-issue invalidates; entities and scripts bootstrap the same way. Buildable now.

## Decision gates (operator)
- Q1: the exact unlock list — suspend/resume account, rotate token, host pause, cancel/resume a
  stuck run in another plane, answer a tool-approval wait, clear an entity seat or maintenance hold;
  and whether pausing a user's automation (row 9) is an unlock or an alteration.
- Q2: is a conversation's workspace choice an account parameter or the user's data?
- Q11: may an admin read run CONTENT in other planes, or summaries only?

## Acceptance criteria
- [ ] Alice/Bob/admin matrix: with Bob's run id, the admin cannot resume, cancel, steer, answer, rewrite workspaces, or obtain Bob's token through any route; the matrix lists every `/admin/*`, `/host/*`, `/sessions/*`, `/commands` route with the expected code.
- [ ] Availability off: Bob's next occurrence is refused at admission with a reason on the automation; nothing is written into Bob's plane.
- [ ] Every admin action in another plane produces one audit line `{admin, plane, run_id?, verb}`; a test deletes the audit call and goes red.
- [ ] Adversarial review of the matrix before merge.

## Receipts
- Audit table: `README.md` rows 6–12 (2026-10-15).
- Live: `GET /admin/runtime-reservations` (only `console-e2e-user` reserved; `users/default/admin` and `users/local/local-admin` unowned, 19 MB of ledgers).
