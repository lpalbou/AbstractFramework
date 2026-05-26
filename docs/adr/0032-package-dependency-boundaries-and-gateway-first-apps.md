# ADR-0032: Package Dependency Boundaries and Gateway-First Apps

## Status
Proposed (2026-05-06)

## Dates
- Proposed: 2026-05-06
- Accepted: (TBD)

## Context
AbstractFramework is a multi-package ecosystem. Its packages are useful on
their own, but the framework goal is stronger: persistent LLM and agent
capabilities that can be reused consistently from multiple clients.

That requires a shared understanding of package dependencies. The same
dependency map guides:
- deployment topology,
- optional dependency selection,
- install profile ownership,
- capability plugin evolution,
- test blast radius,
- and code review expectations.

The distinction matters because lower-level changes cascade upward. A semantics
registry change in `abstractsemantics`, a memory contract change in
`abstractmemory`, or a syntax/capability change in `abstractvoice`,
`abstractvision`, or `abstractmusic` can affect `abstractcore`,
`abstractruntime`, and `abstractgateway`; that can then surface in higher-level
apps such as `abstractflow`, `abstractassistant`, `abstractcode`, and
`abstractobserver`. Changes made higher in the stack usually have less impact on
other packages.

## Decision

### 1) Treat Voice, Vision, and Music as primary capability packages
`abstractvoice`, `abstractvision`, and `abstractmusic` are primary modality
capability packages in the AbstractFramework ecosystem.

They may be used directly, but their framework integration role is to provide
optional capability plugins for `abstractcore`:
- `abstractvoice`: speech/audio capabilities such as STT and TTS.
- `abstractvision`: image/video-related capabilities such as vision input,
  image generation, and vision fallback paths.
- `abstractmusic`: music generation and music/audio-domain capabilities.

`abstractmusic` is experimental. It must not be treated as a stable or trusted
dependency path unless a caller, deployment, or workflow explicitly opts into it.
Production defaults should avoid silently depending on it.

### 2) Treat Semantics and Memory as separate knowledge-layer packages
`abstractsemantics` is a small, standalone semantics registry. It describes the
canonical vocabulary the framework should use for entities, predicates,
relationships, and JSON Schema references such as
`abstractsemantics:kg_assertion_schema_v0`.

`abstractsemantics` is intentionally lower than the runtime and apps:
- It has no dependency on the rest of AbstractFramework.
- It is a required dependency of `abstractruntime` today, because Runtime must
  resolve stable structured-output schema refs and validate semantics-aware
  workflow behavior without each app inventing its own vocabulary.
- It is exposed by `abstractgateway` for thin clients that need registry data.

`abstractmemory` is the long-term semantic memory package: an append-only,
temporal, provenance-aware triple store with optional persistent/vector
backends. It remains a separate knowledge store, not part of the runtime kernel.

Current package metadata keeps `abstractmemory` dependency-light: it has no hard
AbstractFramework dependency and only optional backend extras such as LanceDB.
In framework usage, however, memory workflows are normally paired with
`abstractsemantics` through Runtime/Gateway integration:
- Runtime ships optional `abstractruntime.integrations.abstractmemory` effect
  handlers for `memory_kg_*` effects.
- Those handlers import `abstractmemory` only when memory effects are enabled.
- They use `abstractsemantics` for predicate validation and schema consistency.
- Gateway can provision/query the AbstractMemory store when the memory package
  is installed.

So the correct dependency statement is: Runtime depends on Semantics; Runtime
does not hard-depend on Memory. Memory is an optional knowledge-store capability
used by Gateway-hosted workflows and specialized apps such as SmartNote and
ai-space.

### 3) Keep AbstractCore as the capability and LLM abstraction layer
`abstractcore` is the core abstraction layer for:
- LLM provider/model access,
- provider routing and OpenAI-compatible surfaces,
- structured output and tool schemas,
- capability plugin discovery,
- media/capability integration,
- and local-first library usage.

`abstractcore` can optionally discover and use Voice, Vision, and Music
capability plugins, but it must remain dependency-light by default. Missing
plugins should fail with actionable install/configuration guidance rather than
silent behavior changes.

