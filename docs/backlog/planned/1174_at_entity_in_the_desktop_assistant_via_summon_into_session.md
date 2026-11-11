# 1174 — `@entity` in the desktop Assistant: a mention chip summons the entity into the chat's own session

> Package: AbstractAssistant (desktop composer, chip, summon on send, author label, refusal sentence); AbstractGateway read only (existing `GET /entities`, `POST /entities/{name}/summon`, identity route)
> Type: feature
> Status: completed 2026-11-11 — built in AbstractAssistant 6ae96c6, 0332713, 54ed4fa, 2ca569e, 462aeda (main); adversarial review `abstractassistant/untracked/review-mentions-desktop/REVIEW.md` (F1, F2 fixed in 462aeda); documented as desktop 0.19.0 in AbstractAssistant 0680108 (not tagged, not published). The summon-based design below is SUPERSEDED, see the next section. The file stays in planned/ until the next backlog hygiene pass moves it.
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
- `54ed4fa` + `2ca569e`: the Qt UI (`ui/mention_composer.py`, `ui/mention_picker.py`, `ui/mention_chip.py`,
  `ui/mention_card.py`, `ui/pending_bubble.py`, `app.py`): `@` at the start or after a space opens the list
  (agent first, then the entities), the pick is a chip object inside the sentence (orb + name; never parsed from
  the words), the sent message keeps its chips, the entity's card after a short rest on a chip, one pending
  bubble per entity (name + dots) replaced by its answer and removed at once on a refusal with its sentence, the
  answer headed by its author, no thinking card / "no written reply" line for an entities-only message, no
  informational line about who reads what; `tests/basic/test_mentions_desktop_ui.py`.
- `462aeda`: the review's fixes: F1 (a follow-up typed while only entities answer waits and is sent after,
  "Your message will send when the answers are in."; Stop ends the asking only, no `cancel_run` of the previous
  run; pause/resume disabled), F2 (the entities-only mark is reset on reattach and when the worker ends), no
  "Running assistant workflow…" flash, offsets in UTF-16 code units at every boundary (sent chips, clipboard,
  sent-bubble placement, paste), the sent chip's card also on keyboard focus; 8 more UI tests, each red against
  its mutant.

## Completion (2026-11-11)

- Behaviour delivered = the web Assistant's over the mention contract: structured chips from `GET /entities`,
  entities asked one after the other in mention order with `repeat_of` + `mention_id`, a message naming only
  entities starts no agent run, the person's words shown once, a reloaded chat names who wrote each answer,
  409 "<Name> is in another conversation." and 404 `entity_not_found` skip, 503 / 422 / a failed call stop and
  give the words back with the unsent chips (a resend asks only those), an uncoded 404/405 = "This gateway does
  not offer mentions yet.", Stop ends the asking.
- Acceptance criteria above, as rewritten by the superseded-design section: met (structured chips, sequential
  answers in mention order, one answer per mention, the 409 sentence and skip, member scope from `GET /entities`,
  no entity-to-entity messaging, adversarial review with real screenshots). The summon call, the 30-minute probe
  and the first-use confirmation sentence are replaced by the contract and not built.
- Review: `abstractassistant/untracked/review-mentions-desktop/REVIEW.md` (FIX-BEFORE-RELEASE F1, F2: fixed in
  462aeda; 13/14 mutants killed at review time); screenshots `abstractassistant/untracked/mentions-desktop/`
  (light, dark, narrow).
- Docs and version (AbstractAssistant 0680108): desktop 0.19.0, CHANGELOG [0.19.0] - 2026-11-11, README "What's
  new", `docs/getting-started.md` "Talk to your entities with `@`", `docs/api.md` (mention routes),
  `docs/architecture.md` (mention modules), llms files regenerated; web/CHANGELOG [Unreleased] carries 985d57b.
- Left for the release: the operator's user test, the tag and the publish (operator's decision). Open question
  from the review (item 8), for the operator: after a 503 both apps stop asking (the contract's "keep the message
  in the composer"), not "the next entity is still asked".

The acceptance criteria below keep their intent (structured chips, sequential answers in mention order, one
answer per mention, "<Name> is in another conversation" and skip, member scope, no entity-to-entity messaging);
the summon call, the 30-minute probe and the "first use" confirmation sentence are replaced by the contract (the
first-use sentence was removed from the web Assistant, AbstractAssistant aa68850, operator 2026-11-10 23:02).

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
