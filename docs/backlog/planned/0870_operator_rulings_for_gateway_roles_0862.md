# 0870 — Operator rulings needed to promote the gateway roles proposal (0862)

> Package: abstractgateway (security, console)
> Type: task
> Created: 2026-09-25
> Priority: normal
> Labels: decision-gate, security, rbac

## Summary

OPERATOR DECISION GATE (never assignable): `proposed/0862_gateway_roles_members_and_admin_authorised_choices.md`
cannot move to `planned/` until three questions are ruled. This gate item exists so the pending
decision is visible on the board; 0862 keeps the full analysis.

## Why

The operator asked on 2026-09-24 whether one member account should be forced to protect the admin
account; mission AA wrote 0862 and found two authorization defects (fixed in abstractgateway 0.4.1,
missions BB and Z). The rulings are the only thing blocking promotion.

## Questions to rule (from 0862 "Promotion criteria")

1. Add a `viewer` role, or only `admin` and `member`?
2. May a member configure their own entities (the entity-mutation rows were signed admin-only)?
3. When the network mode becomes `lan` / `internet`: prompt for a daily-use member account with a
   recorded skip, or require it?

## Current code reality

- abstractgateway 0.4.2: token-only mode admits only admin accounts to the console and the browser
  apps (0.4.1 upgrade note); `PROTECT_READ=0` refused for `lan`/`internet`; route policy table in
  `security/authorization.py` (0146 in progress).

## Acceptance criteria

- [ ] The three rulings recorded verbatim in 0862 and here.
- [ ] 0862 moved to `planned/` (or to `deprecated/` with the reason), overview updated.
- [ ] ADR need decided (0862 says a role set is a cross-task rule).

## Testing

- `n/a` for the gate itself; after promotion, 0862's acceptance criteria carry the tests
  (`python -m pytest abstractgateway/tests/test_gateway_route_authorization_contract.py -q`).

## ADR status

- Governing: ADR-0018, ADR-0021, ADR-0033. ADR impact: needs a new ADR or revision if 0862 is
  promoted.

## Receipts

- `untracked/missionAA/REPORT.md`, `untracked/missionBB/REPORT.md`, `untracked/missionZ/REPORT.md`.
