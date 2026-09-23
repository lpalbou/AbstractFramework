# Planned: Gateway replayable session and action envelope for cross-app thin clients

## Metadata
- Created: 2026-06-14
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0033, ADR-0035, ADR-0036
- ADR impact: May revise the new ADR introduced by `0201_gateway_action_descriptor_contract.md` if the replay envelope needs new durable action/session vocabulary.

## Context
The user clarified a non-negotiable requirement: a task started in one Gateway-native app should be
replayable in another app, even if each app renders it differently.

That means the durable surface cannot stop at “available actions”. Gateway also needs a portable
session/action envelope that lets thin clients reconstruct:
- the user turns and assistant turns that matter for the task;
- the bounded capability/workflow affordance set that mattered at decision time;
- the policy/budget class that applied;
- which action or workflow was selected;
- what normalized `request` and `output` shape actually mattered at decision time;
- which source artifacts were used;
- which tool approvals or waits occurred; and
- which artifacts or outputs were produced.

## Current code reality
- `abstractgateway/src/abstractgateway/routes/gateway.py` already exposes `/runs/{run_id}/history_bundle` as a Runtime-owned replay contract intended for thin clients.
- Runtime `history_bundle` already exports root run metadata, descendant run ledgers with absolute
  cursors, timeline rows, workflow snapshot refs, session turns, and replay artifact summaries.
- Runtime artifact descriptors already preserve workflow/node/turn/cursor/provenance/source-ref
  fields used by replay and observability.
- `abstractassistant` replays `history_bundle` and `ledger/stream` into its chat view.
- `abstractcode/web` already seeds chat replay from `history_bundle` and separately replays session-memory ledger to restore durable voice events.
- `abstractobserver` already loads replay bundles for read-only reconstruction of run and session context.
- Each app still performs some local seeding/projection logic, so the missing piece is a shared
  semantic replay projection for action/workflow awareness rather than a new base replay substrate.

## Problem
`history_bundle` already provides the durable replay substrate for run state, ledgers, waits,
artifacts, timeline, session turns, and workflow snapshot refs. The missing contract is a small
Gateway projection for cross-app action/workflow replay: first-class `workflow_ref`/version,
subworkflow edge export, normalized request/output summary, resolved-route summary, override
disposition summary, policy class, and selected action/workflow summary.

## What we want to do
Define a versioned replayable session/action envelope, likely built on top of the Runtime
`history_bundle` contract, so Gateway-native apps can reconstruct and continue the same work across
different UIs without inventing their own chat/action translation layers.

## Why
- Cross-app continuity is one of the framework’s core promises.
- Capability awareness is incomplete if the selected action/workflow is not replayable in a
  portable way.
- Thin clients should be viewers/players over one durable history contract, not local state
  machines with private replay semantics.

## Requirements
- Keep Runtime’s append-only ledger and `history_bundle` as the authoritative substrate.
- Add or normalize a Gateway-owned portable envelope that captures session turns, action/workflow
  selections, source artifact refs, waits, approvals, and produced artifacts with stable IDs.
- Reuse existing `run_id`, `step_id`, `artifact_id`, and ledger cursor anchors. Introduce new IDs
  only for Gateway-projected decision records such as `decision_id` or `selection_id`.
- Preserve a bounded decision snapshot:
  - capability/action/workflow affordances actually shown to the run;
  - selected action/workflow identity;
  - `workflow_ref` when known (`workflow_id`, `bundle_id`, `bundle_version`, snapshot artifact ref);
  - applicable policy or budget class;
  - normalized request summary;
  - normalized output summary;
  - resolved-route summary;
  - requested override summary and override disposition when relevant;
  - source-artifact/context-role summary;
  - subworkflow/delegation edge summary when a workflow or super-agent run delegates to child
    actions/workflows.
- Preserve enough structure for apps to render different views without losing the meaning of the
  underlying work.
- Make the envelope compatible with action/workflow descriptors from `0201`.
- Ensure cross-app replay works without requiring each app to infer “what happened” from local
  heuristics.
- Keep transport/tool-noise filtering explicit and documented rather than hidden in each client.

## Suggested implementation
1. Audit `history_bundle`, session-turn export, and ledger records against the needs of action and
   workflow replay.
2. Add a normalized action/workflow replay projection where needed, but keep Runtime as the source
   substrate.
3. Define stable portable IDs and envelope fragments for turns, decision snapshots, normalized
   request/output summaries, resolved-route summaries, requested-override summaries,
   route-provenance summaries, selections, bounded delegation chains, waits, approvals, artifacts,
   and outputs.
4. Document which parts are Gateway-owned projections versus raw Runtime exports.
5. Add cross-app replay tests using at least two different clients over the same run/session.

## Scope
- Gateway/Runtime replay envelope design and tests.
- Cross-app portable session/action reconstruction semantics.
- Documentation for thin-client replay and handoff behavior.

## Non-goals
- Do not make one UI’s chat layout the canonical replay format.
- Do not duplicate the ledger into a second durable history store.
- Do not put replay responsibility into app-local glue when the contract can be shared.
- Do not replace Runtime session turns or artifacts with a second replay store.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0204_runtime_capability_intent_resolution_and_policy.md`
- `0207_cross_client_replayable_action_handoff.md`
- `docs/backlog/proposed/runtime-artifact-observability/0195_observer_wait_replay_chat_session_handoff.md`

## Expected outcomes
- Work started in one Gateway-native app can be replayed and continued in another without semantic
  loss.
- Action/workflow selections and normalized request/output intent become part of the portable
  durable story, not only of the live UI.
- Expert users and operators can audit whether a modality used the ambient default route or a
  temporary one-off override without reopening the originating client.
- Capability awareness becomes replayable because another app can inspect the bounded decision
  snapshot instead of guessing from prompt prose or app-local state.
- App-specific replay heuristics shrink because Gateway owns more of the projection contract.

## Validation
- Cross-app tests verify the same run/session can be reconstructed in multiple clients from the
  shared envelope.
- Replay tests verify actions, waits, approvals, and artifacts survive handoff without app-local
  inference.
- Docs clearly state which contract pieces belong to Runtime, which to Gateway projection, and
  which remain app-local presentation.

## Implementation note - 2026-06-15

The envelope work now has a first Runtime-owned substrate improvement:

- `history_bundle` exports `resolved_actions`, a bounded action summary list derived from Runtime
  ledger records and Core route metadata.

That is not the final Gateway replay envelope yet. Gateway still needs to decide how to project
decision snapshots, workflow references, and cross-client handoff metadata over the Runtime
history substrate.

## Progress checklist
- [x] Audit current `history_bundle` and session-turn portability gaps.
- [ ] Define the portable session/action envelope, bounded decision snapshot, and stable IDs.
- [ ] Add Gateway projection/tests for action/workflow replay metadata.
- [ ] Verify at least two different thin clients can replay the same work faithfully.

## Guidance for the implementing agent
Treat replay portability as a contract problem, not a widget problem. Reuse Runtime history where
possible, but make Gateway own the additional projection needed for cross-app action/workflow
reconstruction.
