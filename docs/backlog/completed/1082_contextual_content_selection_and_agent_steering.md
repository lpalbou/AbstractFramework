# 1082 — Contextual content selection and agent steering

> Package: abstracttui, abstractcode
> Type: feature
> Created: 2026-10-31
> Completed: 2026-10-31
> Status: Completed
> Priority: high
> Labels: interaction, selection, provenance, steering, accessibility

## Summary and scope

Make pointer attention useful: click gaze, source-aware content hits and highlighted selections,
then explicit Explain / Use as context / Change actions through the existing composer and normal
send/steer path. The generic selection mechanism belongs to TUI; application/AI actions to Code.

## Current code reality at intake

Code forwards mouse movement to AvatarPointer, with Ready/motion/visibility gating. TUI provides
clip-aware hit tests, semantic ActionIds and globally enabled screen-text drag/copy. Internal
Markdown search helpers map grapheme cells to bytes within a wrapped rendered line, but original
Markdown/source identity is not exposed. Code right-click resolves whole transcript items;
Quote in composer inserts a whole message and replaces the draft. TUI proposal 0160 contains
the remaining logical-selection scope; extend it rather than create a conflicting subsystem.

## Requirements and intended outcome

- Add bounded click attention without global pointer capture or breaking normal widget clicks.
- Retain source identity/ranges during layout so word, sentence/paragraph, table cell and code
  contexts come from actual source rather than reconstructed screen glyphs. Respect Unicode,
  wrapping, clipping, scrolling, links, code fences and table structure.
- A selected region has visible feedback and an explicit content/context preview. Actions never
  send or execute tools on click; the user retains the ordinary Send/steer decision.
- Preserve drafts and queued attachments; adding context must not silently overwrite text.
- Retain a stable source identity and selected excerpt; invalidate or re-resolve safely when
  streamed content, folds, viewport, session or transcript changes. A stale click never points
  at a different message. Bound retained context and explain over-limit rejection.
- Keep keyboard selection/action affordances and ordinary copy, links, scrollbar and menu behavior.
- Respect server workspace/tool policy; a clicked path does not authorize reading arbitrary files.

## Non-goals

Sending all visible screen content, OCR, hidden prompt injection, automatic tool execution,
new backend AI routes, arbitrary renderer callbacks with application authority, licensing changes.

## Validation

Headless terminal mouse/key tests through real layout and dispatch: words, Unicode/wide glyphs,
paragraphs, table cell/header identity, code line/block, scrolling/reflow, selected highlighting,
draft preservation, cancellation, stale/mutated/session-switched content and normal UI gestures.
Verify Explain/Context/Change seed the composer accurately and ordinary send/steer carries context.

## Dependencies and ADR state

Coordinate 1081 and existing TUI proposed app-widgets/0160. Existing TUI selection ownership and
Code gateway-first ADRs apply. Record a TUI ADR for the new logical content contract if its public
API introduces durable source/provenance semantics; preserve source content as data.

## Coverage boundary discovered during implementation

Mapped Feed Markdown/Text/Rich/Code and streamed Markdown provide the requested prose/table/code
flow. Code custom user cards, folded tool previews and JSON DrawFn blocks lack logical geometry
and retain normal screen copy. Proposed 1086 preserves their producer-authored mapping work.
This item does not claim semantic hit testing for arbitrary custom drawing.

## Completion report

Completed 2026-10-31; source implementation and local acceptance verified, unreleased.
Original path: `docs/backlog/planned/1082_contextual_content_selection_and_agent_steering.md`.
Final path: `docs/backlog/completed/1082_contextual_content_selection_and_agent_steering.md`.

- TUI retains original UTF-8 provenance through Markdown parsing, rich wrapping and table
  layout in private Row sidecars. `ContentHit`, `ContentSelection`, `SelectedContent` and
  `ContentContext` expose word/sentence/paragraph/table/code context without reconstructing
  source from screen glyphs. Mapping is lazy per interacted Feed item; existing Span literals
  remain compatible. Click origin survives unit round trips; drag follows actual wrapped rows.
- Additive sparse `Element::drag_hit_test` preserves link/control/scrollbar/unmapped-row ownership.
  Logical selection owns only its capture/follow-tail hold and clears safely on invalid data,
  source replacement, session/focus change and unmount. Public mutable hit ranges are validated
  during selection and drag; malformed UTF-8/overflow ranges cannot panic.
- Code forwards real pointer presses to bounded Avatar gaze. Selected text highlights, then
  Explain / Use as context / Change stage quoted data and centered context into the preserved
  composer draft, with table/code provenance and omission labels. Selected source is bounded
  to 32,768 bytes; surrounding context to 2,048 characters. Slash-command drafts refuse append.
- A responsive single-row action host reuses the existing spacer, avoiding transcript movement
  under the click. Tab/Left/Right/Enter/Space and narrow overflow menus work; Esc retains urgent
  voice cancellation and preserves the draft. Actions never send/approve/execute: normal Send
  uses existing new-run/active-run steering. No backend policy or file-read authority is added.
- Focused validation: 9 source-selection tests, 8 actual TUI Driver acceptance tests, 24 existing
  screen-selection checks and 8 real Code root interaction tests pass. Independent adversary
  also exercises an external public-API Unicode/source-range/unit/drag probe and approves.
- Full TUI all-targets: **2,569 passed / 89 ignored**; base library: **1,822 / 23**. Code
  workspace: **1,246 / 23**. Strict all-target Clippy, formatting and Rust 1.87 checks
  pass; exact matrix/results and fixture/structural changes are retained with
  [evidence and try guide](../evidence/1082/README.md). The optimized local Code binary builds
  with explicit per-command sibling source overrides and responds to `--help`.
- Coredoc: accepted TUI ADR 0007 and index, public API, Code selected-content guide/README,
  changelogs, existing package skills and TUI plus both Code LLM indexes updated. TUI 0160 is
  narrowed to remaining standalone/custom content work. Architecture assigns source geometry
  to producers, selection mechanics to TUI and AI actions to Code.

Residual/follow-up triage: custom user cards, tool previews and JSON DrawFn blocks retain safe
screen copy; producer-authored logical geometry is proposed 1086 rather than guessed. Broader
reader bindings remain in TUI 0160. Registry floor/lock propagation is proposed 1079. CaptureTerm
covers production dispatch/layout/rendering without a physical terminal; no signed distribution
or pixel-protocol claim is made. No unsafe fallback, hidden context upload or automatic send was
introduced. Priority work is complete; further custom-block mapping is separately proposed.
