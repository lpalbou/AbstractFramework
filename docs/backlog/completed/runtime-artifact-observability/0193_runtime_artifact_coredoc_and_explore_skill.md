# Planned: Runtime artifact coredoc and explore skill

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0032, ADR-0036
- ADR impact: Documents ADR-0036 adoption; no separate ADR expected for docs/skill work.

## Context
The runtime artifact/retrieval story is spread across package docs, source comments, API references, and backlog notes. A maintainer-facing `runtime-explore` skill could be useful, but only after the current behavior and intended descriptor contract are documented clearly.

## Current code reality
- ADR-0036 and Runtime descriptor/catalog foundations are complete, and Gateway/Observer now document the first canonical artifact envelope and Artifact Explorer behavior.
- `abstractruntime/docs/api.md` mentions artifacts and JSON-safe/offloading behavior, but there is no single artifact model and retrieval guide.
- `abstractruntime/docs/evidence.md` documents evidence separately from artifacts.
- `abstractgateway/docs/api.md` documents canonical artifact envelopes, stats/facets, `artifact_kind`, access actions, and bounded search; it still needs a broader cross-package retrieval guide.
- `abstractobserver/docs/api.md` and `abstractobserver/docs/architecture.md` document the Gateway-backed Runtime Artifact Explorer; they intentionally do not own the full Runtime storage contract.
- Root `docs/backlog/proposed/gateway-control-plane/0151_runtime_explorer_contract.md` already proposes a broader Runtime Explorer envelope, but it remains proposed and broader than the artifact-specific work here.
- `llms.txt` files do not yet provide a concise cross-package decision map for artifact metadata search vs ledger/history vs KG/memory retrieval.

## Problem
Without faithful docs, agents and developers will keep rediscovering where artifacts, memory, ledgers, and Gateway routes overlap. Creating a skill before the docs and descriptor contract are stable would encode current gaps as procedure.

## What we want to do
Add faithful coredoc pages for runtime artifacts and retrieval, then create a small `runtime-explore` skill that references those docs as the source of truth for maintainer investigations.

## Why
Users and agents need to know how to answer runtime questions without conflating artifact search, KG retrieval, ledger replay, provider traces, raw workspace browsing, and Observer presentation.

## Requirements
- Document current behavior faithfully; keep remaining producer/activity gaps in backlog instead of describing them as current behavior.
- Add a Runtime artifact/retrieval page covering artifact identity, `artifact_id`, `blob_id`, run namespacing, refs, storage layout, metadata, tags, dedupe, legacy layout, descriptors, access stats, catalog search, and repair behavior.
- Add a Gateway runtime resources/query page or section covering artifact endpoints, session/run visibility, search limits, stats/pagination, import/export, `/kg/query`, provider trace links when available, and sensitivity limits.
- Add an Observer runtime explorer page or section explaining what the Runtime page, Artifact Explorer, Observe page, and Mindmap consume, and that Observer does not own persistence/provenance semantics.
- Add a root guide mapping responsibilities: Runtime stores, Gateway exposes/indexes/authorizes, Observer visualizes, AbstractMemory/KG retrieves semantic/context data, AbstractSemantics validates predicates.
- Update relevant `docs/README.md` indexes and package `llms.txt`/`llms-full.txt` files.
- Only after docs are in place, create `runtime-explore` with `$skill-creator`.
- The skill should standardize maintainer investigations: inspect Gateway data dir, trace `run_id`/`session_id`/`artifact_id`, query Gateway endpoints, distinguish artifact metadata search from KG retrieval, find provider traces, and produce bounded redacted summaries.
- The skill must warn against dumping sensitive prompts, provider payloads, or artifact contents unless explicitly required.

