# Backlog Item: Workspace policy prompt alignment

## Summary
- Align the ReAct system prompt with workspace access policy so absolute paths are allowed when policy permits.

## Reason
- The runtime already allows absolute paths under `all_except_ignored` or `workspace_or_allowed`, but the prompt forbids them, causing false refusals.

## Scope
### In scope
- Add dynamic workspace policy guidance to the ReAct prompt based on run vars.
- Ensure the prompt explicitly allows absolute paths when policy permits.

### Out of scope
- Changing workspace policy defaults or enforcement logic.

## Dependencies
- None beyond AbstractAgent (prompt-only change).

## Expected Outcomes
- Agents no longer refuse valid absolute paths when the policy allows them.

## Report
### What changed
- Added dynamic workspace policy guidance in `abstractagent/logic/react.py` that reflects:
  - `workspace_root` (or default run workspace)
  - `workspace_access_mode`
  - `workspace_allowed_paths` / `workspace_ignored_paths`
  - When absolute paths are allowed or blocked
  - Explicit note that `../` traversal is normalized and blocked when outside allowed roots
- Replaced the static “never use absolute paths outside the workspace” line with policy-aware guidance.

### Why this fixes the issue
- When `workspace_access_mode=all_except_ignored`, absolute paths are valid unless ignored. The prompt now matches that behavior, so agents no longer refuse legitimate absolute paths.
- When `workspace_or_allowed`, absolute paths are permitted under `workspace_root` or `workspace_allowed_paths`, and the prompt states exactly that.

### Tests run
- `python -m pytest abstractagent/tests/test_react_workflow_system_prompt_and_tools_override.py -q`
