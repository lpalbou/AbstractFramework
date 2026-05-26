# ADR-0016: Tool Calling Pipeline and Responsibility Boundaries

## Status
Proposed (2026-01-04)

## Dates
- Proposed: 2026-01-04
- Accepted: (TBD)


## Context
Tool calling is a cross-cutting capability that spans multiple packages:
- **AbstractCore**: LLM provider abstraction + tool-call parsing/normalization.
- **AbstractRuntime**: durable orchestration + effect execution.
- **AbstractAgent**: agent loop semantics + prompt policy on top of runtime.
- **Hosts** (AbstractCode/AbstractFlow): UX, approvals, observability.

We have repeatedly observed failures caused by unclear responsibility boundaries and duplicated responsibilities:
- native-tool servers (e.g. OpenAI-compatible local servers) may enforce tool calling via **hidden grammars/templates**;
  duplicating tool definitions or tool-call transcript instructions inside the visible system prompt can cause “text leaked” tool calls
  that the server **does not** parse into structured tool calls.
- provider responses can vary (native tool-calls, transcript-style tool calls, wrapped tool names, streaming deltas); without a single normalization contract,
  hosts/runtimes are tempted to add ad-hoc parsing workarounds.

We already have an extensive report describing the implementation-level details:
- `docs/misc/report-tool-calls-native-prompt-providers.md`

This ADR exists to codify the **stable framework contract** and the **ownership boundaries** so future work (especially memory systems) integrates cleanly.

## Decision

### 1) Define two distinct pipelines (Outbound vs Inbound)
Tool calling must always be reasoned about as two separate pipelines:

- **Outbound (ToolSpec transport)**: how tool definitions are sent to the provider/model.
- **Inbound (ToolCall transport)**: how tool-call requests are returned and normalized.

These pipelines are independent: “how tools are sent” is not the same as “how tool calls are returned”.

### 2) Canonical tool-call normalization contract (single truth)
AbstractCore is the **single source of truth** for tool-call parsing/normalization.

Regardless of provider/model/tool mode (prompted vs native; streaming vs non-streaming), AbstractCore must normalize to:

- `tool_calls`: a list of canonical tool calls:
  - `{"name": str, "arguments": dict, "call_id": Optional[str]}`
- `content`: cleaned assistant content by default (tool markup removed when applicable)

Downstream layers (Runtime/Agent/Host) must treat this contract as authoritative and must not re-parse assistant text to “recover” tool calls.

### 3) Tool calling modes
We support two outward modes; they differ only in the outbound transport, not in the inbound contract.

#### 3.1 Native tool calling
- **Outbound**: AbstractCore sends structured tool definitions in the provider request (e.g. `payload["tools"]`, `payload["tool_choice"]`).
- **Inbound**: AbstractCore extracts structured tool calls from provider response fields (e.g. OpenAI `tool_calls`, Anthropic `tool_use` blocks) and normalizes.

Important constraint:
- When native tools are enabled, avoid duplicating a visible tool catalog (or tool-call transcript instructions) in the system prompt.
  Doing so can conflict with provider-enforced tool grammars and cause “text leaked” tool calls.

#### 3.2 Prompted tool calling
- **Outbound**: tool definitions + tool-call syntax instructions are injected as prompt text (model-appropriate transcript format).
- **Inbound**: AbstractCore parses tool-call transcripts from assistant content and normalizes.

Prompted tools are *format-sensitive*. The “tool-call transcript tags” (e.g. `<|tool_call|>...</|tool_call|>`) are not the same as chat-template role tokens.

### 4) Control tokens vs tool-call transcript tags
We explicitly separate:
- **Chat-template role/control tokens**: a provider/server concern (how `system/user/assistant/tool` roles become tokens).
- **Tool-call transcript tags**: literal text markers used only in the prompted-tool strategy (e.g. `<|tool_call|>...</|tool_call|>`).

Conflating these leads to incorrect fixes (e.g. trying to “add control tokens” when the real issue is duplicated prompted tool instructions).

### 5) Responsibility boundaries (non-negotiable)

