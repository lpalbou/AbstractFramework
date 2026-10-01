# 0998 — @-mentions of agents and entities from a session

> Package: abstractgateway, abstractruntime, abstractagent, abstractentity, abstractuic (panel-chat composer), apps
> Type: feature (future, not now)
> Created: 2026-10-01
> Priority: low
> Labels: collaboration, agents, entities, agora, mentions

## Summary

From one session, mention other agents and entities (for example `@agent_1`, `@entity_1`) to
involve them in the work: they read the shared context the person allows and contribute turns
that land in the same replayable ledger. This is the session-level face of collaborative
workspaces and of the agora hub integration (how agents and entities work together).

## Why

Operator (2026-10-01): involve other agents and entities from the same context with an
@-mention; relate it to collaborative workspaces and agorahub.

## Related items (read first)

- [0213](0213_at_mention_summoning_in_conversation.md) — @mention summoning of entities: its
  binding adversarial corrections (room broker, MAC-bound room stamp, SPEAK vs WITNESS turns,
  forgeable `speaker=`, consent) apply to any entity mention here.
- [0212](0212_entity_handles_and_summoning_addresses.md) — entity handles are routing labels, not
  identity.
- [0214](0214_cross_gateway_entity_federation_handshake_keychain.md) — cross-gateway entities.
- [008](../planned/008-abstractagent-adopt-the-headless-fleet-bridge-as-abstractagent-s-ready-to-use-collaborative-ag.md)
  — abstractagent as the ready-to-use collaborative (agora) agent.
- [0997](0997_cross_session_references_under_user_supervision.md) — the grant model: an involved
  agent or entity sees only what the person grants.
- [0993](../planned/0993_one_ledger_replay_many_views.md) — every participant's turns replay
  through the one ledger contract.

## Current code reality (2026-10-01)

No mention syntax in panel-chat or the apps; entity shared rooms are one home / one writer (0213);
agora collaboration runs through the hub, outside gateway sessions.

## Scope

### In scope

- Typed mention picker (agents and entities the person can address), never free-text parsing.
- A participation record in the ledger (who joined, by whose mention, what context was granted).
- A decision on the bridge to agora channels (session ↔ channel) versus gateway-native rooms.

### Out of scope

- Agents or entities joining without a person's mention; cross-user or cross-gateway mentions in
  the first cut (0214).

## Acceptance criteria

- [ ] Design note that adopts 0213's corrections and chooses the agora bridge shape.
- [ ] Contract test: a mentioned agent's turn is in the session ledger with its participation
      record, and it cannot read anything outside the granted context.

## Receipts

- Operator statement 2026-10-01 (round 3).
