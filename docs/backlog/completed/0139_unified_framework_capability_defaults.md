# Completed: Unified Framework Capability Defaults

## Metadata
- Created: 2026-05-24
- Status: Completed
- Completed: 2026-05-24

## ADR status
- Governing ADRs: ADR-0035
- ADR impact: Revises ADR-0035 to cover non-generative routing defaults, Gateway as framework control plane, and the future `generate(request, output)` shape.

## Context

AbstractFramework is moving toward one clean routing configuration model for Core, Runtime,
Gateway, Flow, and capability plugins. The current user-facing problem started in AbstractFlow's
model residency modal: configured defaults were mixed with provider-loaded residency rows, and a
browser-native unload confirmation leaked through the UI.

The first implementation separated loaded models from defaults and introduced
`input.*` / `output.*` capability defaults in AbstractCore. A second design pass is needed because:

- legacy global text defaults should not define the new abstraction;
- embeddings also require provider/model/base URL defaults;
- a future reranker manager will need the same routing shape;
- AbstractCore's end goal is a single `generate(request, provider, model, output)` entrypoint, then
  `generate(request, output)` once defaults are complete;
- Gateway should be a control plane for the framework and execution host, not a second persistence
  owner for model defaults.

## Current code reality

Inspected and changed across this pass:

- `abstractcore/abstractcore/config/capability_defaults.py` defines the shared route schema.
- `abstractcore/abstractcore/config/manager.py` persists `capability_defaults` and now lists
  explicit route records instead of silently mapping older defaults into configured rows.
- `abstractcore/abstractcore/server/app.py` exposes `/v1/config/capability-defaults`.
- `abstractgateway/src/abstractgateway/capability_defaults.py` reads/writes the local Core config
  when embedded and proxies to an AbstractCore server when split.
- `abstractgateway/src/abstractgateway/provider_defaults.py` resolves text provider/model for
  Gateway LLM helper paths, with execution-host route defaults ahead of transitional Gateway env
  fallback.
- `abstractgateway/src/abstractgateway/embeddings_config.py` now resolves the execution-host
  `embedding.text` route and no longer persists `gateway_embeddings.json`.
- `abstractflow/web/frontend/src/components/ModelResidencyPanel.tsx` separates `Loaded models` and
  `Defaults` and uses themed dialogs.
