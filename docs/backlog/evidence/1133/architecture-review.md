# Client-device execution: architecture review and proposal refinement

Date: 2026-11-07. Planning evidence for proposed 1133–1136, not an accepted ADR or implementation receipt.

## Execution Mode

Independent source audit and synthesis. Root authored the documents; two subagents inspected code read-only. No runtime tests, fault injection, installed-copy verification or live deployment experiment. Agora intentionally excluded by the operator.

## Planned Reviewer Set

One architect and one adversarial subagent, exactly as requested by the operator. The architect skill's default three-charter swarm is superseded by that explicit reviewer count.

## Actual Reviewer Set

Architect: minimal extension, platform boundaries and alternatives. Adversary: completion authority, failure windows, scope and operational risks. Root: primary-source research, independent spot checks, synthesis and document validation.

## Subagents Used

`/root/architect` and `/root/adversarial`. Both completed independent read-only reviews. No nested agents.

## Fallback Reason

None: tools worked. Two reviewers are the requested execution mode, not a capacity fallback.

## Contract Degradation

No claim of a three-charter swarm. Both agents issued their own findings/verdict before synthesis. The requested architect explored three genuine alternatives; the adversary independently tested the safety of the proposed boundary.

## Decision Question

What is the smallest extension that lets one Runtime run use authorized Gateway-host and client-device tools without duplicating execution authority or weakening recovery and resource permissions?

## Current Reality

Verified source HEADs: Core `b4cc7dd5e730abd418b40bb6cfe32e601619388a`, Runtime `86fc207b4d298d67b13ec5184f48def19415f8e4`, Gateway `2b952dd0c6816c5703a44484ca903977dcbaa82d`. No affected source changed during the pull sweep. The operator reports Gateway and client colocated on the laptop and theforge-nvidia serving inference only. This review does not independently verify the running installation.

Existing pieces include host/MCP routing, Runtime-owned artifact tools, approval wrappers, one current run wait, command storage, per-principal service planes and runtime integration facades. Our task is to extend those pieces, not reproduce another framework.

## Observed Evidence

Package-relative locations, verified 2026-11-07:

| Evidence | Implication |
|---|---|
| Gateway `src/abstractgateway/hosts/bundle_host.py:1907–1972`; `mcp_run_tools.py:176–210` | Existing host+MCP composition, with host-wide delegated mode. New work is client bindings/recovery, not the invention of remote tools. MCP registry metadata is reread at call time. |
| Runtime `src/abstractruntime/integrations/abstractcore/effect_handlers.py:4300–4358` | Paths/media are resolved under host scope before executor dispatch. Target admission must happen before these transformations. |
| Runtime `core/models.py:177–216`; `effect_handlers.py:4531–4580` | One current wait and durable delegated payload already exist. Initial ordered segments fit this model better than a target scheduler. |
| Runtime `core/runtime.py:589–593` | Nonempty incoming runtime_call_id is preserved. Existing IDs are correlation primitives, not credentials or proof of origin. |
| Runtime `core/runtime.py:3442,3548,3635–3681`; Gateway `runner.py:2605–2614` | Generic resume accepts trusted external result payloads, and result merging is positional/conditional. New client waits need exact target-bound validation at the authoritative boundary, including alternate ingress. |
| Runtime `storage/commands.py:293–296`; `core/runtime.py:3683–3742,3806–3873` | Command ID dedupe does not compare content; completion ledger writes and run save are separate. Command acceptance is not a durable applied completion receipt. Review each backend's recovery semantics. |
| Gateway `service.py:523–539,591–610` | Principal/runtime plane isolation exists and must survive target binding. Two accounts on one machine remain different authorities. |
| Runtime ADR 0008; Gateway ADR 0001 | Gateway accesses Core through Runtime facades. No new direct Core imports or copied schema conversion. |
| Root ADRs 0036 and 0037 | Runtime owns artifacts; Gateway owns scoped WorkspacePath authority. Existing Local File upload becomes ArtifactRef. Live client resources require an explicit narrow policy extension. |

