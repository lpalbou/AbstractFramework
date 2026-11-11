# 1174 — `@entity` in the desktop Assistant: a mention chip summons the entity into the chat's own session

> Package: AbstractAssistant (desktop composer, chip, summon on send, author label, refusal sentence); AbstractGateway read only (existing `GET /entities`, `POST /entities/{name}/summon`, identity route)
> Type: feature
> Status: planned (IN PROGRESS 2026-11-11: contract client + send path built in AbstractAssistant 6ae96c6 + 0332713; the Qt UI is in progress) — the summon-based design below is SUPERSEDED, see the next section
> Created: 2026-11-08
> Priority: P1
> Labels: entities, mentions, assistant, seat-framework

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Superseded design (2026-11-11)

Operator 2026-11-11: the desktop Assistant does `@entity_name` "following the same logic as other apps". The
summon-based plan below (`POST /entities/{name}/summon` with the chat's session, the 30-minute probe) is
SUPERSEDED by the mention contract every client now follows,
`untracked/entity-mentions-2026-11-08/CONTRACT-mentions.md` and its Additions: the chips ride `POST runs/start` as
`mentions` (a message naming entities and not `@agent` starts no agent run: `agent: "not_addressed"` + `turn_id`);
each entity is asked through `POST /sessions/{sid}/mentions` (the visit door), in order, one after the other, with
`repeat_of` (the person's turn) and `mention_id`; refusals 409 / 404 `entity_not_found` / 503 / 422
`repeat_of_unknown` / an uncoded 404 (older gateway); every turn carries `author`. The reference implementation is
the web Assistant (`abstractassistant/web/src/lib/mentions.ts`, `web/src/ui/Workspace.tsx`).

Built in AbstractAssistant (main, unreleased):

- `6ae96c6`: `abstractassistant/core/mentions.py` (the Qt-free port of `mentions.ts`: roster from `GET /entities`,
  structured chips, the send plan, the refusal sentences, `MentionsSummary`) and the worker API the palette wires
  (`GatewayWorker.set_mentions` + `mention_asked` / `mention_answered` / `mention_skipped` / `mentions_done`).
- `0332713`: the gateway client (`list_entities`, `post_mention`, `start_run_with_mentions`, `GatewayCodedError`),
  the worker's send path (no agent run for an entities-only message; entities asked in order beside the agent's run
  otherwise; Stop; resend of the unsent chips), and the history (a reloaded chat labels each answer with its
  `author`, shows the person's words once by `repeat_of`, orders the answers by `updated_at`). Tests
  `tests/basic/test_mentions.py` + `test_mention_worker.py`, 20 of 20 mutants killed; the roster and an
  `entity_not_found` refusal checked live on the hermetic gateway (:18851).
- Still open: the Qt composer `@` picker, chips and the entity's answer bubble (second worker, `app.py` / `ui/`),
  the docs, the operator's user test. This item moves to completed when those land.

The acceptance criteria below keep their intent (structured chips, sequential answers in mention order, one
answer per mention, "<Name> is in another conversation" and skip, member scope, no entity-to-entity messaging);
the summon call, the 30-minute probe and the "first use" confirmation sentence are replaced by the contract (the
first-use sentence was removed in every app, operator 2026-11-10 23:02).

## Summary

The first, client-only slice of [1138](../proposed/1138_talk_to_entities_from_code_assistant_and_notes.md) (talk to
entities from the apps), planned for the release that was being prepared. In the desktop Assistant the person picks
`@castor` from an autocomplete fed by `GET /entities`; the composer holds a structured chip, never text parsed for
`@`. On send the client calls `POST /entities/castor/summon` with the chat's own `session_id`, so the entity's answer
is a turn of that session on the same ledger and every client shows it. No base-package change. It is gated on a
30-minute probe (below). Design: `untracked/entity-mentions-2026-11-08/ANALYSIS.md` §3–4; framework seat view in
[1111](../proposed/1111_at_mention_summoning_in_conversation.md).

## Why

Operator direction 2026-11-07 (1138): "the goal is to be able to speak and interact with them through AbstractCode,
AbstractAssistant or even AbstractNote, by referencing them in a discussion, e.g. `@castor did you see ...`". The
operator's group-chat rules (2026-11-08) fix how a chat with mentions behaves; they are the acceptance criteria below.

## Current code reality (2026-11-08)

- Summon door (abstractgateway `routes/entities.py`, `@router.post("/{name}/summon")` ~3354, `SummonEntityRequest`):
  takes `session_id`, `input_data`, `caller_kind`, `queue`, `park`; starts an ordinary run in the caller's workspace
  with the entity's identity prelude and the entity's own model; participants `[person:<caller>, entity]`; a held
  seat answers 409 + `retry_after_s` unless `queue=true`.
- One life, one visit: visit, chat and summon share one conversation seat (`entity_visits.py`, `entity_seat.py`); an
  open Entity-app visit holds the seat up to an hour (idle auto-close).
- Who may summon: admins every entity, a member only the entities they created, hidden entities 404
  (`entity_access.py` `entity_visible_to`).
- Each `GET /entities` row carries a handle `<name>@<gateway address>` (display only); the identity route serves
  name/look/voice by reference (ADR 0052).
- The shared `ChatComposer` (abstractuic panel-chat) has `leading`/`overlay`/`onPaste` slots and no mention
  primitive; the shared primitive is next release (1138). This slice builds the chip in the desktop Assistant only.

## Scope

### In scope

1. The probe (0.5 h, gate): a summon with a chat's `session_id` shows in that session's history, the chat's next
   agent turn sees it, AND the entity's HOME keeps the episode (its own ledger and artifacts, root
   [1145](../completed/1145_entity_activity_is_durable_in_the_runtime.md)). If any of the three fails, stop and close that gap
   first (a base-package item, next release); this slice does not ship around it.
2. Desktop Assistant (1–1.5 d + review and screenshots): `@` completer from `GET /entities` (only entities the
   person may summon), a structured chip, summon on send with `{session_id: <chat sid>, prompt: <text>, caller_kind:
   "human", input_data: {use_session_history: true, mention: {entity: "<slug>"}}}`, the answer labelled with the
   entity's name and avatar from the identity route, the refusal sentences below.

### Out of scope

The shared composer primitive and other apps (1138, next release); `POST /sessions/{sid}/mentions`, remote
`name@host` mentions ([1112](../proposed/1112_cross_gateway_entity_federation_handshake_keychain.md)), a "may visit"
permission ([1175](../proposed/1175_may_visit_permission_for_entities.md)), an entity as a conversation's responder
([1176](../proposed/1176_an_entity_as_a_conversations_responder.md)); mention tools for agents; entity-to-entity
messaging.

## Acceptance criteria (the operator's group-chat rules, 2026-11-08)

- [ ] A mention is a structured chip chosen from `GET /entities`; nothing parses `@` out of free text (client or
      server).
- [ ] The summon carries the chat's `session_id`: the entity's answer is a turn of that session, shown by every client
      from the session view.
- [ ] Several mentions in one message answer sequentially, in mention order: the second entity's summon starts after
      the first answer landed, so it sees it in the history window.
- [ ] One answer per mention; no entity answers twice for one mention.
- [ ] The session's own agent orchestrates by reading: it sees the entity answers at its next message; agents get no
      mention tool in this phase.
- [ ] No entity-to-entity messaging: the room (the session) is the channel; an entity's answer never triggers
      another summon.
- [ ] A held seat (409) shows "<Name> is in another conversation" and that mention is skipped; the remaining
      mentions continue.
- [ ] Member scope: the completer offers only entities the person may summon; a refused summon shows the gateway's
      sentence.
- [ ] The chip's confirmation states that the chat's history window reaches the entity's mind (its model provider).
- [ ] The probe in scope item 1 passed and its evidence (session history read, next agent turn, the home's ledger
      row) is in the receipts.
- [ ] Adversarial review with real screenshots (desktop and 400 px where the surface exists), local CI, the
      operator's user test.

## Testing

- `python -m pytest tests -q -k mention` (abstractassistant)
- `scripts/ci_local.sh`

## Receipts

- Analysis: `untracked/entity-mentions-2026-11-08/ANALYSIS.md` (Opus worker, read-only, 2026-11-08).
- Framework seat view: [1111](../proposed/1111_at_mention_summoning_in_conversation.md) section of 2026-11-08 (root `985d042`).
