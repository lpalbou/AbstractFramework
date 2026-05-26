## Summary
- Rehydrate pending waits from history bundles during gateway attach.
- Detect tool approval waits even when tool call lists are missing.

## Why
- Approval waits can be missed on reattach, leaving runs stuck with no UI prompt.
- Tool approval waits must surface reliably to avoid silent deadlocks.

## Scope
- Parse history bundle waiting state and emit pending wait events.
- Improve tool approval detection in the gateway event adapter.

## Out of Scope
- Gateway backend changes.
- Workflow behavior changes.

## Dependencies
- Gateway history bundle endpoint.
- Gateway event adapter.

## Expected Outcomes
- Reattached sessions show approval prompts immediately when waiting.
- Tool approval waits are not misclassified as generic input waits.

## Plan
- Add wait detection from history bundles in `GatewayWorker`.
- Enhance wait parsing + tool approval detection in `GatewayEventAdapter`.
- Run tests.

## Report
- **Pending wait rehydrate**: on attach, the worker inspects the history bundle for `run.waiting` (and ledger tail fallback) and injects the wait into the normal event path so approvals are prompted immediately.
- **Approval detection**: adapter now treats `mode=approval_required` (or executor kind `tool_approval`) as a tool approval wait even if `tool_calls` is missing, preventing it from being misrouted as a free‑text input wait.
- **Wait reason coercion**: wait reasons coming from `WaitReason` enums are normalized before dispatch.

## Tests
- `python -m pytest abstractassistant`
