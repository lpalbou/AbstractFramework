# Completed: Observer observability replay workbench

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0036
- ADR impact: None

## Context
Recent Observer work made artifact search, runtime activity, wait details, provider traces, and logs more useful, but the product still feels split between observation and operation. External observability patterns point in the same direction: OpenClaw-style mission control focuses on runs, sessions, logs, failures, tool events, and artifacts; Hermes Web Dashboard/Desktop puts sessions, logs, active workers, and task context upfront; LangSmith, Langfuse, Phoenix, Agno, AgentOps, and Braintrust all make replayable traces and session context the central observability surface.

Observer should explain and replay what happened across AbstractFramework. It may link to interventions, but it should not become the primary runtime administration console.

## Current code reality
- `abstractruntime.history_bundle.export_run_history_bundle(...)` already returns root run metadata, ledgers, a timeline, filtered input data, and an optional best-effort `session.turns` section.
- `_best_effort_session_turns(...)` scans a bounded `list_runs(...)` window even though `RunStore.list_run_index(session_id=..., root_only=True)` now exists in concrete stores.
- Runtime artifact descriptors now carry session/run/workflow/node/turn/provenance/generation/media/access metadata, but `history_bundle` does not expose artifact summaries to replay clients.
- `abstractobserver/src/lib/gateway_client.ts` exposes `get_run_history_bundle(...)`, but `abstractobserver/src/ui/app.tsx` uses it with `include_session=false` only for subrun discovery.
- Observe has tabs for Overview, Timeline, Ledger, Providers, Graph, Digest, Attachments, and Chat, but no first-class read-only replay tab that combines session turns, ledger timeline, and produced artifacts.
- Runtime Activity still exposes destructive controls directly; larger product-boundary work remains tracked by `0150`, `0195`, and `0196`.

## Problem
Users cannot reliably reconstruct a run or waiting discussion from Observer without manually switching between ledger, artifacts, runtime rows, logs, and guessed context. The runtime has enough descriptor data to make replay richer, but it is not exposed through the bundle that replay-capable clients should consume.

## What we want to do
Make `history_bundle` the read-only replay handoff for Observer:
- prefer indexed session run discovery where available;
- attach bounded artifact summaries to run ledgers and session turns;
- add an Observe `Replay` tab that presents bounded session turns, run timeline, and replay artifacts together;
- keep mutation/admin flows out of the new replay surface.

## Why
Observer should make computations understandable at scale: what was requested, what happened, which tools/providers ran, what artifacts were created, and how the current run relates to a session. A replay bundle also gives future chat/replay work a shared contract instead of another Observer-only reconstruction.

## Requirements
- Runtime must keep `history_bundle` backward-compatible and bounded.
- Artifact summaries must be metadata-only and descriptor-driven, with no raw content reads.
- Session turns must remain labeled best-effort until a first-class session history contract lands.
- Observer Replay must be read-only and link to existing Ledger, Attachments, and Chat surfaces.
- Runtime Activity destructive controls should not expand in this task; product-boundary follow-up remains in `0150`, `0195`, and `0196`.

## Suggested implementation
- Update `_best_effort_session_turns(...)` to use `list_run_index(session_id=..., root_only=True)` when available, falling back to the existing bounded scan.
- Add small Runtime helpers to serialize bounded artifact summaries from `ArtifactMetadata` without loading content.
- Include `artifacts` on each ledger entry in the bundle and on each session turn.
- Add Observer state for `history_bundle` replay loading/caching.
- Add a `Replay` tab between `Timeline` and `Ledger` with session turns, timeline events, artifact chips, and navigation actions.

## Scope
- Runtime history bundle export.
- Focused Runtime tests for indexed session turns and artifact replay summaries.
- Observer Replay tab UI and TypeScript build coverage.
- Backlog completion record.

## Non-goals
- Do not implement full replay chat, wait answer chat handoff, or canonical Session -> Turn -> Run tree in this task.
- Do not make Observer the source of artifact meaning.
- Do not fetch raw artifact content for replay summaries.
- Do not move admin, process, or launch surfaces in this task.

