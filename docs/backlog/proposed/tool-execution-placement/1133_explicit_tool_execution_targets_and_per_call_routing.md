# 1133 — Define explicit tool execution targets and per-call routing

> Package: abstractruntime, abstractgateway; abstractcore only if portable tool metadata changes
> Type: feature
> Created: 2026-11-07
> Priority: P2
> Labels: tool-execution-placement, durability, seat-framework

## Summary

Define where each tool may execute and how a run selects an authorized target. Support server and client tools in the same run without confusing human approval, LLM hosting, or a remote service with execution placement.

## Why

The operator asks for both client and server execution. Today Gateway's default is server-host execution; a server can itself run on the user's laptop. The operator clarified that the screenshot's topology is correct: the laptop hosts both Gateway and client; theforge-nvidia provides inference only. Moving Gateway to theforge would move default host tool execution there. The missing feature is explicit selection between Gateway-host and client-device execution regardless of colocation.

## Current code reality

Audit date: 2026-11-07. Paths below are relative to the named package, except root backlog IDs.
See [track audit](README.md) for pinned source revisions and limits.

- Core `abstractcore/tools/core.py:ToolDefinition` describes schemas/callables and policy metadata, but has no first-class execution placement contract.
- Gateway `src/abstractgateway/hosts/bundle_host.py` constructs `MappingToolExecutor` under `McpRoutingToolExecutor` and approval policy; `ABSTRACTGATEWAY_TOOL_MODE` selects approval/local/delegated behavior for the host.
- Gateway `src/abstractgateway/mcp_run_tools.py` already routes namespaced MCP tools alongside ordinary tools. This is existing mixed local/MCP execution, not a complete client-device routing protocol.
- Runtime `integrations/abstractcore/effect_handlers.py` already handles runtime-owned tools separately from host-executed calls. Extend these seams rather than introducing a second execution engine.

- Additional review: Runtime `effect_handlers.py:4300–4358` currently resolves media and rewrites tool paths under host workspace policy before executor dispatch. Routing only inside the final executor wrapper would be too late.
- Runtime `core/models.py:177–216` has one current wait per run. Gateway `service.py:523–539,591–610` resolves separate principal/runtime storage planes; physical host identity cannot replace those authority boundaries.

## Scope

### In scope

- Preserve existing host-only behavior by default. Opt-in first support combines existing host and MCP execution with one explicitly paired client adapter; select its owning app and demonstrate local permissions/storage before promotion. First client capabilities are bounded reads/inspection, not arbitrary shell or writes.
- Separate portable tool schema from deployment binding. Runtime composes the admitted binding from schema, target and resource policy; Core needs new metadata only if a portable semantic requirement justifies it. Gateway reaches Core through Runtime facades, never a new direct import or duplicated schema conversion.
- Resolve the target **before** workspace/media rewriting, path authorization and approval presentation. Keep tool identity, executor binding, resource scope and model endpoint distinct. Gateway-host and client-device roles may share hardware without sharing grants.
- Bind the same logical tool to explicit eligible instances. A model may choose among admitted capabilities; arbitrary model-supplied URLs, roots or device IDs grant nothing. Preserve principal/runtime-plane ownership, with independently enforced device-local permissions and no copying of Gateway credentials to the adapter.
- Persist a frozen execution binding before approval/dispatch: existing authoritative call identity, tool/schema revision, executor binding generation, scoped resource references and arguments digest. These are concepts, not adopted field names. Reuse existing call identity after verifying origin/uniqueness; do not invent another operation-ID hierarchy. A changed target/resource/tool binding invalidates prior approval; narrower grants are rechecked at dispatch.
- Initial mixed execution uses ordered target-bound segments and one current delegated wait, retaining authoritative partial results by call identity. No promise of independent server calls overtaking an offline client inside the same batch. Preserve existing host-only ordering/safe parallelism; define opted-in mixed ordering explicitly. Prove persistence of each completed segment before dispatching the next; do not assume it from today's final batch record.
- No automatic client replacement or routing fallback. An unavailable target waits or refuses explicitly. Capability registration is a declaration, not proof of isolation. Existing MCP endpoints remain one adapter option; the first client need not expose an inbound network port.
- Keep bindings optional/versioned. Old runs retain old interpretation, old clients cannot receive unsupported requests, disabling the feature stops new dispatch without migrating pending calls, and new durable vocabulary requires an ADR/migration decision before first real writes.

