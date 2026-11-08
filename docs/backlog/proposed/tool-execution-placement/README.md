# Client-device and Gateway-host tool execution

## Status and purpose

Proposed, 2026-11-07. Four cross-package items clarify placement, recovery, server resource access and agent/user understanding. No implementation commitment or publication. Agora is excluded at the operator's explicit request.

## Items and sequence

- [1133 — Define explicit tool execution targets and per-call routing](1133_explicit_tool_execution_targets_and_per_call_routing.md)
- [1134 — Make delegated client execution recover safely after disconnects](1134_durable_client_tool_jobs_and_uncertain_outcome_recovery.md)
- [1135 — Expose scoped server-owned ledger and artifact tools](1135_server_owned_runtime_and_artifact_tool_capabilities.md)
- [1136 — Show agents and users where each tool actually executes](1136_execution_provenance_and_agent_topology_grounding.md)

1133 and 1134 are the paired foundation for opted-in client execution: explicit bindings plus safe delivery/completion. 1135 can first expose existing scoped server reads independently; 1136 can document current topology independently. Their mixed-execution/provenance extensions use the foundation later. Nothing requires all four items to ship together.

The [architecture comparison and adversarial findings](../../evidence/1133/architecture-review.md)
record the requested one architect + one adversarial review. Both recommend the narrow integrated
adapter **with reservations**; client implementation promotion remains gated on the adapter,
authority/commit contract and ADR. No new scheduler, Temporal dependency or required MCP Tasks
service is proposed.

## What “client” and “server” mean here

The **server** is the Gateway/runtime execution host, not the model inference endpoint. The **client** is the connected user device/application; executing there requires an actual execution adapter, not just an approval UI. A phone, browser or desktop client must advertise only capabilities it can execute.

The operator's concrete current setup is Gateway + client on the laptop, with inference on theforge-nvidia. The screenshot's all-laptop tool explanation is consistent with this topology. If Gateway moves to theforge, ordinary host tools move there, while the laptop remains a client. Colocation must not erase these logical roles.

Desired scenarios include client-local image/code processing and server-local workspace/artifact inspection or web search. File origin does not force processing location: a client image can be processed locally, or explicitly uploaded for server processing. Paths, credentials and permissions are target-scoped. Web search is not intrinsically server-only; contact with an external search service does not locate the executor.

## Current code audit

Inspected source revisions (2026-11-07, after the pull sweep):

| Package | Git HEAD |
|---|---|
| abstractcore | `b4cc7dd5e730abd418b40bb6cfe32e601619388a` |
| abstractruntime | `86fc207b4d298d67b13ec5184f48def19415f8e4` |
| abstractgateway | `2b952dd0c6816c5703a44484ca903977dcbaa82d` |
| root, before this planning change | `408bade2961585b90e7500126c38898711b66634` |

| Surface | Existing behavior and limits |
|---|---|
| Core tool definitions | `abstractcore/abstractcore/tools/core.py:ToolDefinition` supplies schemas and optional callables; no first-class client/Gateway placement field. Core callable execution happens in its embedding process; tool declarations alone do not locate execution. |
| Core compatibility server | `abstractcore/abstractcore/server/app.py:_normalize_openai_responses_tools` normalizes declarations; its documentation explicitly excludes server-side tool execution in this path. Do not confuse Core inference server with Gateway runtime host. |
| Gateway host | `abstractgateway/src/abstractgateway/hosts/bundle_host.py` defaults to approval-wrapped in-process execution. Client approval resumes execution in Runtime, not on the approving client. `local/local_all` and `delegated` are alternative host modes. |
| Default tools | Runtime `integrations/abstractcore/default_tools.py` supplies web, filesystem and command tools to Gateway's mapping executor. Web tools are not a separate hard-coded server-only class. |
| MCP | Gateway `mcp_run_tools.py` routes namespaced calls to registered MCP servers (stdio on its host or HTTP elsewhere). Runtime supplies direct and delegated MCP executors. This is real remote-tool support already; this track does not propose it from scratch. |
| Runtime-owned tools | Runtime `effect_handlers.py` resolves `open_attachment` using its artifact store and preserves those results when host calls wait. Gateway also binds server-owned skill/note tools. |
| Durable waits | Runtime records delegated calls as JOB waits, and `core/runtime.py` consumes externally submitted results. The existing MCP test reconstructs Runtime from disk before external completion. A durable pending request is not a complete client reconnect dispatcher. |
| Identity and retries | Runtime fills missing runtime call IDs but preserves supplied ones. Gateway command IDs deduplicate command acceptance. Neither authenticates a device nor proves that an external side effect happened once. Direct MCP calls inspected send name/arguments, while the bundled worker uses literal call_id `mcp`; no end-to-end durable worker dedupe contract was found in these paths. |

