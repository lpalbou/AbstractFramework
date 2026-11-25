# 1346 — An account marked read-only can still write its own conversations

> Package: abstractgateway (security/authorization.py, security/gateway_security.py, route policy)
> Type: bug
> Created: 2026-11-25
> Priority: high
> Labels: security, authorization, scopes, accounts, gateway

## Summary

An account whose role is `readonly` and whose only scope is `gateway:read` can rename (`PUT
/api/gateway/sessions/{session_id}/title`, 200) and archive (`POST /api/gateway/sessions/{session_id}/archive`,
200) its own conversations, and passes authorisation on `POST /api/gateway/runs/start`. Scopes are consulted
only after the admin gate, and the one place that authorises routes always asks for an admin, so a scope never
restricts a user-level write. Found on 2026-11-25 by the adversarial review of the session-title route
(backlog 1343). It predates that route: titles are no weaker than archive.

## Why

"Read-only" is a promise to whoever creates the account. Today an account can be read-only in name and still
start runs, which spend models and tools, and change its conversations. A security setting that does nothing
is worse than having none, because people rely on it.

## Current code reality (audited 2026-11-25, abstractgateway `origin/feat/session-title` 1532e978)

- `src/abstractgateway/security/authorization.py:378-396` `authorize_gateway_principal`: an admin passes
  (`:388-389`), a cross-tenant target is refused, then `if admin_required:` refuses (`:392-393`), and only after
  that are the scopes read (`_scope_allows(tuple(principal.scopes or ()), ...)`, `:394`).
- `src/abstractgateway/security/gateway_security.py:1418-1423`: the security middleware calls
  `authorize_gateway_principal(..., admin_required=True)` for every route with a policy row. It is the only call
  site in `src/` (`require_gateway_authorization`, `authorization.py:399`, is called only by itself at `:407`).
  Admin routes are refused to non-admins there; for every other route the scopes are never consulted.
- Scopes exist on accounts: `src/abstractgateway/users.py:270` (`scopes: tuple[str, ...]`), set on create and
  update (`:638`, `:686`). The loopback read-only principal is `roles=("readonly",)`, `scopes=("gateway:read",)`
  (`security/principal.py:90-103`).
- User-level write routes reached by such an account include `routes/session_titles.py:57`
  (`/sessions/{session_id}/title`), `routes/session_archive.py:117` (`/sessions/{session_id}/archive`) and
  `routes/gateway.py:9516` (`POST /runs/start`).
- `tests/test_gateway_route_authorization_contract.py` checks that every write route has an authorisation
  decision (`:600`) and that non-admins are refused on admin policy families (`:714`), but nothing about scopes.
  Its `test_user_accounts_off_a_non_admin_session_reaches_no_write_route` (`:849`) was reported by the review
  as failing on the release baseline with a capability-defaults payload mismatch (not re-run for this item).

## Scope

### In scope

- Decide, on the record, what `gateway:read` (and role `readonly`) must refuse: at least every write that
  changes the account's own state (start or resume a run, rename, archive, settings, uploads), and say which
  writes stay allowed (signing out, changing one's own password).
- Enforce it in the security middleware for every user-level write route (scopes consulted when
  `admin_required` is false, or a separate read-only check before the route), with one sentence and a
  `reason_code` on refusal.
- A contract test that enumerates every write route from the app and asserts a `gateway:read` account is
  refused on each, except a named, reviewed allow-list.
- Fix or explain the existing failure of `test_user_accounts_off_a_non_admin_session_reaches_no_write_route`.
- Docs: `docs/security.md` (roles and scopes), the console's account page wording.

### Out of scope

- New scope names or a full permission model.
- Admin accounts (unchanged).

## Acceptance criteria

- [ ] A `readonly` / `gateway:read` account gets 403 on `PUT /sessions/{id}/title`, `POST /sessions/{id}/archive`
      and `POST /runs/start`, and on every other user-level write the contract test enumerates, except the
      reviewed allow-list.
- [ ] Its reads (`GET /runs`, search, a conversation's turns) still answer 200.
- [ ] A member account with default scopes is unaffected (its writes still pass).
- [ ] The contract test fails when a new write route is added without a decision for read-only accounts.
- [ ] `test_user_accounts_off_a_non_admin_session_reaches_no_write_route` passes, or its failure is explained
      and fixed in the same change.

## Testing

- `python -m pytest tests/test_gateway_route_authorization_contract.py tests/test_session_titles.py tests/test_session_archive.py -q` (abstractgateway)
