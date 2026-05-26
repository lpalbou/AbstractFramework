# Abstract Framework - Architectural Decision Records (ADRs)

This directory contains centralized ADRs for the entire Abstract Framework ecosystem:
- **AbstractCore** - LLM abstraction and provider routing
- **AbstractRuntime** - Durable workflow execution
- **AbstractAgent** - Agent patterns (ReAct, CodeAct)
- **AbstractGateway** - Protected runtime control plane and thin-client API
- **AbstractFlow** - Visual authoring + workflow orchestration
- **AbstractSemantics** - Standalone semantics registry for predicates/types/schema refs
- **AbstractMemory** - Optional temporal KG memory store
- **AbstractCode** - Host UX (CLI/REPL) for running workflows
- **AbstractVoice / AbstractVision / AbstractMusic** - Optional modality capability plugins

## Why Centralized ADRs?

The Abstract Framework is a multi-package ecosystem where architectural decisions often span multiple packages. Centralizing ADRs:
- Prevents duplicate/conflicting decisions across packages
- Shows the full picture of framework architecture
- Makes cross-cutting concerns visible
- Simplifies onboarding for new contributors

## ADR Index

### Framework-Wide Decisions

| ID | Title | Status | Date | Packages | Summary |
|----|-------|--------|------|----------|---------|
| 0001 | [Layered Architecture](0001-layered-architecture.md) | Accepted | 2025-12-14 | All | Core + Runtime → Agent → Flow (refined by ADR-0032) |
| 0002 | [Effect System Design](0002-effect-system-design.md) | Accepted | 2025-12-14 | Runtime, Agent | Effects as first-class side-effect requests |
| 0003 | [Tool System Architecture](0003-tool-system-architecture.md) | Accepted | 2025-12-14 | Core, Runtime, Agent | Single decorator, session-level registry, passthrough |
| 0004 | [Observability Strategy](0004-observability-strategy.md) | Accepted | 2025-12-14 | All | Unified events, fingerprint channels, agent communication |
| 0005 | [Memory Architecture](0005-memory-architecture.md) | Proposed | 2025-12-14 | Core, Runtime, Agent, Memory | ArtifactStore now; long-term memory as separate package |
| 0006 | [Durable Tool Execution (Toolsets & Executors)](0006-durable-tool-execution.md) | Accepted | 2025-12-15 | Core, Runtime, Agent | Persist tool specs only; execute via host-configured executors |
| 0007 | [Active Context vs Stored Memory (Provenance)](0007-active-context-and-memory-provenance.md) | Accepted | 2025-12-17 | Runtime, Agent, Code, Memory | Active context is a view; archived spans stored with provenance |
| 0008 | [Token Terminology and Parameter Naming](0008-token-terminology.md) | Accepted | 2025-12-17 | Core, Runtime, Agent, Code | Clarifies max_tokens vs max_output_tokens semantics |
| 0009 | [Connected Memory Recall (Provenance-First, Graph-Ready)](0009-connected-memory-recall-and-provenance.md) | Accepted | 2025-12-18 | Runtime, Agent, Code, Memory | Runtime-owned recall by span/time/tags; connected recall contracts |
| 0010 | [Runtime-Owned Node Traces (Scratchpad/Trace)](0010-runtime-owned-node-traces.md) | Accepted | 2025-12-21 | Runtime, Agent, Flow, Code | Durable per-node traces under run.vars["_runtime"]["node_traces"] |
| 0011 | [Runtime Ledger Subscriptions + AbstractCore Event Bridge](0011-ledger-subscriptions-and-event-bridge.md) | Accepted | 2025-12-21 | Runtime, Core, Flow, Code | Subscribe to StepRecord appends; optional GlobalEventBus bridge |
| 0012 | [Portable WorkflowArtifact (Serializable)](0012-portable-workflowartifact.md) | Deprecated | 2026-01-08 | Runtime, Flow, Code | Deprecated to avoid dual semantics engines; prefer VisualFlow bundles + runtime compiler |
| 0013 | [Durable Run Controls (Pause/Resume/Cancel)](0013-durable-run-controls-pause-resume-cancel.md) | Accepted | 2025-12-26 | Runtime, Flow | Runtime-owned pause/resume/cancel via vars["_runtime"]["control"] |
| 0014 | [Runtime-Authoritative Timeouts (LLM + Tool Execution)](0014-runtime-authority-timeouts.md) | Proposed | 2025-12-31 | Runtime, Core, Flow | Runtime defines LLM/tool timeouts and propagates them to AbstractCore (local + server) |
| 0015 | [Execution Targets + Remote Tool Workers (MCP-first)](0015-execution-targets-and-remote-tool-workers.md) | Proposed | 2026-01-02 | Runtime, Core, Flow, Code | Placement + discovery + MCP-first remote tool execution |
| 0016 | [Tool Calling Pipeline and Responsibility Boundaries](0016-tool-calling-pipeline-and-responsibility-boundaries.md) | Proposed | 2026-01-04 | Core, Runtime, Agent, Code, Flow, Memory | Codifies outbound/inbound tool pipelines and ownership boundaries |
| 0017 | [Host UI Events and Durable Prompts](0017-host-ui-events-and-durable-prompts.md) | Proposed | 2026-01-07 | Runtime, Flow, Code | Reserved host UX events + durable ask/wait prompting |
| 0018 | [Durable Run Gateway and Remote Host Control Plane (Commands + Ledger Replay)](0018-durable-run-gateway-and-remote-host-control-plane.md) | Accepted | 2026-01-08 | Runtime, Flow, Code | Remote control plane: durable commands + ledger replay; thin-client friendly |
| 0019 | [Testing Strategy and Levels (Basic → Intermediate → Full)](0019-testing-strategy-and-levels.md) | Accepted | 2026-01-07 | All | Test taxonomy and expectations for durability/portability |
| 0020 | [Agent Host Pool and Orchestrator Placement (Run-Pinned Hosts)](0020-agent-host-pool-and-orchestrator-placement.md) | Accepted | 2026-01-08 | Runtime, Flow, Code | Pin each run to one orchestrator host; host pool is discovery+routing; no mid-run migration |
| 0021 | [Deployment Topologies and Supported Scenarios](0021-deployment-topologies-and-supported-scenarios.md) | Accepted | 2026-01-08 | Runtime, Gateway, Flow, Code, Core | What works today vs what needs more work (thin clients, remote tools, gateway) |
| 0022 | [Orchestrator Host Model (Runtime Kernel vs Gateway Service)](0022-orchestrator-host-and-runtime-daemonization.md) | Proposed | 2026-01-16 | Runtime, Gateway, Flow, Code, Observer | Clarifies “who runs” the kernel; recommends API/runner separation vs runtime daemon |
| 0023 | [File Attachment Path Resolution and Authorization (Absolute Paths + Mounts)](0023-file-attachment-path-resolution-and-authorization.md) | Proposed | 2026-01-19 | Code | Allow `@/abs/path` only under workspace/mount roots; canonicalize to virtual paths; blacklist wins |
| 0024 | [Attachment Placeholders + Compaction Invariants (No Duplicate File Content)](0024-attachment-placeholders-and-compaction-invariants.md) | Proposed | 2026-01-19 | Runtime, Core, Gateway, Code, Observer | Store once; inject metadata-only placeholders; bounded `open_attachment`; compaction preserves placeholders |
| 0025 | [KG Entity Normalization (Stable CURIEs) and De-duplication Strategy](0025-kg-entity-normalization-and-dedup.md) | Proposed | 2026-01-20 | Memory, Runtime, Flow | Stable `ex:` instance IDs + deterministic normalization; sets a pragmatic path toward de-dup |
| 0026 | [Truncation Policy and Contract (CRITICAL)](0026-truncation-policy-and-contract.md) | Accepted | 2026-01-25 | All | Forbid silent truncation; warn+tag truncation; fail loudly on critical paths |
| 0027 | [Timeout Policy and Contract (CRITICAL)](0027-timeout-policy-and-contract.md) | Accepted | 2026-01-26 | All | Forbid silent timeouts; conservative defaults; warn+tag timeouts |
| 0028 | [Capabilities Plugins + Library/Framework Modes (Audio/Voice/Vision/Music)](0028-capabilities-plugins-and-library-framework-modes.md) | Accepted | 2026-02-04 | Core, Runtime, Gateway, Code, Voice, Vision, Music | Clarifies usage modes + plugin-first multimodal integration |
| 0029 | [Permissive Dependency and Licensing Policy](0029-permissive-dependency-and-licensing-policy.md) | Proposed | 2026-01-31 | All | Keep dependencies permissive and minimal by default |
| 0030 | [Security test fixtures and isolation (no real sensitive paths)](0030-security-test-fixtures-and-isolation.md) | Proposed | 2026-02-02 | Gateway, Runtime | Avoid real OS-sensitive paths in tests; prevent repo-state leakage |
| 0031 | [Workflow LLM routing overrides (`provider`/`model` first, `base_url` advanced)](0031-workflow-llm-routing-overrides-provider-model-and-base-url.md) | Proposed | 2026-02-08 | Runtime, Core, Gateway, Flow, Code | Keeps provider/model as portable workflow routing; treats base_url as host policy |
| 0032 | [Package Dependency Boundaries and Gateway-First Apps](0032-package-dependency-boundaries-and-gateway-first-apps.md) | Proposed | 2026-05-06 | All | Clarifies Semantics/Memory placement, capability plugins, Core/Agent/Runtime/Gateway layering, app direction, and change impact |
| 0033 | [Install Profiles, Config Entrypoints, and Server Boundaries](0033-install-profiles-config-entrypoints-and-server-boundaries.md) | Accepted | 2026-05-08 | All | Defines Core/Gateway entry points, profile vocabulary, config precedence, and auth/CORS boundaries |
| 0034 | [Framework Release Sequence and Gates](0034-framework-release-sequence-and-gates.md) | Accepted | 2026-05-09 | All | Defines topological release order, PyPI propagation gates, branch CI gates, and Gateway-last discipline |
| 0035 | [Capability Routing Defaults](0035-capability-routing-defaults.md) | Accepted | 2026-05-24 | Core, Gateway, Flow, capability plugins | Defines input/output, embedding, and rerank capability routes with Core-owned persistence and Gateway control-plane access |