- `abstractflow/web/frontend/src/components/nodes/BaseNode.tsx` and
  `abstractflow/web/frontend/src/components/PropertiesPanel.tsx` author media residency steps from
  modality-specific provider/model fields only; voice/image/music/STT warm-up no longer inherits a
  generic text model.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py` delegates local
  media residency for `image_generation`, `tts`, `stt`, and `music_generation` to AbstractCore
  capability plugin residency hooks instead of hard-coding media tasks as remote-server-only.
- `docs/adr/0035-capability-routing-defaults.md` records Core-owned persistence and Gateway
  control-plane access.

Resolved design issues in this pass:

- Capability defaults now cover `input.*`, `output.*`, `embedding.*`, and future `rerank.*`
  routes.
- The route payload uses `kind` terminology; `direction` is only tolerated as an older-reader
  compatibility alias where already needed.
- The API and UI no longer mark inherited legacy defaults as configured capability rows.
- `AbstractCoreConfig.embeddings` has a durable base URL field, synchronized into `embedding.text`
  when embeddings are configured through the Core config manager.
- Gateway text helper startup now resolves request values, workflow defaults, and execution-host
  route defaults without a separate Gateway provider/model env fallback.
- The Gateway embedding path is no longer a Gateway-owned default; embedded mode uses local Core, split
  mode delegates to remote Core `/v1/embeddings`.
- AbstractFlow TTS/STT provider selectors prefetch provider-only catalogs and show an explicit
  loading state instead of flashing "No results" while the catalog request is in flight.
- Runtime local media warm-up failures now remain supported residency operations and fail on actual
  plugin load truth (`loaded != true`), preserving actionable plugin/provider errors without
  mislabeling the operation unsupported.
- Embedding default selectors use a dedicated `embedding.text` catalog route instead of generic LLM
  provider model discovery.
- Non-text model residency no longer inherits the default text model when the media model is empty.
  Provider-only local TTS warmup (for example Omnivoice) stays provider-scoped and can report true
  resident state.
- Gateway provider/model catalog filtering now removes stale model maps and catalog items from
  other providers, preventing old text/TTS model choices from leaking into modality-specific
  selectors.
- Existing saved `model_residency` nodes can still contain an explicit stale media model such as
  `gemma-3-1b-it`; the runtime now avoids inventing this value, and newly authored media residency
  steps use modality-specific fields only, but explicit saved node config remains user-authored
  state.
- `embedding.image` is present in the shared route matrix as a reserved capability default, but
  AbstractCore's implemented `EmbeddingManager` and `/v1/embeddings` endpoint remain text-embedding
  surfaces today. Image embedding execution needs a future plugin/manager implementation.

## Problem

The framework needs a small, explicit routing-default abstraction that can serve text/image/voice
generation today and embeddings/rerank/default Core generation later without becoming a pile of
legacy aliases.

## What we want to do

Make capability defaults operation-based:

- `input.<modality>`: understanding/enrichment of request media/context.
- `output.<modality>`: generation target defaults.
- `embedding.<modality>`: vectorization defaults for retrieval/indexing.
- `rerank.<modality>`: ranking defaults for a future reranker manager.

Keep the persisted route payload small and shared:

- provider
- model
- base URL
- provider/plugin options

Use Core as the persistence owner and Gateway as the control plane.

## Requirements

- Avoid adding a Gateway-owned defaults file.
- Do not hide old global text/model settings behind new capability rows.
- Add embeddings to the shared capability-default matrix, including base URL.
- Leave an explicit design slot for reranker defaults without implementing a reranker manager now.
- Keep Flow's model modal clear: loaded residency is separate from routing defaults.
- Keep split deployments honest: Gateway must proxy to the execution Core/Runtime host or report
  unavailable/read-only state.

## Suggested implementation

- Rename the conceptual axis from `direction` to `kind` / route kind in the shared schema.
- Keep route keys compact: `output.text`, `embedding.text`, `rerank.text`.
- Remove legacy fallback mapping from the new capability-default list.
- Have `abstractcore --set-global-default` populate `input.text` and `output.text` as the framework
  text default while retaining older fields only where existing lower-level code still reads them.
- Add `embedding.text` and `embedding.image` specs; add `rerank.text` as a future-ready row.
- Teach the embedding manager to prefer `embedding.text` defaults and carry `base_url` into
  provider kwargs.
- Update ADR-0035 and tests with the new vocabulary.

## Design review result

Two independent design reviews converged on the same boundary:

- Use `kind.modality`, not `direction.modality`, because embeddings and rerank are operations rather
  than input/output directions.
- Keep Core as the schema/persistence owner.
- Treat Gateway as the control plane for the execution host, including split deployments where the
  Core host may be remote.
- Remove Gateway-owned embedding defaults; `embedding.text` is the single configured text embedding
  route.
- Treat provider/model as an atomic pair for text helper resolution. Gateway no longer composes
  partial request, flow, route, or environment fragments into a mixed provider/model target.
- Gate AbstractFlow's Defaults tab by `common.configuration.capability_defaults`, not by model
  residency availability. Defaults are configuration; provider-loaded truth belongs only to the
  Loaded models tab.
- Defaults editing must use the same catalog-backed AbstractFlow selectors as node authoring:
  provider choices are scoped to the route capability where catalogs exist, model choices refresh
  from the selected provider, and freeform/custom entry remains only as a fallback.
- Keep `rerank.text` as a reserved route so the future reranker manager has a clean landing point,
  without implementing that manager now.
- Model residency authoring is not allowed to cross modality boundaries. A voice, music, image, or
  STT load step may use the route's own default or a selected model for that modality, but must not
  borrow the generic text model.
- Image search should eventually use a hybrid retrieval design: direct multimodal/image embeddings
  for visual semantics plus caption/OCR/object text embeddings for explainable lexical recall.
  Today AbstractCore supports the caption/OCR/text-embedding side, not first-class image vectors.

## Non-goals

- Implement the future reranker manager.
- Implement the final `generate(request, output)` API.
- Migrate every existing historical runtime record or old saved flow.
- Remove all old config fields in one pass if current runtime code still reads them.
- Align every Core output selector name with the final capability-route modality vocabulary.

## Validation

- `PYTHONPATH=abstractcore pytest -q abstractcore/tests/config/test_capability_defaults_config.py abstractcore/tests/config/test_capability_defaults_server.py`
  passed: 7 tests.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src pytest -q abstractgateway/tests/test_gateway_provider_defaults.py abstractgateway/tests/test_gateway_embeddings_endpoint.py abstractgateway/tests/test_gateway_config_cli.py`
  passed: 17 tests.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src pytest -q abstractgateway/tests/test_gateway_http_api.py abstractgateway/tests/test_backlog_advisor_and_maintain_readonly_scope.py abstractgateway/tests/test_backlog_write_endpoints_basic.py abstractgateway/tests/test_gateway_discovery_endpoints.py`
  passed: 14 tests.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src pytest -q abstractgateway/tests/test_gateway_bundle_llm_tools_agents.py abstractgateway/tests/test_gateway_prompt_cache_endpoints.py`
  passed: 17 tests.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src pytest -q abstractgateway/tests/test_gateway_e2e_split_api_runner.py abstractgateway/tests/test_gateway_split_api_runner.py`
  passed: 1 test, 1 optional E2E skipped because `ABSTRACT_E2E_GATEWAY_SPLIT` was not set.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src pytest -q abstractgateway/tests/test_gateway_model_residency_endpoints.py`
  passed: 4 tests.
