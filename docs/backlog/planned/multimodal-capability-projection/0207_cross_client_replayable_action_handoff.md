# Planned: Cross-client replayable action handoff for gateway-first apps

## Metadata
- Created: 2026-06-14
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0035, ADR-0036
- ADR impact: May revise the ADR introduced by `0201_gateway_action_descriptor_contract.md` if replay-visible action facts need durable contract language.

## Context
AbstractFramework's higher-level apps are supposed to be lightweight viewers/players/command
senders over Gateway and Runtime truth. A session or task started in one app should be replayable
in another app even if formatting and emphasis differ.

That requires more than shared artifacts. If one app chose a typed capability action and another app
later replays the run, the second app should not have to guess from prompt text alone whether the
agent selected `generate_image`, `image_to_video`, `generate_sound`, or a governed workflow.

## Current code reality
- `abstractruntime/src/abstractruntime/history_bundle.py` is already explicitly client-agnostic and replay-first, but it does not yet expose a first-class typed action summary.
- `abstractobserver` already consumes history bundles and ledger replay as the read-only replay contract.
- `abstractcode/web` and `abstractassistant` already reconstruct live state from Gateway replay plus SSE rather than from local orchestration state.
- `abstractgateway/src/abstractgateway/console.py` Sandbox UI is lightweight, but today keeps browser-local transcript state and uses smoke-test-oriented direct generation paths rather than a shared replayable run contract.
- Runtime artifact descriptors already preserve rich provenance for outputs, but action choice/policy context is weaker than artifact provenance today.

## Problem
Without a replayable action handoff, capability awareness is only partially durable:

- the live client may know what the agent could do now;
- the final run may show which artifact was produced;
- but another client may not know which typed action was selected, why that policy path applied, or
  whether the result came from a direct action versus a higher-order workflow.

That weakens the gateway-first model because each app is pushed toward inventing its own semantic
explanation layer instead of projecting the same durable action facts into app-specific views.

## What we want to do
Make selected actions and normalized capability intent durable enough that any gateway-first app can
replay the decision context from shared history rather than inferring it from UI-local state or raw
prompt prose.

## Why
- Cross-app continuity is a core framework promise, not a cosmetic enhancement.
- Observer, Code Web, Assistant, Flow replay surfaces, and future thin apps should all be able to
  explain what happened from the same durable handoff contract.
- This is the missing link between live capability discovery and long-lived agent self-awareness.

## Requirements
- Record replay-safe action facts in Runtime/Gateway history:
  - selected `action_id`;
  - normalized family/modality/task;
  - normalized request/output summary;
  - resolved-route summary;
  - requested-override summary and override disposition when relevant;
  - policy class;
  - source-role summary;
  - whether execution resolved to a direct canonical action or a published workflow/composite;
  - bounded delegation-chain summary for workflow/composite or super-agent paths.
- Reuse the bounded decision snapshot from `0202` rather than forcing each client to invent its
  own action/workflow context cache.
- Keep the replay contract bounded and JSON-safe; do not dump full live discovery payloads into run
  history.
- Reuse existing history bundle and ledger patterns rather than inventing a UI-specific replay API.
- Ensure apps can render these facts differently without changing their meaning.
- Preserve app-local replay projection helpers such as chat seeding, trace panels, approval
  widgets, and artifact previews as consumers of the shared handoff; this item removes semantic
  guesswork, not client-side presentation logic.
- Distinguish durable action facts from client-owned convenience state such as local transcript
  layout, dedup, truncation, and transport-specific message shaping.
- Decide and document the Sandbox boundary:
  - either keep it explicitly non-durable as a smoke-test surface;
  - or add a run-backed mode when continuity/replay matters.

## Suggested implementation
1. Extend Runtime action-resolution output or ledger metadata with replay-safe action summaries and
   normalized request/output summaries.
2. Extend Gateway history/replay projection so those summaries and decision-snapshot fragments are
   available to thin clients.
3. Add consumer adapters for Observer replay and at least one live client, proving that clients can
   keep their own view models while dropping prompt-only or route-taxonomy inference for action
   meaning.
4. Make Sandbox durability status explicit in docs and discovery so it does not masquerade as a
   replayable agent surface if it is still smoke-test-only.

## Scope
- Runtime/Gateway replay-visible action metadata.
- History bundle or equivalent replay projection updates.
- Cross-client rendering guidance for lightweight apps.

## Non-goals
- Do not make every client render the same UI.
- Do not serialize full prompt/router internals or large capability snapshots into history by
  default.
- Do not turn Observer into an orchestration owner.
- Do not eliminate bounded client-side replay shaping or chat-history seeding that sits above the
  shared replay contract.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0202_gateway_replayable_session_and_action_envelope.md`
- `0204_runtime_capability_intent_resolution_and_policy.md`
- `docs/backlog/completed/runtime-artifact-observability/0198_observer_observability_replay_workbench.md`

## Expected outcomes
- A run started in one gateway-first app is explainable in another without UI-local action
  reconstruction or prompt-only intent guessing.
- Capability-aware decisions become durable and inspectable rather than ephemeral prompt behavior.
- Lightweight apps stay lightweight because the shared replay contract becomes richer.

## Validation
- Runtime/Gateway tests verify action summaries appear in replay-safe history and stay bounded.
- Observer or another replay consumer can render action summaries without extra inference.
- Documentation labels Sandbox replay semantics honestly.

## Progress checklist
- [ ] Define the minimal replay-safe action summary shape.
- [ ] Persist action summaries through Runtime/Gateway history surfaces.
- [ ] Add replay-consumer coverage for at least one read-only app and one live app.
- [ ] Clarify Sandbox durable vs smoke-test behavior in docs/discovery.

## Guidance for the implementing agent
Do not overfit this to one UI. Start from the strongest version of the invariant: another app should
be able to explain what capability ran without reverse-engineering the first app's routing logic.
