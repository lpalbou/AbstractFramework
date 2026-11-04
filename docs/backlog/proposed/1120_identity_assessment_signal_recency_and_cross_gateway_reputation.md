# 1120 — Identity follow-up: an assessment signal, recency weighting, colleague notes on entities, cross-gateway reputation

> Package: AbstractRuntime, AbstractGateway (and the apps that show reputation)
> Type: task
> Created: 2026-11-04
> Priority: normal
> Labels: entities, identity, reputation, follow-up
> Follows: [1119](../planned/1119_digital_identity_avatar_voice_fingerprint_track_record_reputation.md); [ADR 0052](../../adr/0052-digital-identity.md) §5–§6 and "Out of scope"

## Summary

The follow-ups named by 1119 and ADR 0052, not built in that wave: an assessment signal for the quality of a run's
work (`POST /runs/{id}/assessment`, recorded as `_meta.assessment`, counted in `TrackRecord.assessed` and as a
success/failure signal), recency weighting of trust, colleague notes on entities, and cross-gateway reputation with
[1112](1112_cross_gateway_entity_federation_handshake_keychain.md).

## Why

Until an assessment exists, "success" means "the run completed" (ADR 0052, Consequences): an entity that completes
every run with poor work keeps a perfect record. The operator's article asks for "a quality assessment of the work"
and reputation "over time".

## Scope

### In scope

- The assessment route and record, its place in the track record and the trust formula, and its evidence row
  (`signal: assessment`).
- Recency weighting of trust, deterministic and stated in the reputation it produces.
- Colleague notes on entities; cross-gateway reputation designed with 1112.

### Out of scope

- Anything 1119 delivers.

## Acceptance criteria

- [ ] To be written when this item is planned (ADR 0052 amended first where the trust rule changes).

## Receipts

- 1119 "Follow-ups"; architect draft `untracked/release-2026-11-03/identity/BACKLOG-draft.md` (root, untracked).