- `PYTHONPATH=abstractflow:abstractruntime/src:abstractcore pytest -q abstractflow/tests/test_frontend_gateway_contract.py`
  passed: 16 tests. Re-run after the Defaults editor selector correction.
- `PYTHONPATH=abstractruntime/src:abstractcore pytest -q abstractruntime/tests/test_model_residency_control_plane.py`
  passed: 24 tests. Re-run after connecting local media residency to AbstractCore capability plugin
  hooks and adding truthful plugin-load failure coverage.
- `PYTHONPATH=abstractflow:abstractruntime/src:abstractcore pytest -q abstractflow/tests/test_frontend_gateway_contract.py`
  passed: 16 tests. Re-run after fixing the TTS/STT provider selector prefetch path and guarding
  against generic text-model fallback in media residency authoring.
- `PYTHONPATH=abstractgateway/src:abstractruntime/src:abstractcore pytest -q abstractgateway/tests/test_gateway_capability_catalog_proxy.py`
  passed: 14 tests. Re-run after adding the fast `providers_only=true` TTS provider catalog path.
- `npm run build` passed in `abstractflow/web/frontend`. Re-run after the Defaults editor selector
  correction and again after the selector/residency authoring fix; latest served Flow assets include
  `assets/index-CG75q1Fj.js` and `assets/index-BdPD4qar.css`.
- `npm run lint` passed in `abstractflow/web/frontend`. Re-run after the Defaults editor selector
  correction and again after the selector/residency authoring fix.
- Live Flow proxy checks confirmed catalog data is available for default-route selectors:
  `/api/gateway/discovery/providers`, `/api/gateway/discovery/providers/lmstudio/models`,
  `/api/gateway/vision/provider_models?task=text_to_image&providers_only=true`,
  `/api/gateway/audio/speech/models`, `/api/gateway/audio/transcriptions/models`, and
  `/api/gateway/audio/music/models?task=text_to_music&provider=stable-audio`.
- Live Flow proxy check after the fast-path fix confirmed
  `/api/gateway/audio/speech/models?providers_only=true` returns a provider catalog with no models
  in ~14.6 ms cold after restart and ~2 ms warm, instead of blocking on full TTS model discovery.
