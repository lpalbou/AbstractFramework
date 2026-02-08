# Scenario: Specialized Agent as a Portable `.flow`

Goal: build a specialized agent once, then run it in:

- AbstractCode (terminal)
- Code Web UI (browser)
- AbstractObserver (browser)
- your own apps (via gateway bundle discovery)

The key is an interface contract: `abstractcode.agent.v1`.

## Step 1: Create the flow

In the Flow Editor (`npx @abstractframework/flow`):

1. Add an **On Flow Start** node.
2. Add an **Agent** node (or **LLM Call** for a single-shot step).
3. Add an **On Flow End** node.
4. Wire the pins:
   - Start outputs to Agent inputs: `provider`, `model`, `prompt` (and optional `tools`, `context`, `memory`)
   - Agent outputs to End inputs: `response`, `success`, `meta` (and optional `scratchpad`)
5. In flow properties, set:
   - `interfaces: ["abstractcode.agent.v1"]`

## Agent vs LLM Call

- Use **Agent** when you want an internal multi-step loop (ReAct/CodeAct/MemAct style).
- Use **LLM Call** when you want a single request/response and explicit tool wiring in the graph.

See [Guide: Agent vs LLM Call](../guide/agent-vs-llm.md).

## Step 2: Export as a bundle

Export the workflow as a `.flow` bundle.

A `.flow` bundle packages:
- the root VisualFlow JSON
- any referenced subflows
- optional assets

## Step 3: Run locally (terminal)

With AbstractCode:

```bash
abstractcode --workflow /path/to/my-agent.flow
```

Or install the bundle into the local registry:

```bash
abstractcode workflow install /path/to/my-agent.flow
abstractcode --workflow my-agent
```

## Step 4: Deploy to a gateway

Copy the `.flow` bundle into `ABSTRACTGATEWAY_FLOWS_DIR`.

Then it will appear in:
- Observer workflow picker
- Code Web UI workflow picker
- Gateway discovery endpoints

## Step 5: Pass memory (optional)

If you want KG memory recall/writeback, wire a `memory` object into the Agent/LLM Call node.

See [Guide: Flow + KG memory](../guide/flow-and-kg-memory.md).

