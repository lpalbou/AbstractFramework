# ADR-0003: Tool System Architecture

## Status
Accepted (2025-12-14)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-14


## Context

AbstractCore provides tool support for LLMs. The current implementation has:
- Two `@tool` decorators with different behavior
- A global registry for tool lookup
- Two execution modes (`execute_tools=True/False`)
- Multiple deployment topologies (local, remote, passthrough)

This creates confusion about:
- Which decorator to use
- When to use the registry
- How tools flow through the system

## Decision

### 1. Tool Definition: Single `@tool` Decorator

**Current state (problematic):**
- `abstractcore.tools.core.tool` (line 108) - Creates `_tool_definition`, no registration
- `abstractcore.tools.registry.tool` (line 311) - Registers globally, no `_tool_definition`

**Decision:** Keep only `core.tool`, remove `registry.tool`

```python
from abstractcore.tools import tool

@tool(name="get_weather", description="Get weather for a city")
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 22C"

# Creates get_weather._tool_definition with:
# - name, description, parameters schema
# - Reference to the function
```

### 2. Tool Registry: Session-Level, Not Global

**Current state (problematic):**
- Global `_global_registry` singleton
- `BasicSession._register_tools()` registers on init
- Provider `execute_tools()` looks up in global registry
- AbstractRuntime executes tool calls via a host-configured `ToolExecutor` (see ADR-0006)

**Decision:** Make registry a session-level concern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TOOL REGISTRY SCOPE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BEFORE: Global Registry                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  BasicSession(tools=[...])                                                  │
│       │                                                                     │
│       ▼                                                                     │
│  _register_tools() → _global_registry (singleton)                           │
│       │                                                                     │
│       ▼                                                                     │
│  provider.generate(execute_tools=True)                                      │
│       │                                                                     │
│       ▼                                                                     │
│  execute_tools() → _global_registry.get(name)                               │
│                                                                             │
│  Problems:                                                                  │
│  - Global state (hard to test, race conditions)                             │
│  - Order-dependent (must register before use)                               │
│  - Confusing with AbstractRuntime (which ignores it)                        │
│                                                                             │
│  AFTER: Session-Level Registry                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  BasicSession(tools=[...])                                                  │
│       │                                                                     │
│       ▼                                                                     │
│  self._tool_registry = {name: func for ...}  # Instance variable            │
│       │                                                                     │
│       ▼                                                                     │
│  session.generate() → provider.generate(execute_tools=False)                │
│       │                                                                     │
│       ▼                                                                     │
│  session._execute_tools() → self._tool_registry.get(name)                   │
│                                                                             │
│  Benefits:                                                                  │
│  - No global state                                                          │
│  - Session owns its tools                                                   │
│  - Consistent with AbstractRuntime pattern                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. Execution Modes: Passthrough as Default

**Decision:** Provider always returns raw tool calls. Execution is caller's responsibility.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXECUTION FLOW                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Provider (AbstractCore)                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  provider.generate(prompt, tools=[...])                                     │
│       │                                                                     │
│       ▼                                                                     │
│  1. Format tools into prompt (UniversalToolHandler)                         │
│  2. Call LLM                                                                │
│  3. Return response with raw content                                        │
│       │                                                                     │
│       ▼                                                                     │
│  response.content = "<|tool_call|>{...}</|tool_call|>"                      │
│                                                                             │
│  Caller (Session or Runtime)                                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # BasicSession path                                                        │
│  session.generate(prompt)                                                   │
│       │                                                                     │
│       ▼                                                                     │
│  1. Call provider.generate()                                                │
│  2. Parse tool calls from response                                          │
│  3. Execute tools using session._tool_registry                              │
│  4. Add results to conversation                                             │
│  5. Continue if needed                                                      │
│                                                                             │
│  # AbstractRuntime path                                                     │
│  LocalAbstractCoreLLMClient.generate()                                      │
│       │                                                                     │
│       ▼                                                                     │
│  1. Call provider.generate()                                                │
│  2. Parse tool calls (UniversalToolHandler)                                 │
│  3. Return structured result                                                │
│       │                                                                     │
│       ▼                                                                     │
│  TOOL_CALLS effect handler                                                  │
│       │                                                                     │
│       ▼                                                                     │
│  Execute tools via ToolExecutor.execute(tool_calls)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Deployment Topologies

The passthrough model enables multiple deployment scenarios:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT TOPOLOGIES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TOPOLOGY 1: Local Execution (Development)                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Same Process                                                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │   │
│  │  │  Agent  │─▶│ Runtime │─▶│  Core   │─▶│  Ollama │                 │   │
│  │  │         │  │         │  │         │  │ (local) │                 │   │
│  │  │  Tools  │◀─│ Execute │◀─│ Parse   │◀─│         │                 │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOPOLOGY 2: Backend Execution (Production)                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌─────────────┐         ┌─────────────────────────────────────────────┐   │
│  │   Client    │  HTTP   │              Server                          │   │
│  │  (thin UI)  │────────▶│  Agent → Runtime → Core → OpenAI            │   │
│  │             │◀────────│  Tools executed on server                   │   │
│  └─────────────┘         └─────────────────────────────────────────────┘   │
│                                                                             │
│  TOPOLOGY 3: Client Execution (Thin Server)                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌─────────────────────────────────────────────┐         ┌─────────────┐   │
│  │              Client                          │  HTTP   │   Server    │   │
│  │  Agent → Runtime → Tools (local)            │────────▶│ Core only   │   │
│  │                    ↓                         │         │ (LLM proxy) │   │
│  │              Execute locally                 │◀────────│             │   │
│  └─────────────────────────────────────────────┘         └─────────────┘   │
│                                                                             │
│  TOPOLOGY 4: Remote Tool Worker (Sandboxed)                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐           │
│  │   Agent     │────────▶│   Runtime   │────────▶│ Tool Worker │           │
│  │             │         │  (no tools) │         │ (sandboxed) │           │
│  │             │◀────────│   WAITING   │◀────────│             │           │
│  └─────────────┘         └─────────────┘         └─────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5. Code References

