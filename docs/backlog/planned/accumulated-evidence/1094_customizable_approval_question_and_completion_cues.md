# 1094 — Customizable approval, question and completion cues

> Package: abstractassistant, abstractuic, abstractgateway, abstractruntime
> Type: feature
> Created: 2026-10-31
> Status: planned
> Priority: P2
> Labels: notifications, audio, visual, accessibility
> Work-item id: abstractframework-1094
> Owner: framework

## Summary

Independently customize visual and audible cues for
approval required, a question and finished work, with haptics where supported. **Implementation authorized by the operator on 2026-11-01.** An alert is not an answer or an authorization.

## Baseline before implementation

Watch has approval/question attention, haptics, spoken-answer settings and background/push paths;
its primary activity rail remains tool-oriented. Shared UIC has host-controlled avatars and
attention/session surfaces. No complete three-category per-modality preference contract was
verified. Root ADR 0041 requires explicit notification effects for triggered flows and auditable
delivery; completion must not acquire a new hidden post-flow notifier.

## Authorized scope and outcome

- Separate Approval / Question / Finished preferences, with independent visual, sound and supported
  haptic choices. Distinguish a short sound from speaking the full question/answer. Quiet operation
  remains available; muted cues do not hide pending items, resolve waits or change TTL.
- Avatar state, subtitle and exact question/approval remain accessible even if its attention
  animation/sound is disabled. Use text and shape as well as color.
- Prioritize active listening/response and required attention; coalesce stale narration. Do not
  recite every missed brève or replay completion sounds when opening history.
- Deduplicate per actual question/approval/outcome revision. Suppress obsolete attention before
  dispatch, cancel pending local alerts where supported and set suitable push expiry. An OS/push
  alert already queued may arrive stale: revalidate on open and show that exact item's resolved
  state, never resurrect its wait. Transport expiry is separate from the question's lifetime.
- Foreground completion feedback while viewing a conversation is distinct from background
  delivery. Reuse authorized attention/push/Notify paths; triggered-flow background notification
  still requires an explicit effect under ADR 0041. Preference changes do not create new channels
  or authorize alerts from previously quiet flows. Record deliveries where current policy requires.
- Scope preferences to the signed-in person and relevant device capabilities; define precedence
  before implementation without requiring a new cross-device settings service for the pilot.

## Acceptance criteria

- [x] Operator authorized on 2026-11-01: desired categories/defaults and first host.
- [x] Each category's visual/audio/haptic preference is independently testable where supported.
- [x] Asking, approval and completion have intelligible distinct feedback without color/sound alone.
- [x] Muting/dismissing/reading never answers, approves, expires or completes work.
- [ ] Reconnect/history/revisions deduplicate app alerts; stale OS/push arrivals revalidate against
      resolved state and cannot resurrect a question. Document platform cancellation limits.
- [x] Foreground and authorized background delivery obey ADR 0041 and existing channel policy.

## Testing

Validation: `python -m pytest abstractgateway/tests/test_events_stream_waits.py abstractgateway/tests/test_automations_attention.py abstractgateway/tests/test_run_after.py`.
Add a three-category modality matrix through the chosen UI, muted/speech-overlap/expired/offline
fixtures, preference persistence and dedup assertions. Watch OS delivery checks belong to 1095.

## Dependencies, non-goals and ADR state

Requires question identity/state from 1093 and stable conversation/outcome identity from 1088.
Coordinate existing attention/push work; no general push rewrite or blanket completion broadcaster.
Governing ADRs 0039/0041/0043; proposed 0044 and accepted 0045/0046 do not relax permission/delivery rules.

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
