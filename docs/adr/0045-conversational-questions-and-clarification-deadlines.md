# Conversational questions and clarification deadlines

Status: Accepted (operator authorization 2026-11-01). Implementation is tracked separately; existing
ASK_USER callers remain compatible until the new optional question policy is requested.

## Context

An avatar-led assistant should ask about the person's task while working and make questions
easy to notice and answer. Missing essential information must stop dependent work, while a
minor clarification can wait a few minutes then continue transparently with a safe fallback.
An unanswered question must never be confused with permission to perform an action.

The current runtime has indefinite ASK_USER waits and event deadlines, but timed ordinary
questions, fresh question generations and strict answer-versus-expiry arbitration need work.
A timer in a browser would fail across restarts, multiple devices and offline periods.

## Decision

The approved opt-in contract is:

1. Distinguish conversational questions, tool/action approvals and ordinary nonblocking brèves.
   Asking/awaiting an answer is an explicit host-owned state, distinct from microphone listening.
2. Essential questions have no automatic deadline. Hold dependent work until answered or explicitly
   cancelled. The initial implementation may park the whole actor; independent parallel work is
   not required to introduce this behavior.
3. A clarification may use a configured two-to-five-minute window only when its safe fallback
   is declared with the question. Otherwise wait. State that fallback before waiting, then explain
   what happened if no answer arrived. Silence never creates consent or a fabricated user choice.
4. Runtime owns durable question identity/generation, text, timing policy, fallback and terminal
   outcome. The proposed timer starts at durable publication, not first browser display. Preserve
   delivery evidence separately: no answer does not imply the person saw or ignored the question.
5. Answer/expiry/cancellation has one durable winner under existing per-run mutation authority.
   Specify server cutoff semantics and test delayed expiry processing; a late reply cannot resolve
   an old or newer question by reusing a node-based wait key. Retain late text as a contextual
   correction and explain whether work can still change. Reload must not reset deadlines; manual
   pause/cancellation must not trigger unobserved continuation.
6. Reuse existing waits, due indexes, Gateway runner and Flow authoring. Choose the USER/EVENT
   representation through a current-code design review; no second scheduler or client-side authority.
7. Alert preferences change visual/audio/haptic cues, not the wait's policy. Preserve the exact
   question beyond subtitle replacement; suppress obsolete attention after resolution. Background
   delivery still follows ADR 0041's explicit effects; this adds no hidden completion notifier.

## Consequences

Questions become ordinary collaboration with visible, predictable waiting behavior. The price is
a bounded cross-package extension: question authoring, durable resolution/indexing and client
presentation must agree. Expiration is an expected, explicit outcome rather than silent failure.
The first experience needs no KG and can preserve legacy avatar poses with a host question label.

## Enforcement

Reject client-only TTL execution, implicit permission-by-silence, indefinite questions
silently given deadlines, and read/dismiss actions treated as answers. Review any public wire
fields before their first durable write. Reuse existing per-run locks and notification authority.
Operator confirmation was given on 2026-11-01. Completion requires implementation and validation;
acceptance of this contract does not assert that every caller already conforms.

## Validation

Fake-clock and real-runner checks must cover essential no-timeout, timed fallback, answer at the
deadline, delayed scheduler, repeat asks at one node, multiple devices, late answers, restart,
manual pause/cancel and stale alerts. User testing must show the person understands what waits,
what will happen without a reply and how to change it later.

## Backlog links

- [1093 question behavior](../backlog/completed/accumulated-evidence/1093_question_state_and_durable_clarification_deadlines.md).
- [1092 live replies](../backlog/completed/accumulated-evidence/1092_reply_to_breves_during_active_work.md).
- [1094 cues](../backlog/planned/accumulated-evidence/1094_customizable_approval_question_and_completion_cues.md).
- [1095 Watch adoption](../backlog/planned/accumulated-evidence/1095_watch_conversation_adoption_and_user_validation.md).

## Related

Root ADRs 0002 (effects), 0027 (explicit timeouts), 0041 (explicit notification effects),
0043 (readable labels) and proposed 0044 (host-owned activity and expression).
Code verification: 2026-11-01; implementation and tests are recorded in the completed 1093 card.
Physical-device/user validation remains in 1095; no running production deployment inferred.