#### AbstractCore (owns parsing + normalization)
- Owns model capability detection (`tool_support: none|prompted|native`).
- Owns outbound request shaping for tools (native fields vs prompted tool prompt generation).
- Owns inbound tool-call extraction and normalization into the canonical `tool_calls` structure.
- Owns syntax/tag rewriting layers (when required to support multiple prompted formats or streaming).

#### AbstractRuntime (owns durable orchestration + effect execution)
- Owns execution policy (timeouts, pause/resume/cancel) and durability (ADR-0014, ADR-0013).
- Executes tool calls via durable effects (`EffectType.TOOL_CALLS`) using a host-configured `ToolExecutor` (ADR-0006).
- Must not implement tool-call parsing; it consumes canonical tool calls from AbstractCore results.
- Must persist enough routing metadata (provider/model) in `vars["_runtime"]` so prompt composition can be deterministic and replayable.

#### AbstractAgent (owns loop semantics; not transport)
- Builds prompts/policies for agent behavior, but must not contain provider-specific tool-call transport logic.
- Treats tools as “available actions” and consumes structured tool calls from runtime LLM results.
- Must not inject tool definitions in ways that conflict with native tool calling; when prompted tools are used, the agent should rely on the orchestrated tool prompt strategy rather than inventing one.

#### Hosts (AbstractCode/AbstractFlow) (owns UX; not parsing)
- Display and approval gating, plus verbatim observability of request/response payloads.
- Must not implement tool parsing workarounds. If tool calling is broken, fixes belong in AbstractCore (parsing/normalization) or AbstractRuntime (orchestration boundaries).

### 6) Memory systems integration (Active Memory now; AbstractMemory later)
Tool calling interacts with memory because prompted tool calling requires prompt-text injection.

We anticipate a tension for **prompted tools**:
- AbstractCore is the authority for **formatting** the prompted tool-call instructions for each model architecture.
- A memory system (Active Memory today; `abstractmemory` later) may be the authority for **where** those instructions live in the prompt (system memory blocks, policy-controlled placement, budgeting).

Guidance for future memory systems:
- Do not duplicate responsibilities: do not create a parallel tool-call transcript format in `abstractmemory`/agents/hosts.
- Prefer a contract where AbstractCore provides a “prompted tool prompt” (rendered text) and the memory system decides placement and budgeting,
  while inbound tool-call parsing/normalization remains exclusively in AbstractCore.

This ADR does not select the final `abstractmemory` design, but it requires any future memory system to preserve the above separation.

## Consequences

### Positive
- Clear ownership prevents drift: parsing/normalization stays in AbstractCore; orchestration stays in AbstractRuntime.
- Native tool calling becomes reliable by avoiding conflicting tool catalogs in the visible system prompt.
- Future memory systems can evolve prompt composition without forking the tool pipeline.

### Negative
- Requires discipline: hosts/runtimes must resist “quick parsing fixes” for tool-call edge cases.
- Prompted tool calling remains inherently fragile; format selection must be capability-driven and tested (see conformance suite backlog).

### Neutral
- This ADR is primarily a contract; implementation details live in the report and provider-specific backlogs/tests.

## Packages Affected
- AbstractCore
- AbstractRuntime
- AbstractAgent
- AbstractCode
- AbstractFlow
- AbstractMemory (future)

## Related
- `docs/misc/report-tool-calls-native-prompt-providers.md`
- ADR-0003: Tool System Architecture
- ADR-0006: Durable Tool Execution (Toolsets & Executors)
- ADR-0007: Active Context vs Stored Memory (Provenance)
- ADR-0014: Runtime-Authoritative Timeouts (LLM + Tool Execution)
- Backlog (testing): `docs/backlog/planned/118-framework-provider-toolcall-conformance-suite.md`
- Backlog (memory/tool synergy): `docs/backlog/planned/281-framework-active-memory-and-abstractcore-tool-synergy.md`
- Backlog (AbstractMemory blocks): `docs/backlog/planned/266-abstractmemory-typed-memory-blocks-and-multimodal.md`


