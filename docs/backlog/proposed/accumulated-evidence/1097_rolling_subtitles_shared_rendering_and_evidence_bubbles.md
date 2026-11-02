# 1097 — Rolling subtitles, shared rendering and evidence bubbles beside the avatar

> Package: abstractuic, abstractcode, abstractassistant, abstractentity, abstractagent
> Type: feature
> Created: 2026-11-01
> Status: Proposed (rolling captions delivered 2026-11-02; evidence rail remains, decision-gated)
> Priority: P2
> Labels: conversation, avatar, subtitles, evidence, decision-gate
> Work-item id: abstractframework-1097
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable until confirmed): redesign the Avatar view's caption
area. Today (`panel-chat/src/avatar_conversation.tsx`) it shows ONE message, the latest
assistant text, as raw text split into 180-character pages that auto-cycle every ≥6.5 s
(`conversationPages`). A long final answer therefore becomes a 12-page teleprompter with visible
Markdown syntax (`###`, `**`, `---`), which the operator rejected on 2026-11-01. The target is:
captions rendered through the shared panel-chat message renderer so any modality displays
correctly; a realtime rolling list of recent public updates (older lines move up, the newest
enters from the bottom, never cycling) that both informs and asks questions; and the
accumulated findings/evidence shown as comic-style speech bubbles or cards beside the avatar so
the person can see what led to the current state.

## Why

Operator, 2026-11-01: "the 'subtitle' of the avatar must render properly any of our modality,
so this should reuse a component from abstractuic (eg do we have a 'chat message' where we
already handle rendering?). also, it should roll the message down (eg old message getting up,
new message appearing from the bottom). BUT this should be realtime, unlike what is happening
now where it just cycle continuously. the idea is to inform also by text on what's going on AND
to ask questions when relevant. for the findings, i would show them as cards or bubbles ... next
to the avatar so we can see the accumulated set of evidences that is leading to the current
state. for the moment, i am not pleased by the experience, so we have room to evolve."

## Current code reality

- `avatar_conversation.tsx`: single `shown` message, `pages[page]` in a `<p>`, Previous/Next
  subtitle buttons, Pause subtitles, history panel; attention/request rows above.
- `conversation_model.ts`: `conversationPages(text, 180)`; `conversationMessages` already
  filters public updates (`publicUpdate`), question outcomes and final results.
- Shared renderers that already exist and handle every modality: `Markdown`, `ChatMessageCard`
  (`chat_message_card.tsx`) and the media/attachment presenters used by `ChatThread`.
- Agent brèves are typed public events (1089) but carry no evidence/finding kind yet; 1090
  (structured triples) is still a separate proposal.

## Proposed scope

- Replace the pager with a rolling caption list: last N public updates (N≈3 lines on Watch-like
  layouts, more on desktop), newest at the bottom, animated entry, no auto-cycling; reading
  (hover/focus/touch) pauses nothing because nothing cycles. Questions and requests stay pinned
  above the list as today.
- Render each caption with the shared message renderer (Markdown, media, files), with a caption
  density style; the final answer is rendered once, as a message, not paginated.
- An "evidence" rail beside the avatar: bubbles/cards for findings and evidence, fed by typed
  public updates (`kind: evidence | finding | decision | question`), expandable to their source,
  accumulated for the session. Requires a small typed-update contract in Agent/Runtime (1089
  residual) and must not require 1090's graph.
- Phone (390 px) and Watch layouts verified; technical view untouched.

## Design rule from the operator (2026-11-01)

The avatar view is an incarnation, a personification of the AI, not a dashboard around it. Nothing
in that view is a setting or a control panel: no cue toggles, no technical counters, no labels like
"Observation/Finding". Settings live in the host's settings menu; the view holds the avatar, what it
says (subtitles), what it has found (evidence bubbles), its questions and the way to answer. Keep
this rule when designing the rolling captions and the evidence rail.

## Progress

2026-11-02, rolling captions and layout (operator approval the same evening to fix the Avatar view;
council findings C1 and A8). Delivered on branch `feat/avatar-rolling-captions` in AbstractUIC
(panel-chat), AbstractAssistant (web), AbstractCode (web) and AbstractEntity; not published.

Assumptions taken for this round (state them back to the operator):

- Captions are the CURRENT turn's public messages (public updates, questions, question outcomes,
  the answer) after the person's latest message; accepted mid-run guidance does not start a new
  turn; the person's own words are not captions.
- Visible lines: 4 on desktop, 3 below 480 px, 2 while a question or approval is open
  (`--pc-avatar-caption-lines`). Older captions move up, dim and fade at the top edge; the area
  scrolls (wheel, touch, keyboard) to reread the turn. Nothing is scheduled, so nothing cycles and
  nothing needs pausing.
- The final answer is one caption rendered once (never paginated); a long answer is shown from its
  first line and scrolls in place; the full exchange stays in the Conversation view and in
  Conversation history. The completion cue is shown on the answer itself.
- Every caption goes through the shared renderer: `ChatMessageCard` with the new
  `variant: "caption"` (Markdown, links, media, files, structured results; no card chrome).
- Removed: Previous / Next subtitle, Pause subtitles, Return to latest, hover/focus freezing, and
  `conversationPages`. Kept: Conversation history (now shown in place of the captions, with a
  small avatar), Reply to this, the host's Talk and read-aloud controls.
- Layout: one column that fits its container above the composer; the avatar scales to the space
  left; action targets are at least 44 px. Checked in Chrome at 1440 and 400 px, light and dark,
  in the panel-chat harness and in the three apps.
- `conversationCaptions(messages)` in `conversation_model.ts` is pure and unit-tested; the
  component only renders it.

## Remaining

- The evidence rail (bubbles or cards of findings beside the avatar), which needs the typed
  public-update vocabulary (1089 residual) and the operator decisions below.
- Watch-like layout and a real local-model run producing at least 3 captions (the validation
  expectation below; this round used deterministic fixtures and the gateway e2e fixture).
- Operator questions raised by this round: the Assistant's in-view "Assistant settings" button
  (kept; the design rule says settings live in the host's settings menu), and the history
  panel's technical words ("Public update", raw source call ids under "Sources").

## Open decisions for the operator

- Caption lines: delivered as 4 desktop / 3 phone / 2 with a request, older captions fading; confirm or change (Watch still open).
- Whether the evidence rail is on by default in Avatar mode or a toggle.
- The typed-update vocabulary (evidence/finding/decision/question) versus waiting for the 1090
  discussion (pure semantic extraction vs AbstractNote vs AbstractMemory).

## Dependencies

- 1096 (shared composer default) committed first so the Avatar composer is stable.
- 1089 residual: typed public update kinds.

## Validation expectations

- Browser checks: rolling order, no cycling, Markdown/media rendering, request pinning, phone
  geometry; a real local-model run producing ≥3 captions and ≥2 evidence bubbles.
