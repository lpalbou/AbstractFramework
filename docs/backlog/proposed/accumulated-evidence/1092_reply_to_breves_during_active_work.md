# 1092 — Reply to brèves during active work

> Package: abstractassistant, abstractcode, abstractuic, abstractgateway, abstractruntime
> Type: feature
> Created: 2026-10-31
> Status: proposed
> Priority: P2
> Labels: decision-gate, awaiting-user-confirmation, conversation, steering, voice
> Work-item id: abstractframework-1092
> Owner: framework

## Summary

OPERATOR DECISION GATE (never assignable): let a person naturally correct, question or refine
what the avatar says while it works, then see the assistant's behavior change. Reuse existing
guidance and conversation paths. **Await explicit user confirmation before implementation.**

## Current code reality

Code web `src/workspace/app.tsx` routes busy-run input to guidance. UIC `steer_composer.tsx`
reports queued guidance; `abstract.steer_seen` means inbox delivery, not semantic adoption.
Gateway guidance can fan out to descendants; raw entity steering is refused. Watch's
`AskView.swift` normally does nothing on an orb tap while thinking unless a wait is pending.
Thus web mechanisms are reusable, but Watch behavior and targeted-message context need work.

## Proposed scope and outcome

- Keep an obvious speak/type action available while working or waiting. No slash commands.
- Interpret a natural reply against current conversation. Selecting an earlier brève fixes its
  quotation/identity through composition; selection is optional, never required before talking.
- Send the person's words and relevant brève context through the supported route. Start with a
  single actual actor/task; audit entity/parallel routing before broadening. No generic fan-out
  assumption that every actor shares the same conversation.
- Display the person's transcript and a small sent/error/retry signal. Only the actor's real
  continuation can say it changed its plan. Preserve actual change, disagreement or clarification.
- A reply stops/suspends current playback before recording. Explicit task stop and speech-only
  pause have clear effects. Do not promise always-listening or instant interruption of in-flight work.
- Preserve late messages as corrections with their original context; never answer a different
  question, silently switch runs or imply a completed action was undone.

## Acceptance criteria

- [ ] Operator confirms first-host and single-actor scope.
- [ ] Person can say “Keep that option” during work without a special command or selection ritual.
- [ ] Earlier selected text remains the referent despite newer brèves/session changes.
- [ ] Next search/choice changes appropriately; “Understood” alone does not pass.
- [ ] Sent versus considered feedback, retry, task-finished and offline cases are honest.
- [ ] Speaking, reading, replying and stopping do not conflict or lose user text.

## Testing

After confirmation: `python -m pytest abstractgateway/tests/test_gateway_steer_door.py abstractruntime/tests/test_steer_sidecar.py`.
Drive a real host through discovery → spoken/typed correction → actor acknowledgment → changed
next action; test stale references, finalization races and send failure. Watch validation is 1095.

## Dependencies, non-goals and ADR state

First delivery is 1088/1089/1092; questions use 1093. Reuse root 1082 context identity and existing
Runtime/Gateway authority. No receipt subsystem, graph, hidden approval or entity-rite bypass.
No new public schema is adopted here; any durable interaction contract needs ADR review.