### Answer to the reconnect question

A persisted JOB wait can survive a restart and an external executor can later return its result. The ledger is a record, not an active requester: a Gateway/client protocol must discover pending work, authenticate its recipient, deliver it and submit completion. If the client crashed after a side effect but before recording/reporting success, the server cannot know from the pending wait alone whether to execute again. 1134 covers durable client journals/outboxes, delivery ownership, result deduplication and explicit uncertain-outcome handling. Exactly-once arbitrary external effects are not promised. Server-host execution has analogous crash windows.

## Refined first implementation and ownership

Keep Gateway-host execution as default. Add one explicitly paired, opted-in client adapter with
installed bounded read-only handlers. Pick its owning app and prove permissions/storage first;
a browser connection alone is not a filesystem/shell executor. Existing MCP routing remains
available. Client mutations, automatic replacement and generalized scheduling remain deferred.

| Fact | Proposed authoritative owner |
|---|---|
| Portable callable/provider schema | Core; no deployment/device binding forced into ToolDefinition |
| Pending operation, frozen binding, accepted result and replay | Runtime, using existing effects/waits/stores and a defined recovery commit |
| Principal/plane admission, hosted workspace policy, pairing and exposed transport | Gateway, through Runtime facades for execution semantics |
| Local resource permission, started attempt, saved result and completion outbox | Client adapter; local facts do not complete the workflow by themselves |
| Pending-work lookup / labels / availability | Bounded projections of authoritative state, not competing lifecycle stores |

Resolve targets **before** current workspace/media argument rewriting. Bind approval to the
actual executor/resource/arguments. Use ordered mixed segments and a single current wait first;
this may defer a later host call while a prior client call is offline. Existing host-only
execution behavior stays unchanged. No silent route fallback.

Client results enter a narrow authenticated completion contract, enforced at Runtime's new
client-wait boundary as well as transport admission; generic resume must not bypass it. Exact
pending identities and delegated membership are validated; server-owned results are reconstructed
by the server. An accepted command is not yet an applied completion. A stable durable applied
receipt lets the client safely retire its outbox. Backend crash consistency must be demonstrated.

## Concrete scenarios for validation

These are desired behaviors, not adopted field names or claims of current implementation.

| Request | Executor and resource | Required behavior |
|---|---|---|
| Inspect code selected on the laptop while Gateway is on theforge | Paired laptop handler; locally granted resource | Resolve on laptop, never rewrite the path under theforge's workspace. First adapter supports bounded inspection, not arbitrary shell. |
| Inspect generated server artifacts | Owning Runtime; authorized ArtifactRef | Use existing scoped capability; no client store mount or storage MCP service. |
| Analyze a local image on the server | Explicit upload, then server processing | Preserve ADR 0037 Local File -> ArtifactRef; bytes, quota and data destination are explicit. |
| Process an image on the laptop, then summarize with remote inference | Paired client; local input; permitted result sent to model | Local execution does not mean the result remains on-device. |
| Search the web | Admitted host or client implementation; its allowed network access | Search-provider location does not determine executor location; default remains host. |
| Client disconnects after producing a result | Same persisted operation and paired executor | Reconcile and resend saved result; do not blindly reexecute or move to another device. |
| A future client mutation loses its outcome | Original binding and recorded attempt | Uncertain; reconcile rather than retry by timeout alone. Such mutations are not in the first adapter scope. |
| Gateway and client share the laptop | Distinct logical scopes, possibly same machine | Preserve grants and accurate display; remote model choice does not move tools. |

## External precedents, verified 2026-11-07

These are design inputs, not dependencies or claims that those products solve the whole problem.

