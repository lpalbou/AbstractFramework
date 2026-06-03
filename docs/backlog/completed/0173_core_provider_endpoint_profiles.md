# Completed: Core provider endpoint profiles

## Metadata
- Created: 2026-06-02
- Status: Completed
- Completed: 2026-06-02

## ADR status
- Governing ADRs: ADR-0033, ADR-0035
- ADR impact: None. This extends the existing Core-owned configuration and provider-routing policy without changing package boundaries.

## Context
Gateway has reusable provider endpoint profiles that expose stable virtual provider ids such as `endpoint:ovh-provider`. Core users can already configure provider keys and capability route defaults, but direct Core usage has no persisted named endpoint profile abstraction. That means a Core-only developer must repeat `base_url` and key setup across defaults or calls, while Gateway users can configure the endpoint once.

## Current code reality
- `abstractcore.config.manager.ConfigurationManager` persists API keys and `capability_defaults` in `abstractcore.json`, and supports explicit `config_file` / `config_dir` contexts.
- `abstractcore.config.main` exposes `abstractcore config defaults|set-default|clear-default`, but not provider profile commands.
- `abstractcore.providers.registry.ProviderRegistry` only knows registered base providers. It merges transient runtime overrides from `configure_provider()`, but it does not resolve `endpoint:*` ids from persisted Core config.
- `abstractgateway.provider_endpoint_profiles.ProviderEndpointProfileStore` already validates/stores Gateway profiles and exposes public/write-only-secret behavior, but its `scope` and per-principal semantics belong to Gateway.
- Docs already use examples such as `--provider endpoint:office-vlm`; those examples are not fully backed by standalone Core.

## Problem
Core and Gateway now share capability route defaults, but only Gateway can create reusable named endpoint providers. That is brittle for developers who use Core directly, and it makes exported workflow/default examples depend on Gateway even when the endpoint is just a local or hosted OpenAI-compatible API.

## What we want to do
Add Core-owned provider profiles that are persisted in Core config, exposed through Core CLI, and resolved by Core provider discovery/factory as virtual providers.

## Why
Developers should be able to define a provider once:

```bash
abstractcore config set-provider ovh-provider \
  --family openai-compatible \
  --base-url https://oai.endpoints.kepler.ai.cloud.ovh.net/v1 \
  --api-key "$OVH_KEY" \
  --description "OVH inference endpoint"
```

and then reuse it everywhere:

```bash
abstractcore config set-default input.text --provider endpoint:ovh-provider --model Qwen3.5-9B
```

## Requirements
- Persist Core provider profiles in `abstractcore.json` with private file mode.
- Keep raw API keys write-only in CLI/status JSON; list commands may show only `api_key_set` and a short fingerprint.
- Support `endpoint:<id>` resolution in `create_llm`, provider model discovery, and provider status/metadata.
- Support OpenAI-compatible endpoints as the primary target, while retaining a `provider_family` field for OpenAI, Anthropic, OpenRouter, Portkey, LM Studio, Ollama, and future compatible families.
- Let explicit per-call kwargs override profile defaults for developer escape hatches.
- Keep Gateway profile scoping and user isolation in Gateway; do not move Gateway profiles into Core.

## Suggested implementation
- Add a Core `provider_profiles` config section and validation helpers.
- Add `abstractcore config providers`, `set-provider`, `delete-provider`, and optionally `models` commands.
- Teach `ProviderRegistry` to synthesize provider metadata for enabled `endpoint:*` profiles and route creation/model listing to the profile family with profile `base_url` and `api_key`.
- Update docs and tests with an OVH-style example.

## Scope
- `abstractcore` config schema, CLI, provider registry, and tests.
- Root/Core docs describing the standalone Core flow.
- Backlog traceability for this implementation.

## Non-goals
- Do not add a Core web console.
- Do not change Gateway Console storage or per-user profile scope.
- Do not migrate Gateway provider profile files into Core.
- Do not expose raw API keys in provider listing, status, discovery, or docs output.

