## Summary
- Follow the most recent subworkflow wait on reattach.
- Prevent stale subrun selection that hides active tool approvals.

## Why
- Root runs can record multiple subworkflow waits; following the first one can ignore the active child.
- Ignoring the latest subrun leaves approvals unseen and the UI stuck in “running.”

## Scope
- Select the most recent subworkflow wait during ledger replay.
- Keep streaming behavior unchanged for live waits.

## Out of Scope
- Gateway backend changes.
- Workflow engine behavior changes.

## Dependencies
- GatewayRunController ledger replay logic.

## Expected Outcomes
- Reattach follows the active subrun and surfaces its tool approval.
- Runs no longer hang with hidden approvals.

## Plan
- Update replay logic to choose latest un-seen subworkflow wait.
- Run tests.

## Report
- **Replay selection fix**: ledger replay now chooses the most recent subworkflow wait in a batch instead of the first, ensuring reattach follows the active subrun.
- **Test reliability**: `test_final_verification` now times out subprocess shutdown to avoid hangs during the full suite.

## Tests
- `python -m pytest abstractassistant`