| Precedent and primary source | Useful pattern | AbstractFramework difference / limit |
|---|---|---|
| [VS Code extension hosts](https://code.visualstudio.com/api/advanced-topics/extension-host) and [remote APIs](https://code.visualstudio.com/api/advanced-topics/remote-extensions) | Declared execution requirements distinguish UI/device from workspace host; resource APIs can route separately. | Gateway owns durable runs and may serve many devices/accounts/entities. Copy explicit placement, not the extension lifecycle or automatic relocation. Scope every resource; a colocated process is not automatically authorized. |
| [Temporal queues](https://docs.temporal.io/task-queue) and [idempotency](https://temporal.io/blog/idempotency-and-durable-execution) | Workers retrieve pending activities; stable operation identity and application-level deduplication make selected retries safe. | Runtime already has effects, waits, ledger and resume. Add no Temporal service or competing workflow/queue authority. A laptop with private files is not a fungible worker that another device can replace. |
| [LangGraph Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api) | Restore saved task results during replay; isolate side effects and design retries to be idempotent. | Use Runtime's existing explicit effects and result records, not a second checkpoint system. A saved batch result is not evidence of durable per-call progress before that batch commits. |
| [MCP Tasks](https://tasks.extensions.modelcontextprotocol.io/) | Durable handles separate task lifetime from an HTTP connection; negotiated support permits later status/result retrieval. | MCP server is a protocol role, not necessarily our Gateway. A laptop executor may be behind NAT. Tasks are an optional adapter capability, not the source of run truth or a required first-release transport. A task handle is not side-effect deduplication. |
| [Claude client/server tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) | Declare who executes a call; provider-hosted tools differ from application-executed calls. | An API provider's “client tool” may execute inside our Gateway on theforge. Use Gateway-host/device terminology in our product, independent of model-provider hosting. |

The [MCP Python SDK migration guide](https://py.sdk.modelcontextprotocol.io/migration/) currently
says its redesigned Tasks extension is not implemented. This is a dated upstream observation,
not an audit of AbstractCore's installed dependencies; validate actual peer/adapter capabilities
before selecting it. Never infer durable task support merely because an endpoint speaks MCP.

## Existing decisions and related work

- [ADR 0037, hosted file sources](../../../adr/0037-hosted-file-source-contract-and-workspacepath-authority.md): preserve Local File uploads becoming ArtifactRef and Gateway-owned WorkspacePath. Live device capabilities need an explicit scoped extension to this policy before implementation.
- [ADR 0036, artifact ownership](../../../adr/0036-artifact-descriptor-contract.md): Runtime owns canonical artifact meaning and provenance.
- Runtime ADR 0008 and Gateway ADR 0001: Gateway reaches Core through Runtime facades; this track must not add a direct dependency.
- [ADR 0006, accepted durable tool execution](../../../adr/0006-durable-tool-execution.md).
- [ADR 0015, proposed execution targets and remote workers](../../../adr/0015-execution-targets-and-remote-tool-workers.md): relevant direction, not a shipped guarantee. Its legacy backlog paths are absent from the current tree; similarly numbered current items refer to unrelated work. Do not recreate or silently reuse those old IDs.
- [ADR 0021, deployment topologies](../../../adr/0021-deployment-topologies-and-supported-scenarios.md): explicitly calls mixed client/server routing a missing stable end-to-end protocol. Broader topology/auth statements need rechecking against current code.
- [0993 canonical replay](../../planned/0993_one_ledger_replay_many_views.md): use its shared projections for provenance and recovery views.
- [1059 runtime holdings](../1059_runtime_holdings_as_a_queryable_virtual_space.md): owns universal browsing/search; 1135 owns placement and agent integration of existing scoped capabilities.

## Validation and limits

This is a source/test inspection, not a live deployment or fault-injection result. No claims are made about the running user's current environment beyond their topology clarification. Existing test commands and proposed validation are in each item. Planning checks cover links, metadata, unique existing track IDs, cited local paths and overview counts. The external-source comparison and review record are planning evidence, not application test receipts. Application code is unchanged.

## Non-goals

No new scheduler, mid-run orchestrator migration, machine persistence, mandatory client execution, arbitrary raw-ledger edits or universal exactly-once guarantee. No automatic transfer of user files or permissions between execution domains.
