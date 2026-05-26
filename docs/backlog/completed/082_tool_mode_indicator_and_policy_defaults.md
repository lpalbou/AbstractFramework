## Summary
- Surface gateway tool execution mode prominently in tool selectors.
- Align tool approval defaults so read-only/search tools auto-approve.
- Keep backend and shared UI kit defaults consistent across thin clients.

## Why
- Users need to see when gateway tool mode bypasses approvals.
- Current defaults still ask for non file/system tools, contradicting policy.
- Shared UI components must mirror backend approval logic.

## Scope
- Expose gateway tool mode through discovery and render it in UI.
- Update approval defaults to only require ask for file/system effects.
- Update AbstractUIC ToolPolicyEditor defaults and UI mode banner.

## Out of Scope
- Changing workflow logic or tool execution paths.
- Adding new tool types or modifying tool implementations.

## Dependencies
- Gateway discovery endpoint for tools.
- AbstractRuntime ToolApprovalPolicy defaults.

## Expected Outcomes
- Tool mode banner is visible and explicit in the tools dialog.
- Read-only/search tools default to approve; file/system tools default to ask.
- AbstractUIC defaults stay in sync with AbstractRuntime.

## Plan
- Update discovery/tools to include tool_mode and consume it in the UI.
- Update approval default lists in AbstractRuntime and AbstractUIC.
- Add ToolPolicyEditor banner for tool mode in AbstractUIC.

## Report
- **Tool mode indicator**: gateway `/discovery/tools` now returns `tool_mode`, and the Qt tools dialog renders a prominent banner (with `#FALLBACK` messaging when missing).
- **Shared UI banner**: AbstractUIC `ToolPolicyEditor` now supports `toolMode` (with tone-aware banner styling) to surface gateway mode in all thin clients.
- **Approval defaults**: read-only/search + comms tools auto-approve; only file/system mutation tools default to ask (aligned in AbstractRuntime + AbstractUIC).

## Tests
- `python -m pytest abstractruntime/tests/test_tool_approval_executor.py`
- `PYTHONPATH=src python -m pytest tests/test_gateway_discovery_endpoints.py` (gateway src layout; emitted logging warnings from AbstractCore cache shutdown)
- `python -m pytest abstractassistant`
