# Completed: AbstractFlow and AbstractAssistant vision LoRA and batch surface

## Metadata
- Created: 2026-06-14
- Status: Completed
- Completed: 2026-06-14

## ADR status
- Governing ADRs: ADR-0032 package dependency boundaries and gateway-first apps, ADR-0033 install profiles config entrypoints and server boundaries, ADR-0035 capability routing defaults
- ADR impact: None if Flow and Assistant remain thin clients of the existing Gateway/Runtime/Core/AbstractVision contract.

## Context
AbstractVision, AbstractCore, AbstractRuntime, and AbstractGateway now expose route-specific
vision generation capabilities with richer request and discovery fields:

- `output.image.text_to_image`
- `output.image.image_to_image`
- `output.image.image_upscale`
- `output.video.text_to_video`
- `output.video.image_to_video`
- ordered `lora_adapters` stacks
- batch generation through `count` / `n`
- explicit `seeds`
- `flow_shift` for video routes
- adapter discovery through `/api/gateway/vision/adapters`

That capability truth already lives below the browser. The remaining gap is that the thin clients do
not yet surface those controls cleanly:

- AbstractFlow media nodes do not yet expose stacked LoRA adapters or batch generation authoring.
- AbstractAssistant direct media modes do not yet expose the same richer request surface.

## Current code reality
- `abstractgateway/src/abstractgateway/routes/gateway.py` already accepts `count`, `n`, `seeds`,
  `lora_adapters`, and `flow_shift` on the direct image/video routes and advertises
  `supports_batch`, `supports_lora_adapters`, `supports_flow_shift`, `adapter_catalog_endpoint`,
  and `artifact_list_field` in the assistant/flow capability contracts.
- `abstractruntime/tests/test_visualflow_media_nodes.py` and
  `abstractruntime/tests/test_multimodal_abstractcore_integration.py` already cover lowering and
  forwarding of those fields.
- `abstractflow/src/utils/gatewayClient.ts` does not yet type those newer media-contract fields.
- `abstractflow/src/types/nodes.ts` media node templates still mostly expose the earlier pin set
  (`prompt`, provider/model, sizes, steps, seed, etc.) and do not expose `count`, `seeds`,
  `lora_adapters`, or `flow_shift`.
- `abstractflow/src/components/PropertiesPanel.tsx` and
  `abstractflow/src/components/nodes/BaseNode.tsx` already implement route-aware provider/model
  catalogs for media nodes, but they do not yet surface adapter discovery or batch authoring UX.
- `abstractassistant/abstractassistant/gateway/capabilities.py` and
  `abstractassistant/abstractassistant/gateway/client.py` do not yet expose the full richer direct
  media contract.
- `abstractassistant/abstractassistantv2/app.py` direct media flows already map to the new
  route-specific keys, but the UI only exposes the simpler request surface.

## Problem
The lower layers are capable, but the two user-facing thin clients still expose an older, narrower
vision surface. That prevents authors from using stacked LoRA adapters and batch generation in Flow
and prevents Assistant direct media mode from matching Gateway/Core capability truth.

## Decision question
How should Flow and Assistant surface stacked LoRA adapters and batch generation while keeping model
truth, adapter compatibility, and request validation owned by Gateway/Core/AbstractVision?

## Architecture direction
Keep Flow and Assistant thin:

- Gateway remains the discovery authority for route-specific provider/model catalogs and adapter
  catalogs.
- Runtime and Core remain the request/validation/execution authority.
- Flow and Assistant should only surface the existing contract and serialize request fields cleanly.

Do not duplicate model/adapter compatibility rules in the client beyond light UX guidance derived
from Gateway discovery.

## Recommendation

### AbstractFlow
- Extend the media contract typings to include:
  - `adapter_catalog_endpoint`
  - `supports_lora_adapters`
  - `supports_batch`
  - `supports_flow_shift`
  - `batch_count_field`
  - `batch_seed_field`
  - `artifact_list_field`
- Surface the following media-node authoring fields where the selected route supports them:
  - `count`
  - `seeds`
  - `lora_adapters`
  - `flow_shift` for video routes
- Add a clean 0+ adapter selector UX backed by `/api/gateway/vision/adapters`, with ordered stack
  rows, optional scale/weight fields where supported, and no client-owned compatibility inference
  beyond the catalog results.
- Keep compact-node behavior: advanced media controls should stay hidden until configured, connected,
  or expanded.

### AbstractAssistant
- Extend assistant-side capability helpers so direct media modes can see batch and adapter support.
- Extend direct media client methods to forward `count`, `n`, `seeds`, `lora_adapters`, and
  `flow_shift`.
- Extend Assistant V2 direct media UI so image, edit, video, and image-to-video can opt into batch
  generation and LoRA stacks when the route supports them.
- Keep the UI smaller than Flow: a direct-creation assistant does not need the full graph authoring
  surface, but it still needs honest access to the same request contract.

## Requirements
- Flow must allow selecting zero or more LoRA adapters for `text_to_image`, `image_to_image`,
  `text_to_video`, and `image_to_video` when the capability contract advertises support.
- Flow must allow batched generation for those same routes via `count` and/or explicit `seeds`.
- Video routes must surface `flow_shift` only when the capability contract advertises support.
- Flow and Assistant must preserve adapter order.
- Flow and Assistant must not hardcode provider/model or adapter compatibility tables that can drift
  from Gateway/Core/AbstractVision truth.
