# Backlog Item: Runtime workspace gating confirmation

## Summary
- Confirm runtime (not prompt) enforces tool/path access.
- Adjust ReAct prompt to avoid self-restricting paths; defer to runtime enforcement.

## Reason
- Security and correctness must be enforced by runtime, not LLM instructions.

## Scope
### In scope
- Inspect runtime tool gating for paths (absolute + traversal).
- Update prompt guidance to be non-gating and runtime-aligned.

### Out of scope
- Changing enforcement policy or tool executor behavior.

## Dependencies
- None.

## Expected Outcomes
- Clear confirmation of runtime enforcement.
- Prompt no longer blocks allowed absolute paths.

## Report
### Runtime enforcement (source of truth)
- Tool args are rewritten/validated in `abstractruntime/integrations/abstractcore/workspace_scoped_tools.py` via `rewrite_tool_arguments()` and `resolve_user_path()`. This is executed in runtime effect handling before any tool runs.
- For **absolute paths**:
  - `workspace_only`: must be under `workspace_root`.
  - `workspace_or_allowed`: allowed under `workspace_root` or any `workspace_allowed_paths`.
  - `all_except_ignored`: allowed unless under `workspace_ignored_paths`.
- For **relative paths**, `_resolve_under_root_strict()` resolves against `workspace_root` and blocks `../` escapes.
- This enforcement is performed in runtime (`effect_handlers.py`), not in prompt text.

### Prompt alignment
- Removed workspace policy guidance from the ReAct prompt entirely. Runtime remains the sole enforcement gate.

### Tests run
- `python -m pytest abstractagent/tests/test_react_workflow_system_prompt_and_tools_override.py -q`
