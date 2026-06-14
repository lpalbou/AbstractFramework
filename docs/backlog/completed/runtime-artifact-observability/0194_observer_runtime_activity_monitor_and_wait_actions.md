# Planned: Observer runtime activity monitor and wait actions

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0018, ADR-0032
- ADR impact: Clarifies the Observer UI responsibility for run supervision while Gateway remains the run-control and authorization boundary.

## Context
Artifact browsing and runtime supervision are related but not the same workflow. A user who sees mysterious computation needs to answer: what is running, what is waiting, what failed, what needs my action, what generated artifacts/logs/provider calls, and how do I stop or resume it safely?

Observer already has run-control hooks, wait modals, and a Runtime activity component, but the experience is not yet specified as a coherent activity monitor. The backlog must prevent another UI pass that improves artifacts while leaving active computation hard to understand.

## Current code reality
- Gateway lists runs through `/api/gateway/runs` with status filters and bounded `limit` up to 500.
- Gateway accepts run commands through `/api/gateway/commands` for `pause`, `resume`, `cancel`, `emit_event`, `update_schedule`, and `compact_memory`.
- Observer has `RuntimeActivityConsole`, queue filters, search, sort, open-run/open-ledger/open-artifacts/open-logs/cancel hooks, and wait modals for tool approval and user input.
- Observer still counts and slices some runtime/activity data locally, and waiting-run context can be unclear when a wait has no explicit prompt or only raw diagnostics.
- Artifact counts in the activity view currently depend on locally loaded artifact rows, so they are not reliable at scale until Gateway stats/envelopes from `0191` are available.

## Problem
Users cannot supervise real computation if the Runtime tab only lists runs and artifacts. Waiting, running, failed, scheduled, cancelled, stale, and terminal states need clear queues, clear explanations, and safe actions. A user should not have to inspect raw JSON to know whether they need to answer a question, approve a tool, cancel a run, open a child workflow, or wait.

## What we want to do
Redesign Observer's Runtime Activity monitor and waiting-run workflows around actionable queues, readable blocked-run context, bounded/paginated data, and safe Gateway-backed run controls.

## Why
This is the direct answer to "I have a lot of computation right now and I have no idea where it comes from." Artifact Explorer explains outputs. Activity Monitor must explain live work and what to do next.

## Requirements
- Keep Runtime Activity separate from Artifact Explorer. Activity is for run supervision; Artifact Explorer is for artifact inventory and provenance.
- Default to a visible `Needs attention` queue that includes waiting, failed, long-running, stale, and blocked runs. Also expose `Waiting for me`, `Running now`, `Failed`, `Finished`, and `All runs`.
- Provide bounded run pages with visible pagination or virtualization. Do not silently slice the first 300 rows without explaining that more rows exist.
- If exact queue counts across more than one page are required, add Gateway run stats instead of presenting page-local counts as exact.
- Search by workflow, run id, session id, node, status, wait reason, error, provider/model when available, and recent ledger summary when available.
- Sort by attention priority, latest event, oldest event, longest duration, token usage, provider calls, artifact count, and workflow.
- Show row-level facts: status, workflow, root/child relation, current or blocking node, elapsed time, last event, calls/tokens, artifact count, wait reason, error summary, and stale/long-running indicators.
- Show detail-level context: run input, current wait, recent ledger events, generated artifacts, provider trace/log availability, child/subworkflow links, and copyable ids.
- Waiting-run UI must state what is expected: answer a user prompt, choose from choices, approve/reject a tool, wait for subworkflow, wait until a schedule/time, or unknown context requiring ledger review.
- Waiting-run UI must explain action consequences: submit resumes only this wait, approve/reject resolves the tool approval, cancel attempts to stop the whole workflow and prevent further work.
- Expose safe actions where authorized: open Observe, open ledger, open artifacts, open logs/provider traces, copy run id/session id/wait key, submit response, approve/reject tool call, pause/suspend, resume, and cancel/stop.
- Require confirmation for destructive or broad actions such as cancel/stop. Bulk actions are out of scope unless explicitly designed with selection and confirmation.
- Preserve accessibility: visible tabs/buttons, readable focus states, keyboard navigation, no ultra-thin tab affordances, and no action hidden behind unlabeled icons.

## Suggested implementation
1. Define a typed Activity run view model that separates status, attention reason, wait expectation, metrics, links, and action availability.
2. Add fixtures for waiting user prompt, waiting choices, tool approval, subworkflow wait, scheduled/until wait, running, long-running, failed, cancelled, and completed runs.
3. Redesign the Runtime Activity layout around queues, a dense sortable run table, and a selected-run detail/action panel.
4. Wire Gateway-backed run controls through existing command submission and make success/failure visible in the row/detail state.
5. Replace page-local exact-looking counts with Gateway stats or explicit fetched-count labels.
6. Use `0191` artifact stats/envelopes for artifact counts and artifact links when available; until then label artifact counts as best effort.
7. Add browser QA for desktop and narrow viewports with several hundred mocked runs.

