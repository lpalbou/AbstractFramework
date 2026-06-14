# Runtime Artifact Observability Completed Track

This track records completed work for making runtime artifacts explorable without
Observer-side guessing.

The 2026-06-06 track established ADR-0036, implemented the Runtime storage
contract, projected canonical artifact envelopes through Gateway, switched
Observer's Runtime Artifact Explorer to Gateway-backed counts/filters/paging,
added Runtime Activity supervision, enriched generated-media provenance, and
created coredoc plus a validated `runtime-explore` skill.

Post-completion refinements on 2026-06-06 made Code a first-class artifact
kind, separated Runtime Logs into run ledger/provider calls/Gateway audit, and
made generic waiting prompts visibly unsafe/inferred until the user reviews
session and ledger context.

## Reading order

1. `0188_artifact_descriptor_contract_and_adr.md`
2. `0189_runtime_artifact_catalog_and_access_stats.md`
3. `0191_gateway_artifact_envelope_query_and_provider_traces.md`
4. `0192_observer_canonical_artifact_explorer_ui.md`
5. `0194_observer_runtime_activity_monitor_and_wait_actions.md`
6. `0190_media_generation_provenance_and_enrichment.md`
7. `0193_runtime_artifact_coredoc_and_explore_skill.md`

## Related decisions and docs

- `docs/adr/0036-artifact-descriptor-contract.md`
- `docs/backlog/planned/runtime-artifact-observability/README.md`
- `docs/guide/runtime-artifacts.md`
- `abstractruntime/src/abstractruntime/storage/artifacts.py`
- `abstractgateway/src/abstractgateway/routes/gateway.py`
- `abstractobserver/src/ui/app.tsx`
- `abstractruntime/tests/test_artifacts.py`

## Non-goals

- Do not make UI inference canonical; legacy fallback labels remain fallback labels.
- Do not store unredacted provider secrets or large raw provider payloads in indexed metadata.
- Do not treat loaded-page Runtime Activity counts as exact global counts until Gateway exposes a run-stats endpoint.
