# ADR-0005: Memory Architecture

## Status
Proposed (2025-12-14)

## Dates
- Proposed: 2025-12-14
- Accepted: (TBD)


## Context

The Abstract Series needs memory capabilities at multiple levels:
1. **Per-run working memory** - State during a single workflow execution
2. **Cross-run long-term memory** - Persistent knowledge across sessions
3. **Processing capabilities** - Summarization, extraction, assessment

Research into SOTA frameworks (Letta/MemGPT, Mem0, Zep, AgentScope) reveals:
- Memory is application-specific (no one-size-fits-all)
- Three memory types: Episodic, Semantic, Procedural
- Graph-based memory outperforms vector-only for complex reasoning
- Scheduled consolidation (daily/weekly/monthly) enables temporal tracking

## Decision

### 1. Separate Concerns by Package

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEMORY RESPONSIBILITY BY PACKAGE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AbstractCore                                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│  - BasicSession (conversation state, auto-compact)                          │
│  - Processing modules (summarizer, extractor, judge)                        │
│  - Provider-agnostic LLM access                                             │
│                                                                             │
│  AbstractRuntime                                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  - RunState.vars (per-run working memory)                                   │
│  - ArtifactStore (large payloads)                                           │
│  - LedgerStore (execution history - episodic)                               │
│  - Processing helpers (state-graph aware wrappers)                          │
│                                                                             │
│  AbstractAgent                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  - Workflow definitions using memory                                        │
│  - Agent-specific memory patterns (scratchpad, observations)                │
│                                                                             │
│  AbstractMemory (Future)                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  - Memory Blocks (Letta-style, always-visible context)                      │
│  - Archival Memory (semantic search, unlimited storage)                     │
│  - Knowledge Graphs (entity relationships, temporal edges)                  │
│  - Scheduled Consolidation (daily/weekly/monthly summaries)                 │
│  - Cross-agent memory sharing                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. AbstractRuntime Gets ArtifactStore (Not Full Memory)

AbstractRuntime needs to store large payloads that don't fit in `run.vars`:

```python
class ArtifactStore(ABC):
    def put(self, run_id: str, key: str, data: bytes, ...) -> str: ...
    def get(self, artifact_id: str) -> Tuple[bytes, str, Dict]: ...
    def list(self, run_id: str) -> List[Dict]: ...
    def delete(self, artifact_id: str) -> None: ...
```

This is **not** long-term memory. Artifacts are scoped to a run and can be cleaned up when the run completes.

**Important clarification (active vs stored memory):**
- `RunState.vars` may contain an **active context view** (what is sent to an LLM).
- The full underlying source (message spans, large tool outputs) must remain durably accessible via stores (RunStore/LedgerStore/ArtifactStore).

This separation and the provenance requirements for compaction are codified in:
- [ADR-0007: Active Context vs Stored Memory (Provenance)](0007-active-context-and-memory-provenance.md)

### 3. AbstractRuntime Remains Independent (Adapters Pattern)

The current design with `integrations/abstractcore/` is **correct**:

```
AbstractRuntime (pure kernel)
└── integrations/
    └── abstractcore/     # Adapter for AbstractCore
        ├── llm_client.py
        ├── effect_handlers.py
        └── tool_executor.py
```

**Why this is right:**
- AbstractRuntime is a generic workflow kernel (not LLM-specific)
- Could orchestrate non-LLM workflows (data pipelines, scheduled jobs)
- Enables thin client mode (runtime on edge, LLM on server)
- Proper separation of concerns
- Testing without LLM dependencies

**AbstractAgent** is where the coupling happens - it depends on both AbstractCore and AbstractRuntime.

### 4. AbstractMemory is a Separate Project (Design TBD)

Long-term memory is complex and application-specific. It deserves its own package.

> **Note**: This is preliminary thinking, not final design. The actual AbstractMemory architecture will be disclosed later after deeper analysis.

**Concepts being explored (inspired by SOTA):**
- **Memory Blocks** (Letta) - Always-visible context sections
- **Archival Memory** (Letta) - Semantic search over unlimited storage
- **Temporal Edges** (Zep/Graphiti) - Facts with `valid_from`/`valid_until`
- **Scheduled Consolidation** - Daily/weekly/monthly summaries for temporal tracking
- **Knowledge Graphs** - Entity-relationship storage
- **Procedural Memory** (Mem^p) - Abstract skill templates
- **Destructive Updates** (Mem0) - Conflict resolution, not append-only

**Open questions:**
- Does AbstractMemory depend on AbstractAgent (for agentic consolidation)?
- Or are they peers that optionally connect?
- How does scheduled consolidation work without agents?

**Not in scope for AbstractMemory:**
- Per-run state (that's AbstractRuntime)
- Conversation history (that's BasicSession or run.vars)
- LLM weights/fine-tuning (that's model training)

### 5. Processing Stays in AbstractCore

The processing modules (BasicSummarizer, BasicExtractor, BasicJudge) work on text. They don't need state-graph awareness.

AbstractRuntime provides thin wrappers that:
1. Serialize state-graph to text
2. Call AbstractCore processor
3. Store results back in run.vars or ArtifactStore

```python
# abstractruntime/processing/helpers.py
from abstractcore.processing import BasicSummarizer

def compact_messages(messages: List[Dict], summarizer: BasicSummarizer = None) -> Dict:
    """Summarize conversation messages."""
    if summarizer is None:
        summarizer = BasicSummarizer()
    
    text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    result = summarizer.summarize(text, style=SummaryStyle.CONVERSATIONAL)
    
    return {
        "summary": result.summary,
        "key_points": result.key_points,
        "original_count": len(messages),
    }
```

## Consequences

### Positive
- Clear separation of concerns
- AbstractRuntime stays focused on durable execution (generic kernel)
- AbstractMemory can evolve independently
- Processing modules are reusable across packages
- No premature complexity in runtime
- Adapters pattern enables flexibility (thin client, non-LLM workflows)

### Negative
- AbstractMemory is not yet implemented
- Cross-run memory requires additional package
- Some duplication between BasicSession and runtime memory patterns

### Neutral
- AbstractRuntime stays independent (adapters connect to AbstractCore)
- Apps module stays in AbstractCore (CLI wrappers, not agent-specific)

## Implementation Roadmap

### Phase 1: Runtime Improvements (Now)
1. Add ArtifactStore to AbstractRuntime (implemented in `abstractruntime.storage.artifacts`)
2. Keep AbstractCore integration via adapters only (no dependency from runtime kernel)
3. Add processing helpers (via adapters/wrappers)

### Phase 2: Agent Improvements (Next)
1. Implement structured vars namespacing
2. Add CodeActAgent
3. Improve REPL

### Phase 3: AbstractMemory (Future)
1. Design Memory Block abstraction
2. Implement Archival Memory with vector search
3. Add Knowledge Graph integration
4. Implement scheduled consolidation

## Related
- Research: `abstractcore/docs/research/memory/Agentic AI Persistent Memory Overview.md`
- Architecture: `abstractcore/docs/research/framework/acore-runtime.md`
- Backlog: `docs/backlog/completed/014-abstractruntime-artifact-store.md`
- Letta docs: Memory blocks, Archival memory
- Mem0: Hybrid vector-graph architecture
- Zep: Temporal knowledge graphs (Graphiti)
