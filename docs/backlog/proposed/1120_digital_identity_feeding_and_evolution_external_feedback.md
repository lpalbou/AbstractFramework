# 1120 — How the digital identity is fed and evolves over time: external feedback first

> Package: AbstractRuntime, AbstractGateway (and the apps that show the track record and reputation)
> Type: task
> Created: 2026-11-04
> Priority: normal
> Labels: entities, identity, reputation, feedback, follow-up
> Follows: [1119](../planned/1119_digital_identity_avatar_voice_fingerprint_track_record_reputation.md); [ADR 0052](../../adr/0052-digital-identity.md) §5–§6 and "Out of scope"

## Summary

Operator, 2026-11-04 (verbatim): "reputation requires external feedback, provided by users or other agents. we can
discuss it later; create a backlog item so that we later fine tune how this digital identity is fed and evolves over
time."

This item decides, later and with the operator, how an entity's digital identity is fed and how it evolves:

- **External feedback as the primary reputation signal**: ratings and approvals from users, assessments from other
  agents, and colleague notes with an attributed "why", as the agora hub does (per-message ratings collapsed per
  colleague, explainable from its votes).
- **The assessment signal for completed runs**: a quality verdict on a run's work (for example
  `POST /runs/{id}/assessment`, recorded as `_meta.assessment`), counted in `TrackRecord.assessed` and used as an
  outcome.
- **Recency and decay**: how older outcomes weigh against recent ones, deterministic and stated in the reputation it
  produces.
- **The task-kind taxonomy**: which kinds trust is kept for (today `<phase or role>/<workflow_id>`, ADR 0052 §5).
- **Cross-gateway reputation**, designed with [1112](1112_cross_gateway_entity_federation_handshake_keychain.md).

**Until this lands, the numbers ADR 0052 / 1119 compute are completion rates only** (a success is a run, occurrence,
task or work order that completed; a failure one that failed or was blocked). They are not a judgement of the quality
of the work, and every surface that shows them (Entity app, Observer, CLI, gateway routes) says so in plain words.

## Why

ADR 0052 computes trust from records that exist today. A run that completes with poor work counts as a success, so
an entity can hold a perfect record while doing poor work. The operator's article asks for "a quality assessment of
the work" and reputation "over time"; the operator's ruling above makes external feedback the source of reputation.

## Scope

### In scope

- The feedback sources, their record and authority (who may rate what), and how each enters the track record and the
  trust formula, with its evidence row.
- The assessment route and record for completed runs.
- Recency/decay, the task-kind taxonomy, cross-gateway reputation with 1112.
- An amendment of ADR 0052 where the trust rule changes.

### Out of scope

- Anything 1119 delivers (the record, the default, the references, the derived counts).

## Acceptance criteria

- [ ] To be written with the operator when this item is planned (the operator: "we can discuss it later").

## Receipts

- Operator ruling of 2026-11-04 (quoted above), relayed by the coordinator for root PR #54.
- 1119 "Follow-ups"; architect draft `untracked/release-2026-11-03/identity/BACKLOG-draft.md` (root, untracked).
