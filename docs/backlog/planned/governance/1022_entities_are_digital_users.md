# 1022 — Entities are digital users: their own runtime, owner-side operational control, nobody edits their mind

> Package: abstractgateway, abstractruntime, abstractentity, abstractmemory
> Type: task
> Created: 2026-10-15
> Priority: high
> Labels: governance, security, entities, identity, decision-gate, adversarial-review-required
> Track: governance (README rows 19–24)

## Summary

OPERATOR DECISION GATE (never assignable) for Q4, Q5, Q6; the visitor check (row 23) and the
workspace drop (row 22) are buildable now. Today an entity is not a user: its home and run store sit
under its creator's folder and are reached only through the caller's service; the registry's
`runtime_id=<slug>` never exists on disk; an admin gets 404 on entities in user planes, so "suspend"
only switches off a credential (row 19). The creator cannot exercise operational control (state,
tool policy, substrate, loop start/stop, grants, mounts, tasks are admin-only by route pattern; a
creator can archive but not suspend or unarchive; live: all 16 homes have `created_by: null`, row 20).
Admins alter entity data directly — the prompt overlay, memory-candidate promotion, task status, the
shared phase spec (row 21, P0) — and the creator can write files into the entity's workspace with no
gate (row 22, P0). Visit turn/close do not check that the caller is the stamped visitor, so an
admin's words are recorded as the creator's (row 23). An entity never acts under its own principal:
summon runs live in the summoner's plane with actor "gateway", the summoner's workspace policy and
the client's tool policy; nothing applies the entity account's own policy (row 24).

## Why

Operator, 2026-10-15: "an entity is a digital user, and should behave / be treated mostly like a
human user. so the owner of an entity should not be able to alter the entity runtime, but it should
have read-only access to everything the entity has + have operational control over the entity (in
the same way an admin has operational control over all users, except the human user only has control
over its entities. by operational control, i mean the ability to suspend, elevate or decrease
privileges to its entities, to start, pause, stop processes."

## Scope

### In scope
- Row 19: each entity gets its OWN plane (`entities/<slug>` at the gateway level, or
  `users/<tenant>/<slug>` — Q6) with an `owner` pointer; the home, memory, run store and runner live
  there; resolution by slug, never by caller; admin views list it like any plane.
- Row 20: operational verbs (suspend/resume, privilege up/down = tool ceiling and workspace grant
  within the owner's own realm, loop start/pause/stop, process start/stop) open to "admin OR owner";
  the owner is set at creation (`created_by`) and backfilled for the 16 live homes by ruling.
- Rows 21–22: data verbs CLOSED to owner and admin alike per Q5 — for mind writes (prompt overlay,
  memory promotion, tasks, phase spec) the entity proposes, the owner approves, the entity applies;
  the workspace file write becomes an inbox drop the entity moves itself.
- Row 23: visit turn and close refuse unless `principal.user_id` is among the stamped participants.
- Row 24: the entity acts under its own principal: summon and visit runs start in the entity's plane
  as the entity (actor/executor unchanged; requester = the summoner per 1024), with the ENTITY
  account's workspace policy and tool ceiling.
- Owner read-only access to everything the entity has (card, replay, diary redaction as today,
  runs, artifacts, workspace) through the entity's plane.

### Out of scope
- The entity app's own UI; memory blocs (root 1015).

## Decision gates (operator)
- Q4: may an owner archive or delete their entity?
- Q5: which entity writes are privileges (owner) and which are mind (entity only): tool policy, substrate, skills, work order, tasks, prompt overlay, memory-candidate promotion, the shared phase spec?
- Q6: where the entity's plane lives, and whether summon runs are stored in the entity's plane (summoner recorded as requester) or the summoner's.

## Acceptance criteria
- [ ] An entity has a plane of its own; its creator can read everything in it and can suspend, resume, start/pause/stop its loop and change its ceilings within the creator's realm; the creator cannot write memory, prompt overlay, tasks or workspace files directly (matrix test, owner × admin × stranger × the entity itself).
- [ ] A visit turn by a principal who is not a stamped participant is refused (403), and a test deletes the check and goes red.
- [ ] A summon run's ledger shows the entity's plane, the entity's workspace policy and the summoner as requester.
- [ ] Adversarial review of the matrix before merge.

## Receipts
- Audit table: `README.md` rows 19–24 (2026-10-15); live manifests (`created_by: null` on all 16 homes).
