# Completed: Observer canonical artifact explorer UI

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0032, ADR-0036
- ADR impact: Implements the Observer consumption side of ADR-0036; no separate Observer ADR expected unless UI ownership changes.

## Context
Observer's Runtime and Observe tabs should help users understand active work and artifacts. The current Artifact Explorer is useful, but it still relies on client inference, collapses voice/music into Audio, and does not show enough generation/provenance detail for users to diagnose expensive or mysterious computation.

## Current code reality
- `RuntimeArtifact` in `abstractobserver/src/ui/app.tsx` stores a small normalized shape with ids, content type, modality, created time, size, filename/path, sha256, tags, source, and raw row.
- Artifact rendering helpers classify preview and display kind from MIME, modality, filename/source path, tags, and content sniffing.
- Type options include Markdown, HTML, JSON, Image, Audio, Video, Document, Text, and Other. Voice and Music are not separate filter choices.
- Artifact grouping supports type, run, time, turn, node, workflow, location, and source, but many labels are derived from tags or synthesized fallback strings.
- Runtime Artifact Explorer uses `RUNTIME_ARTIFACT_LIMIT = 0`, local filter chips, local exact counts over the fetched set, and client-side paging.
- Artifact detail can preview media/content and show raw metadata, but generation prompt/model/source/provenance are not first-class fields.
- Gateway does not yet expose canonical artifact envelopes or server facet stats, so a full Observer rewrite should wait for `0191`.

## Problem
Users cannot trust the UI as a runtime monitor if it guesses artifact classes and hides the information needed to act. For generated media, the detail view should answer "what created this, with which prompt/model/params, from which source assets, and how do I open the responsible run/turn/provider trace?"

## What we want to do
Refactor Observer's Runtime Artifact Explorer to consume Gateway artifact envelopes, present canonical metadata first, separate semantic kinds such as Voice and Music, and make provenance/actions obvious.

## Why
Observer should be a high-quality control room, not a JSON viewer with inferred labels. The UI should expose real actions and relationships while keeping legacy artifact fallback behavior visible and honest.

## Requirements
- Add a typed client model for Gateway artifact envelopes. Prefer canonical fields; use tags/content sniffing only for legacy fallback with visible fallback labels.
- Separate `render_kind` from `semantic_kind`. Voice, Music, Sound/Recording, and generic Audio must be separate filterable semantic kinds while still using audio preview controls.
- Use server-backed filters for fields supported by `0191`; do not simulate exact counts from local pages. Provider/model/source/turn filters should be enabled only when Gateway exposes canonical fields or clearly labeled legacy fallback fields.
- Add explicit sorting controls for newest, oldest, last access, size, semantic kind, workflow, run, and turn where Gateway can support stable ordering.
- Show exact counts returned by Gateway, not counts from a limited page.
- Show the first 500 artifacts by default with visible pagination for additional pages. Default to bounded newest-first browsing.
- Improve artifact rows: human title, semantic type icon/chip, created time, size, duration/dimensions, workflow/run/turn, source/provenance, provider/model when present, and access summary.
- Improve artifact detail: embedded preview, compact metadata grid, generation prompt/input, provider/model/backend, params, source artifacts/media, media facts, access stats, provenance graph/links, raw metadata, and actions.
- Add actions: open full preview, download, show run artifacts, open in Observe, open ledger/turn, open provider trace/log when available, copy artifact id/ref.
- Make grouping by turn use canonical turn id/ledger cursor, not string labels.
- Keep legacy artifacts browseable but label `legacy inferred` or equivalent where type/provenance is not canonical.
- Preserve accessibility: visible tabs/chips, keyboard focus, readable labels, no ultra-thin tab affordances.

## Suggested implementation
1. Add an `ArtifactEnvelope` parser in the Observer client and fixtures for canonical and legacy responses.
2. Update artifact query state to request Gateway filters/pages/stats instead of loading everything by default.
3. Replace display-kind-only filters with semantic/render kind chips.
4. Redesign artifact rows and detail panel around canonical fields and actions.
5. Keep rendering helpers for legacy/text-preview fallback only.
6. Add focused React/Vitest tests for voice/music separation, pagination, provenance labels, exact count display, and legacy fallback.
7. Use browser QA screenshots for desktop and narrow viewport layouts.

## Scope
- `abstractobserver` Runtime Artifact Explorer UI, client models, filters, rows, detail panel, tests, and docs hooks.
- Minimal Gateway client changes needed for new envelope/stats endpoints.

## Non-goals
- Do not persist or infer artifact metadata in Observer.
- Do not expose admin cross-user runtime browsing in this item.
- Do not implement delete/export actions here.
- Do not remove legacy rendering helpers until legacy artifacts have a migration path.

## Hard dependencies
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`.
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`.

