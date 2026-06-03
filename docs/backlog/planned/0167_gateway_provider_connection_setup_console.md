# Planned: Gateway provider connection setup console

## Metadata
- Created: 2026-05-31
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0001
- ADR impact: None

## Context
Gateway already has provider endpoint profiles that store descriptions, base URLs, optional API keys, optional model allowlists, and expose virtual providers such as `endpoint:office-vllm`. Users still need a clearer setup surface for cloud providers, local servers, and OpenAI-compatible endpoints.

## Current code reality
- `ProviderEndpointProfileStore` stores write-only API keys under Gateway data dirs.
- Gateway discovery exposes endpoint profiles as virtual providers.
- AbstractRuntime receives resolved provider/base URL/API key parameters transiently.
- The console now exposes provider connections as a guided setup flow, but the
  contract still uses the historical `provider-endpoint-profiles` API path.

## Problem
Provider configuration is still too technical and too easy to confuse with per-node provider/model selection in Flow.

## What we want to do
Make Gateway Console the control plane for provider connections and multimodal capability defaults. Flow should only select provider/model values surfaced by Gateway.

## Why
Secrets belong server-side in Gateway. Workflows should reference stable virtual providers and discovered models, not hardcoded browser-side keys.

## Requirements
- Support OpenAI, Anthropic, OpenRouter, Portkey, LM Studio, Ollama, and custom OpenAI-compatible connections.
- Keep API keys write-only and never echo them in HTML/API responses.
- Discover models from the endpoint; do not require users to manually type model lists.
- Hide model capability classification from setup; AbstractCore owns that metadata.
- Preserve optional model allowlists only as an advanced control.
- Let admins create Gateway-wide connections and users create user-scoped connections.

## Suggested implementation
Use provider endpoint profiles as the single provider connection abstraction for now. Improve Console labels, hints, family options, validation, and docs. Defer a second built-in provider secret store unless endpoint-profile semantics prove insufficient.

## Architect/review synthesis
- **Alternative A: Flow-owned provider config.** This is convenient for node authors, but it would put secrets and endpoint credentials in the wrong app boundary and would duplicate configuration in Code, Observer, Assistant, and Flow.
- **Alternative B: Gateway provider connections backed by existing endpoint profiles.** This keeps secrets server-side, reuses the already-tested virtual-provider discovery contract, works for built-in providers and custom OpenAI-compatible endpoints, and lets Flow remain a selector instead of a credential store. This is the selected design.
- **Alternative C: Separate built-in provider secret store plus endpoint profiles only for custom endpoints.** This might make OpenAI/Anthropic feel more first-class, but it creates two abstractions that both produce provider/model choices and would increase drift unless a real limitation appears.
- **Key tension:** OpenAI/OpenRouter/Anthropic defaults can work with provider-native URLs, while custom OpenAI-compatible endpoints need explicit base URLs. The console should make that difference visible through connection-type hints and validation, not by asking users to understand internal capabilities.
- **Review outcome:** The selected design is acceptable if model discovery stays endpoint-driven, raw keys are never echoed, normal users do not classify model capabilities manually, and Gateway-wide connections remain admin-only.
- **Latest UX split:** The console now uses four top-level tabs: **Users & Runtimes** for RBAC/runtime routing, **Providers** for endpoint URL/API key setup, **Multimodal Capabilities** for capability-route provider/model selection, and **Sandbox** for provider/model and configured-route smoke tests. The Multimodal Capabilities tab deliberately has no Base URL/API key fields; those belong only to provider connections or scoped Core/environment configuration.
- **Reviewer tension resolved:** One reviewer argued that capability defaults should keep generic provider discovery as a convenience, but the stronger security/UX argument won: showing unconfigured Anthropic/OpenAI options made the console look available before credentials existed. The tab now uses available providers as its source: saved Gateway provider connections plus direct providers that are already usable from scoped Core config or process environment.
- **Local-provider refinement:** LM Studio and Ollama are connectionless in the common local case. If their configured/default endpoints are reachable and model discovery succeeds, they surface automatically as available direct providers without forcing users to save a redundant endpoint profile.
- **Follow-up pressure:** Gateway has route-specific catalogs for embeddings, vision, voice, and music, but the Console defaults editor still uses provider-level model discovery. A future pass should decide whether Defaults needs route-specific filtering in Gateway Console or whether route-level filtering should remain primarily in Flow's specialized selectors.

