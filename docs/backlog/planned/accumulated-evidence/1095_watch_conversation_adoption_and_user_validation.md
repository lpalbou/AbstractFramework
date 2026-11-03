# 1095 — Watch conversation adoption and user validation

> Package: abstractassistant, abstractavatar, abstractuic
> Type: feature
> Created: 2026-10-31
> Status: planned
> Priority: P2
> Labels: watch, conversation, accessibility, validation
> Work-item id: abstractframework-1095
> Owner: framework

## Summary

Adopt the tested avatar/subtitles conversation on
Watch, including live corrections, question state and configured cues. Validate with real users,
including the operator's mother if she wishes. **Implementation authorized by the operator on 2026-11-01.**

## Baseline before implementation

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

- [x] Operator authorized on 2026-11-01: device/adoption scope and testing participants.
- [ ] Real-device conversation includes a live correction that changes later work.
- [x] Critical question, timed clarification, explicit approval and completion are distinguishable.
- [ ] Missed updates, expired/late reply, quiet mode, background/foreground and offline recovery work.
- [ ] Large text, VoiceOver, reduced motion and speech/text parity remain usable.
- [x] Stop reflects confirmed outcome; incomplete/offline cancellation is not presented as completed.
- [x] Findings/technical view remain available through the supported surface without crowding the face.

## Testing

For validation, run the relevant Watch package/Xcode UI suites using commands documented in
`abstractassistant/watch/apple/BUILD.md` and `swift test --package-path abstractassistant/watch/apple/Packages/AbstractGatewayClient`.
Record simulator coverage separately from physical Watch voice, haptic, background and usability
checks. Success requires observed behavior, not only a screenshot or an agent's approval.

## Dependencies, non-goals and ADR state

Depends on the first-host conversation contract and 1093/1094. No avatar ABI rewrite, graph/Note
dependency, automatic always-on microphone, new OS persistence or independent Watch agent.
Root ADRs 0039/0041/0043, proposed 0044 and accepted 0045/0046 and existing Watch thin-client rules apply.

## Authorization and implementation tracking

The operator authorized development on 2026-11-01 after root checkpoint `30bcc40`. Earlier
confirmation gates are discharged for this scope. Preserve the existing view and add a second
view for agent and entity work. Shared mission/tests/ownership: [implementation record](../../evidence/1088/implementation.md).
No package release or deployment is implied.

## Delivery checkpoint — 2026-11-01

Development is authorized and underway; no further implementation confirmation is pending.
See the [shared implementation/test record](../../evidence/1088/implementation.md) and
[public conversation ADR0046](../../../adr/0046-optional-public-conversation-view.md).
Default chat/technical views remain available. Physical Watch and human usability validation,
and quantitative backend KV/memory comparisons, remain separate from automated/source delivery.
