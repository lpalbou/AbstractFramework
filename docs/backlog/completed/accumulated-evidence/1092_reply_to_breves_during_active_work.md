# 1092 — Reply to brèves during active work

> Package: abstractassistant, abstractcode, abstractuic, abstractgateway, abstractruntime
> Type: feature
> Created: 2026-10-31
> Status: Completed
> Completed: 2026-11-01
> Priority: P2
> Labels: conversation, steering, voice
> Work-item id: abstractframework-1092
> Owner: framework

## Summary

Let a person naturally correct, question or refine
what the avatar says while it works, then see the assistant's behavior change. Reuse existing
guidance and conversation paths. **Implementation authorized by the operator on 2026-11-01.**

## Baseline before implementation

Code web `src/workspace/app.tsx` routes busy-run input to guidance. UIC `steer_composer.tsx`
reports queued guidance; `abstract.steer_seen` means inbox delivery, not semantic adoption.
Gateway guidance can fan out to descendants; raw entity steering is refused. Watch's
`AskView.swift` normally does nothing on an orb tap while thinking unless a wait is pending.
Thus web mechanisms are reusable, but Watch behavior and targeted-message context need work.

## Authorized scope and outcome

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

- [x] Operator authorized on 2026-11-01: first-host and single-actor scope.
- [x] Person can say “Keep that option” during work without a special command or selection ritual.
- [x] Earlier selected text remains the referent despite newer brèves/session changes.
- [x] Next search/choice changes appropriately; “Understood” alone does not pass.
- [x] Sent versus considered feedback, retry, task-finished and offline cases are honest.
- [x] Speaking, reading, replying and stopping do not conflict or lose user text.

## Testing

Validation: `python -m pytest abstractgateway/tests/test_gateway_steer_door.py abstractruntime/tests/test_steer_sidecar.py`.
Drive a real host through discovery → spoken/typed correction → actor acknowledgment → changed
next action; test stale references, finalization races and send failure. Watch validation is 1095.

## Dependencies, non-goals and ADR state

First delivery is 1088/1089/1092; questions use 1093. Reuse root 1082 context identity and existing
Runtime/Gateway authority. No receipt subsystem, graph, hidden approval or entity-rite bypass.
The public communication and receipt contract is governed by accepted ADR 0046.

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

## Completion report

Date: 2026-11-01. ADR impact: accepted 0045/0046; broader 0044 remains proposed.

Implemented typed/voice participation through existing agent/Flow commands and canonical owned
entity visit routes. Public referents keep their identity across new messages and validated actor
children; unrelated runs are refused. Original human text, acceptance receipts and command
correlation restore once in chronological history. The real local GGUF fixture changed its next
native tool batch and final recommendation after a human correction; generic agreement was not
used as proof. Web send failure, exact question routing and explicit approval boundaries passed.

Implementation spans Agent ReAct/public_update, Runtime questions/receipts/replay, Gateway
commands/owned visit projection, shared UIC conversation, Code/Assistant/Entity hosts and Watch.
Package docs, existing operating skills and generated indexes were updated. Independent adversarial
review approved the source and verified corrected native xcresults. Final producer snapshots match
canonical UIC across all three web hosts.

Validation: real GGUF correction loop; Runtime 191+110 and Gateway 68+16 selected passes;
Code 501 / Assistant 63 / Entity 601 unit passes; shared panel-chat and built Chrome checks;
Flow 1318 tests; native 220 SDK  / 231 dependent  / 17 focused tests, 3/3 UI plus 1/1reopening lifecycle.
These are separate suites/reruns, not a sum of unique tests. Full evidence, screenshots, commits
and limits: [delivery receipt](../../evidence/1088/delivery.md).

Original intake: `proposed/accumulated-evidence/1092_reply_to_breves_during_active_work.md` (created 2026-10-31).
Authorized/intermediate path: `planned/accumulated-evidence/1092_reply_to_breves_during_active_work.md`.
Final path: `completed/accumulated-evidence/1092_reply_to_breves_during_active_work.md`.
No publication or production restart. Hub unavailable; no remote mirror completion claimed.

Residuals are already tracked: manual accessibility 1088, quantitative KV comparison 1089,
OS/device cues 1094 and physical Watch/human validation 1095. Optional KG 1090 and broad warning
review 1091 remain separately proposed; no new product scope or priority change. Gateway global
changelog validation has an unrelated pre-existing malformed 0980 fragment; this change's fragment
parses independently. Runtime retains process-local single-writer arbitration, not distributed locks.
