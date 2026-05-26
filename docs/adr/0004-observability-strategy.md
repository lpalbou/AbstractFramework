# ADR-0004: Observability Strategy

## Status
Accepted (2025-12-14)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-14


## Context

The Abstract Framework has multiple observability mechanisms that evolved independently:
- **AbstractCore events**: GENERATION_STARTED, TOOL_COMPLETED, etc.
- **AbstractCore tracing**: `enable_tracing=True`, `trace_id`, `trace_metadata`
- **AbstractCore structured logging**: `get_logger()` with structured fields
- **AbstractRuntime ledger**: StepRecord with effect details
- **AbstractRuntime hash chain**: Tamper-evident audit trail
- **AbstractRuntime ActorFingerprint**: AI identity tracking

These mechanisms don't integrate well:
- Events and ledger use different schemas
- No unified trace ID across packages
- Client/server scenarios fragment observability
- No way to track a single agent across its full lifecycle

### Key Questions

1. **What is a trace_id?** Is it per-request, per-task, or per-agent-session?
2. **How does trace_id relate to AI fingerprint?** Are they the same concept?
3. **How do we track specialized agents (DeepSearch) that are workflows themselves?**
4. **How do we track multi-agent systems composed of multiple sub-agents?**

## Decision

### 1. Trace Hierarchy

Define a clear hierarchy of identifiers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRACE HIERARCHY                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  actor_id (AI Fingerprint)                                                  │
│  ├── Identifies WHO: the agent/service/human                                │
│  ├── Stable across sessions                                                 │
│  ├── Bound to public key (when signatures enabled)                          │
│  └── Example: "ar_abc123def456..."                                          │
│                                                                             │
│  session_id                                                                 │
│  ├── Identifies a continuous agent session                                  │
│  ├── Created when agent starts, persists across tasks                       │
│  ├── Survives pause/resume                                                  │
│  └── Example: "sess_xyz789..."                                              │
│                                                                             │
│  run_id                                                                     │
│  ├── Identifies a single workflow execution                                 │
│  ├── One task = one run_id                                                  │
│  ├── Already exists in AbstractRuntime                                      │
│  └── Example: "550e8400-e29b-41d4-a716-446655440000"                        │
│                                                                             │
│  trace_id                                                                   │
│  ├── Identifies a single LLM interaction                                    │
│  ├── One generate() call = one trace_id                                     │
│  ├── Already exists in AbstractCore                                         │
│  └── Example: "tr_abc123..."                                                │
│                                                                             │
│  span_id (future)                                                           │
│  ├── Identifies a sub-operation within a trace                              │
│  ├── For OpenTelemetry compatibility                                        │
│  └── Example: "span_def456..."                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Relationship Between Identifiers

```
actor_id (WHO)
    │
    └── session_id (WHEN - continuous session)
            │
            ├── run_id (WHAT - task 1)
            │       │
            │       ├── trace_id (LLM call 1)
            │       ├── trace_id (LLM call 2)
            │       └── trace_id (LLM call 3)
            │
            └── run_id (WHAT - task 2)
                    │
                    ├── trace_id (LLM call 1)
                    └── trace_id (LLM call 2)
```

### 3. Tracking Specialized Agents (Workflows)