### 4) Keep AbstractAgent parallel to the core capability layer
`abstractagent` defines reusable agent patterns and agent behavior. It sits next
to the core capability layer conceptually: agents use `abstractcore` to call
models and tools, but agent definitions are not a replacement for durable
runtime execution.

At the import level, the `abstractruntime` kernel stays dependency-light. Agent
and Core integrations live in optional integration modules and host wiring. At
the product architecture level, however, Runtime/Gateway are the place where
Core capabilities and Agent behavior become protected, persistent, observable
runs.

### 5) Place durable execution behind Runtime and Gateway
`abstractruntime` owns durable workflow execution:
- effects and waits,
- run state,
- ledger records,
- artifacts,
- resumability,
- and workflow semantics.

`abstractgateway` standardizes and protects access to the runtime:
- authenticated HTTP/SSE control plane,
- durable command inbox,
- run start/pause/resume/cancel,
- ledger replay/streaming,
- bundle discovery,
- policy boundaries for tools and capabilities.

The gateway is the preferred boundary for persistent LLM and agent capabilities.
It lets clients share one durable execution model instead of each app inventing
its own runtime host.

### 6) Move higher-level apps toward Gateway-first usage
Higher-level apps should prefer `abstractgateway` as their execution boundary:
- `abstractflow` is gateway-first: it authors, publishes, starts, and observes
  durable workflow bundles through the gateway.
- `abstractassistant` is gateway-first in normal deployments, with local
  behavior treated as compatibility or development mode.
- `abstractcode` exists in both web and CLI forms. The web form should sit on
  the gateway. The CLI began closer to `abstractcore`, but its direction is also
  gateway/runtime-backed execution where durable workflows, approvals, memory,
  and artifacts matter.
- `abstractobserver` and other thin clients should consume gateway run state
  rather than reaching directly into runtime internals.

Local in-process use remains valid for library mode, development, smoke tests,
and small scripts. It is not the preferred architecture for reusable persistent
agent systems.

### 7) Treat AbstractFlow bundles as reusable specialized agents
`abstractflow` is not only a visual editor. It is the authoring surface for
clean, complex, recursive orchestration of multiple agents and deterministic
steps.

A published `.flow` bundle can become a specialized workflow, or effectively a
specialized agent, that exposes a simple input/output contract. This lets a
complex multi-agent system be reused from `abstractassistant`, `abstractcode`,
custom apps, or other workflows as though it were a simple query-to-answer
capability.

This is the main reason to standardize higher-level package usage on
`abstractgateway`: the same specialized workflow should run with the same
durability, approvals, artifacts, memory, and observability everywhere.

### 8) Use dependency level to assess code evolution impact
Every cross-package change should identify the lowest affected layer:

```
Shared vocabulary and schemas
  abstractsemantics
        |
        +--> AbstractRuntime (required schema refs)
        +--> AbstractGateway semantics endpoint
        +--> memory workflow validation

Knowledge store
  abstractmemory
        |
        +--> optional Runtime/Gateway memory_kg handlers
        +--> SmartNote / ai-space / custom knowledge apps

Capability packages (plugins)
  abstractvoice / abstractvision / abstractmusic
        |
        v
AbstractCore
  LLMs, providers, tools, media, capabilities
        |
        +--------+
                 |
AbstractAgent    |
  reusable       |
  agent patterns |
        |        |
        +--------+
        |
        v
AbstractRuntime
  durable workflow kernel and semantics
        |
        v
AbstractGateway
  protected runtime access and control plane
        |
        v
Higher-level apps
  abstractflow / abstractassistant / abstractcode / abstractobserver / custom clients
```

Lower-layer changes require broader review and testing because they can cascade
upward. Higher-layer app changes normally require narrower review, unless they
alter a shared contract such as bundle format, run inputs, ledger mapping,
artifact references, capability discovery, or gateway APIs.

### 9) Record the verified package dependency tree
As of this ADR, the package metadata and runtime integrations imply this tree:

