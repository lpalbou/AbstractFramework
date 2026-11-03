# 1051 — Every shipped workflow loadable in Flow (ADR-0040 adoption)

> Package: gateway, flow
> Type: hygiene
> Created: 2026-10-25 21:20:00 +0200
> Priority: P2
> Labels: adr-0040, flow-library, shipped-workflows

## Summary

Make ADR-0040 checkable: a gateway test that every bundle shipped in the wheel (the `pyproject.toml` package-data list) carries a visual flow for each entrypoint, except ids declared under an "Exceptions" heading in `docs/shipped-workflows.md`; decide for the three native-loop agents (`react-agent`, `codeact-agent`, `memact-agent`) whether to wrap each in a one-node visual flow that Flow can open (an Agent node with the native loop as its mode) or to keep them as documented exceptions.

## Why

Operator ruling 2026-10-25: everything that runs for a person must be visible and editable in Flow. Today it holds for every repository bundle but those three.

## Current code reality

- `abstractgateway/flows/bundles/`: 129 non-draft bundles, 126 carry visual flows (`data.nodeType` nodes), 3 are native (`metadata.native_loop_factory`): react-agent@0.1.0, codeact-agent@0.1.0, memact-agent@0.1.0 (counted 2026-10-25).
- Flow's library shows bundles that carry a visual flow ("bundle" tag rows); native bundles never appear.
- `live-mailbox-judge` was hand-packaged on 2026-10-25 and later saved into the library as "Judge what arrived" (visualflow 8ee07990) and republished as 1.0.2; the automations run 1.0.2.

## Scope

- The test; the Exceptions section; the decision on the three agents (wrap or except), with the operator.
- Non-goal: changing how bundles are published.

## Validation

- `cd abstractgateway && python -m pytest tests -q -k shipped_bundles_visual`.