## Scope
- `abstractobserver` Runtime Activity monitor, wait modals/panels, run queue filters, run detail/action panels, tests, and browser QA.
- Minimal Gateway run stats/query additions if exact queue counts or server-backed activity filters are needed.
- Integration hooks to canonical artifact counts/links once `0191` is available.

## Non-goals
- Do not move run-control authority into Observer.
- Do not expose raw provider logs or prompt payloads without redaction and authorization.
- Do not implement delete/export/admin cross-user runtime management here.
- Do not make Activity responsible for artifact classification or provenance.
- Do not ship bulk destructive actions in this item.

## Hard dependencies
- Existing Gateway run list and command APIs.
- Existing Observer wait extraction and run-control plumbing.

## Related and follow-on tasks
- `docs/backlog/completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md`.
- `docs/backlog/completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md`.
- `0193_runtime_artifact_coredoc_and_explore_skill.md`.
- `docs/backlog/proposed/gateway-control-plane/0151_runtime_explorer_contract.md`.

## Expected outcomes
- Users can immediately identify which runs need attention and why.
- Waiting runs explain the requested action in human terms before showing diagnostics.
- Users can safely stop/cancel waiting or running workflows from Runtime Activity.
- Running and failed runs expose useful next actions: open Observe, ledger, artifacts, logs/provider traces, and copy ids.
- Large run lists remain bounded, searchable, sortable, and honest about count precision.

## Implementation completed
- Added `abstractobserver/src/ui/runtime_activity.ts` as the typed run-supervision view model for attention queues, terminal status handling, wait-kind classification, expected-action copy, search, and sort.
- Reworked Runtime Activity into explicit queues: Needs attention, Needs my response, Tool approvals, Running, Failed, Scheduled/subflows, Finished, and All loaded.
- Replaced large stacked run cards with a dense keyboard-selectable table plus selected-run detail/action panel.
- Added readable wait context: the selected run explains the blocker, expected action, request text when available, tool names/risk labels, and raw wait payload behind a shared JSON viewer.
- Kept sensitive wait resolution in Observe, where the run ledger and existing response/approval modals provide context. Runtime Activity routes user-response/tool-approval rows to Observe and exposes direct cancel/stop, ledger, artifacts, logs, and copy-id actions.
- Added explicit loaded-page count language instead of presenting local counts as global totals.
- Added gateway-offline states, reconnect/settings actions, visible focus rings, and responsive layout safeguards for Runtime Activity and Artifact Explorer controls.

## Validation
- `npm test -- --run src/ui/runtime_activity.test.ts`
- `npm test -- --run src/ui/artifact_rendering.test.ts`
- `npm run build`
- Chrome/headless smoke of the Runtime page with gateway offline states. Image artifact contents were not inspected; only UI structure and metadata/search affordances were reviewed.

## Progress checklist
- [x] Add Activity run view model and fixtures.
- [x] Redesign queues, table, detail panel, and visible actions.
- [x] Improve waiting-run explanation and action consequences.
- [x] Wire safe Gateway run controls with visible results.
- [x] Add bounded pagination or virtualization and honest counts.
- [x] Link Activity to canonical artifact counts/details when `0191` is available.
- [x] Add tests and browser QA.

## Residual follow-up
- A future Gateway run-stats endpoint can make Activity queue counts exact across the whole runtime instead of the loaded run page.
- Direct approve/reject/submit inside the Runtime table remains intentionally deferred; the current design opens Observe so the user sees ledger context before resolving the wait.

## Post-completion refinement: 2026-06-06
- Runtime Logs now separates selected-run ledger records, selected-run provider calls extracted from `llm_call` ledger effects, and global Gateway HTTP audit. Gateway audit is explicitly labeled as global system activity rather than artifact or run provenance.
- Runtime Activity row actions now include direct Logs routing for the selected run, sharing selected run/session context with the Runtime tabs.
- Waiting-run modals show an inferred-context warning when the runtime only emits a generic prompt such as "Please respond", keep recent workflow steps visible, and explain that submitting should happen only when the visible request is clear.
- Fresh Observer settings default the Gateway URL to `http://127.0.0.1:8080` so local Gateway discovery is explicit on a clean browser profile.

## Guidance for the implementing agent
Design from the user question: "What is happening right now, why is it blocked or expensive, and what can I safely do?" Keep the Activity monitor operational and dense. Do not turn it into a second artifact explorer, and do not hide critical run actions behind raw JSON or tiny tab affordances.
