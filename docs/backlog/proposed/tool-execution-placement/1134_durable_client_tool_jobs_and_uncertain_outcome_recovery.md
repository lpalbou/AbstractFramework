# 1134 — Make delegated client execution recover safely after disconnects

> Package: abstractruntime, abstractgateway, client adapters
> Type: feature
> Created: 2026-11-07
> Priority: P2
> Labels: tool-execution-placement, durability, seat-framework

## Summary

Build authenticated client tool delivery and recovery on existing durable JOB waits. Recover pending work and acknowledged results after reconnect while explicitly handling the interval in which a side effect happened but its result was lost.

## Why

A durable wait preserves the request, but cannot establish whether a disconnected client already sent an email or modified a file. Reissuing every pending call on reconnect risks duplicate effects. The operator's reconnect hypothesis is valid as a delivery goal, not an existing exactly-once guarantee.

## Current code reality

Audit date: 2026-11-07. Paths below are relative to the named package, except root backlog IDs.
See [track audit](README.md) for pinned source revisions and limits.

- Runtime `PassthroughToolExecutor` and `DelegatingMcpToolExecutor` yield delegated work; `make_tool_calls_handler` persists `WaitReason.JOB`, calls and executor metadata.
- `core/runtime.py:589–593` derives missing runtime call IDs but preserves supplied IDs; correlation is not authenticated provenance. Generic resume allows an omitted wait key (`3442`) and accepts external result envelopes. Approval-only resume instead executes the configured runtime executor.
- `tests/test_mcp_remote_tool_executor.py::test_delegating_mcp_executor_waits_and_resumes_durably` covers persisted wait, Runtime reconstruction and external completion; it does not cover a client crashing after a side effect.
- `McpToolExecutor` calls MCP with name/arguments; its local result retains call IDs, but the inspected call does not forward those IDs as a worker idempotency contract. `mcp_worker.py:handle_mcp_request` executes calls with literal call_id `mcp`; no durable result deduplication is established there.
- Gateway `/commands` persists commands and reports duplicate command IDs; this is command acceptance deduplication, not proof of tool-side effect deduplication. SSE replay restores events, not ownership of execution.

- Adversarial review: `runtime.py:3548` skips the approval-choice path for `mode/results`; `3645–3681` merges external results positionally and conditionally. Gateway `runner.py:2605–2614` forwards raw resume payloads. These are trusted-host seams, not an authenticated device completion contract; this audit does not establish an unauthenticated exploit.
- Runtime `storage/commands.py:293–296` (used by Gateway) deduplicates command IDs without comparing payload equivalence. Runtime completion ledger appends are best-effort before run save (`runtime.py:3683–3742,3806–3873`). Accepted command, applied completion and durable workflow state must not be conflated.

## Scope

### In scope

- Reuse Runtime's effect/wait/result authority. Gateway authenticates principal/runtime-plane and paired executor, exposes transport and derives a pending-delivery index from Runtime state under its commit contract. No second authoritative queue, workflow ledger or polling of every ledger. Client journal stores local attempts/results/outbox, never authoritative workflow status.
- Start with one opted-in client adapter and bounded read-only capabilities. Adapter invokes installed permitted handlers, not executable payloads downloaded from a model. Browser/mobile support is not implied. Use outbound authenticated pending-work queries, optionally notifications, with bounded page sizes, outstanding calls, result/upload bytes, polling rate/backoff and retention; set measured budgets before promotion.
- Authenticate client completion through a narrow command/facade and enforce the same guard at Runtime's new client-wait boundary. Generic resume/event/other external completion paths cannot bypass it. Preserve trusted embedded-host use explicitly. Payload client_id or runtime_call_id is not a credential.
- Validate exact persisted wait and delegated call identities, executor binding/generation, principal, arguments digest, schema and result membership before mutation. Key results by identity and reconstruct the batch from server-owned entries; client results cannot overwrite precomputed artifacts or allowlist refusals. Reject missing, extra, duplicate or foreign results; input ordering never establishes authority.
- Define a recoverable completion commit point and queryable stable applied receipt in existing storage. Client retains its result outbox until validated application is durably acknowledged, not just command append. Equal completion retries return the same applied outcome; same identity with different content is a conflict. Specify recovery for ledger/checkpoint/command-index disagreements on every supported backend, or explicitly refuse unsupported backends for this feature.
- Persist intent before delivery and local started/result facts around execution. A process reconnect does not create another attempt; local single-owner execution must survive concurrent/repeated deliveries without duplicate starts. Do not reassign to another device on timeout/lease expiry. Loss or reinstall of the local journal makes previously started unknown operations uncertain, not safe to restart.
- Classify retries by tool semantics. The initial read-only set can retry when safe, but mutable input reads must record which snapshot/hash was observed; read-only is not repeatable-result equivalence. Later mutating tools require idempotency/reconciliation evidence per tool before enabling them. A journal cannot atomically commit an arbitrary external effect.
- Cancellation revokes further dispatch and prevents late results from reviving a run; distinguish cancellation requested from confirmed remote stop. Retain bounded late-attempt evidence where permitted. Recheck grants, target binding, deadlines and artifact access at application time; rejected/revoked completions have a terminal disposition so the outbox does not loop forever.
- Large results use existing authenticated artifact upload/ref contracts, with integrity, quota, retention and ordering before referencing them in completion. Credentials never enter ledger or journal. Document analogous server-side side-effect crash windows; this work promises no universal exactly-once guarantee.

