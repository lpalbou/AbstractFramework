# Proposed: AbstractCore lightweight capability surface boundary

## Metadata
- Created: 2026-06-14
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0035, ADR-0036
- ADR impact: Known drift tracked by `0201_gateway_action_descriptor_contract.md` unless direct Core demand justifies a narrower Core-specific contract.

## Context
The framework now has a clearer two-entrypoint story:

- `abstractgateway` for persistent high-level functionality, durable runs, replay, workflow policy,
  and cross-client continuity;
- `abstractcore` for lower-level direct capability access in scripts, notebooks, existing apps, and
  lightweight `/v1` usage.

The risk is accidental contract inflation: as Gateway gains typed durable action projection, people
may try to copy that same surface into Core even when direct Core users only need lower-level
catalogs, route defaults, and a narrow `generate(request, output)` contract.

## Current code reality
- Root `docs/architecture.md` already describes Gateway as the durable control plane and Core as the lightweight LLM/kernel entrypoint.
- `abstractcore` already exposes provider/model abstraction, capability plugins, route defaults, and optional `/v1` servers without Gateway workflow/replay semantics.
- Runtime discovery facades already treat provider/model/voice/music/vision catalogs as snapshot reads rather than durable run actions.
- No dedicated Core-side typed action contract exists today, which is currently a feature rather than an omission.

## Problem or opportunity
The gateway-first action track needs a durable memory of where the lower-level boundary should stop.
Without that, future work may overload Core with Gateway-specific action/workflow/policy/replay
concepts and make direct lightweight apps heavier than necessary.

## Proposed direction
Keep AbstractCore lower-level by default:

- preserve existing provider/model/catalog/default-route surfaces as the normal discovery layer for
  direct Core apps;
- allow a narrow Core-owned `generate(request, output)` contract and small request/output helpers
  as the main lower-level semantic API for direct scripts, notebooks, and Core-server callers;
- allow a narrow per-call route-resolution surface beneath that contract, and only consider a
  separate advanced public override surface if real evidence justifies it and it remains
  lower-level than Gateway action/workflow descriptors and replay semantics;
- only add a narrower Core-side capability snapshot contract if real direct-Core consumers need
  more structure than those existing surfaces provide;
- if such a contract is ever added, keep it explicitly non-durable and free of workflow catalog,
  run-policy, or cross-client replay semantics.

## Why it might matter
- Preserves the Gateway/Core separation the top-level architecture already documents.
- Avoids duplicating policy and replay concepts in the wrong package.
- Keeps direct Core scripts and lightweight apps small while still allowing multimodal growth.

## Promotion criteria
- Direct Core users demonstrate repeated need for a stable typed discovery surface beyond existing
  catalogs/default-route helpers.
- The proposed Core surface can stay clearly non-durable and lower-level than Gateway actions.
- There is a concrete interoperability need that cannot be met by Gateway-first deployment.

## Validation ideas
- Audit real Core-only consumers and list which discovery fields they currently need.
- Compare an existing Core catalog/default route flow against any proposed lighter snapshot surface.
- Confirm the boundary remains understandable in docs and package ownership.

## Non-goals
- This proposal does not authorize copying Gateway action descriptors into Core.
- It does not forbid a narrow Core `request/output` contract; that is the intended lower-level
  abstraction and remains materially smaller than Gateway actions/workflows/replay.
- It does not change Runtime ownership of durability or Gateway ownership of high-level replayable
  actions.
- It does not weaken Core's existing multimodal plugin/capability role.

## Guidance for future agents
Promote this only if direct Core usage proves the current lower-level catalogs/default-route APIs
are insufficient. Until then, let Gateway own the durable/high-level capability vocabulary.