A specialized agent like DeepSearch is a workflow with sub-runs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEEPSEARCH AS WORKFLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DeepSearchAgent.start("Research quantum computing")                        │
│       │                                                                     │
│       ▼                                                                     │
│  run_id: "main-run-123"                                                     │
│  actor_id: "ar_deepsearch_abc"                                              │
│       │                                                                     │
│       ├── plan_node                                                         │
│       │       └── trace_id: "tr_plan_001" (LLM call)                        │
│       │                                                                     │
│       ├── search_node (sub-agent)                                           │
│       │       └── sub_run_id: "search-run-456"                              │
│       │           └── parent_run_id: "main-run-123"                         │
│       │           └── trace_id: "tr_search_001"                             │
│       │           └── trace_id: "tr_search_002"                             │
│       │                                                                     │
│       ├── fetch_node (function, no LLM)                                     │
│       │                                                                     │
│       └── synthesize_node (sub-agent)                                       │
│               └── sub_run_id: "synth-run-789"                               │
│                   └── parent_run_id: "main-run-123"                         │
│                   └── trace_id: "tr_synth_001"                              │
│                                                                             │
│  All linked by parent_run_id for full trace reconstruction                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Tracking Multi-Agent Systems

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT ORCHESTRATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Orchestrator (AbstractFlow)                                                │
│  actor_id: "ar_orchestrator_001"                                            │
│  run_id: "orch-run-000"                                                     │
│       │                                                                     │
│       ├── ResearcherAgent                                                   │
│       │   actor_id: "ar_researcher_002"                                     │
│       │   run_id: "research-run-111"                                        │
│       │   parent_run_id: "orch-run-000"                                     │
│       │       │                                                             │
│       │       └── trace_id: "tr_research_*"                                 │
│       │                                                                     │
│       ├── CoderAgent                                                        │
│       │   actor_id: "ar_coder_003"                                          │
│       │   run_id: "code-run-222"                                            │
│       │   parent_run_id: "orch-run-000"                                     │
│       │       │                                                             │
│       │       └── trace_id: "tr_code_*"                                     │
│       │                                                                     │
│       └── ReviewerAgent                                                     │
│           actor_id: "ar_reviewer_004"                                       │
│           run_id: "review-run-333"                                          │
│           parent_run_id: "orch-run-000"                                     │
│               │                                                             │
│               └── trace_id: "tr_review_*"                                   │
│                                                                             │
│  Query: "Show me all activity for orch-run-000"                             │
│  Result: All sub-runs and their traces, linked by parent_run_id             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5. Centralized Event Emission with Channels

**All events flow through a single event bus with channel support:**

```python
# abstractcore/events/bus.py

class EventBus:
    """Centralized event bus with channel support for agent-agent communication."""
    
    _subscribers: Dict[EventType, List[Callable]] = {}
    _channel_subscribers: Dict[str, Dict[EventType, List[Callable]]] = {}
    _collectors: List[EventCollector] = []
    
    @classmethod
    def emit(cls, event: FrameworkEvent, channel: Optional[str] = None) -> None:
        """Emit an event to subscribers and collectors.
        
        Args:
            event: The event to emit
            channel: Optional channel for targeted delivery
        """
        # Always log for observability (all channels)
        for collector in cls._collectors:
            collector.collect(event)
        
        # Deliver to channel subscribers (if channel specified)
        if channel and channel in cls._channel_subscribers:
            for subscriber in cls._channel_subscribers[channel].get(event.event_type, []):
                subscriber(event)
        
        # Deliver to global subscribers (no channel filter)
        for subscriber in cls._subscribers.get(event.event_type, []):
            subscriber(event)
    
    @classmethod
    def subscribe(cls, event_type: EventType, callback: Callable, 
                  channel: Optional[str] = None) -> None:
        """Subscribe to events, optionally filtered by channel."""
        if channel:
            if channel not in cls._channel_subscribers:
                cls._channel_subscribers[channel] = {}
            if event_type not in cls._channel_subscribers[channel]:
                cls._channel_subscribers[channel][event_type] = []
            cls._channel_subscribers[channel][event_type].append(callback)
        else:
            if event_type not in cls._subscribers:
                cls._subscribers[event_type] = []
            cls._subscribers[event_type].append(callback)
    
    @classmethod
    def create_channel(cls, channel_id: str) -> "Channel":
        """Create a private channel for agent-agent communication."""
        return Channel(channel_id)


class Channel:
    """Private channel for targeted agent-agent communication."""
    
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
    
    def emit(self, event: FrameworkEvent) -> None:
        """Emit event on this channel."""
        EventBus.emit(event, channel=self.channel_id)
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to events on this channel."""
        EventBus.subscribe(event_type, callback, channel=self.channel_id)
```

