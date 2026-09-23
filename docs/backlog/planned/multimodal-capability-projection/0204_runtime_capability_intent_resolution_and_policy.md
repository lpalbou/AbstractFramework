# Planned: Runtime capability intent resolution and policy

## Metadata
- Created: 2026-06-14
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0035, ADR-0036
- ADR impact: May revise the new ADR created by `0201_gateway_action_descriptor_contract.md` if Runtime needs additional action-policy vocabulary or canonical intent fields.

## Context
The long-term durable kernel is already generic: Runtime executes multimodal work through canonical
`LLM_CALL` child runs with artifact/media inputs plus `output={modality, task}` lowering. The
missing piece is a clean Runtime-side resolution/policy layer that can receive typed actions from
Gateway, normalize them into a lower-level `request + output + source bindings + execution hints`
shape, and then lower that into one execution contract with explicit policy classes and audit
semantics.

## Current code reality
- `abstractruntime/src/abstractruntime/integrations/abstractcore/run_facade.py` already exposes typed helper methods that lower to canonical `execute_llm_call(...)`.
- `abstractruntime/src/abstractruntime/core/models.py` already has `EffectType.LLM_CALL` as the durable primitive.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/tool_executor.py` still centers tool approval on tool-call policy, not on a first-class action/generation policy class.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py` already owns artifact normalization, generated-media lineage, and replay-friendly output handling.
- Runtime already preserves generated-media/source lineage and replay-friendly artifact metadata;
  this item should not re-solve artifact provenance.
- Runtime already forwards scoped capability-default payloads into Core clients and decorates some
  generated-media output specs from those defaults, but it does not yet materialize one canonical
  call-scoped resolved route object for the whole request.
- Endpoint-profile resolution can currently derive the call-global provider from the first output
  provider/profile hint, which is exactly the kind of topology-dependent implicit rewrite this item
  needs to remove.
- `history_bundle` already exports waits, artifacts, timeline, and workflow snapshot refs; this
  item only needs to add resolved-action metadata that replay can reference.

## Problem
The missing Runtime contract is an explicit resolved-action record per call: normalized
request/output summary, resolved-route summary, override disposition, policy class, and
workflow/delegation summary. Without that record, clients must infer action semantics from prompts,
output specs, or topology-specific behavior.

## What we want to do
Define the Runtime-side canonical intent and action-resolution path so Gateway-projected actions map
cleanly to one durable execution contract with explicit policy and audit semantics.

## Why
- The generic runtime kernel is a strength and should stay the only execution substrate.
- Approval and policy should not collapse accidentally just because several capabilities reduce to
  the same `LLM_CALL` effect.
- Future modalities need a stable internal landing zone even if external typed actions evolve.

## Requirements
- Define a canonical internal intent/action-resolution shape that maps action descriptors to
  normalized `request`, normalized `output`, media/source refs, and execution hints before the
  current `LLM_CALL` lowering.
- Materialize one resolved route object per call, not ambient config reads plus partial output-spec
  mutation. That resolved route should include distinct text/input/output route fields, provenance,
  override decisions, and policy ceilings.
  Compatibility fields should normalize into one small override plane that can target specific
  route keys without mutating the rest of the inherited defaults; a stable public API for that
  plane remains deferred until the shared resolver and policy ceilings are proven.
- Preserve `LLM_CALL` as the durable primitive; do not add a second media execution effect type
  without strong evidence.
- Introduce explicit policy classes or equivalent semantics so generation actions do not inherit
  side-effect/tool approval rules by accident.
- Use one shared resolved-route path across direct Core, local Runtime, remote Runtime, and server
  execution so topology does not silently change provider/model/base URL behavior.
- Support per-modality one-off overrides through that resolved route object so a caller can inherit
  defaults broadly while overriding only the relevant route for this action.
- Treat routes as executable only when they resolve atomically for the capability in question.
  Partial defaults may exist as configuration state, but they must not dispatch silently.
- Keep text/input routing separate from output routing. An output profile or output provider must
  not rewrite the call-global text route implicitly.
- Apply the same override policy everywhere. Provider/model/base URL/profile overrides are either
  explicitly allowed and recorded or explicitly denied with a clear failure.
- Record route-merge provenance explicitly so replay and diagnostics can tell which route fields
  came from defaults, which from compatibility aliases, and which from explicit per-call
  overrides.
- Distinguish clearly between requested override, effective resolved route, and override
  disposition in the durable record so operator and replay surfaces do not have to infer that
  difference from provenance alone.
- Reuse existing artifact lineage and replay fields. Add only the missing resolved-action metadata:
  `action_id`, capability family, normalized task, policy class, normalized request summary,
  normalized output summary, resolved-route summary, requested override summary, override
  disposition summary, and workflow/delegation summary.
- Emit a bounded resolved-action record that can be linked from replay/history surfaces, including
  descriptor identity plus any normalized source-role or workflow-resolution facts needed for
  cross-client explanation.
