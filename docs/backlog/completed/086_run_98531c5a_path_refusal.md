# Backlog Item: Run 98531c5a path refusal

## Summary
- Investigate run `98531c5a-728d-4997-862d-2eb5db12e61d` end-to-end.
- Identify root cause and implement a fix for path refusal.

## Reason
- User reports agent still refused to write to the requested absolute path.

## Scope
### In scope
- Pull run history bundle + subrun ledgers.
- Inspect tool calls and prompt payload.
- Fix any logic/prompt/tooling errors that prevent honoring allowed absolute paths.

### Out of scope
- Large policy redesigns unrelated to the failure.

## Dependencies
- Gateway run history endpoint access (auth token).

## Expected Outcomes
- Root-cause explanation backed by run evidence.
- Concrete fix with tests where applicable.

## Report
### Findings (evidence)
- `input_data.workspace_access_mode` was `all_except_ignored`, and the user prompt explicitly requested `/Users/alboul/flow-rtype/`.
- The system prompt for this run still included the **old workspace policy guidance** with the ambiguous line:  
  “If a path is outside allowed roots, do NOT attempt it…”
- The agent **did run tools**, but it created the project **relative to the workspace root** (`flow-rtype/`) instead of the requested absolute path.
- Tool call payload shows `working_directory` set to the run workspace and **relative paths only**, confirming the agent avoided the absolute path.

### Root cause
- The stale prompt guidance (from before removal) was still embedded in this run and **contradicted `all_except_ignored`**, pushing the model to avoid absolute paths even though the runtime would allow them.

### Fix
- Removed all workspace-policy guidance from the ReAct prompt so the runtime is the sole enforcement gate.
- This ensures models no longer self‑refuse based on prompt text.

### Tests run
- `python -m pytest abstractagent/tests/test_react_workflow_system_prompt_and_tools_override.py -q`