### Channel Use Cases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL PATTERNS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATTERN 1: Private Agent-Agent Communication                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # Orchestrator creates private channel for sub-agents                      │
│  channel = EventBus.create_channel("orch-123-private")                      │
│                                                                             │
│  # ResearcherAgent subscribes                                               │
│  channel.subscribe(EventType.AGENT_MESSAGE, researcher.on_message)          │
│                                                                             │
│  # CoderAgent sends message                                                 │
│  channel.emit(FrameworkEvent(                                               │
│      event_type="agent_message",                                            │
│      data={"from": "coder", "content": "Research complete, here's data"}    │
│  ))                                                                         │
│                                                                             │
│  # Only ResearcherAgent receives (not all agents in system)                 │
│  # But collectors still log for observability                               │
│                                                                             │
│  PATTERN 2: Task Completion Triggers                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # Agent A completes task                                                   │
│  channel.emit(FrameworkEvent(                                               │
│      event_type="task_completed",                                           │
│      data={"task_id": "research-123", "result": {...}}                      │
│  ))                                                                         │
│                                                                             │
│  # Agent B waiting for this task can now proceed                            │
│  def on_task_completed(event):                                              │
│      if event.data["task_id"] == "research-123":                            │
│          self.resume_with_data(event.data["result"])                        │
│                                                                             │
│  PATTERN 3: User Injection (existing inbox pattern)                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # User sends guidance to running agent                                     │
│  agent_channel = EventBus.create_channel(f"agent-{agent.run_id}")           │
│  agent_channel.emit(FrameworkEvent(                                         │
│      event_type="user_message",                                             │
│      data={"content": "Focus on Python files only"}                         │
│  ))                                                                         │
│                                                                             │
│  # Agent receives in next iteration (like current inbox)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Principle: Observability vs Delivery

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ALL events → Collectors (full observability, logging, audit)               │
│                    │                                                        │
│                    ▼                                                        │
│  Channel events → Channel subscribers only (targeted delivery)              │
│                                                                             │
│  Global events → All subscribers (broadcast)                                │
│                                                                             │
│  This ensures:                                                              │
│  ✅ Full observability (everything logged)                                  │
│  ✅ Privacy (agents only see their channels)                                │
│  ✅ Efficiency (no noise from unrelated events)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6. AI Fingerprint as Channel Identity

Each agent has an AI fingerprint (actor_id) that serves as its unique identity. This fingerprint can be used as a channel for agent-agent communication:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FINGERPRINT-BASED CHANNELS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Every agent automatically gets a channel based on its fingerprint:         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  class BaseAgent:                                                    │   │
│  │      def __init__(self, ...):                                        │   │
│  │          self.fingerprint = ActorFingerprint.generate()              │   │
│  │          self.actor_id = self.fingerprint.actor_id                   │   │
│  │                                                                      │   │
│  │          # Auto-create channel for this agent                        │   │
│  │          self._channel = EventBus.get_or_create_channel(             │   │
│  │              self.actor_id                                           │   │
│  │          )                                                           │   │
│  │                                                                      │   │
│  │          # Subscribe to messages on own channel                      │   │
│  │          self._channel.subscribe(                                    │   │
│  │              EventType.AGENT_MESSAGE,                                │   │
│  │              self._on_message                                        │   │
│  │          )                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Other agents can listen to what an agent says:                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  # ResearcherAgent wants to know what CoderAgent is doing            │   │
│  │  coder_channel = EventBus.get_channel(coder_agent.actor_id)          │   │
│  │                                                                      │   │
│  │  # Subscribe to coder's broadcasts                                   │   │
│  │  coder_channel.subscribe(                                            │   │
│  │      EventType.AGENT_STATUS,                                         │   │
│  │      researcher.on_coder_status                                      │   │
│  │  )                                                                   │   │
│  │                                                                      │   │
│  │  # Later, if not interested anymore                                  │   │
│  │  coder_channel.unsubscribe(                                          │   │
│  │      EventType.AGENT_STATUS,                                         │   │
│  │      researcher.on_coder_status                                      │   │
│  │  )                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION PATTERNS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PATTERN 1: Direct Message (to specific agent)                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # Send message to specific agent by fingerprint                            │
│  target_channel = EventBus.get_channel(target_actor_id)                     │
│  target_channel.emit(FrameworkEvent(                                        │
│      event_type="agent_message",                                            │
│      actor_id=self.actor_id,  # Sender                                      │
│      data={"content": "Here's the research data you requested"}             │
│  ))                                                                         │
│                                                                             │
│  PATTERN 2: Broadcast (from agent to all listeners)                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # Agent broadcasts status on its own channel                               │
│  self._channel.emit(FrameworkEvent(                                         │
│      event_type="agent_status",                                             │
│      actor_id=self.actor_id,                                                │
│      data={"status": "completed", "task": "research", "result_id": "..."}   │
│  ))                                                                         │
│                                                                             │
│  # Any agent subscribed to this channel receives it                         │
│                                                                             │
│  PATTERN 3: Discovery (find interesting agents)                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # Agent wants to find other agents working on related topics               │
│  def discover_relevant_agents(self, topic: str) -> List[str]:               │
│      # Subscribe to global AGENT_STATUS events temporarily                  │
│      relevant = []                                                          │
│                                                                             │
│      def on_status(event):                                                  │
│          if topic in event.data.get("task", ""):                            │
│              relevant.append(event.actor_id)                                │
│                                                                             │
│      EventBus.subscribe(EventType.AGENT_STATUS, on_status)                  │
│      # ... wait for some time ...                                           │
│      EventBus.unsubscribe(EventType.AGENT_STATUS, on_status)                │
│                                                                             │
│      return relevant                                                        │
│                                                                             │
│  PATTERN 4: Collaboration Group (private channel)                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  # Orchestrator creates private channel for a task                          │
│  task_channel = EventBus.create_channel(f"task-{task_id}")                  │
│                                                                             │
│  # Invite specific agents by their fingerprints                             │
│  for agent_id in [researcher.actor_id, coder.actor_id]:                     │
│      agent = get_agent_by_id(agent_id)                                      │
│      agent.join_channel(task_channel)                                       │
│                                                                             │
│  # Now they can communicate privately on this channel                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    HUMAN ANALOGY                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Like humans in a workplace:                                                │
│                                                                             │
│  - Each person has an ID badge (actor_id / fingerprint)                     │
│  - Each person has a "desk" where messages arrive (personal channel)        │
│  - You can send a message to someone's desk (direct message)                │
│  - You can announce something from your desk (broadcast)                    │
│  - You can listen to what someone is saying (subscribe to their channel)    │
│  - You can stop listening if not interested (unsubscribe)                   │
│  - You can join a meeting room (private channel for collaboration)          │
│  - Everything is logged in the company records (collectors/ledger)          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation Considerations

