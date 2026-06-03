# Completed: Core and Gateway capability-default config convergence

## Metadata
- Created: 2026-06-01
- Status: Completed
- Completed: 2026-06-01

## ADR status
- Governing ADRs: ADR-0033, ADR-0035
- ADR impact: None; this implements the existing Core-owned defaults policy.

## Context
`abstractcore` and `abstractgateway` are both framework entry points. Users can
enter through Core for low-level provider/library usage or through Gateway for
durable runs, users, runtime routing, and hosted apps.

Capability defaults are already a Core-owned route concept. Gateway should edit
those defaults for the relevant execution context, not persist a separate
Gateway-only default model.

## Current code reality
- `abstractcore.config.capability_defaults` defines the shared route schema.
- `abstractcore.config.manager.ConfigurationManager` persists capability
  defaults, but currently uses `~/.abstractcore/config/abstractcore.json`
  unconditionally and applies persisted provider API keys to process env.
- `abstractcore` exposes capability defaults through legacy flags such as
  `--set-capability-default`, `--capability-provider`, and
  `--capability-model`; it does not yet provide the cleaner
  `abstractcore config set-default input.text --provider ... --model ...`
  syntax.
- `abstractgateway config` already forwards to `abstractgateway-config`, and
  `abstractgateway-config set-default` writes execution-host Core defaults in
  non-user-auth mode.
- In user-auth mode, Gateway previously wrote per-principal
  `config/capability_defaults.json` overlays. Those overlays used the Core
  schema but were not Core config files, which obscured the ownership boundary.
- Gateway Console calls the Gateway config routes, so it can migrate without a
  separate UI storage model.

## Problem
Defaults are conceptually Core capability route defaults, but the current CLI
and storage paths make them look split between Core and Gateway. That confuses
users and complicates standalone Gateway deployments, app-bundled Gateway
deployments, and multi-user runtime isolation.

## What we want to do
Make Core and Gateway expose matching defaults commands while keeping one
defaults schema and one persistence concept: Core capability defaults.

Gateway should select the correct Core config context for the current runtime
or user and edit that Core config on behalf of the user or admin.

## Why
This gives users one mental model:

- use `abstractcore config ...` when configuring Core directly;
- use `abstractgateway config ...` or Gateway Console when configuring a
  Gateway-hosted runtime;
- defaults are always Core capability route defaults.

## Requirements
- Add clean Core defaults subcommands:
  `abstractcore config defaults`,
  `abstractcore config set-default`,
  and `abstractcore config clear-default`.
- Keep existing Core flags and Gateway commands as compatibility aliases.
- Let `ConfigurationManager` target an explicit config file or config
  directory.
- Let Gateway create per-runtime/per-principal Core config files without
  injecting persisted API keys into process-wide environment variables.
- Refactor Gateway per-principal default overlays to read/write Core config
  files only. Existing `config/capability_defaults.json` overlays are ignored
  and must be recreated with `abstractgateway-config set-default ...`.
- Keep Gateway Console using Gateway config routes, so the UI leverages the
  same implementation as `abstractgateway config`.
- Do not move provider connections or Gateway user/RBAC state into Core.
- Do not expose raw provider secrets through defaults.

## Suggested implementation
- Extend `ConfigurationManager` with optional `config_dir`, `config_file`, and
  `apply_env` arguments.
- Add Core argparse subcommands under `abstractcore config`.
- In Gateway `capability_defaults.py`, replace custom overlay writes with
  `ConfigurationManager(config_file=<runtime>/config/abstractcore.json,
  apply_env=False)`.
- Remove Gateway `config/capability_defaults.json` overlay reads and writes;
  this is a breaking storage cleanup.
- Preserve `abstractgateway config set-default` syntax and make Console routes
  call the same helper.

## Scope
- `abstractcore` config manager and CLI.
- `abstractgateway` capability default helpers, config CLI, routes, console
  wording where needed, tests, and docs.
- Root docs that describe Core/Gateway config entry points.

## Non-goals
- No provider-secret vault/encryption work in this item.
- No forced migration of provider endpoint profiles into Core.
- No removal of legacy CLI flags.
- No compatibility migration for Gateway `config/capability_defaults.json`
  overlays; this is an intentional breaking storage cleanup.
- No app-specific provider/default settings cleanup outside Gateway Console
  behavior needed for this change.

## Dependencies and related tasks
- ADR-0033: install profiles, config entry points, and server boundaries.
- ADR-0035: Core-owned capability routing defaults.
- `0139_unified_framework_capability_defaults.md`
- `0147_gateway_per_principal_config_secrets_defaults.md`
- `0167_gateway_provider_connection_setup_console.md`

