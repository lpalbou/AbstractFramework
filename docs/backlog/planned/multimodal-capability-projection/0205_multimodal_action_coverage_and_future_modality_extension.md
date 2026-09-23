# Planned: Multimodal action coverage and future modality extension

## Metadata
- Created: 2026-06-14
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0035, ADR-0036
- ADR impact: May revise the ADR introduced by `0201_gateway_action_descriptor_contract.md` if future modality naming or task-vs-modality rules need durable clarification.

## Context
The current route taxonomy already reaches beyond today’s public action surfaces. Some gaps are
already visible:

- `text_to_audio` exists under current music/audio generation plumbing, but the public surface is
  still centered on `generated_music`.
- `voice_clone` appears in some Gateway-side capability hints but is not yet a uniformly callable
  route-backed action.
- `scene3d` already exists in route taxonomy/model-capability mapping, but it is not yet surfaced
  as a real projected action family.

This item is the parity and forward-compatibility pass after the lower-level Core `request/output`
contract and the Gateway action projection contract exist.

## Current code reality
- `docs/adr/0035-capability-routing-defaults.md` already defines routes like `output.sound`, `output.music`, and `output.scene3d`.
- `abstractcore/abstractcore/config/capability_defaults.py` and `abstractcore/abstractcore/providers/model_capabilities.py` already carry `scene3d`.
- `abstractgateway/src/abstractgateway/routes/gateway.py` already accepts `text_to_audio` through current music/audio generation plumbing.
- Assistant already routes to `sound` in `abstractassistant/abstractassistantv2/assistant_workflow.py`, while Flow remains more image/video/music-centric in its first-class node surfaces.

## Problem
If the action surface is introduced without a parity pass, today’s gaps and soft hints will turn
into long-lived product inconsistencies. New modalities such as `scene3d`, characters, and
environments will then repeat the same drift.

## What we want to do
Close current action coverage gaps and define the extension rules for future modalities/tasks so
new capabilities appear through the same projection pipeline rather than through ad hoc client work.

## Why
- `generate_sound` should not stay hidden behind `generated_music` if the underlying route already
  supports it.
- Soft hints like `voice_clone` should not be projected as callable actions until route-backed
  truth exists.
- Future modality growth should be deliberate: `scene3d` likely deserves a top-level family, while
  characters and environments should start as tasks or semantic kinds unless evidence says
  otherwise.
- Cross-client parity depends on these concepts being projected once through shared Gateway truth,
  not rediscovered differently by each UI/app.

## Requirements
- Expose distinct typed actions for currently supported capability/task combinations such as
  `generate_sound` where the route truth supports them.
- Refuse to project actions from soft hints alone; only route-backed callable truth should surface
  as model-facing actions.
- Require new modality/task families to land first in the lower-level Core `request/output`
  vocabulary and route-default truth before Gateway projects them as durable actions.
- Define the first-class action-family rule for `scene3d`.
- Define the default growth rule that characters/environments begin as tasks, profiles, or
  semantic kinds under an existing modality before being promoted to top-level families.
- Keep artifact descriptor semantics aligned with any new family/task projection.

## Suggested implementation
1. Audit current route-capability truth against projected actions and identify missing or
   overclaimed actions.
2. Add parity fixes for current gaps such as sound-generation coverage.
3. Add extension rules and tests for future modality families/tasks before exposing them to clients.
4. Add docs/examples showing how new modalities should be introduced across Core request/output
   semantics, Gateway action projection, Runtime lowering, and thin clients without inventing
   app-local capability semantics.

## Scope
- Current action coverage parity.
- Future modality/task projection rules.
- Discovery/tests/docs for newly surfaced action families or guarded placeholders.

## Non-goals
- Do not expose experimental actions just because a UI control or provider hint mentions them.
- Do not create top-level modalities for every semantic domain immediately.
- Do not add `scene3d` execution paths without route-backed/Core-backed evidence.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0203_flow_action_descriptor_alignment.md`
- `docs/backlog/completed/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md`
- `docs/backlog/proposed/multimodal-capabilities/0176_multimodal_model_acquisition_guidance.md`

## Expected outcomes
- The public action surface covers current real capability combinations more faithfully because new
  capability families extend one Core vocabulary before they project outward.
- Future modality additions follow one documented projection rule rather than per-client invention.
- Thin-client parity improves for sound and future modalities because all clients read one Gateway
  truth instead of maintaining private capability maps.

## Validation
- Discovery tests verify route-backed actions are projected and soft-hint-only actions are not.
- Client tests verify sound and future-modality placeholders stay in sync with Gateway truth.
- Documentation explains when a new concept is a task/profile versus a new top-level family.

## Progress checklist
- [ ] Audit current route/action parity.
- [ ] Add `generate_sound` or equivalent parity coverage if route truth supports it.
- [ ] Document/prove `voice_clone` readiness rules.
- [ ] Define `scene3d` and future modality extension rules.
- [ ] Add parity tests across Gateway discovery and multiple thin-client consumers.

## Guidance for the implementing agent
Do not guess future modality semantics from marketing names. Start from current route truth, Core
request/output vocabulary, artifact semantics, and task requirements. Promote new concepts to
top-level families only when the provider/model/discovery surface genuinely needs that boundary.
