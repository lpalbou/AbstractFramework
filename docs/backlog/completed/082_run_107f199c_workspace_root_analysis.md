# Backlog Item: Run 107f199c workspace root analysis

## Summary
- Investigate run `107f199c-6b9e-4afe-8d7f-9dbfd881630e` and explain why the agent refused to act.
- Clarify workspace root behavior and whether it is required for user-specified paths.

## Reason
- User observed non-action despite configuring access mode; needs a clear, evidence-based explanation.
- Workspace scoping impacts UX and must be transparent.

## Scope
### In scope
- Inspect run history bundle + workflow snapshot for the run and its subruns.
- Identify prompt/tooling constraints leading to the refusal.
- Explain how workspace_root and access modes affect tool execution.

### Out of scope
- Changing workspace policy defaults.
- Modifying agent prompts or tool policies (unless explicitly requested).

## Dependencies
- Gateway run history endpoint access (auth token).

## Expected Outcomes
- Clear root-cause explanation grounded in run data.
- Actionable guidance on workspace_root usage.

## Report
### Findings (evidence)
- The run completed without tool calls. The subrun LLM response explicitly refused to write to `/Users/alboul/test-rt/` and asked for an alternate option.
- `input_data.workspace_root` for this run is the **default per-run workspace** (`.../runtime/gateway/workspaces/...`), not `/Users/alboul/test-rt/`.
- The workflow snapshot shows the agent config with `tools: ["execute_command"]` and `pinDefaults.max_iterations = 5`.

### Root cause
- The agent prompt forbids filesystem/tool use on absolute paths outside `workspace_root`. Because the run used the default per-run workspace, the requested path `/Users/alboul/test-rt/` was outside the allowed scope, so the model declined to proceed.
- The access mode `all_except_ignored` was set, but the override path was never actually passed as `workspace_root`, so the prompt still treated `/Users/alboul/test-rt/` as out-of-workspace.

### Recommended user action
- If you want files written to `/Users/alboul/test-rt/`, set `workspace_root` explicitly to that path in the Run Flow modal, or add it to `workspace_allowed_paths` and choose `workspace_or_allowed`.
- If you want to use the default per-run workspace (recommended for isolation), keep `workspace_root` empty and copy results afterward.