| Component | File | Line | Purpose |
|-----------|------|------|---------|
| `@tool` decorator | `abstractcore/tools/core.py` | 108 | Creates `_tool_definition` |
| `@tool` (duplicate) | `abstractcore/tools/registry.py` | 311 | **TO BE REMOVED** |
| `_global_registry` | `abstractcore/tools/registry.py` | 17 | **TO BE DEPRECATED** |
| `_register_tools` | `abstractcore/core/session.py` | 568 | Session tool registration |
| `execute_tools` | `abstractcore/tools/registry.py` | 289 | Global registry execution |
| Tool parsing | `abstractruntime/.../llm_client.py` | 174 | Runtime parses tool calls |
| Tool execution | `abstractruntime/.../effect_handlers.py` | - | Runtime executes tools |

## Consequences

### Positive
- Single `@tool` decorator - no confusion
- Session-level registry - no global state
- Passthrough default - consistent with runtime
- Clear separation: Core formats, caller executes

### Negative
- Breaking change for `execute_tools=True` users
- Migration needed for code using global registry

### Migration Path

```python
# Before (global registry)
from abstractcore.tools.registry import register_tool
register_tool(my_tool)
llm.generate("...", execute_tools=True)

# After (session-level)
from abstractcore import BasicSession
from abstractcore.tools import tool

@tool
def my_tool(...): ...

session = BasicSession(tools=[my_tool])
session.generate("...")  # Session handles execution
```

## Implementation

See backlog task: `docs/backlog/completed/013-abstractcore-consolidate-tool-decorator.md`

## Packages Affected
- **AbstractCore**: Remove duplicate decorator, deprecate global registry
- **AbstractRuntime**: TOOL_CALLS executes via `ToolExecutor` (durable; no callables in RunState)
- **AbstractAgent**: Persist tool specs only; host wires tool execution via ToolExecutor

## Investigation Notes (2025-12-14)

### Why AbstractRuntime Uses a ToolExecutor Instead of Persisting Callables

AbstractRuntime is designed for **durable execution** with JSON-serializable state. Key differences:

| Aspect | BasicSession | AbstractRuntime |
|--------|--------------|-----------------|
| State storage | In-memory `self.messages` | `RunState.vars` (JSON-serializable) |
| Persistence | `to_dict()`/`from_dict()` | `RunStore.save()`/`load()` |
| Tool execution | Session-level `_tool_registry` | Host-configured `ToolExecutor` |
| Execution model | Synchronous loop | Effect-based with pause/resume |

AbstractRuntime persists **tool specs** (schemas/metadata) in `RunState.vars` for auditability, but never persists tool callables. Tool callables live in-process only and are provided by the host (runtime/session) via a `ToolExecutor`.

### Provider execute_tools Support

All providers support `execute_tools` parameter (default: `False`):
- `anthropic_provider.py` - Line 479
- `huggingface_provider.py` - Line 1708
- `lmstudio_provider.py` - Lines 136, 269, 399, 506
- `mlx_provider.py` - Line 25 (imports)
- `ollama_provider.py` - Lines 303, 382, 536, 605
- `openai_compatible_provider.py` - Lines 187, 319, 449, 556
- `openai_provider.py` - Line 513
- `vllm_provider.py` - Lines 142, 274, 397, 514

### BasicSession vs AbstractRuntime Serialization

**BasicSession** (`session.py:463-563`):
- Uses `session-archive/v1` schema
- Serializes: id, created_at, provider name, model, system_prompt, tool_registry (schemas only), messages
- Does NOT serialize: provider instance, tool callables

**AbstractRuntime** (`models.py:113-145`):
- Uses `RunState` dataclass
- Serializes: run_id, workflow_id, status, current_node, vars, waiting, output, error, timestamps
- Stores tool schemas in `vars`, not callables

### Does AbstractRuntime Need BasicSession?

**No.** They serve different purposes:

- **BasicSession**: Stateful conversation wrapper for interactive use
- **AbstractRuntime**: Durable workflow execution with pause/resume

AbstractRuntime's `LocalAbstractCoreLLMClient` uses providers directly, not sessions. This is intentional - sessions add state management that conflicts with runtime's own state model.

### Where Should Registry Live?

**Recommendation**: Keep current architecture with clarification:

1. **Global registry** (`_global_registry`): Deprecated, remove in v2
2. **Session registry** (`BasicSession._tool_registry`): For interactive use
3. **Runtime tool execution** (`ToolExecutor`): For durable execution (ADR-0006)

The key insight: tool *schemas* are portable (JSON), but tool *callables* are not. Each layer manages its own callable lookup.

## Related
- `abstractcore/abstractcore/tools/core.py:108` - Current `@tool` decorator
- `abstractcore/abstractcore/tools/registry.py:311` - Duplicate decorator (remove)
- `abstractcore/abstractcore/core/session.py:568` - Session tool registration
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py:174` - Parsing
