# Agent vs LLM Call (VisualFlow)

VisualFlow has two LLM-oriented nodes that intentionally look similar, but differ in **autonomy**.

## When to use which

### Use **LLM Call**

- You want a **single** LLM request/response step (no internal loop).
- You want to explicitly wire tool execution in the graph:
  - `LLM Call.tool_calls` -> `Tool Calls.tool_calls` -> (your next node).

### Use **Agent**

- You want the node to run an **internal multi-step loop** (ReAct-style) until it finishes or hits a cap.
- You want a runtime-owned **scratchpad** (trace/transcript) for observability.

## Inputs (shared contract)

Agent and LLM Call share the same parameter set and ordering (Agent has one extra cap: `max_iterations`):

1. `use_context` (boolean): include the run's active context messages (`context.messages`) in the request.
2. `context` (object): explicit context override. When provided, `context.messages` overrides inherited run context
   messages.
3. `provider` (provider), `model` (model): route the call.
4. `system` (string): optional system instructions for this node.
5. `prompt` (string): the user prompt/content for this node.
6. `tools` (tools): allowlist of tools the model may request (execution is still explicit in the graph).
7. Agent-only: `max_iterations` (number): maximum internal loop iterations (safety cap).
8. `max_in_tokens` (number): optional per-call/per-agent input token budget (VisualFlow shorthand for
   `max_input_tokens`).
9. `temperature` (number), `seed` (number): sampling controls.
10. `resp_schema` (object): optional JSON Schema for schema-constrained responses.

Notes:
- The canonical prompt key/pin is always `prompt` (there is no `request` alias).

## Outputs (what differs)

### LLM Call outputs

- `response` (string), `success` (boolean), `meta` (object), `tool_calls` (array)

### Agent outputs

- `response` (string), `success` (boolean), `meta` (object), `scratchpad` (object)

There is no separate `result` output pin in the durable contract.

### Agent `scratchpad` (what it contains)

The Agent scratchpad is runtime-owned observability (it can be large). Common fields:

- `messages`: agent-internal transcript for the sub-run (ReAct loop)
- `task`: the agent prompt/task for this node
- `context_extra`: any extra fields passed in `context` besides `task`/`messages` (host-defined)
- `node_traces` / `steps`: structured per-node trace + flattened UI-friendly steps
- `tool_calls` / `tool_results`: best-effort extraction from the trace

## `resp_schema` (structured responses)

When `resp_schema` is provided:

- `response` is a JSON string matching the schema (so it stays a simple `string` pin).
- Use a JSON parser node if you want to treat it as an object downstream.

## RunnableFlow interface (for chat-like clients)

The RunnableFlow (v1) interface (id: `abstractcode.agent.v1`) is the host contract used by AbstractCode, AbstractObserver,
and similar clients:

- `On Flow Start` exposes the same parameter set (in the same order) so hosts can configure a workflow run.
- Required `On Flow Start` pins: `provider`, `model`, `prompt` (everything else optional).
- Required `On Flow End` pins: `response`, `success`, `meta` (others optional).

