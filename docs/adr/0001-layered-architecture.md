# ADR-0001: Layered Architecture

## Status
Accepted (2025-12-14); refined by ADR-0032

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-14


## Context

The Abstract Framework needs to support:
- LLM abstraction across multiple providers
- Durable workflow execution with pause/resume
- Agent patterns (ReAct, CodeAct)
- Multi-agent orchestration
- Long-term memory systems

These capabilities have natural dependencies:
- Agents need LLM access
- Agents need durable execution for long-running tasks
- Multi-agent systems need to coordinate individual agents
- Memory workflows may use LLM extraction/embeddings and agent outputs, but the
  memory store itself should remain separately usable

The question: How should these packages depend on each other?

## Decision

Adopt a strict layered architecture where dependencies flow in one direction:

Current refinement (2026-05-06): ADR-0032 updates the package map for the
gateway-first architecture. In particular, `abstractruntime` now has a required
dependency on the tiny standalone `abstractsemantics` package for stable schema
refs; `abstractruntime` still does not hard-depend on `abstractmemory`;
`abstractgateway` is the preferred control-plane boundary for persistent runs;
and `abstractcore` remains free of Runtime imports.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AbstractFlow                                    │
│  Multi-agent orchestration, workflow composition                            │
│  Depends on: AbstractAgent, AbstractRuntime                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AbstractAgent                                   │
│  Agent patterns (ReAct, CodeAct), tool implementations                      │
│  Depends on: AbstractRuntime, AbstractCore                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AbstractRuntime                                  │
│  Durable execution, effect system, pause/resume, ledger                     │
│  Depends on: AbstractSemantics (schema refs)                                │
│  Optional: AbstractCore and AbstractMemory integration modules              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AbstractCore                                    │
│  LLM abstraction, provider routing, tool primitives                         │
│  Depends on: (external only - httpx, pydantic)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Rules

1. **No upward dependencies**: AbstractCore never imports from AbstractRuntime
2. **No circular dependencies**: If A depends on B, B cannot depend on A
3. **Integration modules**: Cross-package integration lives in the higher package
4. **Kernel isolation**: AbstractRuntime kernel has no AbstractCore imports

### AbstractMemory Position

AbstractMemory is a **peer** to AbstractAgent, not a dependency:

Current refinement: AbstractSemantics is the lower-level schema/vocabulary
authority used by Runtime and memory workflows. AbstractMemory remains optional
storage; Runtime/Gateway memory handlers import it only when KG effects or
queries are enabled.

```
                    AbstractCore
                         │
            ┌────────────┴────────────┐
            │                         │
      AbstractAgent ◄─── optional ───► AbstractMemory
            │                         │
            └────────────┬────────────┘
                         │
                    AbstractFlow
```

Both can exist independently:
- AbstractMemory is useful without agents (RAG, search)
- AbstractAgent works without memory (simple scratchpad)

## Consequences

### Positive
- Clear dependency graph prevents circular imports
- Each package can be used independently
- Testing is simpler (mock lower layers)
- Evolution is safer (changes don't ripple upward)

### Negative
- Integration code lives in higher packages (some duplication)
- Cross-cutting concerns (logging, events) need careful design
- Some features require multiple packages

### Neutral
- Documentation must explain the layering
- Users need to understand which package provides what

## Packages Affected
- All packages in the Abstract Framework

## Related
- `abstractruntime/docs/adr/0001_layered_coupling_with_abstractcore.md`
- `abstractcore/docs/research/framework/architecture-discussion1.md`
- `abstractcore/docs/research/framework/architecture-discussion2.md`
