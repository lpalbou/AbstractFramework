# 1135 — Expose scoped server-owned ledger and artifact tools

> Package: abstractruntime, abstractgateway
> Type: feature
> Created: 2026-11-07
> Priority: P2
> Labels: tool-execution-placement, durability, seat-framework

## Summary

Make server-owned run, ledger and artifact operations available as explicit agent capabilities, including in runs that also use client tools. Keep storage authority in the owning runtime while permitting authorized client access through APIs.

## Why

The operator needs tools operating on ledger/artifact state. Direct store access belongs on the server, but a client may invoke an authorized server API; the implementation location and the caller's location are distinct. Raw filesystem access to a server data directory is not the appropriate public tool contract.

## Current code reality

Audit date: 2026-11-07. Paths below are relative to the named package, except root backlog IDs.
See [track audit](README.md) for pinned source revisions and limits.

- Runtime `integrations/abstractcore/effect_handlers.py` already handles `open_attachment` against the artifact store before delegating host calls, retaining precomputed results in wait details.
- Gateway `hosts/bundle_host.py` binds `read_skill` to its data root and optional note tools to its artifact store/account.
- Gateway `routes/gateway.py` already exposes artifact search/content and ledger/history surfaces. Reuse scoped facades rather than inventing another store.
- Existing proposed 1059 (runtime holdings as a queryable virtual space) covers the broader cross-resource browsing/search model; planned 0993 covers canonical replay. This item supplies placement and agent capability integration, not a competing search project.

## Scope

### In scope

- First increment is a small read-only inventory: inspect an authorized run's existing ledger/history projection and open/list its artifacts using existing Runtime facades. Record gaps before adding tools; do not duplicate existing open_attachment. No arbitrary ledger mutations or universal search/index implementation.
- Own-runtime resource operations stay runtime capabilities; they do not require an MCP server around storage or client routing to exist first. Gateway admits the request under the correct principal/runtime plane and serves existing views. Physical host ownership alone confers no access.
- Preserve runtime-owned operations under delegated mode and protect their authoritative results during partial-batch reconstruction. A client result cannot substitute a different artifact or claim server-side completion.
- Reuse ArtifactRef and Gateway-approved WorkspacePath authority from ADRs 0036/0037. A path on the client is neither a server workspace path nor an artifact. Existing user-selected Local File upload remains the default hosted path into ArtifactRef; a future live client capability is separately authorized by the placement ADR.
- Upload/download is an explicit authorized transfer with size/quota, content integrity, retention and cancellation handling. Resource existence/access are checked in the owning plane before accepting a returned reference. Device reconnection does not expand grants or resurrect expired/deleted artifacts.
- Apply existing pagination, access limits, redaction, act-only policy and retention to ledger/artifact output. Tool output is data, never an instruction granting more authority. Preserve provenance without exposing private host paths or credentials.
- Keep hosted workspace import policy intact; a read-only tool still requires permission to disclose bytes to Runtime and possibly a remote model. Selecting local execution does not promise local-only data processing.

### Out of scope

- No implementation, deployment, release or new background service is authorized by this proposal.
- No model-provider hosting redesign, orchestrator migration, universal distributed scheduler or automatic routing based on tool names alone.

## Dependencies and ADR status

- Work-item id: abstractframework-1135; author: framework. Lifecycle: proposed.
- Agora coordination is intentionally omitted per operator instruction on 2026-11-07.
- Governing foundation: root ADR 0006 (durable tools), ADR 0036 (Runtime-owned artifacts), ADR 0037 (hosted file sources and Gateway workspace authority), Runtime ADR 0008 / Gateway ADR 0001 (Core through Runtime facades), all accepted.
- Live client resources require a scoped ADR 0037 extension before implementation; existing Local File uploads still become ArtifactRef. No portable server path or new universal file primitive is implied.
- Reconcile root ADR 0015 (proposed execution targets/MCP workers) and ADR 0021 (deployment topologies). Their historical backlog links and some topology claims are stale; re-audit before treating them as implementation evidence.
- ADR impact: revise/accept the placement and recovery decisions before closing implementation; this proposal does not enact policy.
- Related items and sequence: [track index](README.md), 1133–1136. Existing 0993 replay and 1059 runtime holdings remain their respective umbrellas.

## Promotion criteria

Select the initial existing read operations, prove principal/plane scoping and check the Runtime facade coverage. This read-only increment can be promoted independently of 1133/1134; mixed client/server execution tests depend on them later. Reconcile with 1059 and 0993, without making their broader query/replay projects prerequisites for exposing an already-safe scoped read. No new placement-policy decision is needed for documentation of existing behavior.

## Acceptance criteria

- [ ] A Gateway-hosted run can inspect its authorized server artifact and ledger excerpt while the UI is disconnected, without exposing server filesystem paths; later mixed runs exercise the same capability unchanged.
- [ ] Cross-principal/run references are rejected according to existing grants; responses and audit records identify the resource owner and execution target.
- [ ] A client-local file requires explicit transfer before server consumption; large outputs remain artifact-backed and recoverable.
- [ ] Independent baseline: existing delegated-mode tests preserve open_attachment behavior and server-owned results. When 1133/1134 mixed execution is available, add mixed-batch reconstruction tests without making that later feature a prerequisite for the initial server reads.
- [ ] Cross-plane artifact references, raw server paths from client results, traversal/symlink escapes and expired artifacts are refused under existing policy; transferred content has checked ownership, hash and limits.
- [ ] Capability documentation explains which operations already exist and links broader search work to 1059. No direct Core import, storage MCP wrapper or parallel content index is introduced.

## Testing

Baseline regression commands from the workspace root (use the repository's configured Python environment):

`python -m pytest abstractruntime/tests/test_mcp_remote_tool_executor.py abstractruntime/tests/test_tool_approval_resume_executes.py abstractruntime/tests/test_tool_wait_allowlist_safety.py`

`python -m pytest abstractgateway/tests/test_gateway_mcp_runs.py abstractgateway/tests/test_gateway_import_boundary.py`

These existing suites are starting points, not sufficient proof of the proposed behavior. Add the targeted contract, authorization and failure-injection scenarios above when implementing; retain commands, source revisions and results. This planning pass inspected code and tests, without running these suites or a live deployment experiment.

## External examples and adaptation

[VS Code remote APIs](https://code.visualstudio.com/api/advanced-topics/remote-extensions) distinguish executor location from resource routing. For us, resource authority is already specified by ADRs 0036/0037: reuse ArtifactRef and scoped WorkspacePath rather than importing a new virtual filesystem design. A server-owned artifact read remains server-owned even when requested from a phone.

## Refinement record — 2026-11-07

The initial proposal intentionally explored broad placement and recovery. The operator then requested external examples plus one architect and one adversarial reviewer. The refinement keeps the original client/server goal but narrows the first release, makes authority boundaries explicit and leaves generalized scheduling deferred. See [external precedents](README.md#external-precedents-verified-2026-11-07) and the [architecture review](../../evidence/1133/architecture-review.md). All work remains proposed; no policy or wire format is adopted here.

## Receipts

- Source audit and operator request, 2026-11-07; [audit evidence](README.md).
- No implementation completion claimed. Recheck current code before promotion and fold useful findings into this item.
