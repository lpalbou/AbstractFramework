# Backlog Item: Run 5bec2a17 workspace policy failure

## Summary
- Investigate run `5bec2a17-7ef3-435f-8013-f094ce4f3764` end-to-end.
- Identify the root cause and implement a fix.

## Reason
- User reports the dynamic workspace policy prompt still “didn’t work.”

## Scope
### In scope
- Pull run history bundle and subrun ledgers.
- Inspect tool calls, prompt payload, and workspace policy vars.
- Apply a targeted fix if behavior is incorrect.

### Out of scope
- Broad policy redesign beyond the specific failure.

## Dependencies
- Gateway run history endpoint access (auth token).

## Expected Outcomes
- Root-cause explanation backed by run evidence.
- Concrete fix with tests (where applicable).

## Report
### Findings (evidence)
- The subrun LLM response refused to act and claimed it lacked permission to write to `/Users/alboul/flow-rtype/`.
- The dynamic prompt previously contained workspace policy guidance and a denial line that misled the model.

### Root cause
- Prompt-based guidance was influencing behavior; the model refused even though runtime would enforce access correctly.

### Fix
- Removed workspace policy guidance from the ReAct prompt entirely so the runtime is the sole enforcement gate.

### Tests run
- `python -m pytest abstractagent/tests/test_react_workflow_system_prompt_and_tools_override.py -q`
