# 1095 — Watch conversation adoption and user validation

> Package: abstractassistant, abstractavatar, abstractuic
> Type: feature
> Created: 2026-10-31
> Status: proposed
> Priority: P2
> Labels: decision-gate, awaiting-user-confirmation, watch, conversation, accessibility, validation
> Work-item id: abstractframework-1095
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable): adopt the tested avatar/subtitles conversation on
Watch, including live corrections, question state and configured cues. Validate with real users,
including the operator's mother if she wishes. **No implementation before user confirmation.**

## Current code reality

Watch already provides dominant orb, voice recording, final-answer reading, history, approvals
and questions. `AskView.swift` generally ignores orb taps during thinking absent a pending wait;
`ActivityRecord` skips full tool outputs. Starting recording stops playback. Current cancellation
can clear the local view before server confirmation. WUI guidance support does not establish
Watch input/control parity; exercise actual Watch code rather than assume the new view is a reskin.

## Proposed scope and expected outcome

- Reuse the shared conversation semantics from 1088/1089/1092; add or adapt native rendering and
  thin-client endpoints/decoding only where needed. Watch renders public messages, not full ledgers
  or technical reasoning to derive its own discoveries.
- Full-screen avatar plus two/three subtitle lines with scrolling to history/final. Large-text
  mode may adjust composition; no unreadable text shrinking or hidden question content.
- Speak/type during work, natural current-reference replies and explicit older-message replies,
  truthful applied feedback, repeat/silence controls and intelligible task stopping.
- Question and approval routing, critical/timed state, late replies, completion and per-category
  visual/audio/haptics all use existing runtime authority and signed-in owner/session identities.
- Real-device microphone/playback, permission, connection/background behavior and cross-device
  answered/expired dedup need testing; do not infer them from browser success.
- Observe a person correcting a meaningful choice without coaching, missing an update, returning
  to history and answering a timed question. Age does not imply a preferred input or reduced agency.

## Acceptance criteria

- [ ] Operator confirms device/adoption scope and testing participants.
- [ ] Real-device conversation includes a live correction that changes later work.
- [ ] Critical question, timed clarification, explicit approval and completion are distinguishable.
- [ ] Missed updates, expired/late reply, quiet mode, background/foreground and offline recovery work.
- [ ] Large text, VoiceOver, reduced motion and speech/text parity remain usable.
- [ ] Stop reflects confirmed outcome; incomplete/offline cancellation is not presented as completed.
- [ ] Findings/technical view remain available through the supported surface without crowding the face.

## Testing

After confirmation, run the relevant Watch package/Xcode UI suites using commands documented in
`abstractassistant/watch/apple/BUILD.md` and `swift test --package-path abstractassistant/watch/apple/Packages/AbstractGatewayClient`.
Record simulator coverage separately from physical Watch voice, haptic, background and usability
checks. Success requires observed behavior, not only a screenshot or an agent's approval.

## Dependencies, non-goals and ADR state

Depends on the first-host conversation contract and 1093/1094. No avatar ABI rewrite, graph/Note
dependency, automatic always-on microphone, new OS persistence or independent Watch agent.
Root ADRs 0039/0041/0043, proposed 0044/0045 and existing Watch thin-client rules apply.
