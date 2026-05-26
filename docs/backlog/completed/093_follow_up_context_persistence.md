## Task
Persist follow-up context across run resets and always forward session id.

## Summary
Store the last completed run’s prompt + answer in a durable UI state so Follow Up
can reliably seed `context.messages` even after run events are cleared. Ensure
session id is always forwarded (explicit or derived).

## Reason
Follow Up runs were starting without any prior context; ledger evidence showed
LLM calls only received the new prompt. This breaks follow-up behavior.

## Scope
- Do: persist a follow-up seed after run completion, use it on Follow Up, and
  always forward session id on run submission.
- Do not: change gateway/runtime memory behavior.

## Dependencies
- None (frontend-only changes).

## Expected Outcomes
- Follow Up requests include `context.messages` from the last run.
- Session id is forwarded even when the input field is left blank.

## Full Report
- **Follow-up seed persistence**: Captured the last run’s prompt + answer in a
  durable `lastRunSeed` state, so Follow Up can reuse it even after execution
  events are cleared.
- **Follow-up injection**: Follow Up now uses `lastRunSeed || followUpSeed` to
  seed `input_data.context.messages` reliably.
- **Session id forwarding**: Run submission now falls back to the derived
  session id when the field is empty, ensuring `session_id` is always set for
  follow-ups.