## Related and follow-on tasks
- `0190_media_generation_provenance_and_enrichment.md`.
- `0193_runtime_artifact_coredoc_and_explore_skill.md`.
- `0194_observer_runtime_activity_monitor_and_wait_actions.md`.

## Expected outcomes
- Users can filter Voice and Music separately.
- Users can inspect a generated media artifact and see prompt/input, provider/model, params, source assets, media facts, and responsible run/turn.
- Counts and pages are server-backed and exact for the selected scope.
- Legacy artifacts remain available but are clearly marked as inferred.
- Artifact detail gives useful actions without forcing users to read raw JSON.

## Validation
- Observer tests for canonical envelope parsing and fallback parsing.
- Observer tests for voice/music/audio semantic filters.
- Observer tests for server filter params and pagination behavior.
- Observer tests for provenance/action rendering with and without provider trace links.
- Browser screenshots across desktop and mobile/narrow widths.
- Manual smoke test against a Gateway runtime containing image, voice, music, JSON, Markdown, HTML, and legacy text artifacts.

## Progress checklist
- [x] Add envelope parser and fixtures after the `0191` response shape is available.
- [x] Wire server-backed filters, stats, and pagination.
- [x] Split semantic/render kind filters and labels.
- [x] Redesign artifact rows and detail panel.
- [x] Add provenance/action panels.
- [x] Add tests and browser QA.

## Guidance for the implementing agent
Treat the screenshots that motivated this item as usability failures to eliminate, not as layouts to patch around. Design from the user question: "What is this artifact, where did it come from, and what can I do next?" Do not build another UI layer on v0 rows; consume `0191` envelopes or keep the work to parser/fixture preparation only.

## Completion report

Date: 2026-06-06

Summary:
- Refactored Observer Runtime Artifact Explorer to consume Gateway artifact envelopes and exact stats rather than default-unlimited local artifact loads.
- Added server-backed filtering, sorting, and paging for the first 500 artifacts per page, with exact total counts and byte totals from Gateway.
- Split artifact semantics from render format in the UI: Voice, Music, Sound, Recording, Unclassified audio, Image, Video, Markdown, HTML, JSON, Document, Text, and Other are visible chips.
- Improved artifact rows and detail with canonical title/type, created/last-access/size/media facts, workflow/run/turn/node, provider/model, access stats, generation prompt, producer metadata, preview/download/run/ledger/provider-trace/audit actions, and legacy-inferred labels.
- Kept shared Markdown, JSON, and HTML renderers for text preview, including HTML source formatting and JSON folding support from earlier shared components.

Files and symbols touched:
- `abstractobserver/src/lib/gateway_client.ts`: expanded artifact search params and access-action content reads.
- `abstractobserver/src/ui/app.tsx`: Runtime artifact query state, envelope normalization, semantic labels, artifact rows, detail panel, actions, and accessibility chip state.
- `abstractobserver/src/ui/artifact_rendering.ts` and `artifact_rendering.test.ts`: Voice/Music/Sound/unclassified audio classification and text renderer regression coverage.
- `abstractobserver/README.md`, `abstractobserver/docs/api.md`, `abstractobserver/docs/architecture.md`, `abstractobserver/llms.txt`, `abstractobserver/llms-full.txt`: Observer coredoc updates.

Validation:
- `npm test -- --run src/ui/artifact_rendering.test.ts` passed (`8 passed`).
- `npm run build` passed; Vite reported only the existing large-chunk warning.
- Headless Chrome smoke verified Runtime -> Artifacts text and captured `/tmp/abstractobserver-runtime-artifacts-smoke.png`.

Behavior changes:
- Voice, Music, and Sound are no longer hidden behind generic Audio when descriptors record semantic kind.
- Generic audio is labeled as Unclassified audio so missing semantic descriptors are visible rather than silently conflated.
- Missing generation prompt is shown as an explicit descriptor gap, not as an unexplained dash.
- Type and date chips expose `aria-pressed`.

Residual risks and follow-ups:
- Provider trace and audit actions depend on artifact envelope links from Runtime/Gateway; richer producer capture remains in `0190`.
- Open ledger currently opens the run ledger; exact turn/provider deep links need stable route support and are follow-up work for the runtime activity/trace slices.
- The run rail still needs search, per-run artifact counts, and scale behavior; keep that in `0194`.
- Narrow/mobile screenshots still need a follow-up QA pass with real runtime data.

Post-completion refinement: 2026-06-06
- Code is now a first-class artifact kind in Runtime/Gateway/Observer classification, with a dedicated Runtime filter chip, display label, and code glyph instead of being hidden under generic Text.
- Artifact display labels now prefer the renderable kind when it is more useful to the user, so Markdown, HTML, JSON, and Code artifacts are not mislabeled by a generic semantic fallback.
- The shared artifact rendering tests cover code classification while keeping JSON and log text out of Markdown rendering.