### Out of scope

- No implementation, deployment, release or new background service is authorized by this proposal.
- No model-provider hosting redesign, orchestrator migration, worker pools, automatic failover, cross-target DAG scheduler or automatic routing based on tool names alone.

## Dependencies and ADR status

- Work-item id: abstractframework-1133; author: framework. Lifecycle: proposed.
- Agora coordination is intentionally omitted per operator instruction on 2026-11-07.
- Governing foundation: root ADR 0006 (durable tools), ADR 0036 (Runtime-owned artifacts), ADR 0037 (hosted file sources and Gateway workspace authority), Runtime ADR 0008 / Gateway ADR 0001 (Core through Runtime facades), all accepted.
- Live client resources require a scoped ADR 0037 extension before implementation; existing Local File uploads still become ArtifactRef. No portable server path or new universal file primitive is implied.
- Reconcile root ADR 0015 (proposed execution targets/MCP workers) and ADR 0021 (deployment topologies). Their historical backlog links and some topology claims are stale; re-audit before treating them as implementation evidence.
- ADR impact: revise/accept the placement and recovery decisions before closing implementation; this proposal does not enact policy.
- Related items and sequence: [track index](README.md), 1133–1136. Existing 0993 replay and 1059 runtime holdings remain their respective umbrellas.

## Promotion criteria

Compare MCP-only, a narrow Runtime client adapter, and a generalized scheduler as recorded in the [architecture review](../../evidence/1133/architecture-review.md). Recommend the narrow adapter with reservations; MCP remains optional and the scheduler is deferred. Promote 1133/1134 together as the client-execution foundation only after the adapter owner, authoritative completion/commit boundary, resource contract and versioned vocabulary are settled. Existing server reads in 1135 and current-topology explanations in 1136 can proceed independently.

## Acceptance criteria

- [ ] Separate Gateway/client processes with different roots execute the same logical read tool against the correct fixture; a same-spelling path cannot cross scopes through pre-dispatch rewriting.
- [ ] A remote-inference-only configuration leaves tool placement unchanged; moving Gateway changes host execution without moving client grants.
- [ ] Unknown/revoked bindings, foreign principals, model-supplied roots and unsupported browser capabilities are refused; no implicit host fallback or direct Core import is introduced.
- [ ] Approval for device/workspace A cannot authorize B after rebinding, even with identical tool names/path strings; expiry and grant narrowing are rechecked.
- [ ] Mixed segments preserve ordered results and committed subsets across restart; one current wait is sufficient and no parallel scheduler is hidden in an executor.
- [ ] Host-only and existing MCP configurations remain compatible; pending new-format calls have a documented disable/downgrade strategy and old clients fail explicitly.

## Testing

Baseline regression commands from the workspace root (use the repository's configured Python environment):

`python -m pytest abstractruntime/tests/test_mcp_remote_tool_executor.py abstractruntime/tests/test_tool_approval_resume_executes.py abstractruntime/tests/test_tool_wait_allowlist_safety.py`

`python -m pytest abstractgateway/tests/test_gateway_mcp_runs.py abstractgateway/tests/test_gateway_import_boundary.py`

These existing suites are starting points, not sufficient proof of the proposed behavior. Add the targeted contract, authorization and failure-injection scenarios above when implementing; retain commands, source revisions and results. This planning pass inspected code and tests, without running these suites or a live deployment experiment.

## External examples and adaptation

[VS Code](https://code.visualstudio.com/api/advanced-topics/extension-host) supplies the explicit local/workspace placement precedent. AbstractFramework additionally has durable effects and principal-specific stores, so extension placement is not our authorization model. [Temporal task queues](https://docs.temporal.io/task-queue) show worker routing, but a laptop holding private files is not interchangeable with another worker. Reuse Runtime, not a second orchestration service.

## Refinement record — 2026-11-07

The initial proposal intentionally explored broad placement and recovery. The operator then requested external examples plus one architect and one adversarial reviewer. The refinement keeps the original client/server goal but narrows the first release, makes authority boundaries explicit and leaves generalized scheduling deferred. See [external precedents](README.md#external-precedents-verified-2026-11-07) and the [architecture review](../../evidence/1133/architecture-review.md). All work remains proposed; no policy or wire format is adopted here.

## Receipts

- Source audit and operator request, 2026-11-07; [audit evidence](README.md).
- No implementation completion claimed. Recheck current code before promotion and fold useful findings into this item.