1. **Auto-create vs On-demand**: Channels could be created automatically when an agent starts, or on-demand when first accessed. Auto-create is simpler but uses more memory.

2. **Channel Lifecycle**: When an agent terminates, its channel could:
   - Remain (for historical queries)
   - Be archived (moved to cold storage)
   - Be deleted (if no subscribers)

3. **Security**: In production, channel access might need authentication:
   - Public channels (anyone can subscribe)
   - Private channels (invitation only)
   - Signed messages (verify sender fingerprint)

### 6. Unified Event Schema

```python
@dataclass
class FrameworkEvent:
    """Unified event schema for all packages."""
    
    # Identity chain
    event_id: str           # Unique event ID
    actor_id: Optional[str] # WHO (AI fingerprint)
    session_id: Optional[str]  # Session context
    run_id: Optional[str]   # Workflow run
    trace_id: Optional[str] # LLM interaction
    parent_run_id: Optional[str]  # For sub-workflows
    
    # Classification
    event_type: str         # "llm_call", "tool_call", "workflow_step", etc.
    package: str            # "abstractcore", "abstractruntime", "abstractagent"
    
    # Timing
    timestamp: datetime
    duration_ms: Optional[float]
    
    # Content
    data: Dict[str, Any]
    
    # Status
    status: str             # "started", "completed", "failed", "waiting"
    error: Optional[str]
```

### 7. Integration Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EVENT FLOW                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AbstractCore                                                               │
│  ├── generate() → emit(LLM_CALL_STARTED, trace_id=...)                      │
│  ├── generate() → emit(LLM_CALL_COMPLETED, trace_id=...)                    │
│  └── execute_tools() → emit(TOOL_EXECUTED, trace_id=...)                    │
│                                                                             │
│  AbstractRuntime                                                            │
│  ├── tick() → emit(WORKFLOW_STEP, run_id=...)                               │
│  ├── effect handler → emit(EFFECT_EXECUTED, run_id=..., trace_id=...)       │
│  └── ledger.append() → emit(LEDGER_RECORD, run_id=...)                      │
│                                                                             │
│  AbstractAgent                                                              │
│  ├── start() → emit(AGENT_STARTED, actor_id=..., run_id=...)                │
│  ├── step() → emit(AGENT_STEP, run_id=...)                                  │
│  └── complete() → emit(AGENT_COMPLETED, run_id=...)                         │
│                                                                             │
│  AbstractFlow                                                               │
│  ├── run() → emit(FLOW_STARTED, run_id=...)                                 │
│  ├── node execution → emit(FLOW_NODE, run_id=..., sub_run_id=...)           │
│  └── complete() → emit(FLOW_COMPLETED, run_id=...)                          │
│                                                                             │
│                          ▼                                                  │
│                    EventBus.emit()                                          │
│                          │                                                  │
│          ┌───────────────┼───────────────┐                                  │
│          ▼               ▼               ▼                                  │
│    Subscribers      Collectors      Ledger                                  │
│    (callbacks)      (external)      (audit)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Consequences