These are extension hazards, not a demonstrated unauthenticated exploit or a claim that current deployed data is compromised.

## Inference Or Unknowns

- No first client adapter is selected yet. An existing desktop app/session helper is the candidate class; browser/phone shell capability or durable storage cannot be assumed. Pairing, local consent and runtime-plane ownership require proof.
- A client journal records what its process knows. Neither that journal nor authenticated transport proves the actual external side effect; stronger attestation is not proposed.
- Actual sandbox guarantees, installed versions and Tasks capability support are unknown. Local execution does not imply local-only data: tool results can enter remote inference.
- Durable partial-batch progress, backend crash recovery and bounded pending queries need implementation evidence. Per-run locking is not a transaction across stores.

## Alternatives

**A — Existing MCP-only integration.** Register a reachable client MCP endpoint and use existing routing. Best for managed desktops with stable reachability and limited offline needs. Small and reversible, but endpoint connectivity/tunnels do not supply local consent, device-specific pending delivery or safe recovery. Keep as an option; insufficient as the universal client contract.

**B — Narrow client adapter inside existing Runtime effects/waits.** Gateway authenticates a paired client; Runtime owns the frozen operation binding, pending state and accepted completion. Adapter executes installed permitted handlers and journals local results. Best fit for the stated laptop/server requirement; needs real result-validation and commit work. No separate scheduler or workflow engine.

**C — General execution-target scheduler.** Model a fleet, scheduling policy, capability matching, worker leases and automatic failover. Appropriate if interchangeable compute fleets and resource mobility become actual requirements. Today it introduces overlapping authority, more operations and difficult migrations; a user's laptop is not an interchangeable worker. Defer.

## Comparison Matrix

| Alternative | Ownership | Migration cost | User impact | Operational burden | Reversibility | Evidence gaps |
|---|---|---|---|---|---|---|
| A: MCP-only | Existing executors/registry | Low | Endpoint setup and reachability | Low–moderate | High | Offline delivery and side-effect recovery |
| B: integrated adapter | Runtime execution; Gateway admission/transport; client local enforcement | Moderate, additive | Explicit pairing and resource selection | Bounded, one adapter first | High before format engraving | Completion authority, crash consistency, adapter guarantees |
| C: scheduler | New authority overlaps | High | More setup and placement policy | High | Low after state adoption | Demonstrated fleet/migration need |

## Charter Verdicts

- **Architect — Recommend With Reservations:** B; retain A as a transport option; defer C. Keep tool schema separate from deployment binding; resolve target before resource rewriting; start with ordered durable segments.
- **Adversary — Recommend With Reservations:** B's direction, **not ready for implementation promotion** until narrow completion authority, commit semantics and immutable binding are specified. New client waits must not remain writable through unchecked generic resume.
- **Root synthesis — Recommend With Reservations:** adopt B as the proposed direction, retain all promotion gates. No production readiness or accepted-policy claim.

## Tensions

- Sequential mixed segments can delay a host call behind an offline client. Accept this clearly documented first-release tradeoff; independent server workflows continue, but same-batch concurrency needs a proven dependency model.
- A rebuildable pending index avoids a second authority, but must be efficient and recoverable. Do not choose full-ledger scans merely to avoid an index, or invent another authoritative queue merely to improve polling.
- A narrow read-only first client reduces mutation risk but still exposes private bytes and can observe changed input. Grants, data destinations and snapshot provenance remain necessary.
- Capturing every target/environment detail makes provenance expensive and leaks data. Record minimal stable binding facts; project labels/liveness; distinguish reported and verified evidence.
- External frameworks provide useful mechanisms, not drop-in architecture: VS Code lacks our durable run contract; Temporal's workers may be interchangeable; MCP roles do not identify resource ownership; LangGraph replay does not make effects atomic.

## Recommendation

Keep four focused proposals, with independently useful server reads/topology documentation and a paired 1133/1134 client foundation:

