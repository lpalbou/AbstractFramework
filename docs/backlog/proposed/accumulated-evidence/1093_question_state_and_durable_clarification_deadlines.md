# 1093 — Question state and durable clarification deadlines

> Package: abstractagent, abstractflow, abstractruntime, abstractgateway, abstractuic, abstractassistant
> Type: feature
> Created: 2026-10-31
> Status: proposed
> Priority: P1
> Labels: decision-gate, awaiting-user-confirmation, questions, waits, deadlines, avatar
> Work-item id: abstractframework-1093
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable): add an explicit conversational question/awaiting-answer
state. Essential questions wait; ordinary clarifications may wait two to five minutes then take
a declared safe fallback. **User confirmation is required before implementation.** These questions
concern the person's task, not tool-execution permissions.

## Current code reality

Runtime `_handle_ask_user` creates an indefinite USER wait, with prompt/choices/free text, without
setting until/details. WaitState already has until/details. Runtime deadline processing and
SQLite due indexes currently handle UNTIL/EVENT, not ordinary USER waits; Gateway already wakes
due waits. EVENT waits support prompt/choices/deadline. Flow Ask User lacks deadline fields while
advanced Wait for Event supports them. Reuse these primitives rather than introduce a scheduler.
Current resume validates wait identity but does not itself check the deadline; delayed expiry
ticks can let a late answer win. Default run/node wait keys can repeat: audit existing callers
and protect logical question generations before adding timeout behavior.

## Proposed behavior

- Essential/critical question: hold dependent work until answered or explicitly cancelled. No
  automatic timeout. Initial scope may park the entire actor; concurrent independent work is deferred.
- Clarification: configurable two-to-five-minute response window, only with a predeclared safe
  fallback. Example: “Inside or outside? If you cannot answer in three minutes, I will compare both.”
  If no safe fallback exists, wait rather than invent facts or permission.
- Importance determines whether the answer is essential; urgency determines alert delivery.
  Neither the model's tone nor notification settings can override permission policy.
- Question identity, prompt, importance, fallback, publication time, deadline and resolution are
  durable server-held state. Proposal: timer starts when the durable question is published;
  absence of a reply is never described as intentional refusal or agreement. Display accurate
  overdue state when offline or notifications are muted. No client-local execution timer.
- Resolve answered/expired/cancelled exactly once under existing mutation authority. Specify
  authoritative server cutoff semantics, answer-versus-expiry races, restart and manual pause.
  Reload cannot reset TTL; paused/cancelled tasks must not resume behind the user's back.
- On expiry, say what fallback was taken and why. Retain question/history and late text as a
  contextual correction, never as an answer to a newer ask or automatic undo of committed action.
- Distinguish speaking a question, awaiting an answer, microphone listening and awaiting approval.
  Keep the full question reachable beyond the subtitle viewport. Use legacy waiting pose + host
  purpose/label until an approved compatible refinement exists; no new v1 numeric pose required.
- Expose behavior through Agent and ordinary Flow Ask User using the existing runtime path.
  Background delivery remains governed by current attention/notification policy.

## Acceptance criteria

- [ ] Operator confirms question policy and proposed ADR 0045 before implementation.
- [ ] Critical questions remain pending; clarification TTL and declared fallback work end to end.
- [ ] Silence never approves a tool, transaction, disclosure, deletion or another permission gate.
- [ ] One generation resolves once across answer/expiry/cancel races and multiple devices.
- [ ] Durable deadlines survive restart/offline; late answers cannot satisfy stale/newer waits.
- [ ] User sees asking/waiting distinctly from approval/listening and can revisit/answer the full question.
- [ ] Flow/Agent authoring, Gateway due indexing/resume and client replay agree on outcome.
- [ ] Expired prompts stop notifying; expiry is a clear expected branch, not a fabricated task failure.

## Testing

After confirmation: `python -m pytest abstractruntime/tests/test_wait_event_deadline.py abstractruntime/tests/test_resume_concurrent_same_wait.py abstractruntime/tests/test_visual_wait_event_deadline_passthrough.py`.
Add fake-clock USER/selected-path tests, strict boundary races with delayed scheduler, repeated
asks at the same node, late text, reconnect, restart, pause and critical no-timeout fixtures.
Exercise real Gateway wake/index integration; a browser countdown alone does not pass.

## Dependencies, non-goals and ADR state

Pair with 1088/1089/1092; 1094 handles cues, 1095 Watch adoption. Proposed ADR 0045 records the
cross-package policy; root ADRs 0002/0027/0041 remain applicable. No new scheduler, automatic
permission, mandatory parallel question management or completed decision reversal.
