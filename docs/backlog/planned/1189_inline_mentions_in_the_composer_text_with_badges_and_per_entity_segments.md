# 1189 — Inline `@mentions` inside the composer's text, drawn as badges, each entity given its own segment

> Package: AbstractUIC panel-chat (the composer's span model, overlay and mention list; the message card's badges), AbstractGateway (`MentionRequest` gains spans; `entity_mentions` builds each entity's turn), AbstractEntity / AbstractAssistant web / AbstractCode web (wiring)
> Type: feature
> Status: planned (IN PROGRESS 2026-11-10, this wave) — next wave (sized 2026-11-09 21:00; not in the 0.14.0 cut)
> Created: 2026-11-10
> Priority: P1
> Labels: entities, mentions, composer, kit, next-wave

## Summary

Today a picked `@Castor` is removed from the text and becomes a chip above the field, and every mentioned entity
receives the whole message. The operator wants to write "hey @castor work on this, @ephemeral control the network" in
one message: the mentions stay inline as badges where he typed them, and each entity knows which part is addressed to
it. Design from the Entity session's analysis: keep the native textarea, keep the visible `@Name` text, hold each
binding structurally as `{id, name, kind, index, start, end}` (never parsed from the text), draw the badges with a
mirror overlay, and let the gateway give each entity the whole message plus its own segment. About **19–27 h**.

## Why

Operator, 2026-11-09 evening test (finding f, running log `untracked/release-2026-11-07/RESUME.md` 20:40): "composer:
inline @mentions in free text with badges, per-entity tasks in one message; session agent should stay silent when
the message is addressed to entities". 21:25: jobs today are "too complex and clanky"; he wants "hey @castor work on
this, @ephemeral control the network".

## Question put to the operator, and its answer (recorded)

Asked 2026-11-09 21:00: should a mention queue a job? Answered by the design he agreed at 21:30 and filed as
[1187](1187_a_mention_becomes_a_job_by_the_entitys_own_judgment.md): **a mention never queues a job by itself.** It is
a question inside a visit; it becomes a job only when the entity takes it (`take_as_job`, its own judgment, no text
heuristics), or when the guardian presses the badge's "leave as task". This item builds the composer and the segments;
the badge action and the job path are 1187's.

## Current code reality (2026-11-10)

- `abstractuic/panel-chat/src/chat_composer.tsx` (native textarea, line 123); a pick removes `@query` from the text and
  adds a chip above the field (`panel-chat/src/mentions.ts:67-75`); mentions are sent as `{id, name, kind, index}`.
- `abstractgateway/src/abstractgateway/routes/session_mentions.py:20` `MentionRequest`; each entity gets the whole text
  as a visit turn (`mention_index` only).
- Built in the 0.14.0 wave and reused here: one answer per mention (`mention_id`), the visit-lane cursor, the fenced
  mirror; the session agent stays silent for a message addressed to entities (gateway `c26d38a2`, agent `ff1c4d1`,
  runtime `f2d9628`); the Code terminal chip (abstractcode `399e4bd`, abstracttui `b06ba9a`).
- Analysis and sizes: `untracked/finish-plan-2026-11-09/operator-test/FINDINGS.md` section (7).

## Scope

### In scope

1. **Kit composer (10–14 h):** span model `{id, name, kind, index, start, end}`, offsets remapped on every edit; a span
   whose text no longer equals its bound `@Name` becomes plain text; mirror overlay behind a transparent textarea (font,
   padding and wrap copied); caret-anchored mention list; `check_mentions` and tests; works at 400 px.
2. **Kit message card (3–4 h):** sent spans render as badges in history.
3. **Gateway (4–6 h):** `MentionRequest` gains the spans; `entity_mentions` builds each entity's turn with the whole
   message, its own segment (from its mention's `end` to the next mention's `start`; text before the first mention
   goes to all — span arithmetic, not NLP) and who else was asked; tests.
4. **App wiring (2–3 h):** Entity drawer, avatar visit, Assistant web, Code web.

### Out of scope

- Turning a mention into a job ([1187](1187_a_mention_becomes_a_job_by_the_entitys_own_judgment.md)).
- A contenteditable editor with atomic chips (truer badges, about twice the cost, high IME/paste/undo/a11y risk).
- Flow, Note and Continuum composers (operator: one app first).

## Acceptance criteria

- [ ] "hey @castor work on this, @ephemeral control the network" sends one message; castor's turn carries the whole
      message plus "work on this", ephemeral's plus "control the network", each knowing the other was asked.
- [ ] Editing, deleting or retyping inside a badge unbinds it to plain text; a pasted `@x` stays plain text; IME
      composition is never remapped mid-composition; after native undo the spans are re-verified.
- [ ] History shows the sent badges; the model sees natural text (no placeholder tokens).
- [ ] 400 px: overlay wrap parity, the list fits the screen (phone screenshot); a11y: the textarea stays the input, the
      overlay is aria-hidden, a live region announces "Castor mentioned", `aria-activedescendant` on the list.
- [ ] Every new test red without its code.

## Receipts

- Operator test findings and the Entity session's analysis: `untracked/finish-plan-2026-11-09/operator-test/FINDINGS.md`
  (7); running log `untracked/release-2026-11-07/RESUME.md` 20:40, 21:00, 21:25.

## Scope change 2026-11-10 14:50

Operator test of Code web 0.16.0: the @castor chip rendered ABOVE the text ("terrible visually and not the inline in text I
was requesting. so do it all over again"). Moved INTO THE 0.14.0 WAVE, before the app tags: the mention is an inline styled
chip in the text, no x, deleted in text; the two info lines stay; kit composer so Assistant web follows. Entity session.
