# 1170 — Session kinds, the client halves: probes declare `process`; Code and Observer get a kind chip; the Entity app an artifact chip

> Package: AbstractAssistant (phone and watch probes send `kind: "process"` at run start), AbstractCode web and AbstractObserver (a filter chip per kind that exists in the data), AbstractEntity (an artifact chip on tool lines from `tool_details[].artifact_id`)
> Type: feature (completes gateway 1166, live since 2026-11-08 13:30)
> Status: planned — FIRST in the next release (operator 2026-11-08: "for this release", then "only the core patch for this release" because of credits; the gateway half is live, this is the visible part)
> Created: 2026-11-08
> Priority: P1
> Labels: sessions, kinds, apps

## The agreed kinds (operator ruling 2026-11-08 11:45)

| kind | meaning | examples |
|---|---|---|
| `conversation` | a person talking, with the Assistant, Code, or an entity (an entity visit is a conversation whose participant is an entity) | Code chats, Assistant chats, nerin visits |
| `docs` | a Docs assistant chat | the kit's Docs drawer |
| `notes` | AbstractNote's user-facing note work | a capture from Note, the phone or the watch |
| `automation` | an occurrence of an automation the user created | "Inbox triage" runs |
| `process` | internal processes the framework runs for its own treatments, never created by the user as such | Note's processor/reflect/consolidate occurrences, model-host verifications, phone and watch voice probes |

No `visit` kind, no `probe` kind, no free tags (later, separately).

## Scope

1. AbstractAssistant phone and watch: the sessions their probes open (`watch-voice-probe-*`, `model-host-verification-*`)
   send `kind: "process"` on `POST /runs/start`; today they land among conversations by default.
2. Code web sidebar and Observer: a kind chip per kind present in the listing (hidden when a kind has no sessions);
   default conversations; the Assistant switcher unchanged (conversations and automations tabs).
3. AbstractEntity: an artifact chip on tool lines reading `tool_details[].artifact_id` and opening
   `GET /entities/{name}/artifacts/{id}` (+ `/meta` for size, tool, arguments).
4. Tests per app; screenshots at desktop and 400 px.

## Size

Assistant ~1 h, Code ~1 h, Observer ~1 h, Entity app ~1 h (Entity owner).
