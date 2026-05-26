# ADR-0002: Effect System Design

## Status
Accepted (2025-12-14)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-14


## Context

Agentic workflows need to perform side effects:
- LLM calls (non-deterministic, expensive)
- Tool execution (may have real-world impact)
- User interaction (pause for input)
- External service calls (network, databases)

Traditional approaches:
1. **Direct execution**: Call LLM/tools directly in workflow code
2. **Callback pattern**: Pass callbacks for side effects
3. **Effect pattern**: Return effect requests, let runtime execute

Problems with direct execution:
- Can't pause/resume (Python stack is lost)
- Can't replay without re-executing side effects
- Can't record what happened (ledger)
- Can't retry with different strategies

## Decision

Adopt an **effect system** where workflow nodes return effect requests instead of executing side effects directly.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EFFECT SYSTEM DESIGN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Workflow Node                    Runtime                    Effect Handler │
│  ────────────                    ───────                    ────────────── │
│       │                              │                              │       │
│       │  StepPlan(effect=...)        │                              │       │
│       │─────────────────────────────▶│                              │       │
│       │                              │  execute effect              │       │
│       │                              │─────────────────────────────▶│       │
│       │                              │                              │       │
│       │                              │  EffectOutcome               │       │
│       │                              │◀─────────────────────────────│       │
│       │                              │                              │       │
│       │                              │  record in ledger            │       │
│       │                              │  update run state            │       │
│       │                              │  transition to next node     │       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Effect Types

```python
class EffectType(str, Enum):
    # Waiting primitives
    WAIT_EVENT = "wait_event"    # Wait for external signal
    WAIT_UNTIL = "wait_until"    # Wait for time
    ASK_USER = "ask_user"        # Wait for user input
    
    # Integration effects
    LLM_CALL = "llm_call"        # Call LLM
    TOOL_CALLS = "tool_calls"    # Execute tools
    
    # Composition
    START_SUBWORKFLOW = "start_subworkflow"
```

### Effect Outcomes

```python
class EffectOutcome:
    status: str  # "completed" | "waiting" | "failed"
    result: Optional[Dict]      # For completed
    wait: Optional[WaitState]   # For waiting
    error: Optional[str]        # For failed
```

### Workflow Node Contract

Nodes return `StepPlan` instead of executing directly:

```python
def reason_node(run: RunState, ctx) -> StepPlan:
    # DON'T: llm.generate(prompt)  # Direct execution
    
    # DO: Return effect request
    return StepPlan(
        node_id="reason",
        effect=Effect(
            type=EffectType.LLM_CALL,
            payload={"prompt": prompt, "tools": tools},
            result_key="llm_response",
        ),
        next_node="parse",
    )
```

### Effect Handlers

Effect handlers are pluggable and registered with the runtime:

```python
def make_llm_call_handler(llm: LLMClient) -> EffectHandler:
    def handler(run: RunState, effect: Effect, next_node: str) -> EffectOutcome:
        result = llm.generate(**effect.payload)
        return EffectOutcome.completed(result=result)
    return handler

runtime = Runtime(
    effect_handlers={
        EffectType.LLM_CALL: make_llm_call_handler(llm),
        EffectType.TOOL_CALLS: make_tool_calls_handler(tools),
    }
)
```

## Consequences

### Positive
- **Durable execution**: State is serializable, no Python stack needed
- **Ledger recording**: Every effect is recorded for audit/replay
- **Pause/resume**: WAITING effects naturally support long pauses
- **Retry/idempotency**: Runtime can retry effects with policies
- **Testability**: Mock effect handlers for testing
- **Flexibility**: Different handlers for different topologies

### Negative
- **Indirection**: More complex than direct execution
- **Learning curve**: Developers must understand effect pattern
- **Boilerplate**: Nodes return StepPlan instead of values

### Neutral
- Effect handlers are the integration point with AbstractCore
- Built-in effects (WAIT_*) are handled by runtime kernel

## Packages Affected
- **AbstractRuntime**: Defines and executes effects
- **AbstractAgent**: Workflows emit effects
- **AbstractFlow**: Orchestration workflows emit effects

## Related
- `abstractruntime/src/abstractruntime/core/models.py` - Effect types
- `abstractruntime/src/abstractruntime/core/runtime.py` - Effect execution
- `abstractruntime/src/abstractruntime/integrations/abstractcore/effect_handlers.py`