### Package-Specific Decisions

See also package-level ADRs:
- `abstractruntime/docs/adr/` - Runtime-specific decisions
- `abstractvoice/docs/adr/` - Voice-specific decisions
- `abstractcore/docs/backlog/006-architecture-decision-records.md` - Core ADR proposal

## ADR Template

```markdown
# ADR-NNNN: Title

## Status
[Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXXX]

## Dates
- Proposed: YYYY-MM-DD
- Accepted: YYYY-MM-DD (or TBD)
- Rejected: YYYY-MM-DD (optional)
- Deprecated: YYYY-MM-DD (optional)

## Context
What is the issue we're facing? What constraints exist?

## Decision
What is the change we're making?

## Consequences

### Positive
- Benefits

### Negative
- Trade-offs

### Neutral
- Other impacts

## Packages Affected
- List of packages this decision impacts

## Related
- Links to related ADRs, backlogs, code
```

## Adding New ADRs

1. Create `docs/adr/NNNN-short-title.md`
2. Use the template above
3. Set status to "Proposed" initially
4. After team review, update to "Accepted"
5. Update this README index

## Relationship to Package ADRs

- **Framework ADRs** (this directory): Cross-cutting decisions affecting multiple packages
- **Package ADRs** (e.g., `abstractruntime/docs/adr/`): Package-specific implementation decisions

When a package ADR has framework-wide implications, consider promoting it to a framework ADR.
