# Planned: Gateway Console sandbox client grounding and media attachments

## Metadata
- Created: 2026-06-01
- Status: Completed
- Completed: 2026-06-01

## ADR status
- Governing ADRs: ADR-0023, ADR-0031, ADR-0035
- ADR impact: None

## Context
The AbstractGateway Console Sandbox lets a signed-in Gateway user test configured providers and
capability defaults directly from `/console`. The chat UI supports browser file upload and sends
requests to `/api/gateway/sandbox/generate`, which calls AbstractRuntime's AbstractCore-backed LLM
client.

The sandbox is a browser-facing UX, so user-facing grounding such as current local time, timezone,
and country should describe the browser user's context. It must not become an authorization,
routing, or audit trust signal.

## Current code reality
- Before completion, `abstractgateway/src/abstractgateway/console.py` uploaded files to
  `/api/gateway/attachments/upload`, displays attachment chips, and sends only provider/model,
  prompt, messages, system prompt, and artifact refs to `/api/gateway/sandbox/generate`.
- Before completion, `abstractgateway/src/abstractgateway/routes/gateway.py` modeled sandbox requests with
  `_GatewaySandboxGenerateRequest(extra="forbid")`; it currently has no client context field.
- Before completion, `gateway_sandbox_generate` created `LocalAbstractCoreLLMClient` server-side and did not pass
  browser timezone, browser local time, locale, or country into Runtime.
- Before completion, `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py` derived runtime
  grounding from the server process timezone, locale, environment, and current clock. That is
  correct for server-only callers, but wrong for browser-facing sandbox prompt grounding.
- Artifact-backed browser uploads resolve through Runtime into file paths. File-backed image media
  must reach AbstractCore providers as native multimodal content, not as a text-only prompt.

## Problem
The sandbox can ground chat turns with server metadata instead of browser metadata. In remote or
Docker deployments this can show the wrong country/time context to the model.

Image attachments can also be visible in the browser transcript while failing to reach the
OpenAI-compatible provider as native image content, causing the model to answer as if no image was
attached.

## What we want to do
Make Console Sandbox requests carry explicit browser-local grounding context and ensure uploaded
image artifacts become native multimodal `image_url` blocks when routed through Gateway, Runtime,
and AbstractCore.

## Why
Users need the sandbox to behave like the app they are testing: the model should see the user's
current local context and any attached image, not the server's locale and a text-only placeholder.

## Requirements
- Browser context must include only bounded, allowlisted fields such as timezone, local datetime,
  locale, and optional locale-derived country.
- Runtime may use browser context for prompt grounding only; it must keep server-derived context as
  provenance and never use browser context for auth, routing, or permission checks.
- Media turns should not inject runtime metadata into the visible multimodal prompt.
- Browser-uploaded image artifacts must be resolved with content type and provider-ready image
  encoding.
- Generic OpenAI-compatible endpoint profiles and LM Studio-style providers must both be covered by
  tests.

## Suggested implementation
- Add a `client_context` field to the sandbox request schema.
- Collect browser timezone/local datetime/locale/country in Console Sandbox JavaScript.
- Pass sanitized client context in `params.trace_metadata.client_context`.
- Teach Runtime grounding to prefer allowlisted browser context for prompt grounding while keeping
  server context in metadata.
- Add tests at Core provider, Runtime artifact-resolution, and Gateway route/UI levels.

## Scope
- AbstractGateway Console Sandbox request/route behavior.
- AbstractRuntime grounding metadata merge behavior.
- AbstractCore media processing for `file_path` dicts produced by artifact resolution.
- Focused docs for current behavior where user-facing documentation is needed.

## Non-goals
- Do not use browser context for authorization, runtime routing, or provider credential selection.
- Do not redesign Gateway sessions or user profiles.
- Do not add broad geolocation; country remains locale/timezone-derived unless user profile work is
  implemented separately.

## Dependencies and related tasks
- ADR-0023 file attachment path resolution and authorization.
- ADR-0031 workflow routing overrides.
- ADR-0035 capability routing defaults.
- Proposed item 0144 for richer user profile grounding.

## Expected outcomes
- Console Sandbox image+text requests reach OpenAI-compatible VLMs as native multimodal requests.
- Browser-local timezone/current time/country are reflected in prompt grounding metadata when
  provided by the browser.
- Runtime metadata records provenance so maintainers can tell browser-derived grounding from
  server-derived fallback grounding.

## Validation
- Focused Python tests for Gateway sandbox request payloads, Runtime grounding, artifact media
  resolution, and AbstractCore OpenAI-compatible media formatting.
- Manual AbstractCore-only payload capture that proves `Qwen3.5-9B` image requests produce an
  `image_url` content block.
- Browser/manual verification should upload an image in `/console` Sandbox and receive an
  image-aware response from a configured VLM.

