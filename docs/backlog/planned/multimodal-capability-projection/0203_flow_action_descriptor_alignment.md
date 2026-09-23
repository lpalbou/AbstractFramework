# Planned: Flow action descriptor alignment

## Metadata
- Created: 2026-06-14
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0035, ADR-0036
- ADR impact: Known drift tracked by `0201_gateway_action_descriptor_contract.md`. Revisit ADR-0035 only if this work needs new route names rather than new tasks/actions.

## Context
AbstractFlow already has strong typed multimodal authoring surfaces. The goal is not to replace
them with a generic “generate anything” node, but to align their discovery/preflight/metadata with
the same action-descriptor truth consumed by other gateway-first clients.

## Current code reality
- `abstractflow/src/types/nodes.ts` defines explicit node types such as Generate Image, Generate Video, Generate Music, Generate Voice, and Transcribe Audio.
- `abstractflow/src/utils/nodeCapabilities.ts` maps nodes to capability names today.
- `abstractflow/src/hooks/useGatewayCapabilities.ts` and `abstractflow/src/utils/gatewayClient.ts` already consume capability contracts with task-specific metadata.
- `abstractflow/src/components/PropertiesPanel.tsx` already uses task-specific fields such as batch, LoRA adapters, formats, and artifact list behavior.

## Problem
Flow already has typed UX, but it still depends on duplicated capability/task mapping logic that can
drift from Gateway truth. That risk will grow as sound, `scene3d`, and future modalities land.

## What we want to do
Align Flow node palette, preflight, property panels, and route-aware affordances with the shared
Gateway action-descriptor contract while preserving the current typed authoring model.

## Why
- Typed Flow nodes are a product strength and should remain.
- Discovery and gating should come from one shared action truth rather than per-client mapping.
- Future modality growth should not require editing capability metadata in several TS layers.
- Flow should stay an authoring/view layer over Gateway/Runtime truth, not a parallel capability
  registry.

## Requirements
- Consume the shared action-descriptor contract from `0201`.
- Keep typed nodes and node palette entries; do not replace them with a generic mega-node in this
  item.
- Derive node availability, task-specific UI fields, and preflight messaging from action
  descriptors where possible.
- Preserve Flow-owned typed-node semantics such as required-input validation, artifact
  compatibility checks, and readable aliases/wrappers where the shared action contract is
  intentionally lower-level.
- Make action-descriptor adoption incremental so current media nodes and tests remain readable.
- Ensure sound/audio parity and future modality placeholders are reflected consistently in palette
  gating and property panels.

## Suggested implementation
1. Add a Flow-side adapter from action descriptors to node availability/task metadata.
2. Replace duplicated capability/task availability catalogs where the new contract is expressive
   enough, but keep node-local validation and typed UX projection in Flow.
3. Keep task-specific node UX and conditional property panels, but source option availability from
   action truth.
4. Add preflight and node-palette regression coverage for existing image/video/music flows and
   future-modality placeholders.

## Scope
- Flow discovery, node gating, property-panel metadata, preflight messaging, and replay-facing
  action projection for typed authoring surfaces.
- Flow docs/tests for capability-aware typed node authoring.

## Non-goals
- Do not replace typed media nodes with one generic node.
- Do not make Flow the source of truth for modality/task semantics.
- Do not invent new route names in TS without Gateway/Core alignment.
- Do not remove Flow-owned node validation or force property panels to become fully schema-rendered
  from Gateway descriptors.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0205_multimodal_action_coverage_and_future_modality_extension.md`
- `docs/backlog/planned/0179_llm_agent_model_input_artifacts.md`
- `docs/backlog/completed/0199_abstractflow_and_abstractassistant_vision_lora_and_batch_surface.md`

## Expected outcomes
- Flow remains typed and readable while sharing the same capability/action truth as the other
  gateway-first clients.
- New modality/task rollouts require less per-client metadata duplication.
- Preflight and node-palette messaging become more faithful to live Gateway truth.

## Validation
- Flow tests verify node availability and property fields derive from action metadata.
- Existing media-node authoring continues to work without a generic node regression.
- Sound/future-modality placeholder coverage does not diverge from Gateway discovery.

## Progress checklist
- [ ] Add a Flow adapter from action descriptors to node metadata.
- [ ] Replace duplicated capability/task mappings where safe.
- [ ] Update node palette/preflight/property-panel tests.
- [ ] Verify typed node UX remains smaller and clearer than a generic schema-driven node.

## Guidance for the implementing agent
Preserve the current typed UX. The point of this item is metadata and discovery unification, not UI
flattening. If the action-descriptor contract cannot express a current Flow affordance cleanly,
capture that gap in `0201` or `0205` instead of deleting the affordance or inventing a second
durable Flow-only semantic source.
