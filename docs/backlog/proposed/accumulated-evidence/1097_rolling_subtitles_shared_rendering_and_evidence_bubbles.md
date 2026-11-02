# 1097 — Rolling subtitles, shared rendering and evidence bubbles beside the avatar

> Package: abstractuic, abstractcode, abstractassistant, abstractentity, abstractagent
> Type: feature
> Created: 2026-11-01
> Status: Proposed (2026-11-03: rolling captions replaced by one live line + Findings panel on branches, unmerged)
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

## Operator direction, 2026-11-03 (supersedes the rolling captions)

Operator, 2026-11-03 00:12, looking at the rolling captions: "whatever this is, this is horrible and
not what i want. again, the apple watch assistant design is much closer. your subtitle things
doesn't make any sense. the goal is to report evidences / things happening while they happen, and
also to have another floating panel with the accumulated evidences/findings so far".

Target, modelled on the Apple Watch Ask view (`abstractassistant/watch/apple/Sources/App/Ask/AskView.swift`:
one live line under the orb, tap to read and reply, "Latest" to follow again):

1. The avatar and ONE live line: the latest public update of the current turn, replaced in real
   time, rendered with the shared message renderer. Clicking it holds it open with "Reply to this"
   and "Latest". Questions and approvals stay pinned above. The answer appears once, as a message.
   No subtitles, paging, pager controls, history pane or counters.
2. A floating "Findings" panel that accumulates the findings reported during the conversation's
   runs, newest last, each a compact card opening to its full text and the results it cited.
   Beside the avatar on a wide view, a bottom sheet (Findings / Close) on a narrow one; no
   findings, no panel.

Rule (no ADR; recorded here): **a finding is typed by its producer, never inferred.** The model
types each public update in its `<public_update>` block as `"kind": "finding"` (a fact or piece of
evidence it established) or `"progress"` (what it is doing); the agent validates it
(`invalid_kind`), persists it in the `public_update` event, and every reader passes it unchanged:
replay view `update_kind`, entity visit state `update_kind`, panel-chat `PublicUpdate.kind`. An
update without a kind is progress. No client derives a kind from text.

Delivered 2026-11-03 on branches `feat/avatar-live-findings` (worker W11), not merged or published:

- AbstractAgent: `kind` in the block, one instruction line, `invalid_kind`, event and cycle record.
- AbstractRuntime: replay `public_update` messages carry `update_kind`; replayed tool-call rows keyed
  by a runtime call id also carry the model's `call_id`, which `source_call_ids` cite (conformance
  goldens regenerated, only that field added).
- AbstractGateway: entity visit state `public_updates[].update_kind`.
- AbstractUIC panel-chat: `conversationLive` (live line, answer, person key) and
  `conversationFindings` (findings with their cited tool activities), both pure; the Avatar view
  rebuilt around them; rolling captions, in-view history, `conversationLabel` and Clear reply
  context removed. Checked with unit checks, an agent -> replay -> panel-chat seam script, and the
  browser harness at 1440 and 400 px, light and dark (screenshots in
  `untracked/w11-avatar/shots/`).

Superseded below: the 2026-11-02 rolling-captions round (kept for history).

## Progress

2026-11-02, rolling captions and layout (operator approval the same evening to fix the Avatar view;
council findings C1 and A8). Delivered on branch `feat/avatar-rolling-captions` in AbstractUIC
(panel-chat), AbstractAssistant (web), AbstractCode (web) and AbstractEntity; not published.

Assumptions taken for this round (state them back to the operator):

- Captions are the CURRENT turn's public messages (public updates, questions, question outcomes,
  the answer) after the person's latest message; accepted mid-run guidance does not start a new
  turn; the person's own words are not captions.
- Visible lines: 4 on desktop, 3 below 480 px, 2 while a question or approval is open
  (`--pc-avatar-caption-lines`). Older captions move up and dim; an edge fades where text
  continues; the area scrolls (wheel, touch, keyboard) to reread the whole turn. Nothing is scheduled, so nothing cycles and
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
- Adversarial review fixes (`untracked/council-2026-11-02/review-W2.md`, MERGE-AFTER-FIXES): the
  caption area shows whole lines only (1.5em grid) and fades at an edge where text continues;
  every caption of a turn is kept (the earlier 12-caption window was an unmarked bound); an open
  question appears once, pinned above the captions (`pinnedRequest`); unchanged captions are
  reused and their cards memoized; the reply-scope errors name the surviving control (Clear
  reply context).
- Coordinator rulings applied the same evening: the Assistant's in-view "Assistant settings" button
  is removed (Settings stays in the conversations sidebar, behind Open Conversations on a phone);
  the history beside the avatar uses plain labels (You, Update, Question, Answer via
  `conversationLabel`) and no longer lists raw source call ids (technical view only).

## Remaining

2026-11-03:

- Merge the four PRs after review, then re-sync the shared bundle into AbstractAssistant web,
  AbstractCode web and AbstractEntity (after the avatar gaze PR AbstractAssistant #45 merges), and
  run `console_islands_sync` at the next gateway release.
- A real local-model run producing progress updates and at least two findings, checked in the
  Assistant's Avatar view (fixtures and the seam script only so far).
- Watch: show findings the same way (the Watch decodes `public_update` but ignores `kind` today).

Earlier (2026-11-02, superseded by the above where they conflict):

- The evidence rail (bubbles or cards of findings beside the avatar), which needs the typed
  public-update vocabulary (1089 residual) and the operator decisions below.
- Watch-like layout and a real local-model run producing at least 3 captions (the validation
  expectation below; this round used deterministic fixtures and the gateway e2e fixture).
- Follow-up for abstractgateway (no gateway change in this round): the console bundles embed
  panel-chat's `panel_chat.css` (`console_islands.py`), so they carry the old Avatar view rules
  until `console_islands_sync` runs at the next gateway release.

## Open decisions for the operator

- Settled 2026-11-03: no caption lines (one live line); the Findings panel is shown whenever there
  are findings (no toggle on a wide view); the vocabulary is `progress | finding` (questions keep
  their own type; 1090 stays separate).

## Dependencies

- 1096 (shared composer default) committed first so the Avatar composer is stable.
- 1089 residual: typed public update kinds.

## Validation expectations

- Browser checks: one live line replaced in real time, hold / Reply to this / Latest, no cycling,
  Markdown/media rendering, request pinning, Findings panel (floating) and sheet (phone),
  geometry at 1440 and 400 px; a real local-model run producing progress updates and ≥2 findings.
