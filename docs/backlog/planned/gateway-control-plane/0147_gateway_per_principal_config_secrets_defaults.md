# Planned: Gateway per-principal config, secrets, and defaults

## Metadata
- Created: 2026-05-30
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0033, ADR-0035
- ADR impact: May revise existing ADR

## Context
Provider/model defaults and API keys are currently configured through Core
local config, environment variables, or duplicated app UI settings. Gateway is
becoming the hosted control-plane UX, but Core should remain the schema and
persistence authority for capability defaults and provider credentials.

## Current code reality
- ADR-0035 states Core owns capability default schema and persistence, while
  Gateway is the control-plane access layer.
- AbstractCore has config primitives for default models, provider API keys,
  base URLs, and capability route defaults.
- Flow mostly supports `Auto` and Gateway-discovered defaults.
- Code and Observer still have app-local settings/auth/defaults that do not yet
  fully match the Gateway browser-session model.
- Gateway currently supports per-principal capability defaults in hosted
  user-auth mode. Writes to
  `/api/gateway/config/capability-defaults/...` are stored under the selected
  runtime data plane as `config/abstractcore.json`, using Core's
  `capability_defaults` schema. Gateway no longer reads or writes
  `config/capability_defaults.json`.
- The admin/root data plane Core config acts as the Gateway baseline.
  Normal users inherit that Gateway baseline first, then apply their own
  runtime-scoped Core config override. User overrides do not mutate the Gateway
  baseline or other users' defaults. The target model is the same cascade
  expressed as Core capability defaults scoped to the selected runtime/user
  context.
- Gateway Console v0 exposes those runtime-scoped Core defaults.
- Gateway provider endpoint profiles now cover the first explicit
  per-principal/gateway-scoped provider-secret injection path for reusable
  virtual providers such as `endpoint:office-vllm`; broader secret vault,
  encryption, bridge, and delegated-tool rules remain open.

## Problem
Users must configure provider/model defaults repeatedly across apps, and hosted
users need their own API keys/defaults isolated from other users. Storing keys
in browser localStorage or mutating global env is wrong for multi-user Gateway
deployments.

## What we want to do
Expose Gateway APIs and UI for per-principal provider credentials, base URLs,
and capability defaults, while delegating schema/persistence mechanics to Core
or runtime-scoped Core config. Apps should consume Gateway defaults and only ask
for provider/model when a user intentionally pins an override.

## Why
This removes duplicated UX, aligns apps behind Gateway, and preserves user
isolation for secrets and model choices.

## Requirements
- Default resolution is preference selection within policy ceilings:
  operator/tenant allowlist and capability policy constrain request overrides,
  workflow pins, user defaults, tenant defaults, gateway defaults, and
  execution-host Core defaults.
- Resolved provider/model metadata reports non-secret provenance so UIs can show
  whether a value came from request, workflow, user, tenant, Gateway baseline,
  or Core.
- Explicit workflow pins remain reproducible unless denied by current host
  policy, in which case denial is explicit rather than silently rerouted.
- API keys and provider secrets are never stored in browser storage.
- Per-user secrets are injected only into that user's runtime context.
- Capability defaults must not expose secret values.
- Gateway Console can collect keys/defaults but must not become a second
  defaults owner independent of Core.
- Before implementation, record the Core/Gateway storage boundary: who encrypts
  secrets, who can read raw values, how rotation/deletion works, how backups are
  handled, and how access is audited.
- Secrets must be redacted from logs, ledgers, artifacts, tool traces, audit
  payloads, and discovery responses.
- Define propagation rules for subruns, bridges, delegated tools, and any
  admin/system execution path before those paths can use per-principal secrets.

## Suggested implementation
Add Gateway config endpoints that wrap Core config/default APIs for the current
principal. Use a per-runtime Core config root/file for capability defaults, and
keep Gateway provider endpoint profiles as the first Gateway-owned secret
injection path. Expose readiness checks and catalog previews in Gateway Console
only after that boundary is explicit.

## Scope
- Gateway APIs for provider credentials and capability defaults.
- Gateway Console config page.
- Per-principal isolation tests for secrets/defaults.
- App docs that point users to Gateway defaults.

