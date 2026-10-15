# 1012 — The model's reasoning text as a node and workflow output

> Package: abstractruntime, abstractflow, (clients later)
> Type: proposal
> Created: 2026-10-11
> Priority: low
> Labels: reasoning, outputs, visualflow

## Summary

Expose the model's reasoning text where a workflow can use it: a `reasoning` output on LLM Call
(and on Agent: the final cycle's, or all cycles'), and optionally an On Flow End `reasoning` pin on
the Runnable / Assistant interfaces, so a host receives it with the answer instead of digging it out
of the ledger.

## Why

Raised 2026-10-11 with 1011 (operator: "create a backlog item for that too"). Today the text exists
only in results and the ledger.

## Current code reality (2026-10-11)

- LLM results carry `reasoning` (`abstractruntime/.../llm_client.py:6815, 6903-6919, 6960, 7502`;
  streamed on a `reasoning` channel `:7268-7306`). The LLM Call node has no reasoning pin: the text
  is only inside its `result` / `raw` / `message` pins (`visualflow_compiler/compiler.py:3177,
  3256-3258`); its meta omits it (`:3213-3240`).
- Agent outputs: `response`, `data`, `success`, `meta`, `scratchpad` (`compiler.py:2619-2626`;
  `abstractflow/src/types/nodes.ts` ~211); ReAct emits a `parse` step with `reasoning`
  (`abstractagent/.../react_runtime.py:2113-2136`).
- Clients read the ledger's LLM_CALL COMPLETED `result.reasoning` (fallback `result.metadata.reasoning`):
  AbstractAssistant `gateway/adapter.py:136-160`, AbstractCode TUI `protocol.rs:1183-1199`,
  Observer `ui/run_steps.ts:473`. AbstractCode web shows none.

## Open questions

- Agent: last cycle's reasoning, every cycle's (a list), or a joined text?
- Size and privacy: reasoning can be long and some providers forbid showing it; opt-in per node?
- Interface: an optional On Flow End pin, or keep hosts on the ledger?

## Promotion criteria

An operator decision on the questions above and a host that needs the text from the workflow
rather than the ledger.
