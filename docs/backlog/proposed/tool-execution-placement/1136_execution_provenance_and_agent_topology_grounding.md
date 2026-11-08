# 1136 — Show agents and users where each tool actually executes

> Package: abstractcore, abstractruntime, abstractgateway, client views
> Type: feature
> Created: 2026-11-07
> Priority: P2
> Labels: tool-execution-placement, durability, seat-framework

## Summary

Give agents and users authoritative, appropriately redacted execution-location information before a call and recorded provenance afterward. Explain current placement correctly and prevent future topology claims based solely on paths.

## Why

The operator clarified that the screenshot is consistent with the actual deployment: Gateway and client are on the laptop, while theforge-nvidia performs inference only. This is not evidence of an incorrect agent answer. If Gateway moves to theforge, default host tools execute there instead. The clarity requirement is to expose that topology and allow deliberate client-device versus Gateway-host selection; a web tool can execute on either while contacting an external service. Sandbox provenance is a general validation requirement, not an audited defect in the screenshot.

## Current code reality

Audit date: 2026-11-07. Paths below are relative to the named package, except root backlog IDs.
See [track audit](README.md) for pinned source revisions and limits.

- Gateway `hosts/bundle_host.py` chooses executors and `mcp_run_tools.py` knows registered MCP transport/target metadata, but these are not one universal per-call placement/provenance contract.
- Core's `server/app.py:_normalize_openai_responses_tools` explicitly says normalization does not execute server tools. A provider tool declaration is not evidence of execution placement.
- Runtime tool results already carry call identities; delegated waits can carry executor metadata. These are foundations for a consistent public projection, not proof that every target/sandbox field is currently recorded.
- Existing 0993 is the canonical replay work and 1059 the resource-space proposal. Reuse their projections instead of adding client-inferred execution truth.

## Scope

### In scope

- Expose a small safe projection of the admitted execution binding: logical executor role/label, permitted resource scope and current availability. Runtime owns durable facts; Gateway serves them; clients and model context render the same meaning. Keep mutable display labels and liveness out of immutable operation identity.
- Separate requested target, admitted binding and executor-reported outcome. An authenticated paired device can still lie about its OS action; record attribution, not an unearned claim of independently verified execution. Existing historical records with no target retain unknown provenance.
- Show target and affected resource before approval. Approval binds tool, arguments and execution/resource binding; changed placement invalidates it. Show client-required waiting, disconnected transport, unknown effect outcome and confirmed completion distinctly in live and replay views.
- Publish current host-only/MCP topology truth independently of client implementation. Later add 1133's optional binding fields and 1134's recoverable result states through existing 0993 projections rather than another UI status engine.
- Distinguish execution host, resource location, remote service, inference endpoint, network access and enforced sandbox. Local tool execution may still send result bytes to a remote model; show this data destination when it affects consent, without redesigning model routing.
- Keep context compact and stable: include the allowed capability summary and update on binding changes, not repeated host inventories/heartbeats each turn. Redact credentials, private addresses and unnecessary OS paths; name unknowns instead of inventing a topology.
- Document colocated laptop; remote Gateway plus laptop; two devices; two principals sharing hardware; offline client; artifact upload then server processing; and registered MCP. Explain initial mixed-batch ordering and supported adapter limits in plain language.

### Out of scope

- No implementation, deployment, release or new background service is authorized by this proposal.
- No model-provider hosting redesign, orchestrator migration, universal distributed scheduler or automatic routing based on tool names alone.

## Dependencies and ADR status

- Work-item id: abstractframework-1136; author: framework. Lifecycle: proposed.
- Agora coordination is intentionally omitted per operator instruction on 2026-11-07.
- Governing foundation: root ADR 0006 (durable tools), ADR 0036 (Runtime-owned artifacts), ADR 0037 (hosted file sources and Gateway workspace authority), Runtime ADR 0008 / Gateway ADR 0001 (Core through Runtime facades), all accepted.
- Live client resources require a scoped ADR 0037 extension before implementation; existing Local File uploads still become ArtifactRef. No portable server path or new universal file primitive is implied.
- Reconcile root ADR 0015 (proposed execution targets/MCP workers) and ADR 0021 (deployment topologies). Their historical backlog links and some topology claims are stale; re-audit before treating them as implementation evidence.
- ADR impact: revise/accept the placement and recovery decisions before closing implementation; this proposal does not enact policy.
- Related items and sequence: [track index](README.md), 1133–1136. Existing 0993 replay and 1059 runtime holdings remain their respective umbrellas.

## Promotion criteria

Current-behavior documentation can proceed independently. Promote full implementation once 1133 supplies the placement schema; integrate 1134's recovery states and existing replay projections.

## Acceptance criteria

- [ ] Model-context fixtures accurately answer “where will this run?” for each supported topology; unavailable facts are explicitly unknown.
- [ ] An external web search service is not mislabelled as the tool execution host; client approval does not change the reported executor.
- [ ] Approval, completed result and replay agree on admitted target/resource and distinguish executor-reported evidence from verified facts; changed bindings invalidate approvals and unknown historical targets remain unknown.
- [ ] Regression scenarios preserve the correct laptop-hosted explanation from the screenshot, then change it when Gateway moves remotely; do not infer sandbox guarantees from topology.
- [ ] Two devices and two principals on the same host retain distinct resource grants; an offline client is not labelled a failed server or cancelled side effect.
- [ ] Local execution with remote inference does not claim that data stayed on-device. Model context stays bounded and unchanged across irrelevant heartbeats.
- [ ] Documentation states which behavior is shipped versus proposed and explains the retry limitations from 1134.

## Testing

Baseline regression commands from the workspace root (use the repository's configured Python environment):

`python -m pytest abstractruntime/tests/test_mcp_remote_tool_executor.py abstractruntime/tests/test_tool_approval_resume_executes.py abstractruntime/tests/test_tool_wait_allowlist_safety.py`

`python -m pytest abstractgateway/tests/test_gateway_mcp_runs.py abstractgateway/tests/test_gateway_import_boundary.py`

These existing suites are starting points, not sufficient proof of the proposed behavior. Add the targeted contract, authorization and failure-injection scenarios above when implementing; retain commands, source revisions and results. This planning pass inspected code and tests, without running these suites or a live deployment experiment.

## External examples and adaptation

[Claude's client/server terms](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) are relative to Anthropic: its application-executed “client tool” may run in our remote Gateway. [VS Code](https://code.visualstudio.com/api/advanced-topics/extension-host) makes local/workspace host placement explicit. Our labels must reflect the run's actual binding and resource authority, rather than copying either vocabulary literally.

## Refinement record — 2026-11-07

The initial proposal intentionally explored broad placement and recovery. The operator then requested external examples plus one architect and one adversarial reviewer. The refinement keeps the original client/server goal but narrows the first release, makes authority boundaries explicit and leaves generalized scheduling deferred. See [external precedents](README.md#external-precedents-verified-2026-11-07) and the [architecture review](../../evidence/1133/architecture-review.md). All work remains proposed; no policy or wire format is adopted here.

## Receipts

- Source audit and operator request, 2026-11-07; [audit evidence](README.md).
- No implementation completion claimed. Recheck current code before promotion and fold useful findings into this item.