## Non-goals
- Do not remove direct AbstractCore CLI/config for local developer usage.
- Do not force every app to remove explicit provider/model overrides.
- Do not store raw secrets in Gateway audit logs or browser storage.

## Dependencies and related tasks
- ADR-0035 and `docs/guide/capability-routing-defaults.md`.
- `0145_gateway_admin_console_bootstrap.md`
- `0146_gateway_rbac_scope_policy_matrix.md`
- `0153_gateway_browser_session_security_contract.md`
- `../../completed/0170_core_gateway_capability_defaults_config_convergence.md`
- `../../completed/0149_cross_app_gateway_auth_defaults_convergence.md`

## Expected outcomes
- A Gateway user can configure provider keys/defaults once and use them from
  Flow, Code, Observer, Assistant, and bridges.
- Alice's provider keys/defaults are not visible or usable by Bob.
- Apps default to Gateway/Core defaults unless a run/workflow explicitly pins.

## Validation
- Alice/Bob secret isolation tests.
- Default cascade tests.
- UI tests proving secrets are write-only or masked after creation.
- App smoke tests with blank provider/model resolving through Gateway defaults.

## Recent validation
- `python -m pytest abstractgateway/tests/test_gateway_security_middleware_unit.py abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_console.py abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py -q` -> 51 passed, 2 warnings.
- `python -m compileall -q abstractgateway/src/abstractgateway abstractflow/web/backend` -> passed.
- `python -m pytest abstractgateway/tests` -> 261 passed, 2 skipped.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_security_middleware_unit.py abstractgateway/tests/test_gateway_console.py` -> 29 passed.
- `python -m pytest abstractgateway/tests/test_gateway_install_profiles.py abstractgateway/tests/test_gateway_capability_catalog_proxy.py` -> 29 passed.

## Progress checklist
- [x] Define initial per-principal capability-default storage boundary with
      Core schema and Gateway per-principal access control.
- [x] Migrate the initial Gateway overlay storage to per-runtime Core config
      files through `0170_core_gateway_capability_defaults_config_convergence`.
- [x] Define and implement the initial provider endpoint profile injection
      boundary for Gateway-owned virtual providers.
- [ ] Define provider-secret encryption/rotation/audit boundary beyond the
      initial local JSON store.
- [x] Define initial provenance behavior for Gateway and runtime-scoped Core
      defaults (`source=abstractcore.gateway_runtime` and
      `source=abstractcore.runtime`).
- [ ] Define runtime/subrun/bridge secret injection rules.
- [x] Add Gateway APIs for runtime-scoped capability-default overrides.
- [x] Add Gateway Console config UX for runtime-scoped defaults.
- [x] Update app/framework docs for current defaults behavior.
- [x] Add Alice/Bob default isolation tests.
- [x] Add initial endpoint profile secret redaction and non-admin scope tests.
- [ ] Add broader secret isolation tests after a complete vault/bridge boundary exists.

## Implementation note - 2026-05-30

This item is partially implemented for provider/model/base URL defaults.
Gateway provider endpoint profiles now provide the first raw provider credential
path without writing user secrets into browser storage, workflow JSON, or
process-wide environment variables. Profiles are resolved per request into
transient Runtime parameters and redacted from persisted Runtime observability.
The remaining design work is a fuller Core/Gateway secret contract covering
encryption at rest, rotation semantics, subruns, bridges, delegated tools,
audit, and deletion.

## Implementation note - 2026-06-01

The defaults boundary is now stricter: capability defaults are Core defaults
even when edited through Gateway. Gateway selects a Core config context for the
active runtime/user and writes Core's `capability_defaults` format there.
Existing `config/capability_defaults.json` Gateway overlays are ignored;
operators should recreate those defaults with `abstractgateway-config
set-default ...`.

Default cascade as implemented today: execution-host Core defaults provide the
base route set, the Gateway/root Core config provides the operator baseline,
and the current user's runtime Core config wins only for that user. Workflow pins and
per-request overrides still need to be resolved by run-start policy in later
items; do not silently reroute explicit workflow pins without an explicit
policy denial or override record.

## Guidance for the implementing agent
Keep the authority split crisp: Core owns config schema and low-level execution
config; Gateway owns authenticated hosted UX and per-principal access control.