## Suggested implementation
1. Add Runtime docs for the implemented descriptor/catalog/access model.
2. Add a cross-package guide mapping Runtime artifact storage, Gateway query/projection, Observer visualization, ledger/history replay, and KG retrieval.
3. Link pages from package/root docs indexes and regenerate or update `llms.txt` and `llms-full.txt` for affected packages.
4. Use `$skill-creator` to scaffold `runtime-explore` against the stable docs.
5. Validate the skill with the skill creator validation script and a small fixture investigation prompt.

## Scope
- Cross-package documentation for current and implemented artifact/retrieval behavior.
- AI-readable docs indexes.
- Optional `runtime-explore` skill after docs are stable.

## Non-goals
- Do not describe planned descriptor fields as current behavior before implementation.
- Do not make the skill a substitute for source docs.
- Do not include incident/postmortem language in coredoc pages.
- Do not add broad runtime delete/export/admin guidance unless the related APIs and RBAC are implemented.

## Hard dependencies
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`.
- `docs/backlog/completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md`.

## Related and follow-on tasks
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`.
- `docs/backlog/completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md`.
- `0194_observer_runtime_activity_monitor_and_wait_actions.md`.
- `docs/backlog/proposed/gateway-control-plane/0151_runtime_explorer_contract.md`.

## Expected outcomes
- A developer can read one cross-package guide to understand artifact storage, retrieval, Gateway exposure, and Observer visualization.
- Docs clearly distinguish artifact metadata search from KG/semantic retrieval.
- `runtime-explore` exists only when it can point to canonical docs and stable APIs.
- Future agents can investigate runtime artifacts without leaking sensitive payloads or relying on Observer heuristics.

## Implementation completed
- Added `abstractruntime/docs/artifacts.md` for artifact identity, refs, tags, structured metadata, descriptors, generated-media provenance, catalog search, access stats, Gateway/Observer boundaries, and retrieval limits.
- Added root guide `docs/guide/runtime-artifacts.md` mapping Runtime, Gateway, Observer, Memory/KG, and Semantics responsibilities.
- Updated Runtime, Gateway, and Observer coredoc pages to document artifact envelopes, stats/facets, Runtime Activity, Artifact Explorer, loaded-page counts, access-action stats, direct transcription descriptors, and generated-media descriptor projection.
- Updated root/package docs indexes plus `llms.txt` and `llms-full.txt` inputs/outputs for affected packages.
- Created `/Users/albou/.codex/skills/runtime-explore/SKILL.md` using the skill format, with safety rules for redaction, image-content non-inspection, Gateway-first queries, artifact-vs-ledger-vs-KG decision guidance, and bounded summaries.
- Added a minimal skill agent config at `/Users/albou/.codex/skills/runtime-explore/agents/openai.yaml`.

## Validation
- `python scripts/gen_llms_full.py`
- `(cd abstractgateway && python scripts/generate-llms-full.py)`
- `(cd abstractobserver && npm run llms:full)`
- `python /Users/albou/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/albou/.codex/skills/runtime-explore`
- Coredoc scan for incident/postmortem language in the new user-facing docs.
- Chrome/headless smoke of Observer Runtime Explorer after the docs-backed UI changes.

## Progress checklist
- [x] Add Runtime artifact/retrieval docs for implemented descriptor/catalog behavior.
- [x] Add Gateway runtime resources/query docs after `0191`.
- [x] Add Observer runtime explorer docs after `0192`.
- [x] Add root cross-package guide mapping Runtime/Gateway/Observer/Memory responsibilities.
- [x] Update docs indexes and LLM files.
- [x] Create and validate `runtime-explore` after docs/contracts are stable.

## Residual follow-up
- Keep `runtime-explore` aligned with future Gateway run-stats/provider-trace APIs. The skill should cite docs and API responses, not freeze UI workarounds.

## Guidance for the implementing agent
Use coredoc first for implemented Runtime behavior, but do not create `runtime-explore` until Gateway and Observer behavior is stable enough to avoid encoding workarounds. If the code and docs disagree, fix the docs or defer the planned behavior to backlog; do not make the docs aspirational.