## Progress checklist
- [x] Add browser client context collection and Gateway request validation.
- [x] Add Runtime prompt-grounding merge with browser-over-server precedence.
- [x] Harden artifact-backed image media formatting through AbstractCore.
- [x] Add and run focused regression tests.
- [x] Update user-facing docs if behavior or troubleshooting guidance changed.

## Guidance for the implementing agent
Keep the fix narrow and evidence-driven. If an attached image still fails, inspect the final
provider request payload before changing UI copy or provider defaults.

## Completion report

Date: 2026-06-01

Summary:
- Gateway Console Sandbox now sends bounded browser-local grounding context with text sandbox
  requests: local datetime, UTC datetime, timezone, timezone offset, locale, and locale-derived
  country fallback.
- Gateway sanitizes that browser context and forwards it only as
  `params.trace_metadata.client_context`.
- Runtime prefers browser timezone/local datetime for prompt grounding while keeping server-derived
  context in result metadata as provenance. Browser locale no longer wins over timezone for country;
  timezone mapping wins, with locale as fallback.
- Runtime still skips injecting runtime metadata into media turns, so attached images are not
  preceded by grounding XML in the provider-visible user text.
- Artifact-backed image uploads now keep MIME/modality metadata through Gateway and Runtime and are
  materialized into typed temp files before AbstractCore provider formatting.
- AbstractCore provider media processing now treats `file_path` media dicts as files through
  `AutoMediaHandler`, so generic OpenAI-compatible and LM Studio providers receive native
  `image_url` content for vision-capable models.

Files or symbols touched:
- `abstractgateway/src/abstractgateway/console.py`: `sandboxClientContext()` and Sandbox request
  payload.
- `abstractgateway/src/abstractgateway/routes/gateway.py`:
  `_GatewaySandboxGenerateRequest.client_context`, `_sandbox_client_context()`, and
  `gateway_sandbox_generate()`.
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`:
  client grounding merge and artifact media resolution.
- `abstractcore/abstractcore/providers/base.py`: file-backed media dict handling.
- `abstractcore/abstractcore/media/types.py`: `content_type` alias handling.
- Focused tests in `abstractgateway/tests`, `abstractruntime/tests`, and `abstractcore/tests`.
- Docs in `abstractgateway/docs/configuration.md` and `docs/guide/gateway-security.md`.

Validation:
- `python -m py_compile abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py abstractgateway/src/abstractgateway/routes/gateway.py abstractgateway/src/abstractgateway/console.py`
- `PYTHONPATH=abstractgateway/src:abstractruntime/src:abstractcore python -m pytest abstractcore/tests/providers/test_lmstudio_requires_user_message_unit.py abstractruntime/tests/test_multimodal_abstractcore_integration.py::test_resolve_media_artifacts_uses_typed_temp_path_for_blob_store abstractgateway/tests/test_gateway_console.py abstractgateway/tests/test_gateway_provider_endpoint_profiles.py::test_gateway_sandbox_text_generation_uses_server_side_endpoint_credentials abstractruntime/tests/test_llm_client_system_context.py abstractruntime/tests/test_media_artifact_resolution.py abstractruntime/tests/test_llm_client_media_artifacts.py abstractcore/tests/media_handling/test_media_content_dict_roundtrip.py -q`
  passed with `30 passed, 6 warnings`.
- `PYTHONPATH=abstractgateway/src:abstractruntime/src:abstractcore python -m pytest abstractgateway/tests/test_gateway_provider_endpoint_profiles.py abstractgateway/tests/test_gateway_console.py abstractruntime/tests/test_llm_client_system_context.py abstractcore/tests/providers/test_lmstudio_requires_user_message_unit.py -q`
  passed with `34 passed, 6 warnings`.

Behavior changes:
- Console Sandbox text chat with an uploaded image now sends the upload as a media artifact and the
  resolved AbstractCore provider request includes an OpenAI `image_url` content block for
  vision-capable OpenAI-compatible models such as `qwen/qwen3.5-9b`.
- Browser-local time and timezone are used for user-facing prompt grounding. Server context remains
  recorded but is not the browser-facing default when browser context is present.
- Browser-provided grounding is explicitly untrusted and is not used for authorization, routing,
  provider credential selection, or audit authority.

Residual risks:
- Browser timezone is still not a precise geolocation signal. This is acceptable for prompt
  grounding, but richer user profile/location behavior remains covered by proposed item 0144.
- Manual verification against a live OVH endpoint should still be performed after restarting the
  local Gateway so the browser serves the updated Console JavaScript.

Priority impact:
- This removes the immediate Sandbox image-analysis blocker and the browser/server grounding drift.
- No ADR update was needed because the existing Gateway security and capability-default boundaries
  already cover the behavior; this item clarifies and validates the implementation.
