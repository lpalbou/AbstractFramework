# 1019 — Admin identity and the gateway home: every admin owns a runtime; the gateway home holds no runs

> Package: abstractgateway
> Type: task
> Created: 2026-10-15
> Priority: high
> Labels: governance, security, identity, decision-gate, adversarial-review-required
> Track: governance (README rows 1–5, 15)

## Summary

OPERATOR DECISION GATE (never assignable) for M1 and Q7/Q10/Q12; the rest is buildable once ruled.
Today "admin" is an identity, not a power: `admin@default` with runtime `admin`/`default` is routed
to the gateway ROOT folder, which is also where `users/` (every plane), `entities/`, `auth/users.json`,
sessions, `audit_log.jsonl`, the backlog queue, the default tool grant, the MCP registry and skills
live (README rows 3, 15). The static operator token, the tray's ephemeral token and the registry
admin all resolve to that same principal, so their actions cannot be told apart. Any number of admin
accounts can be created (row 1); a second admin gets a plane but its cross-plane views are computed
from its own folder and the `/host/runs` cache key ignores the principal (row 2); in single-user
mode every admin shares one plane (row 4); admin power is not bounded by tenant (row 5).

## Why

Operator, 2026-10-15: "one admin should have its own runtime"; "if we have multiple admins, they
should each have their own runtimes, as the goal is to differentiate the actions of different admins
and to consider 'admin' more based on the power they are given"; "runtime should be owned and should
be the isolation layer of what a user do".

## Scope

### In scope
- Separate the GATEWAY HOME (users registry, sessions, audit log, catalog, tool-grant default, MCP
  registry, skills, backlog queue) from any admin's plane: the root keeps no run store.
- Every admin principal — registry admin, static operator token, tray helper — maps to an OWNED plane
  under `users/<tenant>/<runtime_id>`; default `ABSTRACTGATEWAY_ADMIN_USES_DEFAULT_RUNTIME` to false;
  migrate the root's existing runs into `users/default/admin/runtime` with a one-off, audited move.
- Admin views (`/admin/runtimes`, drill-ins, `/host/runs`) are computed from the gateway home, not
  the caller's folder; the `/host/runs` cache key includes the principal.
- Single-user mode: exactly one admin identity (or the mode is declared out of the model — Q12).
- Tenant scope of admin power per the ruling (Q3): `_require_admin_principal` compares tenants.
- One-admin cap per the ruling (Q10): refuse a second enabled human admin (409 `one_admin`) or drop M1.

### Out of scope
- What admins may do in other planes (1020); plane isolation for tools (1021); entities (1022).

## Ruling taken (2026-10-15)
- "Admin is a user with admin powers": the admin gets a normal owned runtime like everyone else; the gateway folder keeps only gateway files. Rows 3, 4, 15 are buildable (Q7 answered for the registry admin; the static token and tray map to that admin).

## Decision gates (operator)
- Q7: are the static token and the tray a distinct admin with its own plane, or "system"?
- Q10: is "one admin" a hard cap?
- Q12: is single-user mode covered by the model?
- Q3: is the admin realm per gateway or per tenant?

## Acceptance criteria
- [ ] A fresh gateway starts with a gateway home and NO run store at the root; the admin's runs live in its own plane; `GET /me` for the static token, the tray and the registry admin report distinct runtime ids (or one, if Q7 rules "system").
- [ ] `/host/runs` and `/admin/runtimes` list every plane from the gateway home; two admins never see each other's cached payload (test with two principals).
- [ ] Migration of an existing root run store is reversible and audited; the stranded `users/default/admin` plane (live) is reconciled.
- [ ] Adversarial review of the plane routing after the change (Alice/Bob/admin matrix extended with a second admin).

## Receipts
- Audit table: `README.md` rows 1–5, 15 (2026-10-15, evidence file:line per row).
- Live: `GET /api/gateway/me` (users mode, per-principal routing, principal `admin/default`, source `legacy-token`); `GET /admin/runtimes` (stranded plane `users/default/admin`).