## Dependencies and related tasks
- Completed `0157_gateway_provider_endpoint_profiles`.
- Completed `0170_core_gateway_capability_defaults_config_convergence`.
- Planned `0167_gateway_provider_connection_setup_console`.
- ADR-0035 capability routing defaults.

## Expected outcomes
- `endpoint:ovh-provider` can be configured in Core without Gateway.
- `abstractcore config providers --json` lists configured profiles without raw keys.
- `abstractcore config models ovh-provider` resolves the profile URL/key and discovers models, or returns the allowlist when configured.
- `create_llm("endpoint:ovh-provider", model="Qwen3.5-9B")` routes through the profile family with the stored base URL/key.
- Capability defaults can reference the virtual provider id directly.

## Validation
- Unit tests for profile persistence, CLI list/set/delete/model allowlist, provider registry metadata, and `create_llm` routing.
- Manual command smoke test using a temporary Core config file and an OVH-style profile.

## Progress checklist
- [x] Add Core provider profile schema and persistence.
- [x] Add Core CLI provider-profile commands.
- [x] Add provider registry/factory endpoint resolution.
- [x] Add focused tests.
- [x] Update docs.
- [x] Record validation evidence and completion notes.

## Guidance for the implementing agent
Keep this as Core's single-principal equivalent to Gateway provider connections. Gateway can continue to use its scoped profile store; the shared user-facing contract is the virtual provider id, not shared storage.

## Completion report

Date: 2026-06-02

Summary:
- Added Core-owned local provider endpoint profiles under the `provider_profiles`
  section of `abstractcore.json`.
- Added redacted profile listing and profile-specific private resolution so
  `endpoint:<id>` injects the configured family, base URL, and API key only at
  provider creation/model discovery time.
- Added Core CLI commands for provider profile create/update/list/show/delete,
  model discovery, live testing, and route-default reuse.
- Added provider registry support for virtual `endpoint:*` providers without
  creating one provider class per endpoint.
- Added endpoint-profile support to the embedding manager so
  `embedding.text -> endpoint:<id>` can use the same profile abstraction.
- Updated configuration documentation and AI-readable docs.

Behavior changes:
- `create_llm("endpoint:ovh-provider", model="Qwen3.5-9B")` now resolves
  through Core config without Gateway.
- `abstractcore config models ovh-provider` resolves a local profile id unless
  the name is a built-in provider; `endpoint:<id>` remains the unambiguous
  virtual provider id.
- `abstractcore config providers --json` and profile status output redact raw
  API keys and expose only `api_key_set`, env-reference metadata when present,
  and a short fingerprint.
- `--api-key` is the only public credential flag. Raw values are stored as
  private config keys; literal `'$ENV_VAR'` values are stored as environment
  references for deployment-friendly config.
- `--clear-api-key` clears either stored key source.

Validation:
- `PYTHONPATH=. python -m pytest tests/config/test_provider_profiles_config.py tests/config/test_capability_defaults_config.py tests/config/test_provider_config.py tests/providers/test_registry_core.py -q` from `abstractcore/` -> 53 passed.
- Manual OVH-style smoke with a temporary config file:
  `set-provider ovh-provider`, `models ovh-provider --json`,
  `set-default input.text --provider endpoint:ovh-provider --model Qwen3.5-9B`,
  `defaults --json`, and env-key-source clearing all succeeded.
- `python scripts/gen_llms_full.py` regenerated `llms-full.txt`.

Docs updated:
- `abstractcore/docs/centralized-config.md`
- `docs/configuration.md`
- `docs/guide/capability-routing-defaults.md`
- `llms.txt`
- `llms-full.txt`

Residual risks:
- Gateway still has its own scoped provider-profile schema. The runtime/user
  behavior is correct, but a future cleanup can reduce schema drift by sharing
  more validation helpers once release/package boundaries are stable.
- Live discovery for profile-backed providers depends on the endpoint's
  `/v1/models` behavior; fixed allowlists remain the deterministic fallback.

Follow-ups:
- Consider a later Gateway refactor that reuses Core's profile validation
  helpers while preserving Gateway's hosted scope and RBAC model.
- Consider adding a `test-provider --model` generation smoke later, but keep it
  opt-in because live generation may cost money.
