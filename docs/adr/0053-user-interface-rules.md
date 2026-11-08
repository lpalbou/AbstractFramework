# ADR 0053: User-Interface Rules — Professional, Untruncated, Faithful, Shared

Status: Accepted (2026-11-07; operator rulings of 2026-11-05/07, written down so they outlive the tasks that
produced them). Applies to every web app, console, desktop palette and phone/Watch screen in the framework.

## Context

During the 0.13.1 wave the operator corrected the same things on several screens: a highlighted card border loud
enough to look like a game; a tool-permission card with more choices than the agreed three; chat bubbles styled
differently in Code and the Assistant; entity cards that cut values short or dropped them; a status line duplicating
information shown elsewhere. Each correction was applied to the screen at hand; the rule behind it lived nowhere,
so the next screen repeated the mistake. The operator's words, 2026-11-07: "this is not a toy or a game, this is a
professional UI"; "never truncate information in cards: '…' to see more"; "show values as they are, it's not up to us to
decide to remove them"; "we should have a default styling with our abstractuic, so normally things should appear in the
same way, unless overridden"; "do not over complexify".

## Decision

1. **Professional, quiet.** Emphasis is a hairline and a tone, never a thick or saturated border; animation signals
   state (working dots, Send turning into Stop) and nothing else. No decoration that does not carry information.
2. **Nothing truncated.** A card or row shows the whole value; when space is short it shows the beginning and an
   explicit "…" control that reveals the rest. No silent cut, no `max-length` on content.
3. **Values as they are.** What the runtime recorded is what the screen shows: no rounding away, no hiding of
   "uninteresting" fields, no re-labelling of raw errors (ADR: raw failure text is shown; operator 2026-11-07: "if it
   fails, show the actual error").
4. **One look, from the kit.** Chat messages, cards, controls and themes come from AbstractUIC with their default
   styling; an app overrides only with a recorded reason. A screen that re-implements a kit component is a defect.
5. **Few choices, one scope.** Permission and similar prompts offer the agreed set (Deny / Allow this tool / Allow all
   tools; this session only) and never change app defaults.
6. **No duplicate chrome.** Information shown in one place (connection status, theme, workflow) is not repeated in a
   second bar or footer.
7. **Phone first-class.** Every screen works at 400 px (operator ruling 2026-10-25); a screenshot at that width is part
   of every UI change's evidence.

## Consequences

- AbstractUIC carries the defaults (kit 0.9.20: hairline card borders; panel-chat 0.9.1/0.9.2: shared message style,
  working dots, Send→Stop morph, Deny / Allow / Allow All). Apps consume them.
- Reviews of UI changes check these seven points with screenshots; a change that violates one is sent back.
- Related: ADR 0041 (outcome records), backlog 1139 (Code vs Assistant roles), 1140 (shared gateway connection).
