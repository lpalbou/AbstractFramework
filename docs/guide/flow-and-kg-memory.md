# Flow + KG Memory (Memory object v0) - Guide

This guide explains how to configure KG memory recall + writeback in VisualFlow using the first-class `memory` object.

It is written for novice users of AbstractFlow and focuses on practical, step-by-step setup.

## What is the `memory` object?

`memory` is a JSON-safe object that groups "what memory the model can use" and "how KG memory is queried/written" into a
single value.

It is designed to:
- keep Agent / LLM Call nodes clean (one pin instead of many),
- be portable (host can pass one object),
- stay backward compatible (legacy per-pin keys still work).

Where it's used:
- Agent node: connect `memory` -> `agent.memory`
- LLM Call node: connect `memory` -> `llm_call.memory`
- RunnableFlow start (optional): `On Flow Start.memory` can be supplied by the client/run modal

## Quick start (recommended): use the Memory literal node

1. In AbstractFlow, add a **Memory** node (Literals -> Memory).
2. Edit its JSON to your desired configuration.
3. Connect:
   - `Memory.value` -> `Agent.memory` (or `LLM Call.memory`)
4. Run the flow and inspect the node trace:
   - When `use_kg_memory=true`, the model should receive a bounded "KG ACTIVE MEMORY" system block when recall finds
     relevant items.

## Provide memory from the client (RunnableFlow)

RunnableFlow workflows (interface `abstractcode.agent.v1`) can accept a `memory` input at start:

1. Ensure your `On Flow Start` node exposes an output pin `memory` (type `memory`).
2. Wire `On Flow Start.memory` into your Agent/LLM Call.
3. In your client (run modal / API), set `memory` as JSON.

### Best practice: defaults + overrides

If you want the flow to have good defaults but still allow overrides from the client:

1. Create a Memory (defaults) literal node (typed `memory`).
2. Ensure `On Flow Start` provides `memory = {}` by default.
3. Merge defaults + overrides and use that output as the effective memory object.

## Memory object schema (v0)

All keys are optional. Omitted keys mean "no override" (runtime defaults apply).

### Recall/source controls (Agent + LLM Call)

- `use_session_attachments: boolean`
- `use_span_memory: boolean`
- `use_semantic_search: boolean` (reserved; not implemented in v0)
- `use_kg_memory: boolean`
- `memory_query: string` (defaults to the node prompt/task if omitted)
- `memory_scope: string` (`run | session | global | all`)
- `recall_level: string` (`urgent | standard | deep`)
- `max_span_messages: number`
- `kg_max_input_tokens: number`
- `kg_limit: number`
- `kg_min_score: number` (0..1)

### KG write defaults (useful for ingest subflows)

- `kg_write_scope: string` (`run | session | global`)
- `kg_domain_focus: string`
- `kg_max_out_tokens: number` (0 means "no cap")

## Example memory object

```json
{
  "use_session_attachments": true,
  "use_span_memory": false,
  "use_semantic_search": false,
  "use_kg_memory": true,
  "memory_query": "",
  "memory_scope": "session",
  "recall_level": "standard",
  "max_span_messages": 24,
  "kg_max_input_tokens": 1200,
  "kg_limit": 80,
  "kg_min_score": 0.35,
  "kg_write_scope": "session",
  "kg_domain_focus": "software / agents / memory systems",
  "kg_max_out_tokens": 0
}
```

## Query and insert (KG recall + KG writeback)

### Query (recall)

To make an Agent/LLM Call use KG recall:
1. Set `memory.use_kg_memory = true`.
2. Optionally set `memory.memory_query` (otherwise the prompt is used).
3. Choose `memory.memory_scope`:
   - `session` is common when you want continuity within one client session.
   - `global` is common when you want durability across independent runs.

### Insert (writeback)

To write new knowledge into the KG, run an ingestion step/subflow after you produce an answer.
The typical pattern is to build a turn transcript string and pass it to an extractor that writes assertions using:
- scope from `memory.kg_write_scope` (or a fixed literal)
- domain hint from `memory.kg_domain_focus`

