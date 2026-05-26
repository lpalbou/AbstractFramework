# Backlog Item: Flow agent non-agency + max-iterations default

## Summary
- Investigate run `6d4a7f5e-3244-4726-a7ca-1066379b73eb` and its subflows to pinpoint non-agency causes.
- Align gateway-first execution with legacy server behavior for prompt/tool handling.
- Set Agent `max_iterations` default to 50 and surface it in the flow and properties UI.

## Reason
- Agent runs are underperforming compared to the previous server/client architecture.
- Users need consistent prompt logic and reliable tool execution.
- The max-iterations safety cap should match expected defaults and be visible in the UI.

## Scope
### In scope
- Compare legacy WebSocket server execution semantics to gateway-hosted execution.
- Fix agent tool allowlist defaults and runtime defaults where mismatched.
- Pass run input data into runtime initialization when starting gateway runs.
- Update runtime defaults to 50 iterations and expose the value in the UI.
- Inspect run history bundle for `6d4a7f5e-3244-4726-a7ca-1066379b73eb` (requires gateway auth).

### Out of scope
- Large UI redesigns outside the agent run details/pin defaults.
- Changing gateway auth policy or disabling auth.
- Altering AbstractAgent core prompting beyond flow/runtime wiring.

## Dependencies
- Gateway run history endpoint access (auth token).
- AbstractRuntime VisualFlow compiler + AbstractFlow UI.

## Expected Outcomes
- Identified root causes for non-agency in the specified run.
- Agent tooling/prompt behavior matches legacy expectations.
- Max-iterations default set to 50 and visible in node + properties panel.

## Report
### What I found (root causes)
- The root run is waiting on a subworkflow; the subrun is waiting for **tool approval** (reason `user`, wait key `tool_approval:*`) after issuing three `execute_command` calls. The UI was not surfacing this approval gate for subruns, so the agent looked “stuck.”
- The agent node in the workflow snapshot is configured with `tools: ["execute_command"]` and `pinDefaults.max_iterations = 5`, which explains the “Iteration 1/5” and the lack of web/search tools in that run.
- Gateway-hosted runs were not passing `input_data` into `create_visual_runner`, so runtime defaults could drift from the run’s configured provider/model (legacy server passed input data explicitly).

### Fixes implemented
- **Tool approval UI for subruns**: ledger wait details now flow through `ExecutionEvent → WaitingInfo`, and the run details panel displays an approval UI (approve/deny) even when the parent step is running and the wait originates from a subrun.
- **Approval placement UX**: approvals now live in a dedicated footer bar with a full tool-call detail panel; the UI no longer forces step selection, so users can browse any step during a run.
- **Resume payload support**: resume commands now accept `approved: true|false` payloads to execute tool approvals via runtime-owned execution.
- **Default tools behavior**: when agent tools are *not specified*, workflow specs now allow the default tool set (matching legacy expectations).
- **Max-iterations default**:
  - Runtime defaults raised to **50**.
  - VisualFlow agent nodes now default `pinDefaults.max_iterations` to **50** and the properties panel exposes the field.
  - Flow loading migration fills the default when missing.
- **Gateway parity**: `input_data` is now passed into `create_visual_runner` (start + resume) so provider/model defaults match run inputs.

### Tests run
- `npm run build` (AbstractFlow frontend)
- `python -m pytest abstractruntime/tests/test_tool_approval_resume_executes.py -q`
- `python -m pytest abstractruntime/tests/test_visual_agent_tool_observations_persist_across_restart.py -q`

### Notes for the specific run
- The run’s workflow snapshot explicitly pins `tools = ["execute_command"]` and `max_iterations = 5`. With the new UI approval flow, the user can now approve those tool calls, but for richer agency (web search + fetch), update the flow’s tool allowlist accordingly.
