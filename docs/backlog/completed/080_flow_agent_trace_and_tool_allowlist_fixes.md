# Backlog Item: Flow agent trace persistence + tool allowlist fixes

## Summary
- Keep agent cycle observations visible after completion (even when ledger output is missing).
- Fix synthetic On Flow Start output to show actual input_data values.
- Restore agent tool availability when no explicit tool allowlist is set.

## Reason
- Ledger streams do not emit node_complete outputs for pure transitions, so agent steps can appear empty after completion.
- The current On Flow Start preview shows run metadata instead of the user inputs, which is misleading.
- Empty tool allowlists disable tool execution for agents, breaking expected tool use.

## Scope
### In scope
- UI-side fallback to derive agent output from sub-run trace events.
- UI change to render agent trace panel even when output is missing.
- Use input_data payload for On Flow Start synthetic step.
- Runtime compiler change to only set allowed_tools when explicitly configured.

### Out of scope
- Adding new ledger record types for pure transitions.
- Changing gateway tool approval policy defaults.
- Full extraction of run-details UI into shared abstractuic components.

## Dependencies
- AbstractFlow frontend (RunFlowModal + SSE trace streams).
- AbstractRuntime VisualFlow compiler (agent allowlist handling).

## Expected Outcomes
- Agent cycles remain visible after a run completes.
- On Flow Start shows the prompt and actual inputs, not run metadata.
- Agents can execute tools by default unless the flow explicitly restricts them.

## Report
### Work completed
- Derived agent outputs from sub-run trace ledger records when parent ledger lacks node output.
- Ensured agent/subflow trace panels render even without node output and clear stale waiting metadata on completion.
- Switched On Flow Start synthetic step to use the `input_data` payload only.
- Updated Visual Agent compiler to only set `allowed_tools` when explicitly provided.
- Used resolved step output for preview, raw JSON, and copy actions.

### Tests
- `npm run build` (abstractflow/web/frontend)
