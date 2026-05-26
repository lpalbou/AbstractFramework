# ADR-0012: Portable WorkflowArtifact (Serializable)

## Status
Deprecated

## Dates
- Proposed: 2025-12-22
- Accepted: 2026-01-08
- Deprecated: 2026-01-08


## Context
Today, AbstractFlow workflows are portable across *hosts* (editor backend vs CLI) primarily via the **VisualFlow JSON** format and the portable compiler/executor helpers in `abstractflow.visual`. This already satisfies the goal “run the same flow outside the AbstractFlow web backend”.

However, we have a second, stricter goal emerging: **execute workflows outside of the `abstractflow` Python dependency** (e.g., in AbstractCode-only installs or inside third-party programs that want a smaller surface area). This is not fully achievable with the current execution substrate:
- `abstractruntime.WorkflowSpec` is **callable-based** (node handlers are Python functions), so it is not a fully serializable workflow artifact.
- Therefore, executing VisualFlow JSON still requires `abstractflow` (to compile VisualFlow → callable graph).

We need a durable, versioned, JSON-safe “workflow execution spec” that can be executed by AbstractRuntime without importing AbstractFlow (while keeping ADR-0001 layering intact).

## Decision
Define (and later implement) a **serializable workflow execution artifact** (“WorkflowArtifact”) with the following properties:

1) **JSON-safe by construction**
- The artifact must be persistable and transferable as JSON (no callables).
- Any non-trivial payloads must be referenced via `ArtifactStore` pointers, not inlined.

2) **Runtime-executable via a registry**
- AbstractRuntime executes the artifact by dispatching node types through a host-provided registry:
  - `node_type` → `NodeHandlerFactory` (builds a runtime node handler or executes an interpreter step).
- This preserves host portability: third-party programs can choose which node types exist and how they are implemented.

3) **Effects remain the universal side-effect boundary**
- The artifact must express side effects only via `EffectType` (LLM_CALL, TOOL_CALLS, ASK_USER, MEMORY_*, START_SUBWORKFLOW, …) per ADR-0002/0006.
- The runtime remains the sole owner of executing effects and persisting the ledger/run state.

4) **AbstractFlow remains an authoring/compiler layer**
- AbstractFlow continues to own:
  - VisualFlow JSON schema (authoring)
  - Flow composition APIs
  - Compilation from Flow/VisualFlow into WorkflowArtifact
- Hosts that want minimal dependencies can load WorkflowArtifact without importing AbstractFlow.

## Consequences

### Positive
- Enables “run workflows anywhere” without pulling the AbstractFlow dependency tree.
- Establishes a stable seam for:
  - third-party integrations
  - server-side execution
  - future packaging splits (e.g., a minimal “workflow spec” package)
- Reduces duplication pressure (multiple compilers/executors re-implementing semantics).

### Negative
- Requires careful schema versioning, migration, and compatibility policies.
- Increases surface area: artifact schema + node registry contracts must be documented and tested.
- Some node types (e.g., sandboxed Python code nodes) will require explicit host support and trust models.

### Neutral
- This ADR does not mandate *where* WorkflowArtifact lives (new package vs `abstractruntime` submodule), but it must not violate ADR-0001 (runtime kernel remains dependency-light).

## Packages Affected
- **AbstractRuntime** (artifact execution support + registry hooks)
- **AbstractFlow** (compiler emits artifact; visual editor exports artifact or VisualFlow JSON + compiler remains available)
- **AbstractCode** (can run artifact directly; can become a “host runner” without requiring AbstractFlow)

## Related
- ADR-0001: Layered Architecture (`docs/adr/0001-layered-architecture.md`)
- ADR-0002: Effect System Design (`docs/adr/0002-effect-system-design.md`)
- ADR-0006: Durable Tool Execution (`docs/adr/0006-durable-tool-execution.md`)
- Backlog: `docs/backlog/completed/082-abstractflow-visual-flow-portability-audit.md`
- Backlog (implemented): `docs/backlog/completed/094-framework-workflowartifact-portable-execution-spec.md`
- `docs/architecture.md`

---
## Deprecation note (2026-01-08)

We deprecated WorkflowArtifact execution because it introduced (and required maintaining) a second semantics engine (`WorkflowArtifact → WorkflowSpec`) alongside the VisualFlow compiler/executor path.

Current architecture:
- VisualFlow compilation semantics live in **one place**: `abstractruntime.visualflow_compiler`.
- Workflows are distributed as **WorkflowBundles (.flow)** containing `flows/*.json` (VisualFlow root + reachable subflows).
- AbstractGateway bundle mode compiles `manifest.flows` via the runtime compiler and executes durably (no `abstractflow` import).

If we later re-introduce a versioned execution IR, it must come with an explicit compatibility policy and must not recreate dual semantics engines.