- Live Flow proxy check confirmed `/api/gateway/models/load` for `task=tts` now reports
  `supported=true` and an actionable plugin/provider load failure when the selected provider cannot
  be resident, rather than returning `model_residency_unsupported`.
- `abstractcore --set-global-default lmstudio:qwen/qwen3.6-35b-a3b` persisted
  `input.text` and `output.text` as `lmstudio:qwen/qwen3.6-35b-a3b`.
- `PYTHONPATH=abstractruntime/src:abstractcore pytest -q abstractruntime/tests/test_model_residency_control_plane.py abstractruntime/tests/test_abstractcore_discovery_facade.py`
  passed: 43 tests. Re-run after adding the embedding discovery facade and fixing media residency
  default-model inheritance.
- `PYTHONPATH=abstractgateway/src:abstractruntime/src:abstractcore pytest -q abstractgateway/tests/test_gateway_capability_catalog_proxy.py abstractgateway/tests/test_capabilities_endpoint_contract.py`
  passed: 23 tests. Re-run after adding `/api/gateway/embeddings/models` and provider-scoped catalog
  filtering.
- `PYTHONPATH=abstractflow:abstractruntime/src:abstractcore pytest -q abstractflow/tests/test_frontend_gateway_contract.py`
  passed: 16 tests after wiring the Defaults editor to the embedding catalog and fast TTS provider
  catalog.
- `npm run lint` and `npm run build` passed in `abstractflow/web/frontend`; latest built asset:
  `assets/index-C22qgepx.js`.
- Live Flow proxy check confirmed `/api/gateway/audio/speech/models?provider=omnivoice` returns no
  models/items instead of leaking other providers' TTS models.
- Live Flow proxy check confirmed provider-only Omnivoice warmup via `/api/gateway/models/load`
  returns `ok=true`, `state=resident`, `model=null`, and appears in
  `/api/gateway/models/loaded?task=tts`.
- Live Flow proxy check confirmed `/api/gateway/embeddings/models?provider=lmstudio` returns
  embedding model ids only, including `text-embedding-nomic-embed-text-v1.5` and
  `text-embedding-qwen3-embedding-0.6b`, not general chat LLMs.
- Live Flow proxy checks confirmed fast catalog responses after the latest fixes:
  `/api/gateway/audio/speech/models?providers_only=true` in ~25 ms,
  `/api/gateway/audio/speech/models?provider=omnivoice` in ~25 ms, and
  `/api/gateway/embeddings/models?provider=lmstudio` in ~20 ms on the running local stack.
- Live Flow proxy check confirmed an explicit stale TTS model
  `{"task":"tts","provider":"omnivoice","model":"gemma-3-1b-it"}` fails as a real provider load
  error, while the provider-only request `model=""` succeeds and reports Omnivoice resident.
- Restarted the local stack through `scripts/gateway-flow-local.sh` only, running detached in
  `screen` session `abstractframework-local`:
  Gateway `http://127.0.0.1:8080`, Flow `http://127.0.0.1:3000`.
- Verified Gateway and Flow proxy `/api/gateway/config/capability-defaults` report `kind` rows for
  input/output/embedding/rerank and qwen3.6 for `input.text`/`output.text`.
- Browser plugin verification was attempted, but the required Node REPL browser tool was not
  exposed in this session; frontend verification used the contract test plus build/lint gates.

## Progress checklist
- [x] Create traceable backlog item for the design pass.
- [x] Compare two independent design reviews.
- [x] Update route schema for route kinds, embeddings, and rerank.
- [x] Remove inherited legacy defaults from the new capability-default API surface.
- [x] Update Core/Gateway/Flow code and ADR-0035.
- [x] Fix media residency authoring so provider/model selection stays modality-scoped.
- [x] Route local media residency through AbstractCore capability plugin residency hooks.
- [x] Add embedding-specific discovery for Defaults selectors and prevent media residency from
      inheriting text defaults.
- [x] Run focused verification and restart local stack.