## Scope
Gateway Console UI, provider endpoint profile docs/tests, and root/Gateway docs.

## Non-goals
- Do not store provider secrets in AbstractFlow.
- Do not create a separate provider-secret abstraction unless profile-based connections cannot handle a real use case.
- Do not ask users to manually classify model modalities in the provider setup form.

## Dependencies and related tasks
- Completed 0157 provider endpoint profiles.
- Related 0147 per-principal config/secrets/defaults.

## Expected outcomes
- Gateway Console presents "Provider Connections" with clear connection types and endpoint/key hints.
- Provider setup opens a modal with `Cancel`, `Test`, and `Confirm`: Test previews endpoint model discovery without saving; Confirm persists the provider profile.
- Saved connections immediately surface as virtual providers in Gateway defaults and Flow nodes.
- Defaults select only a configured provider connection plus a discovered/allowed model; endpoint base URLs and raw keys are never configured from Defaults.
- Discovered models can be selected without manual typing.
- The Sandbox tab can run a text chat against any available provider/model and can smoke-test configured generated-media routes, returning artifact links for completed media.

## Validation
- Provider endpoint profile API tests.
- Console HTML smoke/compile checks.
- Manual/headless browser check against mocked configured providers and multimodal capability defaults.

## Progress checklist
- [x] Rename low-level endpoint wording to provider connections in the console.
- [x] Add missing connection families and setup hints.
- [x] Keep capability internals out of the main setup form.
- [x] Add first-class setup presets for OpenAI, Anthropic, OpenRouter, Portkey,
  LM Studio, Ollama, and custom OpenAI-compatible endpoints.
- [x] Make Gateway defaults load usable provider discovery instead of the
  fast metadata-only catalog.
- [x] Fix OpenAI and Anthropic model discovery to honor provider base URL
  overrides.
- [x] Update coredocs and LLM indexes.
- [x] Move provider setup into a modal with `Cancel`, `Test`, and `Confirm`.
- [x] Rename the lower table to Available Providers and keep it as the fixed
  list of configured provider connections.
- [x] Remove Base URL from Defaults so provider URLs/API keys live only in
  provider connections.
- [x] Make Defaults provider choices come from configured provider connections,
  not the generic discovery catalog.
- [x] Fix refresh so non-auth panel failures do not incorrectly sign the user
  out.
- [x] Auto-surface reachable LM Studio and Ollama default endpoints as
  available direct providers.
- [x] Add a Sandbox tab for provider/model text chat and configured media-route
  smoke tests.
- [x] Re-check the UI with headless screenshots for Providers, provider modal,
  Defaults, and default modal states.

## Latest validation evidence
- `PYTHONPATH="abstractgateway/src:abstractcore:abstractruntime/src:abstractagent/src:abstractmemory:abstractsemantics:abstractuic" python -m pytest abstractgateway/tests/test_gateway_console.py abstractgateway/tests/test_gateway_provider_endpoint_profiles.py abstractcore/tests/providers/test_provider_model_discovery_base_url_unit.py -q` -> 14 passed.
- Headless Chrome screenshots generated for mocked signed-in console states:
  `/tmp/gateway-console-providers.png`,
  `/tmp/gateway-console-provider-modal.png`,
  `/tmp/gateway-console-defaults.png`, and
  `/tmp/gateway-console-default-modal.png`.

## Guidance for the implementing agent
Use the existing profile abstraction before adding new storage. Re-check Flow provider/model dropdowns after Gateway changes because the user-facing proof is discovery in Flow.
