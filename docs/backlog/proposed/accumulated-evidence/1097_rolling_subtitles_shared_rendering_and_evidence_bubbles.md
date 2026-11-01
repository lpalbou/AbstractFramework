# 1097 — Rolling subtitles, shared rendering and evidence bubbles beside the avatar

> Package: abstractuic, abstractcode, abstractassistant, abstractentity, abstractagent
> Type: feature
> Created: 2026-11-01
> Status: Proposed
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

## Open decisions for the operator

- How many caption lines on desktop vs phone vs Watch, and whether older captions fade or stay.
- Whether the evidence rail is on by default in Avatar mode or a toggle.
- The typed-update vocabulary (evidence/finding/decision/question) versus waiting for the 1090
  discussion (pure semantic extraction vs AbstractNote vs AbstractMemory).

## Dependencies

- 1096 (shared composer default) committed first so the Avatar composer is stable.
- 1089 residual: typed public update kinds.

## Validation expectations

- Browser checks: rolling order, no cycling, Markdown/media rendering, request pinning, phone
  geometry; a real local-model run producing ≥3 captions and ≥2 evidence bubbles.