### Out of scope

- No implementation, deployment, release or new background service is authorized by this proposal.
- No model-provider hosting redesign, orchestrator migration, universal distributed scheduler or automatic routing based on tool names alone.

## Dependencies and ADR status

- Work-item id: abstractframework-1134; author: framework. Lifecycle: proposed.
- Agora coordination is intentionally omitted per operator instruction on 2026-11-07.
- Governing foundation: root ADR 0006 (durable tools), ADR 0036 (Runtime-owned artifacts), ADR 0037 (hosted file sources and Gateway workspace authority), Runtime ADR 0008 / Gateway ADR 0001 (Core through Runtime facades), all accepted.
- Live client resources require a scoped ADR 0037 extension before implementation; existing Local File uploads still become ArtifactRef. No portable server path or new universal file primitive is implied.
- Reconcile root ADR 0015 (proposed execution targets/MCP workers) and ADR 0021 (deployment topologies). Their historical backlog links and some topology claims are stale; re-audit before treating them as implementation evidence.
- ADR impact: revise/accept the placement and recovery decisions before closing implementation; this proposal does not enact policy.
- Related items and sequence: [track index](README.md), 1133–1136. Existing 0993 replay and 1059 runtime holdings remain their respective umbrellas.

## Promotion criteria

Promote after 1133's identity and authorization contract is settled and one supported client execution adapter is selected. Decide supported retry guarantees explicitly before enabling mutating tools.

## Acceptance criteria

- [ ] An authorized run observer cannot complete a client job through generic resume with `mode/results`, missing wait key, forged client_id or an event-route bypass; the paired scoped executor can.
- [ ] Duplicate/foreign/missing/extra IDs and a full-sized result array cannot replace server-owned artifact results or allowlist refusals. Reordered valid results are correlated by ID.
- [ ] Same completion twice gives one applied transition/receipt; same ID with different content is a conflict. Client outbox survives command acceptance without application and deletes only after final disposition.
- [ ] Fault injection covers intent-before-delivery, local start/result, artifact upload, command acceptance-before-application, completion-before-run-save and save-before-acknowledgement. Backend recovery yields one authoritative outcome.
- [ ] Reconnect, concurrent adapter sessions, lost local journal, revocation, expiry, cancellation and late results never duplicate a committed result or start an unauthorized attempt. Legitimate retries follow tool policy and are recorded as another attempt under the same operation identity; uncertain attempts are not silently restarted or moved. An ambiguous mutation fixture is never blindly retried, even though real mutations remain disabled initially.
- [ ] Changed source bytes on a repeated read produce honest snapshot provenance; the system does not claim a recovered original result.
- [ ] A separate-process client/server demonstration shows offline waiting, result recovery and continuation; bounded polling/query cost is measured with many unrelated waiting runs, with no full-ledger scan per poll.
- [ ] Existing approval/allowlist/command behavior remains compatible, and no application UI reconnect is required for purely server-owned work whose workflow dependencies permit progress.

## Testing

Baseline regression commands from the workspace root (use the repository's configured Python environment):

`python -m pytest abstractruntime/tests/test_mcp_remote_tool_executor.py abstractruntime/tests/test_tool_approval_resume_executes.py abstractruntime/tests/test_tool_wait_allowlist_safety.py`

`python -m pytest abstractgateway/tests/test_gateway_mcp_runs.py abstractgateway/tests/test_gateway_import_boundary.py`

These existing suites are starting points, not sufficient proof of the proposed behavior. Add the targeted contract, authorization and failure-injection scenarios above when implementing; retain commands, source revisions and results. This planning pass inspected code and tests, without running these suites or a live deployment experiment.

## External examples and adaptation

[Temporal's idempotency guidance](https://temporal.io/blog/idempotency-and-durable-execution) distinguishes retry from deduplicated effects; adopt that failure model without another workflow service. [LangGraph task replay](https://docs.langchain.com/oss/python/langgraph/functional-api) restores recorded results, which motivates per-call persistence but does not prove our commit semantics. [MCP Tasks](https://tasks.extensions.modelcontextprotocol.io/) offers durable remote handles; map supported peers into existing Runtime waits, with negotiated capabilities, never assume Tasks or dedupe from plain MCP support. See the track's dated SDK limitation.

## Refinement record — 2026-11-07

The initial proposal intentionally explored broad placement and recovery. The operator then requested external examples plus one architect and one adversarial reviewer. The refinement keeps the original client/server goal but narrows the first release, makes authority boundaries explicit and leaves generalized scheduling deferred. See [external precedents](README.md#external-precedents-verified-2026-11-07) and the [architecture review](../../evidence/1133/architecture-review.md). All work remains proposed; no policy or wire format is adopted here.

## Receipts

- Source audit and operator request, 2026-11-07; [audit evidence](README.md).
- No implementation completion claimed. Recheck current code before promotion and fold useful findings into this item.
