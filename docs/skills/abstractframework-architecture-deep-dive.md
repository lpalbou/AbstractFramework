# AbstractFramework Architecture Deep Dive — Notes (Feb 2026)

## Scope
This note summarizes the **implemented architecture** across core packages and UIs, based on the official architecture docs in each repo. The goal is to ground any skills recommendations in real constraints.

## System-Level Architecture
AbstractFramework is designed around **durable, observable execution** with a **gateway-first** deployment path (recommended) and a **local in-process** path (alternative).  
Source: `docs/architecture.md`

Key implications:
- Every run is **durable** (explicit waits, restart-safe).
- Every step is **recorded** in an append-only ledger (replay-first UI).
- Tool execution happens at explicit **durable boundaries**.

## Core Invariants (Non-Negotiable)
- **Run state is JSON-safe**; large payloads must be stored as artifacts.  
  Source: `abstractruntime/docs/architecture.md`
- **Ledger is append-only** (hash-chained in some stores); it is the source of truth.  
  Source: `docs/architecture.md`, `abstractruntime/docs/architecture.md`
- **Tool schemas are durable; tool callables are not** (host executes tools after approval).  
  Source: `docs/architecture.md`, `abstractassistant/docs/architecture.md`, `abstractcode/docs/architecture.md`

## Foundation Layer

### AbstractCore (LLM + tools + media)
AbstractCore provides provider-agnostic LLM access, tool schema normalization, and media handling.  
Source: `abstractcore/docs/architecture.md`

Notable capabilities:
- Multi-provider factory (`create_llm`) and consistent interface.
- Tool-call parsing and tag-rewriting for provider compatibility.
- Unified streaming with incremental tool detection.
- Optional capability plugins (voice, vision, music) discovered via entry points.

### AbstractRuntime (durable execution kernel)
AbstractRuntime is the durable workflow engine.  
Source: `abstractruntime/docs/architecture.md`

Notable capabilities:
- `WorkflowSpec` nodes -> `StepPlan` effects.
- Explicit waits (`ASK_USER`, `WAIT_EVENT`, `WAIT_UNTIL`, `TOOL_CALLS`).
- Durable stores (RunStore, LedgerStore, ArtifactStore, Snapshots).
- Workflow bundles (`.flow`) and VisualFlow compiler integration.

## Composition Layer

### AbstractAgent (ReAct / CodeAct / MemAct)
Agent patterns are expressed as runtime workflows with strict namespaces and tool gating.  
Source: `abstractagent/docs/architecture.md`

Key design:
- Logic is runtime-agnostic; adapters wire to AbstractRuntime.
- Tool allowlists are stored in `_runtime.allowed_tools`.
- CodeAct supports fenced python execution as an explicit tool.

### AbstractFlow (VisualFlow + bundles)
AbstractFlow is the authoring layer for VisualFlow workflows and bundles.  
Source: `abstractflow/docs/architecture.md`

Key design:
- VisualFlow JSON is portable and executes in any host.
- `.flow` bundles package VisualFlow graphs + manifest + subflows.
- Session runners support event-driven flows (`on_event` → child workflows).

## Control Plane

### AbstractGateway (durable run gateway)
The gateway provides HTTP/SSE APIs for run control, ledger replay, scheduling, and security.  
Source: `abstractgateway/docs/architecture.md`

Key design:
- Replay-first ledger streaming (SSE is an optimization).
- Runner loop processes durable commands and ticks runs.
- Split-process deployment supported (API + runner).

## Clients and Hosts

### AbstractCode (CLI/TUI + web thin client)
Local CLI is a **host** (runs runtime + tools locally).  
Web app is a **thin client** that talks to the gateway.  
Source: `abstractcode/docs/architecture.md`

### AbstractAssistant (local host)
Tray UI runs AbstractAgent + AbstractRuntime locally; tools executed after approval.  
Source: `abstractassistant/docs/architecture.md`

### AbstractObserver (gateway-only UI)
UI renders by ledger replay + SSE; submits durable commands to gateway.  
Source: `abstractobserver/docs/architecture.md`

### SmartNote (thin client + durable backend)
SmartNote server runs chunked ingestion workflows and writes KG assertions.  
Source: `smartnote/docs/architecture.md`

## Memory and Semantics

### AbstractMemory (temporal triple store)
Stores append-only, provenance-aware triples with deterministic query semantics.  
Source: `abstractmemory/docs/architecture.md`

### AbstractSemantics (registry + schema)
Provides registry of predicates/types + JSON schema builder for KG assertions.  
Source: `abstractsemantics/docs/architecture.md`

## Observability and Evidence
Evidence is an explicit concept: ledger + artifacts + snapshots + history bundles.  
Sources: `docs/architecture.md`, `abstractruntime/docs/architecture.md`

## Implications for Skill Integration (Constraints)
These constraints must be respected by any skills proposal:
- **Durability**: skills should not rely on ephemeral in-memory state.
- **Tool boundary**: tools must remain host-executed with durable waits.
- **Replay-first**: skill activation and outputs should be ledger-recorded.
- **No silent fallbacks**: degraded paths must emit `#FALLBACK` warnings (project policy).

## References (Architecture Docs Used)
- `docs/architecture.md`
- `abstractcore/docs/architecture.md`
- `abstractruntime/docs/architecture.md`
- `abstractagent/docs/architecture.md`
- `abstractflow/docs/architecture.md`
- `abstractgateway/docs/architecture.md`
- `abstractcode/docs/architecture.md`
- `abstractassistant/docs/architecture.md`
- `abstractobserver/docs/architecture.md`
- `abstractmemory/docs/architecture.md`
- `abstractsemantics/docs/architecture.md`
- `smartnote/docs/architecture.md`