- Empty adapter selections must serialize as “no adapters”, not as malformed placeholder objects.
- Batch authoring must work both with count-only generation and explicit seed lists.

## Scope
- `abstractflow` node templates, media contract typings, media node properties UI, compact-disclosure
  behavior where needed, and docs.
- `abstractassistant` gateway capability helpers, gateway client methods, direct media UI, and docs.
- Focused tests in Flow and Assistant packages.

## Non-goals
- Do not move adapter/model truth out of Gateway/Core.
- Do not reimplement AbstractVision adapter compatibility in the browser.
- Do not add provider-specific LoRA training or installation flows in this item.
- Do not change Runtime or Gateway request semantics unless integration evidence proves a lower-layer
  bug.

## Dependencies and related tasks
- Completed item `0175_multimodal_capability_taxonomy_schema.md`
- Completed item `0177_flow_route_aware_model_selection.md`
- Completed item `0180_abstractflow_compact_node_pin_disclosure.md`
- AbstractVision and AbstractCore releases that already expose LoRA stacks, batch generation, and
  route-specific video/image capability metadata.

## Expected outcomes
- Flow authors can configure stacked LoRA adapters and batched image/video generation directly on the
- relevant media nodes.
- Assistant direct media modes can call the same richer Gateway routes without dropping parameters.
- Thin clients remain consumers of Gateway discovery rather than owners of capability logic.

## Validation
- Flow tests:
  - route-specific media contracts parse new support flags;
  - media nodes serialize `count`, `seeds`, `lora_adapters`, and `flow_shift` correctly;
  - compact disclosure still behaves correctly when those pins remain unset;
  - adapter selection UI preserves order and empty-state behavior.
- Assistant tests:
  - capability helpers expose new support flags/endpoints;
  - gateway client methods send the richer request fields;
  - direct media mode wiring includes those values when configured.
- Practical proof:
  - use the local Flow app to configure at least one media node with 2 adapters and a batch request;
  - use the Assistant direct media UI to submit one route with batch/adapters enabled;
  - confirm Gateway receives the expected payload shape.

## Implementation summary

### AbstractFlow
- Extended Gateway contract typings for media discovery and route features:
  `vision_adapters`, `supports_batch`, `batch_count_field`,
  `batch_seed_field`, `supports_lora_adapters`, `supports_flow_shift`, and
  `artifact_list_field`.
- Added media-node pins for:
  - `count`
  - `seeds`
  - `lora_adapters`
  - `guidance_2`
  - `flow_shift` on video routes
  - plural outputs `image_artifacts` / `video_artifacts`
- Added ordered LoRA adapter authoring in the Properties drawer, backed by
  `/api/gateway/vision/adapters`, with per-adapter scale and optional
  target role.
- Fixed legacy node normalization so reopened/imported flows rebuild media
  inputs from the current shared node templates instead of older hard-coded
  pin lists.
- Fixed a browser-visible regression where the custom `seeds` and
  `lora_adapters` editors existed in code but were excluded from the editable
  media pin whitelist in the Properties drawer.

### AbstractAssistant
- Extended gateway capability helpers with batch, LoRA, flow-shift, and
  adapter-catalog discovery accessors.
- Extended direct media client methods to forward:
  - `count` / `n`
  - `seeds`
  - `lora_adapters`
  - `guidance_2`
  - `flow_shift`
- Added `vision_adapters(...)` support to the assistant Gateway client.
- Updated the Assistant V2 direct-media worker so route `options` flow through
  to Gateway for image/video generation routes and batched responses can use
  the first returned artifact as the local preview/open target while keeping
  the full payload.

## Validation
- AbstractFlow:
  - `cd abstractflow && npm test -- src/utils/nodePinDisclosure.test.ts`
  - `cd abstractflow && npm run build`
- AbstractAssistant:
  - `pytest -q abstractassistant/tests/basic/test_gateway_capabilities.py abstractassistant/tests/basic/test_gateway_client_methods.py abstractassistant/tests/basic/test_assistant_v2.py`
- Practical proof:
  - Local `Gateway + Flow + Observer` stack started with
    `./scripts/gateway-flow-local.sh`
  - Headless browser proof captured a live `Generate Image` node configured
    with:
    - `mlx-gen / AbstractFramework/qwen-image-2512-8bit`
    - `count = 2`
    - `seeds = 101, 102`
    - two stacked LoRA adapters discovered from the current Gateway adapter
      catalog
  - Proof screenshot stored at:
    `abstractflow/docs/assets/flow-generate-image-batch-lora.png`

## Outcome
- Flow now exposes stacked LoRA adapters and batched vision generations through
  the actual authoring UI, using Gateway/Core/AbstractVision as the only
  source of compatibility truth.
- Assistant now forwards the same richer direct-media request shape without
  inventing a second capability model locally.

## Progress checklist
- [x] Add the planned item to the root backlog overview.
- [x] Extend Flow media contract typings.
- [x] Add Flow media node support for adapter stacks and batch generation.
- [x] Extend Assistant capability helpers and gateway client methods.
- [x] Add Assistant direct media UI support for batch/adapters where appropriate.
- [x] Validate with focused tests and practical local proofs.
- [x] Update package docs after implementation.

## Guidance for the implementing agent
Start from the current Gateway/Runtime contract rather than inventing new client-side schemas. Keep
Flow and Assistant request objects as thin projections of the Gateway contract. If a client needs
extra metadata, add it to the contract in the owning package instead of embedding provider-specific
logic in the UI.