```
abstractsemantics
  -> required by abstractruntime
  -> used by runtime memory-effect handlers and gateway semantics endpoints

abstractmemory
  -> no hard AbstractFramework dependency in package metadata
  -> optional backend extras, e.g. abstractmemory[lancedb]
  -> used by gateway/runtime memory integrations when installed
  -> used directly by SmartNote and ai-space

abstractcore
  -> base LLM/provider/tool/media abstraction
  -> optional extras for providers, tools, media, embeddings, server, vision
  -> discovers abstractvoice/abstractvision/abstractmusic by entry point

abstractagent
  -> abstractcore[tools]
  -> abstractruntime

abstractruntime
  -> abstractsemantics
  -> optional abstractruntime[abstractcore] integration
  -> optional memory effect handlers that import abstractmemory at use time

abstractgateway
  -> abstractruntime
  -> server/http profiles add runtime[abstractcore], abstractagent, abstractflow
     bundle compatibility, abstractcore tools/media/capability extras,
     abstractvoice, abstractvision, and HTTP server dependencies
  -> memory profile should add abstractmemory[lancedb] when KG workflows are
     expected to work out of the box

abstractflow
  -> abstractruntime
  -> abstractcore[tools]
  -> editor/agent extras add abstractagent and editor server dependencies

abstractcode
  -> abstractagent
  -> abstractruntime
  -> abstractcore[tools,media]
  -> direction: gateway-backed execution for durable/shared workflows

abstractassistant
  -> current package metadata still supports local app mode via abstractagent,
     abstractvoice, and abstractcore extras
  -> normal product direction: gateway-first thin client

smartnote / ai-space / custom clients
  -> compose gateway/runtime/core/memory/semantics according to the workflow
```

### 10) Keep install and config entrypoint rules in ADR-0033
This ADR owns package dependency boundaries and gateway-first app direction.
ADR-0033 owns the related install/config/security rules:

- dependency cascades are implemented by entry-point profiles, not by adding
  fake extras to every package;
- `abstractcore` and `abstractgateway` are the two operational configuration
  entry points;
- Gateway auth, Core server auth, and outbound provider credentials are
  separate security surfaces;
- capability readiness must distinguish installed, registered, configured,
  ready, route_available, and available.

## Consequences

### Positive
- Clarifies which packages are libraries, capability plugins, runtime hosts, and
  thin clients.
- Gives deployment decisions a single dependency model.
- Separates vocabulary/schema authority (`abstractsemantics`) from durable
  knowledge storage (`abstractmemory`).
- Supports gateway-first reuse of specialized workflows across assistants,
  code tools, Flow, Observer, and custom clients.
- Makes lower-layer changes visibly higher risk, improving review and test
  planning.

### Negative
- Gateway-first app direction can require migration work for older local-first
  clients.
- Capability plugin contracts must be maintained carefully because small changes
  can affect multiple downstream packages.
- Semantics registry changes are low-level changes and need review from Runtime,
  Gateway, Flow, Memory, and app owners.
- Experimental packages, especially `abstractmusic`, need explicit guardrails to
  avoid accidental production reliance.

### Neutral
- Direct use of `abstractcore`, `abstractvoice`, `abstractvision`, or
  `abstractmusic` remains valid in library mode.
- Direct use of `abstractmemory` remains valid in library mode; framework memory
  workflows should still validate semantics through `abstractsemantics`.
- This ADR refines ADR-0001 and ADR-0028 rather than replacing them.
- ADR-0033 complements this ADR by defining install profile vocabulary,
  configuration precedence, and server-boundary security.

## Packages Affected
- `abstractvoice`
- `abstractvision`
- `abstractmusic`
- `abstractsemantics`
- `abstractmemory`
- `abstractcore`
- `abstractagent`
- `abstractruntime`
- `abstractgateway`
- `abstractflow`
- `abstractassistant`
- `abstractcode`
- `abstractobserver`
- `smartnote`
- `ai-space`

## Related
- ADR-0001: `docs/adr/0001-layered-architecture.md`
- ADR-0018: `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
- ADR-0021: `docs/adr/0021-deployment-topologies-and-supported-scenarios.md`
- ADR-0028: `docs/adr/0028-capabilities-plugins-and-library-framework-modes.md`
- ADR-0031: `docs/adr/0031-workflow-llm-routing-overrides-provider-model-and-base-url.md`
- ADR-0033: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
