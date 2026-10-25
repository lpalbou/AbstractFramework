# 1045 — SCHEDULE_RUN effect and the schedule_run tool

> Package: runtime, agent
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, runtime, agent, wake

## Summary

A runtime effect `SCHEDULE_RUN {at | after_s | on: {source_id, connection_id?, config}, task | note, tools?, session_id (default: the caller's), mode: same_session | independent}` that creates a one-shot automation bound to the caller's session with `origin_run_id`, the tool ceiling intersected (`resolve_tool_scope`) and copied into the occurrence's `_runtime.allowed_tools`, `schedule_run` excluded from the child scope, and a `wake.scheduled` event in the user stream; exposed to agents as the `schedule_run` builtin and to flows as a node. Cancelling = deleting the automation (`wake.cancelled`).

## Why

The operator wants an agent to spawn work later (in X minutes or on a trigger) with at most its own tools, and "ping me in 5 minutes about X" is that with no task. The runtime has no such effect; `delegate_agent` only runs a child now.

## Scope

### In scope

- Effect, handler in the host (gateway) on the automation controller, agent builtin definition, Flow node (in 1047), `AutomationDefinition.session_id` override (today hard-coded).
- The occurrence runs in the caller's session as a new turn with the trigger header, so the model's replay sees it.

### Out of scope

- Recurring wakes from the tool (use automations).
- A gateway HTTP route the agent calls with a token (never).

## Current code reality

- `abstractagent/.../logic/builtins.py:322` `delegate_agent` → `DELEGATE` effect; `core/tool_scope.py:20-77` fail-closed walk; `models.py:465` `session_id = automation_session_id` hard-coded; `runtime.py:4771` `parent_run_id` only for subworkflows.

## Acceptance criteria

- [ ] An agent calling `schedule_run(after_s=300, note="X")` ends its run; five minutes later a new run appears in the same session with the note and the trigger header; the user stream shows `wake.scheduled` then `run.started`.
- [ ] The child cannot call `schedule_run` and has no tool outside the parent's ceiling.
- [ ] Deleting the automation before it fires emits `wake.cancelled` and nothing runs.

## Testing

- `cd abstractruntime && python -m pytest tests -q -k 'schedule_run or wake'`
- `cd abstractagent && python -m pytest tests -q -k 'schedule_run'`

## References

- Round-1 finding F6, round-2 finding 2.

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)
