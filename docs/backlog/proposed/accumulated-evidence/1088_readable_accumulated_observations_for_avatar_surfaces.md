# 1088 — Avatar-first conversation with rolling subtitles

> Package: abstractassistant, abstractcode, abstractuic, abstracttui
> Type: feature
> Created: 2026-10-31
> Revised: 2026-10-31
> Status: proposed
> Priority: P2
> Labels: decision-gate, awaiting-user-confirmation, avatar, subtitles, conversation, accessibility
> Work-item id: abstractframework-1088
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable): present the assistant through a full-screen avatar
and two or three readable subtitle lines of meaningful brèves. Scroll to earlier exchanges and
the final answer; retain a separate technical view. **Explicit operator confirmation is required
before implementation.** Pair with authored brèves (1089) and live replies (1092) for the first
useful delivery; a passive tool-result display is no longer the intended product milestone.

## Why

The operator describes an incarnated AI that communicates discoveries, choices, reasons and
uncertainty while working, and that the person can contradict or redirect. The Watch's dominant
avatar is the reference. The default screen should remain a calm conversation, comprehensible
without technical vocabulary, including to the operator's 81-year-old mother.

## Current code reality

- Watch `Sources/App/Ask/AskView.swift` is orb-led; `ActivityViews.swift:ActivityPanel` currently
  lists up to 12 technical activity steps below the orb. Its Activity decoder retains tool
  names/status and model text, not full discovery content.
- `abstractuic/ui-kit/src/activity_avatar.tsx` is a presentation-only host-controlled renderer.
- Agent observe formats `[tool]: output` deterministically; meaningful public brèves require
  authored content via 1089, not relabeling technical activity rows.
- Root 1082 owns source-aware selection; 1086 covers custom preview geometry. Original run
  measurements in `../../evidence/1088/README.md` explain why dumping observations is unsuitable.

## Proposed direction and scope

- Full-screen/dominant avatar with two or three subtitle lines; no finding/confidence/type badges
  in the ordinary view. Preserve the complete brève in history; no silent content loss.
- Latest message advances naturally. Reading/scrolling/selecting/replying suspends automatic
  replacement; a clear return-to-latest action restores following. Do not shrink text to fit:
  large-text/reduced-motion modes may adapt layout while preserving the message and history.
- Scroll to accumulated conversation and final response. Return to the avatar without losing
  place. Technical execution remains available in its own view.
- Show the utterance currently being spoken; coalesce superseded narration and support repeat.
- Expose an obvious way to speak/type during work. Asking, awaiting an answer, approval, listening,
  speaking, working and finished are semantically distinguishable. 1093 owns question behavior;
  1094 owns alert cues. Use compatible host mappings; do not invent v1 pose codes here.
- Prefer one reversible task and one existing web host for the first end-to-end experiment;
  validate the same composition on Watch in 1095. No native app changes in this planning pass.

## Acceptance criteria

- [ ] Operator confirms implementation scope and first host.
- [ ] Avatar plus readable two/three-line subtitles is the default work view; history/final remain reachable.
- [ ] Meaningful authored brèves and a working correction loop are demonstrated with 1089/1092.
- [ ] Reading, scrolling or replying cannot race automatic subtitle replacement or change reply identity.
- [ ] Text/speech agree; replayed history cannot restart stale speech or completion/attention alerts.
- [ ] Large text, keyboard/screen reader, muted audio and reduced motion remain usable.
- [ ] Technical mode and original evidence are preserved; no graph or Note dependency.

## Testing

After confirmation, replay the exact cancelled-run fixture for source drill-down and use a
scripted reversible selection task for the new conversation. Assert subtitle/history identity,
scroll-follow suspension, session switching and state precedence in the owning UI harness.
Baseline: `cargo test --manifest-path abstracttui/Cargo.toml content_selection`.
An observed end-to-end user correction is required, not only a static screenshot.

## Dependencies, non-goals and ADR state

First useful delivery: 1088 + 1089 + 1092. Questions/alerts follow in 1093/1094 and Watch in 1095.
Reuse 1082/1083/1086. Root ADRs 0007/0009/0026/0043 apply; 0044 and 0045 are proposed only.
No new graph, memory migration, avatar reasoning engine, or mandatory technical dashboard.

## History and receipts

Initial intake proposed deterministic observation cards. The operator's subsequent clarifications
supersede that as the primary product: cards are optional detail; communication and intervention
are the first milestone. Filename/ID retained for traceability. Prior three-worker councils and
run evidence remain in `../../evidence/1088/README.md`; this revision records the subtitle request.
