# Completed: AbstractFlow web-only product migration

## Metadata
- Created: 2026-05-31
- Status: Completed
- Completed: 2026-05-31

## ADR status
- Governing ADRs: ADR-0001, ADR-0012
- ADR impact: May revise existing ADR if the public AbstractFlow Python package is removed rather than reduced to compatibility shims.

## Context
AbstractFlow's product path is now Gateway-first: the browser editor talks to AbstractGateway for VisualFlow persistence, discovery, run start, ledger streaming, artifacts, and auth. AbstractRuntime owns VisualFlow compilation and workflow-bundle semantics. AbstractGateway owns runtime routing, provider configuration, credentials, sessions, users, and durable execution.

## Completed implementation
- Flattened the npm package from `abstractflow/web/frontend` to the `abstractflow/` repository root.
- Removed the Python package, Python packaging metadata, Python tests, FastAPI compatibility backend, generated Python docs site, and local runtime artifacts from AbstractFlow.
- Moved sample VisualFlow JSON files from `web/flows/` to `examples/flows/`.
- Updated AbstractFlow CI/release workflows to build and publish only the npm package.
- Removed Python `abstractflow` from the root `abstractframework` pip profile and install manifest.
- Updated local and published Gateway+Flow launcher scripts to start Flow through Node/npm instead of a Python server.
- Rewrote current AbstractFlow docs, README, LLM indexes, security, contributing, and acknowledgments around the web-package boundary.

## Problem
The repository looked like AbstractFlow owned execution. That created user confusion, stale token examples, duplicated auth language, and package-boundary drift.

## What changed
AbstractFlow is now a web editor product that connects to AbstractGateway. It no longer ships normal-product local Python execution/server paths.

## Product decision
AbstractFlow should not need local Python execution/server code for the normal product path. The answer for users is **no**: AbstractFlow is the web UI connected to AbstractGateway.

## Why
Users should have one mental model: Gateway owns execution and secrets; Flow owns visual workflow authoring UX.

## Requirements
- Keep `@abstractframework/flow` as the primary install and launch path.
- Remove stale `web/setup.py`.
- Remove or isolate FastAPI/local runtime compatibility code from normal package installs and docs.
- Keep any remaining Python code explicitly scoped to migration, tests, or bundle-authoring compatibility.
- Update README, docs, changelog, and LLM indexes to say AbstractFlow does not own execution.

## Implementation summary
The repository now has `src/`, `bin/`, `examples/flows/`, and `docs/` as its main shape. `package.json` is the release source of truth for `@abstractframework/flow`. VisualFlow compilation and `.flow` execution are treated as Runtime/Gateway concerns.

## Scope
AbstractFlow repository packaging, CLI, docs, tests, and frontend launch documentation.

## Non-goals
- Do not move Gateway auth/session/provider config into Flow.
- Do not change Runtime compiler semantics.
- Do not break Flow's browser editor while deleting compatibility code.

## Dependencies and related tasks
- Completed 0149 and 0153 for browser-session Gateway auth.
- Completed 0157 for Gateway-owned provider endpoint profiles.
- This item should be completed before claiming Flow is web-only in published package metadata.

## Expected outcomes
- A user installing or launching Flow sees only the web editor path on top of AbstractGateway.
- Python compatibility code is no longer shipped in AbstractFlow.
- Package ownership matches the architecture.

## Validation
- `npm install` in `abstractflow`.
- `npm run build` in `abstractflow` -> passed.
- `npm run lint` in `abstractflow` -> passed.
- `node --check bin/cli.js` in `abstractflow` -> passed.
- `npm pack --dry-run` in `abstractflow` -> npm package contains `dist`, `bin`, `README.md`, `LICENSE`, and `package.json`.
- `PYTHONPATH=. pytest -q tests/test_install_profiles.py` -> 6 passed.
- `python -m py_compile abstractframework/install_manifest.py abstractframework/__init__.py` -> passed.
- `bash -n scripts/gateway-flow-local.sh scripts/gateway-flow.sh scripts/build.sh` -> passed.
- `rg` audit found no current user docs/scripts advertising `pip install abstractflow`, `abstractflow serve`, `web/frontend`, or `web/backend`.

## Progress checklist
- [x] Decide whether AbstractFlow keeps a minimal Python shim or removes the Python distribution.
- [x] Delete stale `abstractflow/web/setup.py`.
- [x] Remove normal-product references to `abstractflow serve`.
- [x] Update docs and LLM indexes to state that AbstractFlow is the web editor and runs on top of AbstractGateway.
- [x] Run Flow frontend, packaging, root install profile, and launcher validation.

## Follow-up
Consider a small ADR update clarifying that AbstractFlow is npm-only while VisualFlow compilation and workflow-bundle execution are Runtime/Gateway responsibilities.
