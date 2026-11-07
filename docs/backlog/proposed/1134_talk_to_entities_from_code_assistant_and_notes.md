# 1134 — Talk to entities from Code, the Assistant and Notes (`@castor …`)

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