1. Default stays Gateway-host execution. Add one optional paired client adapter with bounded read-only handlers; do not promise arbitrary browser tools, downloaded code or device failover.
2. Resolve an admitted target/resource binding before arguments are rewritten or approved. Gateway retains hosted workspace authority; adapter independently enforces local grants. Freeze binding and arguments for that call; later reconfiguration requires reauthorization.
3. Reuse existing call identity with validated origin and scope. Runtime owns pending/accepted outcomes, Gateway owns authenticated transport/binding administration, client journal owns local attempt/outbox facts. Specify atomicity or deterministic recovery in existing stores rather than asserting it.
4. Deliver bounded pending work through outbound authenticated queries; notifications are hints. Accept exact delegated results via a guarded Runtime completion path; all external ingress must respect it. Reconstruct server results from authoritative state.
5. Acknowledge applied durable completion, not just command acceptance. Retries of identical completion are stable; conflicting content is refused. Unknown mutations never silently replay or migrate; real client mutations remain deferred until per-tool guarantees are proven.
6. Initial mixed batches use ordered segments with durable partial results. Disable/new-version behavior preserves pending work and never silently translates client paths into host paths.
7. Start server capabilities with existing scoped ledger/artifact reads; no new universal resource layer or MCP wrapper is required. Keep the existing Local File upload contract and propose a narrow ADR extension for live device capabilities.
8. Show admitted execution/resource roles and attributed completion evidence to agents/users. Include inference/data destination only where relevant; never equate placement with sandboxing or data residency.

**Engraving gate:** target/binding vocabulary, versioning and identity grammar remain concepts until an ADR specifies them. No sample JSON in these proposals is an adopted wire contract. Existing persisted records are not renamed or retroactively assigned unknown targets.

## Review Findings Disposition

| Finding | Resolution in proposals |
|---|---|
| Generic resume bypass / forged client identity | 1134 guarded completion at Runtime boundary and all external ingress; authenticated binding, not supplied IDs |
| Client overwrites server/precomputed results | 1134 exact delegated membership by ID; server reconstructs authoritative entries |
| Command accepted versus outcome committed | 1134 applied receipt, content conflict and per-backend crash matrix |
| Target chosen after path rewriting | 1133 resolve before media/workspace transformations |
| Approval survives rebinding | 1133 frozen binding; 1136 invalidated approval and consistent display |
| Duplicate queue/ledger/scheduler | 1133 ordered segments; 1134 Runtime authority and rebuildable bounded index |
| Premature Core schema expansion | 1133 deployment binding outside intrinsic tool schema; Core changes only if justified |
| Server-resource scope creep/dependency | 1135 read-only increment independent of client routing; 1059 retains broad search |
| Local file contract conflict | ADR 0037 explicitly preserved; live capabilities require policy extension |
| Unsupported assurance about device truth | 1136 reported/attributed vs verified provenance and remote-inference distinction |

## Evidence Needed

Before client implementation promotion: chosen adapter/owner and local permission guarantees; reviewed resource/binding/identity schema; narrow completion authorization and backend commit design; defined query/result/upload/retention budgets. Implementation closure then requires separate-process different-root demos, forged-result/cross-plane tests, rebind/revocation tests, crash recovery at each boundary, duplicate-content conflicts, bounded query benchmarks and compatibility/disable tests. Mutating client tools need additional per-tool idempotency/reconciliation evidence. No new package service is justified without evidence that the existing Runtime seam cannot meet these requirements.

External primary-source comparisons are retained in the [track README](../../proposed/tool-execution-placement/README.md#external-precedents-verified-2026-11-07); per-item acceptance criteria make the findings executable without this conversation.

## Final proposal review

Both original reviewers reread the revised four items and this comparison. Both retained
**Recommend With Reservations** for proposal quality, not implementation readiness. Their final
corrections were adopted: 1134 now distinguishes unauthorized duplicate attempts from legitimate
recorded retries; 1135 separates its independent delegated-tool baseline from conditional later
mixed-batch tests. No additional service or abstraction was requested. Remaining reservations are
the explicit promotion evidence above, not undisclosed completed validation.
