# Proposed: @mention summoning — calling another entity into the room

## Metadata
- Created: 2026-07-08
- Status: Proposed
- Completed: N/A

## Adversarial review (2026-07-08, runtime) — binding corrections
Design record: agora `entity-society` channel. The "first cut through
existing endpoints" is UNSAFE as written and must not ship:
- **The current shared-room path is one home / one writer / one voice.**
  Only the HOST entity forms durable memory; the transcript is
  session-lived, not durable. "Co-presence stamped into every participant's
  memory" is FALSE today.
- **`speaker=` is forgeable** (accepted unverified on `chat/turn`); it
  poisons recall/formation/gradation with unverified co-presence. This must
  be fixed before any entity-entity contact.
- **Honesty primitive = per-home formation under a gateway-minted, MAC-bound
  ROOM STAMP.** Introduce a `RoomBroker` above `EntityChatHost` linking N
  per-home sessions by `room_id`. Two turn kinds: SPEAK (the speaker's own
  home, real LLM) and WITNESS (each other participant's home:
  formation-ONLY from the broker transcript bytes, NO LLM paraphrase — the
  folie-à-deux guard; a listener never generates "what they meant").
- **Consent** reuses the state door (asleep/paused refuse; awake+yielded
  joins); an entity can decline/leave; bounded metronome (turn caps,
  timeouts, skip frozen/asleep). **Diary never enters the room**; strip
  diary fences on every witness/verbatim segment.
- **Smallest safe build:** "Castor + one friend", same gateway,
  operator-mediated; contract test — after one round both homes hold
  episodes with matching `utterance_id` + roster, and neither home has an
  episode written by the other's model for the other's speech.

## Context
The shared-room machinery already exists: `POST /chat/{id}/turn` accepts a
`speaker` (namespace:name), voices join the session's participants, and the
transcript is a common record (maintainer's experiment: "several entities
could come together and have a live discussion" — Castor and Ariadne's
sessions were driven this way by hand).

The maintainer's ask (2026-07-08): "in conversation, we should be able to
summon other entities either by @<name of entities> (would mean on the same
network)".

## Proposal
1. **@mention grammar in the chat drawer**: typing `@ariadne` in a turn (or a
   dedicated "invite" affordance) invites that entity into the CURRENT shared
   room. Resolution: same gateway first (slug match), else a full handle
   (`@ariadne@athena.ovh` → 0214 federation).
2. **The invite is a summon with consent semantics**: the invited entity's own
   loop/state gates apply (asleep stays asleep unless its wake rules say
   otherwise; paused always refuses). The room shows the refusal honestly.
3. **Turn brokering**: an invited entity is DRIVEN — something must call the
   turn endpoint with its voice. First cut: a gateway-side room driver that,
   on each human turn, offers the invited entity one reply turn (bounded,
   round-robin; no free-running cross-talk). The driver is the room's
   metronome; entities never spin unattended.
4. **Memory honesty**: every participant's turn is stamped with the full
   participant list (the co-presence convention) so each entity's own memory
   records WHO was in the room — this already works; the item pins it as a
   contract test for multi-entity rooms.
5. **Leaving**: `@ariadne leave` (or the entity's own elected exit) removes
   the voice from subsequent stamps; the transcript records the departure.

## Boundaries / risks
- One life, one summon holds PER ENTITY: an entity in a room is summoned
  there; its own-time loop yields exactly like a visit.
- Bounded turn offers only — no autonomous entity-to-entity loops in v1 (the
  agora protocol thread 0006 owns the wider choreography question).
- Cue dilution: a room of N voices multiplies stimulus text; recall budgets
  may need the room's turns digested, not concatenated.

## First cut
Same-gateway @mention → invite → round-robin reply offer → stamped turns,
all through the existing shared-room endpoints.