### Positive
- **Unified tracing**: All operations linked by consistent ID hierarchy
- **Complete picture**: Can reconstruct any agent's full activity
- **External integration**: Standard interface for LangSmith, W&B, etc.
- **Debugging**: Can trace from high-level task to individual LLM calls
- **Accountability**: AI fingerprint links all activity to specific agent

### Negative
- **Migration effort**: Existing code needs ID propagation
- **Overhead**: Additional fields in all operations
- **Complexity**: More concepts to understand

### Neutral
- Ledger remains the source of truth for durable execution
- Events are for real-time observability
- Both are needed for complete picture

## Implementation Plan

### Phase 1: ID Propagation (Task 001)
- Add session_id to agent lifecycle
- Propagate run_id through effect handlers to AbstractCore
- Include all IDs in events

### Phase 2: Centralized Event Bus
- Create EventBus in AbstractCore
- Migrate existing emit_global() to use EventBus
- Add collectors interface

### Phase 3: Unified Event Schema
- Define FrameworkEvent dataclass
- Adapter for existing AbstractCore events
- Adapter for ledger records

### Phase 4: Agent Tracking
- Add session_id to BaseAgent
- Track parent_run_id for sub-workflows
- Query interface for agent activity

## Packages Affected
- **AbstractCore**: EventBus, trace_id propagation
- **AbstractRuntime**: run_id, parent_run_id, ledger integration
- **AbstractAgent**: session_id, actor_id
- **AbstractFlow**: Orchestration tracking

---

## Appendix: AbstractCore's Role in Tool Unification

AbstractCore is not just a proxy to LLM providers. It provides:

### 1. Tool Syntax Normalization

Different LLMs express tool calls differently:
- Qwen3: `<|tool_call|>{"name": "...", "arguments": {...}}</|tool_call|>`
- Llama3: `<function_call>...</function_call>`
- Gemma: ` ```tool_code\n...\n``` `
- OpenAI: Native API with `tool_calls` field

AbstractCore's `UniversalToolHandler` and `ToolCallSyntaxRewriter` normalize these:

```python
# Parse any format
handler = UniversalToolHandler("qwen3:4b")
tool_calls = handler.parse_response(content, mode="prompted")

# Rewrite to different format
rewriter = ToolCallSyntaxRewriter(target_format=SyntaxFormat.OPENAI)
normalized = rewriter.rewrite_content(content)
```

### 2. Tool Execution Modes

| Mode | execute_tools | Use Case |
|------|---------------|----------|
| Passthrough | False (default) | AbstractRuntime, Codex, Claude Code |
| Direct | True | Simple scripts, single-turn |

Passthrough mode returns raw content with tool call tags. The downstream runtime:
1. Parses tool calls using `UniversalToolHandler`
2. Executes tools with its own strategy
3. Records in ledger for durability

### 3. Streaming Tool Rewriting

`ToolCallTagRewriter` supports real-time tag rewriting during streaming:

```python
rewriter = create_tag_rewriter("custom_tag")
for chunk in stream:
    rewritten_chunk = rewriter.process_chunk(chunk)
    yield rewritten_chunk
```

This enables different agentic CLIs (Codex, Claude Code) to receive tool calls in their expected format.

### 4. Observability for Tool Execution

When `execute_tools=True`, AbstractCore emits:
- `TOOL_STARTED` - Before execution
- `TOOL_PROGRESS` - During execution (for long-running tools)
- `TOOL_COMPLETED` - After execution

When `execute_tools=False`, the downstream runtime is responsible for observability.

---

## Related
- `abstractcore/abstractcore/events/__init__.py` - Current event system
- `abstractcore/abstractcore/tools/syntax_rewriter.py` - Syntax normalization
- `abstractcore/abstractcore/tools/tag_rewriter.py` - Streaming rewriting
- `abstractcore/abstractcore/tools/handler.py` - Universal tool handler
- `abstractcore/docs/backlog/completed/feature_request_interaction_tracing.md` - Original tracing request
- `abstractruntime/src/abstractruntime/identity/fingerprint.py` - ActorFingerprint
- `abstractruntime/docs/adr/0003_provenance_tamper_evident_hash_chain.md`
- `docs/misc/medium-ai-fingerprints.md` - AI fingerprint concept
