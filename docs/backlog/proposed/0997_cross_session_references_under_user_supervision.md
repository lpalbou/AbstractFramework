# 0997 — Referencing other sessions and their attachments, under user supervision

> Package: abstractgateway (grants, artifact access), abstractruntime (ledger records), abstractuic (panel-chat composer), abstractcode, abstractassistant, abstractobserver
> Type: feature (future, not now)
> Created: 2026-10-01
> Priority: low
> Labels: sessions, attachments, ledger, permissions, ux

## Summary

Let a person point a session at another of their sessions and its attachments, for example
"please consult session @session_id and attachment @img1.jpg to do X", with an explicit,
user-visible grant that is recorded in the ledger and can be audited and revoked. Until this
exists the rule stays: **a session sees only its own** inputs, attachments and history, enforced
by the server.

## Why

Operator (2026-10-01), after the cross-session attachment bleed of AbstractCode web 0.9.0 (see
[0993](../planned/0993_one_ledger_replay_many_views.md), "thin clients hold no run-input state"):
cross-session use is a legitimate feature, but only when the person asks for it and can see it;
the bleed was the same capability arriving silently.

## Current code reality (2026-10-01)

- abstractgateway @9c7475c (round 3, unreleased): a session-private artifact (owned by a session
  memory run or tagged `kind=attachment`) referenced by a run of another session is refused with
  a typed 400 `artifact_not_in_session`. Before it, any same-user artifact ref was accepted.
- No grant record, no `@session` / `@attachment` reference syntax, no composer picker for other
  sessions' attachments.

## Scope

### In scope

- A typed reference (session id, artifact id) the composer inserts from a picker, never parsed
  out of free text by heuristics.
- A grant ledger record on the referencing session (who, which session/artifacts, scope, time),
  shown in every client as a visible chip/row; revocable; replayable through the 0993 contract.
- Gateway check: a cross-session ref passes only with a live grant on the referencing session;
  otherwise `artifact_not_in_session` as today.
- Same-owner only; cross-user and entity-owned sessions are out of scope for the first cut.

### Out of scope

- Implicit context sharing between sessions; automatic retrieval across sessions.
- Agents or entities granting themselves access (that needs a person's grant).

## Acceptance criteria

- [ ] Design note with the grant record schema and the client affordance, reviewed by gateway + kit.
- [ ] Red-first tests: a ref without a grant is refused; with a grant it is accepted and the
      grant is in the ledger; after revocation it is refused again.
- [ ] Every client of the 0993 audit shows the grant.

## Receipts

- Operator statement 2026-10-01 (round 3); gateway @9c7475c; AbstractCode web round 3 @53b36ae.
