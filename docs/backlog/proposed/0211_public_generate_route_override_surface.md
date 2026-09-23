# Proposed: Public generate route override surface

## Metadata
- Created: 2026-06-15
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0033, ADR-0035
- ADR impact: Known drift tracked by `0210_core_request_output_contract_and_gateway_projection_alignment.md` and `0204_runtime_capability_intent_resolution_and_policy.md` unless direct-Core or operator evidence justifies a public override surface.

## Context
The framework already has capability-default rows and several ad hoc override paths:

- Gateway text-helper resolution returns `ProviderModelResolution` for some helper flows.
- Runtime local multimodal execution copies default provider/model/base_url into output-spec dicts.
- Local/runtime generation adapters still consume loose `_provider`, `_model`, `base_url`, and
  provider-key fields.
- Gateway per-principal defaults and endpoint profiles already impose policy ceilings and secret
  boundaries.

That means temporary per-call route changes are possible today, but they are not expressed through
one coherent public object and they do not yet rest on one shared resolved-route substrate.

## Current code reality
- `abstractgateway/src/abstractgateway/provider_defaults.py` defines a small text-helper
  `ProviderModelResolution`, but it is not the shared generate-route contract.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py` injects default
  routing into multimodal output spec dicts rather than passing one route object through
  `generate(...)`.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/effect_handlers.py` mutates
  transient route fields when resolving endpoint profiles.
- `docs/backlog/planned/multimodal-capability-projection/0210_core_request_output_contract_and_gateway_projection_alignment.md`
  and `0204_runtime_capability_intent_resolution_and_policy.md` already identify the need for an
  internal structured resolved-route record first.
- `docs/backlog/planned/gateway-control-plane/0147_gateway_per_principal_config_secrets_defaults.md`
  already constrains request/workflow/default precedence through policy ceilings.

## Problem or opportunity
Some direct callers and future workflows may want a structured temporary override surface, for
example:

- keep the configured default image route, but use a different model for one request;
- keep the default voice route, but target a different provider profile for one run;
- choose a dedicated video backend for one output without mutating user or tenant defaults.

However, exposing a public route object too early risks pushing control-plane topology, secret
adjacency, and policy semantics into the lower-level semantic `request/output` contract.

## Proposed direction
Keep this work proposed until the internal route substrate exists.

If promoted later:
- prefer a separate non-durable public override surface such as `route_overrides=` or
  `execution=` rather than nesting a route object inside `request` or `output`;
- make it policy-gated and provenance-carrying;
- keep it compatible with Gateway per-principal ceilings and Runtime replay/audit;
- treat it as an advanced power-user/operator surface, not the default path for apps or prompts.

## Why it might matter
- It could give advanced direct-Core callers and workflow authors a cleaner way to express
  temporary modality-specific routing choices.
- It could reduce ad hoc kwargs sprawl once one internal resolved-route contract exists.
- It could stay optional without weakening the simpler `generate(request, output)` story for most
  users.

## Promotion criteria
- `0210`, `0204`, and `abstractcore/docs/backlog/planned/0809_generate_request_object_and_output_contract.md`
  have landed enough shared route-resolution substrate that the system already emits one structured
  resolved-route record.
- Topology-parity tests prove direct Core, local Runtime, remote Runtime, and Core server agree on
  route resolution or fail closed consistently.
- Real direct-Core or workflow/operator callers show that existing explicit provider/model/base_url
  fields are insufficient or too error-prone.
- Gateway policy and audit rules can constrain any public override surface without allowing secret
  bypass or silent rerouting.

## Validation ideas
- Compare the current scattered override kwargs against one proposed public override object on the
  same scenarios: text route pin, image-model override, video backend swap, and endpoint-profile
  use.
- Verify that any public override surface still yields one explicit resolved-route provenance record
  in replay/history.
- UX-review the advanced override copy so users understand source, permanence, and policy scope.

## Non-goals
- This proposal does not recommend putting a route object inside `request` or `output` now.
- It does not weaken `0210` / `0204` / `0809`; those internal route changes remain the priority.
- It does not authorize thin clients to hand-author provider topology outside Gateway policy.

## Guidance for future agents
Treat this as a conditional advanced-surface question, not as the foundation. The foundation is one
shared internal resolved-route object plus explicit policy ceilings. Only then decide whether a
public structured override surface is worth the extra complexity.
