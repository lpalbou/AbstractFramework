# 1138 — Talk to entities from Code, the Assistant and Notes (`@castor …`)

> Package: AbstractCode, AbstractAssistant, AbstractNote, AbstractGateway, AbstractUIC (panel-chat composer), AbstractEntity
> Type: feature (direction recorded, not scheduled)
> Created: 2026-11-07
> Priority: medium
> Labels: entities, mentions, product-direction

## Operator direction (2026-11-07)

"AbstractEntity is a sandbox to better understand those entities, but the goal is to be able to speak and
interact with them through AbstractCode, AbstractAssistant or even AbstractNote, by referencing them in a
discussion, e.g. `@castor did you see ...`."

## Summary

AbstractEntity stays the place to observe and understand an entity (its card, memory, cognition, identity,
visits). Everyday interaction moves to the apps people already use: in a Code conversation, an Assistant chat
(desktop, web, iPhone, Watch) or a Note capture, `@<entity>` brings that entity into the exchange: it reads what
the person shares, answers in its own voice and identity, and remembers the exchange in its own life.

## Current code reality

- The mechanism is designed, not built: 0998 (`@`-mentions of agents and entities in a session), 1110 (entity
  handles: `<slug>@<gateway>` as a door label, never identity), 1111 (`@mention` summoning; its review found the
  current shared-room path is one home / one writer / one voice and must not ship as is).
- The gateway already serves entity visits (`POST /entities/{name}/visit/open`, `/visit/{run_id}/turn`, `/close`)
  and entity chats (`/entities/{name}/chat/open`), and identities (look + voice, ADR 0052) by reference.
- No composer in panel-chat, the Assistant (desktop/web/Watch/iPhone) or Note offers `@` completion of entities.

## Scope (to split into package items when scheduled)

1. Gateway: resolve `@<handle>` in a turn to an entity the person may visit; open or reuse a visit bound to the
   session; return the entity's reply as a turn with its identity reference; the entity's memory records the
   exchange (1111's one-writer correction applies).
2. panel-chat composer: `@` completion from the gateway's entity roster, shared by Code web and the Assistant web
   app; the reply bubble shows the entity's name, look and voice.
3. AbstractCode (web + terminal), AbstractAssistant (desktop, web, iPhone, Watch), AbstractNote (Capture:
   `@castor` on a note asks the entity about it or files it for the entity).
4. AbstractEntity's pages say plainly that it is the place to understand entities, and link to talking with them
   from the apps.

Non-goals until 0998/1111 are designed: multi-entity rooms, entity-to-entity conversations started by a mention.

## Related

0998, 1110, 1111, ADR 0052 (digital identity), 1119 (identity: avatar, voice, track record).

## Update 2026-11-08: the design is concrete; slice 1 is planned (paused)

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go. This item stays the proposed umbrella (the
product direction); its implementation is split. Sources: the Entity owner's analysis
`untracked/entity-mentions-2026-11-08/ANALYSIS.md` and the framework seat views in
[1111](1111_at_mention_summoning_in_conversation.md) and [1112](1112_cross_gateway_entity_federation_handshake_keychain.md)
(root `985d042`).

**Mechanism (supersedes scope item 1's "open or reuse a visit bound to the session").** A mention is a summon into the
chat's own session: the person picks `@castor` from an autocomplete fed by `GET /entities` (a structured chip; nothing
parses `@` out of text), and the client calls `POST /entities/castor/summon` with the chat's `session_id`, so the
answer is a turn of that session on the same ledger and every client shows it. The summon door already honours
`session_id`. A visit per mention stays an alternative for later: the entity lives it fully, but the quoted chat is
written permanently into a home with no delete, each close costs a reflection call, and the answer lives outside the
chat session.

**The operator's group-chat rules (2026-11-08), for every surface:** structured chip from `GET /entities`, never parse
`@` from text; summon with the chat's `session_id`; several mentions answer sequentially in mention order so the
second entity sees the first answer; one answer per mention; the session's agent orchestrates by reading (no mention
tool for agents in this phase); no entity-to-entity messaging — the room is the channel; a held seat shows "<Name> is
in another conversation" and that mention is skipped; member scope (only entities the person may visit); the chip's
confirmation states that the chat's history window reaches the entity's mind; a 30-minute probe gates the first
slice, including "the entity's HOME must keep the episode" ([1145](../completed/1145_entity_activity_is_durable_in_the_runtime.md)).

**Slices.**

| Slice | Item | Packages | Size | Release |
|---|---|---|---|---|
| Probe + local `@name` in the desktop Assistant | [1174](../planned/1174_at_entity_in_the_desktop_assistant_via_summon_into_session.md) (planned, paused) | abstractassistant | 0.5 h + 1–1.5 d (≈1.5–2 d with review) | the paused one |
| Shared mention autocomplete + chips in `ChatComposer` (`overlay` + `leading`), wired into Code, Flow, Continuum, Note, Assistant web | this item, scope 2–3 | abstractuic, then each app | 1 d + 0.5 d/app | next |
| `POST /sessions/{sid}/mentions` (local or remote; records the responder, stamps `identity_ref`) | this item, scope 1 | abstractgateway | 1.5–2 d | next |
| Remote gateway connections + proxied summon (`name@host`) | [1112](1112_cross_gateway_entity_federation_handshake_keychain.md) | abstractgateway | 2–3 d | next |
| "May visit" permission | [1175](1175_may_visit_permission_for_entities.md) | abstractgateway (+ ruling) | 1–2 d | next |
| An entity as a conversation's responder (A2) | [1176](1176_an_entity_as_a_conversations_responder.md) | abstractgateway + pickers | 2 d | next |
| Signed cross-gateway identity; cross-gateway meets | [1110](1110_entity_handles_and_summoning_addresses.md), 1112 | gateway, runtime | research | later |
