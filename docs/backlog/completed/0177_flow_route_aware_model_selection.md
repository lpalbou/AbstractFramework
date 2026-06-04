# Planned: Flow route-aware provider and model selection

## Metadata
- Created: 2026-06-03
- Status: Completed
- Completed: 2026-06-03

## ADR status
- Governing ADRs: ADR-0035 capability routing defaults
- ADR impact: None

## Context
AbstractCore and Gateway now expose route-aware model discovery through `capability_route`
filters such as `output.text` and `input.image,output.text`. Gateway Console already uses
those route filters for capability defaults. AbstractFlow still asks for generic provider
model lists in several text-model selectors, so authoring can show models that cannot satisfy
the node's intended route.

## Current code reality
- `abstractgateway.routes.gateway.discovery_provider_models` accepts `capability_route` and
  forwards it through the Runtime discovery facade.
- `abstractruntime.integrations.abstractcore.discovery_queries.local_list_provider_models`
  supports route filters.
- `abstractflow/src/hooks/useProviders.ts::useModels` ignores route filters and calls the
  Gateway provider-model endpoint with only `provider_name`.
- `abstractflow/src/components/ProviderModelsPanel.tsx`, `BaseNode.tsx`,
  `PropertiesPanel.tsx`, `RunFlowModal.tsx`, and `ModelResidencyPanel.tsx` consume `useModels`
  without route requirements.
- `abstractruntime.visualflow_compiler.visual.executor._create_provider_models_handler`
  executes the Provider Models node by calling Core's local provider registry without a
  route filter.

## Problem
Flow users cannot reliably browse or save the provider/model set for a required model route.
The UI and runtime can drift from Gateway Console defaults, and a Provider Models node cannot
express "models that support text output" or "models that support image input to text output".

## What we want to do
Make Flow model selectors route-aware while keeping Gateway/Core as the source of truth. The
editor should pass `capability_route` to Gateway discovery, and the Provider Models node should
persist and execute the same route filter.

## Why
Provider/model search and setup need to be capability-first. Flow should not own the model
capability registry or duplicate Gateway Console logic; it should ask Gateway for the current
route-specific catalog and persist only the user's selection intent.

## Requirements
- `useModels` accepts an optional route filter and includes it in its query key and Gateway URL.
- Text LLM selectors default to `output.text`.
- The Provider Models node can choose a route filter and resets stale model selections when the
  route changes.
- Runtime execution of Provider Models applies the persisted or pin-provided route filter.
- Invalid route filters fail closed to an empty result rather than returning an unrelated catalog.

## Suggested implementation
Add a small Flow utility for capability route option labels and normalization. Thread the route
filter through existing selectors, add `capabilityRoute` to `providerModelsConfig`, and use
`abstractcore.providers.model_capabilities.filter_models_by_capabilities` in the Runtime
Provider Models node handler.

## Scope
- AbstractFlow editor hooks, node UI, node type metadata, and run-modal text model selectors.
- AbstractRuntime Provider Models node execution.
- Focused tests for route-filtered Flow query construction and Runtime filtering.

## Non-goals
- Do not move model capability data into AbstractFlow.
- Do not replace existing media-specific discovery endpoints for image/video/voice/music
  generation.
- Do not implement model download or residency orchestration in this item.

## Dependencies and related tasks
- ADR-0035 capability routing defaults.
- Completed backlog item 0175 multimodal capability taxonomy and schema.
- Proposed backlog item 0176 multimodal model acquisition guidance.

## Expected outcomes
- Flow text model dropdowns and Provider Models node catalogs query Gateway with route filters.
- VisualFlow execution can produce a route-filtered models array without the editor present.
- Gateway remains the browser-facing source of truth for provider/model discovery.

## Validation
- Flow TypeScript build succeeds.
- Runtime unit tests prove Provider Models route filtering and invalid-filter fail-closed behavior.
- Static or unit proof shows Flow query URLs include `capability_route`.

## Progress checklist
- [x] Add route-aware Flow model discovery utilities.
- [x] Surface route selection in the Provider Models node.
- [x] Apply route filters in Runtime Provider Models execution.
- [x] Add focused tests.
- [x] Update user-facing docs and LLM indexes.

## Architect review
- Alternative A, Flow owns/parses Core's `model_capabilities.json`: rejected because it violates
  the thin-client boundary and creates a stale registry copy in the browser.
- Alternative B, Gateway adds separate model endpoints per route and modality: rejected as noisy
  API surface because Gateway already has a precise `capability_route` filter.
- Alternative C, Flow passes route filters to existing Gateway discovery and Runtime uses Core
  helpers for node execution: selected because it is the smallest reversible change and preserves
  Core/Gateway ownership.

## Review notes
- Blocking risk: generic model dropdowns can currently show incompatible models.
- Blocking risk: Provider Models execution currently ignores the same route intent the UI needs.
- Required evidence: tests must cover both UI query construction and runtime filtering.

## Completion report

- Date: 2026-06-03
- Summary: Flow model selectors now pass route-aware discovery filters to Gateway, and the
  Provider Models node persists and executes a `capability_route` filter through Runtime/Core
  helpers.
- Files and symbols touched:
  - `abstractflow/src/utils/capabilityRoutes.ts` for shared route options and query
    normalization.
  - `abstractflow/src/hooks/useProviders.ts::useModels` to include `capability_route` in the
    query key and Gateway URL.
  - `abstractflow/src/components/ProviderModelsPanel.tsx`, `BaseNode.tsx`,
    `PropertiesPanel.tsx`, `RunFlowModal.tsx`, and `ModelResidencyPanel.tsx` for route-aware
    selectors.
  - `abstractflow/src/types/flow.ts`, `src/types/nodes.ts`, and `src/hooks/useFlow.ts` for
    persisted Provider Models route config and pin migration.
  - `abstractruntime.visualflow_compiler.visual.executor._create_provider_models_handler` to
    filter models with Core's `filter_models_by_capabilities`.
- Behavior changes:
  - Text model selectors default to `output.text`.
  - Provider Models can choose routes such as `input.image,output.text`.
  - Invalid route filters fail closed with an empty model list and an explicit error.
- Validation:
  - `PYTHONPATH=abstractruntime/src:abstractcore pytest -q abstractruntime/tests/test_abstractcore_discovery_facade.py abstractruntime/tests/test_visualflow_capability_routes_and_thinking.py abstractruntime/tests/test_visualflow_memory_source_pins.py`
  - `npm run build` in `abstractflow`.
- Documentation updates: AbstractFlow README/LLM index and root configuration/LLM docs document
  route-aware discovery.
- Residual risks: Provider support remains Core-owned; Flow intentionally does not validate model
  capability metadata locally.
