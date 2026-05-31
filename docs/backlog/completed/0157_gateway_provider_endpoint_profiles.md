# Completed: Gateway provider endpoint profiles

## Metadata
- Created: 2026-05-31
- Status: Completed
- Completed: 2026-05-31

## ADR status
- Governing ADRs: ADR-0033, ADR-0035
- ADR impact: May revise existing ADR after the wider provider-secret vault and workflow export/import rules settle.

## Context
Gateway Console could edit capability defaults for the current principal:
route, provider, model, and optional base URL. That was not enough to configure
an OpenAI-compatible endpoint with the API key needed by hosted, multi-user
Gateway deployments. Users also needed more than one endpoint; defaults and
custom endpoints are separate concerns.

## Problem
Users need to configure OpenAI-compatible and other custom remote endpoints once
in Gateway, then select and reuse them from Flow nodes without hardcoding raw
secrets in workflow JSON, browser storage, run ledgers, or exported bundles.

## Implemented design
Gateway now owns provider endpoint profiles:

- `id`: stable local identifier.
- `display_name`: user-facing label.
- `description`: operator/user explanation of what the endpoint is for.
- `provider_family`: canonical provider implementation such as
  `openai-compatible`, `openai`, `openrouter`, or `anthropic`.
- `base_url`: optional endpoint URL; blank means provider default.
- `api_key`: stored server-side and returned only as non-secret status and
  fingerprint.
- `scope`: `user` or `gateway`; gateway scope requires admin.
- `capabilities`: text, embeddings, image, video, voice, music, or other route
  families.
- `allowed_models`: optional static allowlist; otherwise Gateway asks the
  underlying discovery facade.

Enabled profiles surface through provider discovery as virtual providers such
as `endpoint:office-vllm`. Runtime resolves that virtual id through a
host-provided resolver into the real provider family, base URL, and API key
only for the transient provider call.

## Scope
- AbstractGateway profile store, config API, discovery integration, console UI,
  bundle-host resolver, tests, and docs.
- AbstractRuntime generic optional resolver hook and local multi-client support
  for per-call provider construction with profile base URL/key.

## Non-goals
- No browser-stored provider keys.
- No raw key in workflow JSON, exported bundles, discovery responses, or Runtime
  observability.
- No new provider class per endpoint alias.
- No full workflow export/import endpoint-requirement mapper yet.
- No encrypted-at-rest vault yet; the initial local profile JSON is permissioned
  with `0600`, and the broader vault/audit policy remains under `0147`.

## Completion report

Date: 2026-05-31

Summary:
- Added `ProviderEndpointProfileStore` under AbstractGateway with public
  non-secret profile views and private runtime resolution.
- Added `/api/gateway/config/provider-endpoint-profiles` CRUD routes.
- Added `/api/gateway/config/provider-endpoint-profiles/discover-models` so the
  console can preview models from a draft or saved endpoint profile without
  exposing the raw key.
- Added profile-backed provider discovery and model discovery. Profiles with
  an allowlist return that model list directly; other profiles discover through
  the configured provider family, base URL, and profile key.
- Added Gateway Console controls for profile id, name, description, provider
  family, scope, base URL, API key, capabilities, and a discovered model picker
  where selected models become the optional allowlist.
- Added virtual provider labels to console provider selectors so profiles are
  selectable like normal providers while preserving the `endpoint:*` id.
- Added Runtime LLM-call profile resolution, provider/base URL/key injection,
  and redaction from persisted observability traces.
- Added local `MultiLocalAbstractCoreLLMClient` support for per-call provider
  construction from profile `base_url` and `api_key`.
- Added bundle-host resolver wiring so Gateway-hosted runs can resolve virtual
  providers without Runtime importing Gateway.

Validation:
- `python -m pytest abstractgateway/tests/test_gateway_provider_endpoint_profiles.py abstractgateway/tests/test_gateway_discovery_endpoints.py abstractgateway/tests/test_gateway_console.py abstractruntime/tests/test_provider_endpoint_profile_resolution.py -q` -> 15 passed.
- `python -m compileall -q abstractgateway/src/abstractgateway abstractruntime/src/abstractruntime` -> passed.

Review notes:
- Code quality: raw keys are write-only through API/UI responses and redacted in
  Runtime observability. Scope changes upsert before deleting the old scoped row
  to avoid losing a profile on validation failure.
- Architecture: Gateway owns endpoint profiles and credentials; Runtime exposes
  only a generic optional resolver hook and does not import Gateway.
- Naive user: Gateway Console presents the endpoint as a named reusable object
  with description, a discover-models action, and a visible virtual provider id
  to copy/select.
- Expert user: profiles support static model allowlists, dynamic discovery,
  provider-family routing, gateway/user scope, and direct use in capability
  defaults or Flow node provider pins.
- Operations: initial storage is local JSON under the relevant Gateway data
  plane with `0600` permissions. A stronger vault/encryption/audit layer remains
  a follow-up under `0147`.

Residual risks:
- Workflow export/import still needs a portable endpoint requirement model so a
  shared workflow can ask the importing user to map or create an endpoint
  profile without exporting secrets.
- Profile resolution is implemented for text provider/model discovery and
  Runtime `LLM_CALL`/Agent execution, including output-selector calls that flow
  through that effect. Direct Gateway embedding/media catalog routes can adopt
  the same profile projection when those UI paths need virtual endpoint
  selection outside `LLM_CALL`.
- Gateway-scoped profile policy is currently admin-only create/update/delete and
  inherited discovery/use. Finer tenant ACLs can be added when endpoint sharing
  policy becomes stricter.
- Secrets are permissioned local JSON, not encrypted at rest. That is acceptable
  for the initial Gateway-local control-plane path but should not be treated as
  the final hosted vault design.