- Emit a bounded parent/child workflow edge summary when execution proceeds through a
  workflow/composite or super-agent layer, so replay can explain direct actions versus delegated
  child actions without recovering that meaning from prompt prose.
- Emit a replay-safe resolved-route snapshot containing at least route key, route source,
  provider/model identity, redacted base URL/profile identity, topology, and policy decision.
- Persist enough action-resolution metadata in the ledger/history path that another lightweight app
  can replay what capability was invoked without re-inferencing intent from prompt prose alone.
- Keep provider/model selection routed by Gateway/Core defaults unless policy explicitly exposes
  overrides.
- Keep any future public structured override surface out of this item. Runtime should first own the
  internal resolved-route object and its audit/provenance semantics before any public route object
  is promoted.

## Suggested implementation
1. Add a Runtime-side action-resolution helper that converts typed actions into canonical
   `request/output` intent, then into current `LLM_CALL` params.
   That helper should also construct the call-scoped resolved route object that Core and server
   execution consume.
   Compatibility overrides such as output-spec `provider/model` selectors should normalize into
   that object instead of bypassing it.
2. Add action-level policy metadata so approvals/quotas can differentiate low-risk generation from
   mutating or outbound side effects.
3. Make route resolution and override-denial semantics shared across local Runtime, remote Runtime,
   direct Core, and server entrypoints.
   Route overrides should normalize once into that path instead of surviving as ad hoc provider,
   model, or base URL fields on different payload branches.
4. Keep typed helper methods as convenience shims over the canonical path where they still add
   value.
5. Record replay-safe resolved-action summaries in ledger/history fields linked to existing
   run/step/artifact anchors; do not introduce a parallel execution store.
6. Add replay/audit coverage to ensure resolved actions remain visible across history bundles and
   cross-client UI reconstruction.

## Scope
- Runtime action normalization, policy class handling, and audit/provenance semantics.
- Cross-package tests proving action-to-`LLM_CALL` parity.

## Non-goals
- Do not make the generic internal intent the only model-facing primitive in this item.
- Do not move published-workflow composition into prompt-only orchestration.
- Do not hide policy decisions inside client discovery alone.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0202_gateway_replayable_session_and_action_envelope.md`
- `0203_flow_action_descriptor_alignment.md`
- `0207_cross_client_replayable_action_handoff.md`
- `../../proposed/0211_public_generate_route_override_surface.md`
- `docs/backlog/planned/0147_gateway_per_principal_config_secrets_defaults.md`
- `docs/backlog/planned/039_tool_argument_type_coercion.md`

## Expected outcomes
- Typed actions resolve to one canonical Runtime execution path with explicit audit and policy
  semantics, without turning `output={modality, task}` into the only user-facing vocabulary.
- Per-call modality overrides stop being topology-specific tricks and become one explicit resolved
  route with provenance and replay truth.
- Generation policy can be tuned independently from host-side tool approvals.
- Cross-client replay can explain which action actually ran, which route/topology resolved, and not
  only which artifact emerged.
- Durable agent bundles and future super-agent workflows can consume Runtime route/action truth as
  read-only execution facts instead of owning their own route-merging logic.
- Future modality additions do not require new Runtime execution machinery by default.

## Validation
- Runtime tests verify several typed actions normalize to equivalent canonical `LLM_CALL` payloads.
- Policy tests verify generation/action policy classes remain distinct from host-side tool
  approvals.
- Replay/history tests retain enough action-level semantics for debugging and observability.

## Implementation note - 2026-06-15

The first Runtime semantics pass is now landed:

- Runtime derives `_runtime_resolved_action` from Core `_resolved_generate_route` metadata for
  Core-backed `LLM_CALL` results.
- `history_bundle` now exports `resolved_actions` for replay/debug consumers.
- local Runtime Core media generation now consumes the Core-owned resolved-route helper instead of
  a separate Runtime-only output-spec defaulting path.

Action-level policy classes and the broader Gateway-to-Runtime action resolver are still pending.

## Progress checklist
- [x] Define canonical Runtime action-resolution shape.
- [x] Define the route-merge provenance and override-denial record.
- [ ] Add action-level policy metadata and tests.
- [x] Prove typed-action parity with existing image/video/music/voice execution helpers.
- [x] Verify replay/history/audit fields remain explicit enough for debugging.

## Guidance for the implementing agent
Keep the internal substrate small. The main failure mode is inventing a second full semantic layer
inside Runtime instead of a thin resolver over the lower-level Core `request/output` contract and
the existing `LLM_CALL` path. Normalize once, then rely on existing artifact/progress/lineage
machinery. Also fail closed: partial defaults, topology-specific reinterpretation, and unguarded
override paths are not acceptable silent behavior for this contract.
Favor a durable `resolved_route` record and one shared compatibility-mapping path over ambient
config lookups and best-effort dict mutation. Any future public override surface belongs in the
separate proposed follow-up, not in this foundational item.
