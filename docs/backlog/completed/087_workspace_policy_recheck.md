## Task
Verify post-fix workspace path behavior and prompt contents for gateway runs.

## Summary
Run a fresh gateway flow to confirm absolute-path tool usage works under
`workspace_access_mode=all_except_ignored`, and verify that workspace policy
prompt guidance is fully removed from the ReAct system prompt.

## Reason
The prior failure showed the agent refusing absolute paths due to prompt
guidance. We need an empirical re-check to confirm runtime-only enforcement.

## Scope
- Do: publish the test VisualFlow, start a run with an absolute path prompt,
  inspect the LLM system prompt in the ledger, approve the tool call, and
  verify execution succeeded at the absolute path.
- Do not: modify production flows or change gateway policy defaults.

## Dependencies
- Running gateway on the local dev environment.
- Access to `ABSTRACTGATEWAY_AUTH_TOKEN`.

## Expected Outcomes
- Evidence that absolute-path tool calls execute under `all_except_ignored`.
- Confirmation whether the system prompt still includes workspace policy
  guidance (and whether a gateway restart is required to clear it).

## Full Report
- **Test flow**: Published VisualFlow `b4c6f107` (name `test`) to bundle `test@dev`.
- **Run execution**: Started root run `7d64d441-4cec-4a8a-bf5d-b379794bb792` with
  prompt `write a snake game in /Users/alboul/flow-rtype/` and
  `workspace_access_mode=all_except_ignored`; subrun `1e9eb790-ea80-4572-a099-08c7489a2d45`
  created for the agent node.
- **Prompt check**: The LLM system prompt in `llm_call` still contains the
  "Workspace policy (runtime-enforced)" block; this indicates the running
  gateway process has not been restarted since prompt removal.
- **Tool approval**: Approved the waiting tool call via
  `/api/gateway/commands` (requires `command_id`), using wait key
  `tool_approval:8befcbba158448138ef7873170ab29ff`.
- **Result**: `execute_command` succeeded and wrote files to the absolute path
  `/Users/alboul/flow-rtype/snake-game`, confirming runtime path gating allows
  absolute paths under `all_except_ignored`.
- **Side effects**: The snake game files were created under
  `/Users/alboul/flow-rtype/snake-game`.