## Expected outcomes
- A Core user can run:
  `abstractcore config set-default input.text --provider openai --model gpt-4.1`.
- A Gateway operator can run:
  `abstractgateway config set-default input.text --provider endpoint:openai-prod --model gpt-4.1`.
- Gateway Console writes the same runtime-scoped Core defaults as the Gateway CLI.
- Per-user Gateway defaults are isolated as per-runtime Core config files.
- Existing Gateway overlay files are ignored.

## Validation
- Unit tests for `ConfigurationManager(config_file=..., apply_env=False)`.
- CLI tests for `abstractcore config set-default/defaults/clear-default`.
- Gateway tests proving per-principal default isolation writes
  `config/abstractcore.json` and ignores removed `config/capability_defaults.json`
  files.
- Gateway API tests for `GET/PUT/DELETE /api/gateway/config/capability-defaults`.
- Console smoke tests proving Defaults UI still contains the expected controls
  and uses Gateway config routes.
- Manual commands showing Core CLI and Gateway CLI produce matching default
  route payloads.

## Progress checklist
- [x] Add backlog and docs updates for the Core-owned defaults model.
- [x] Add configurable Core config manager paths and safe no-env mode.
- [x] Add `abstractcore config` subcommands and preserve legacy flags.
- [x] Refactor Gateway per-principal defaults to per-runtime Core config files.
- [x] Update Gateway Console/defaults copy as needed.
- [x] Add tests and run focused proof commands.
- [x] Update coredocs and LLM indexes.

## Completion notes
- `ConfigurationManager` now accepts explicit config file/directory targets
  and `apply_env=False` for embedded/multi-user hosts.
- Core config saves are atomic and private (`0600` best effort).
- `abstractcore config defaults|set-default|clear-default` is available while
  legacy flags remain supported.
- Gateway baseline/user defaults now write Core config files:
  `$ABSTRACTGATEWAY_DATA_DIR/config/abstractcore.json` for the Gateway baseline
  and `$ABSTRACTGATEWAY_DATA_DIR/users/<tenant>/<runtime>/runtime/config/abstractcore.json`
  for user runtime overrides.
- Existing `config/capability_defaults.json` overlays are ignored. Recreate
  those defaults with `abstractgateway-config set-default ...`.
- Gateway provider/model resolution now accepts the selected runtime base
  directory, so Alice/Bob runtime defaults do not fall back to one process-global
  Core singleton.

## Proof
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src python -m pytest abstractcore/tests/config/test_capability_defaults_config.py abstractgateway/tests/test_gateway_config_cli.py abstractgateway/tests/test_gateway_principal_auth.py::test_capability_defaults_are_isolated_by_gateway_principal abstractgateway/tests/test_gateway_principal_auth.py::test_gateway_defaults_are_inherited_by_users_until_user_override -q`
  passed: `17 passed, 1 warning`.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src python -m pytest abstractgateway/tests/test_gateway_provider_defaults.py abstractgateway/tests/test_gateway_embeddings_endpoint.py -q`
  passed: `14 passed`.
- `PYTHONPATH=abstractgateway/src:abstractcore:abstractruntime/src:abstractmemory/src python -m pytest abstractgateway/tests/test_gateway_principal_isolation_matrix.py -q`
  passed: `4 passed`.
- `PYTHONPATH=abstractcore python -m pytest abstractcore/tests/config/test_capability_defaults_server.py -q`
  passed: `1 passed`.
- Combined proof command across Core/Gateway defaults, provider defaults,
  embeddings, and isolation passed: `36 passed, 3 warnings`.
- Manual Core CLI proof wrote and listed `output.text` in an explicit
  `abstractcore.json` file.
- Manual Gateway CLI proof wrote and listed Gateway baseline defaults in
  `$ABSTRACTGATEWAY_DATA_DIR/config/abstractcore.json`.
- Manual Alice/Bob CLI proof showed Alice's runtime override resolving from
  `abstractcore.runtime`, Bob inheriting the Gateway baseline from
  `abstractcore.gateway_runtime`, and no legacy `capability_defaults.json`
  write.
- Regression tests create removed `capability_defaults.json` files and verify
  they do not affect Gateway baseline or user effective defaults.
- Temporary Gateway `/console` smoke proof returned the expected console HTML
  and its inline JavaScript passed `node --check`.

## Guidance for the implementing agent
Keep the distinction explicit: Core owns capability default schema and
persistence format; Gateway owns user/routing context and calls Core config for
the selected runtime. Do not introduce a new Gateway defaults schema.