## Dependencies and related tasks
- `docs/adr/0036-artifact-descriptor-contract.md`
- `docs/backlog/planned/gateway-control-plane/0150_observer_manager_responsibility_split.md`
- `docs/backlog/proposed/runtime-artifact-observability/0195_observer_wait_replay_chat_session_handoff.md`
- `docs/backlog/proposed/runtime-artifact-observability/0196_observer_session_turn_runtime_hierarchy.md`
- `docs/backlog/completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md`
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`
- `docs/backlog/completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md`

## Expected outcomes
- A selected run can be replayed from one Observe tab using run/session/timeline/artifact metadata.
- Session turns use indexed runtime discovery when available.
- Artifacts created by runs are visible in replay context without raw content access.
- Observer has a clearer observability-first path while larger session/chat/admin questions stay parked as backlog.

## Validation
- Runtime history bundle tests cover artifact summaries and indexed session turn discovery.
- Observer focused tests/build pass.
- Browser smoke check confirms the Replay tab renders and is not blank.
- `git diff --check` passes.

## Progress checklist
- [x] Patch Runtime history bundle.
- [x] Patch Observer Replay tab.
- [x] Validate with tests/build/browser.
- [x] Move item to completed with implementation and validation evidence.

## Completion report

### Implementation
- `abstractruntime.history_bundle` now serializes bounded descriptor-driven artifact summaries into each run ledger bundle and each best-effort session turn. The summaries include artifact ids, content type, size/time, tags, descriptor, structured metadata, and access stats without loading artifact content.
- `history_bundle(include_session=true)` now prefers `RunStore.list_run_index(session_id=..., root_only=True)` when available and falls back to the older bounded `list_runs(...)` scan for compatibility.
- `abstractobserver` now has an Observe `Replay` tab between Timeline and Ledger. It loads `history_bundle` with subruns, session turns, and a bounded ledger tail, then renders replay summary metrics, session turns, user requests, outcomes, a run timeline, artifact chips, and artifact metadata JSON.
- Runtime Activity no longer exposes direct inline cancel buttons. It routes users to Observe, Ledger, Logs, and Artifacts so the monitor remains observational while cancellation remains available in the full run context.

### Validation evidence
- `cd abstractruntime && /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest tests/test_run_history_bundle.py -q` passed: 4 tests.
- `cd abstractobserver && npm test -- --run src/ui/runtime_activity.test.ts src/ui/artifact_rendering.test.ts` passed: 13 tests.
- `cd abstractobserver && npm run build` passed with the existing Vite large-chunk warning.
- `cd abstractgateway && PYTHONPATH=src:../abstractruntime/src:../abstractcore/src:../abstractmemory/src:../abstractstorage/src:../abstractllm/src /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest tests/test_gateway_history_bundle_endpoint.py tests/test_gateway_artifacts_endpoint.py -q` passed: 5 tests.
- `git diff --check` passed.
- Chrome headless smoke rendered `http://127.0.0.1:3001/` to `/tmp/abstractobserver-replay-smoke.png` as a nonblank 1480x900 PNG and DOM output showed the new `Replay` tab in Observe.

### Review synthesis
- External research supported a mission-control style observability surface: runs/sessions/logs/artifacts/provider/tool events first, administration second.
- `$review` and `$uxreview` converged on a scoped read-only replay/session-context improvement rather than implementing the parked full replay chat or canonical session tree.
- The implementation deliberately keeps `0195` and `0196` proposed because answering waits through chat and building a durable Session -> Turn -> Run hierarchy require a larger contract decision.

### Residual risks and follow-up
- Session turns are still labeled best-effort and bounded. Promote `0196` when a canonical session-turn index is ready.
- The Replay tab is read-only. Promote `0195` before turning it into a chat/resume handoff.
- `0150` should still decide the long-term app boundary between Observer, Gateway Console, Manager, and high-trust process/admin pages.

## Guidance for the implementing agent
Keep the implementation narrow. Use the history bundle as the replay contract and label bounded/best-effort data honestly. If full chat replay, canonical session hierarchy, or admin/operate navigation becomes necessary, update the proposed backlog instead of implementing it here.
