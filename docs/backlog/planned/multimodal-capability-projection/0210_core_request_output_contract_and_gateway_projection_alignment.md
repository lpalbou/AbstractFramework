# Planned: Core request/output contract and Gateway projection alignment

## Metadata
- Created: 2026-06-14
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032 package dependency boundaries and gateway-first apps, ADR-0033 install profiles config entrypoints and server boundaries, ADR-0035 capability routing defaults, ADR-0036 artifact descriptor contract
- ADR impact: Should produce or revise the ADR introduced by `0201_gateway_action_descriptor_contract.md` so the stack is explicit: Gateway action/workflow descriptors project over Core request/output semantics and Runtime durable lowering, not over app-local routers or current transport details.

## Context
The framework now has a clearer two-entrypoint story:

- `abstractgateway` is the persistent high-level entrypoint for durable agents, workflows, replay,
  and cross-app continuity.
- `abstractcore` is the lower-level lighter entrypoint for direct SDK usage, the standalone Core
  server, and lightweight apps that do not need Gateway durability.
- `abstractruntime` is the only durable execution substrate.

Completed framework work already pointed toward the end-state `generate(request, output)` shape,
but the active multimodal track is still too anchored on the current compatibility kernel
`generate(..., output=...)` and on current transport adapters such as `media`, `attachments`,
`pending["media"]`, and action-family names.

If the track hardens Gateway descriptors and replay surfaces before it defines the lower-level
semantic contract, it will project implementation details instead of stable capability truth.

## Current code reality
- Root completed item `0139_unified_framework_capability_defaults.md` already records
  `generate(request, output)` as the intended end-state once defaults are complete.
- `abstractcore` already exposes public `generate(..., output=...)` and a public output-selector
  normalization contract.
- `abstractruntime` already lowers typed media helpers to canonical `LLM_CALL` execution using
  `output={modality, task}` plus source media/artifact refs.
- `abstractgateway` already builds rich capability contracts and direct media routes, but its
  action projection track still starts above the missing request/output layer.
- Default-route truth already exists, but it is fragmented: Core persists `CapabilityRouteDefault`
  rows, Gateway text helpers use `ProviderModelResolution`, Runtime decorates output specs with
  route dicts, and Core input fallbacks resolve defaults inline inside provider dispatch. There is
  still no single per-call route object created from defaults plus overrides and then passed
  through the whole execution path.
- Flow, agents, and thin clients already move artifact inputs through adapters such as
  `context.attachments` and `pending["media"]`, which are useful transports but not the desired
  long-term semantic vocabulary.
- Route resolution and override behavior still differ by topology today; the same requested
  generation can resolve differently in direct Core, local Runtime, remote Runtime, and server
  execution unless this contract owns one shared route-resolution path.

## Problem
The framework lacks one explicit lower-level multimodal contract that answers:

1. what a normalized input request is;
2. what a normalized generated output request is;
3. how current `prompt/messages/media/output` kwargs map into that shape;
4. how typed Gateway actions project over it; and
5. how Runtime persists resolved-action facts without inventing a second semantic layer.

It also lacks one explicit answer to a more operational question: when defaults exist but a caller
temporarily overrides one modality route for this call, what is the single route object that
records that decision and survives topology changes and replay?

Without that contract:
- Gateway descriptors risk hardening current transport details or action-family names too early;
- Core can keep accruing routing logic inside duplicated provider code paths;
- replay may preserve artifacts but not the normalized capability intent that produced them;
- topology-specific route resolution and override behavior can remain silent and drift-prone.

## What we want to do
Define the canonical lower-level `request/output` contract for multimodal generation and make the
projection boundary explicit:

- AbstractCore owns the request/output vocabulary, the internal call-scoped default-route merge
  contract, and request/output normalization.
- AbstractRuntime consumes that Core-defined route truth, persists a bounded resolved-route
  snapshot, and owns durable lowering to `LLM_CALL`.
- AbstractGateway may configure defaults and policy ceilings, but it does not define or own the
  route object; it projects over Core/Runtime truth.

## Requirements
- Define a canonical `request` shape for direct Core and Runtime use. The first stable public scope
  should stay small:
  - `text`
  - `messages`
  - `media`
- Keep provider/model/base URL/default selection outside `request`; those remain explicit kwargs
  plus Core/Gateway defaults.
- Define a first-class AbstractCore-level per-call route/default contract:
  - compatibility mapping from current explicit override fields into one route-resolution path;
  - one canonical merged route object produced in Core from capability defaults plus explicit
    compatibility overrides; and
  - one replay-safe resolved-route record derived from that object.
  - Gateway- or Runtime-supplied defaults may feed that merge, but do not redefine the object.
  - the resolved contract may include optional reasoning settings only when the selected
    model/route supports reasoning-capable execution; absent otherwise.
  - reasoning is part of route/default resolution metadata, not part of the semantic request
    payload.
  - preferred examples should use route keys such as `input.text`, `input.voice`,
    `output.image.text_to_image`, `output.video.image_to_video`, `output.voice`,
    `output.sound`, and `output.music`.
- Define a canonical `output` selector vocabulary that keeps modality separate from task and can
  represent at least:
  - `text`
  - `image`
  - `video`
  - `voice`
  - `music`
  - `sound`
  - future `scene3d`
- Define deterministic structural task-inference rules from `request` plus `output`, for example:
  - text request + `output=text` -> text generation;
  - text request + `output=image` -> text-to-image;
  - text request + `output=video` -> text-to-video;
  - text request + `output=music` -> text-to-music;
  - text request + `output=sound` -> text-to-audio/SFX;
  - text request + `output=voice` -> TTS;
  - image request + `output=image` -> image edit/upscale/generation according to roles/task;
  - image request + `output=video` -> image-to-video;
  - audio request + `output=text` -> transcription when structurally unambiguous.
- Preserve current text-only behavior and current multimodal response types as compatibility
  baselines.
- Define how current transports lower into this contract:
  - Flow `input_artifacts`;
  - Gateway run `attachments` / `media`;
  - Runtime `pending["media"]`;
  - Agent `context.attachments`.
- Define one shared resolved-route path across direct Core, local Runtime, remote Runtime, and
  server execution. Partial defaults may exist as configuration state, but they must not dispatch
  silently.
- Define one bounded derived route summary from that shared route object so Gateway descriptors,
  replay envelopes, and workflow/super-agent layers can consume execution truth without needing raw
  provider-topology data or direct route merging.
- Keep the public surface narrow in the first pass. Do not pass raw config payloads or Gateway
  discovery objects into `generate(...)`, and do not add a route object inside `request` or
  `output` yet. Normalize compatibility fields such as output-spec `provider/model` selectors,
  request-level text route pins, or input-specific override kwargs into the same internal route
  object first.
- Do not design a broad public per-call route override API in this item. Normalize existing
  compatibility selectors into the internal Core route object first.
- Only consider a small explicit override surface later if direct-Core evidence shows the
  compatibility normalization path is insufficient.
- If future direct-Core evidence justifies a structured temporary override surface, evaluate it as
  a separate non-durable advanced layer after the shared internal route object and topology-parity
  tests are stable.
- Keep text/input routing separate from output routing. Output-provider or endpoint-profile choices
  must not silently rewrite the call-global text route.
- Apply explicit override ceilings across topologies. Provider/model/base URL/profile overrides are
  either allowed and recorded or denied consistently.
- Define how Gateway action descriptors map to lower-level request/output schema fragments.
- Define how Runtime persists a replay-safe resolved-action record with normalized request/output
  summaries, resolved-route snapshot, selected action/workflow identity, source-role summary,
  policy class, and artifact lineage.
- Stage rollout explicitly:
  - first support a keyword `request=` public form and one internal normalizer;
  - only add positional `generate(request, output)` if direct-Core evidence justifies it and
    session/prompt-history compatibility is well understood.

## Suggested implementation
1. Write the request/output contract and ADR boundary before broad client migration.
2. Add one Core normalizer from current kwargs to canonical request/output plus a shared route
   override/resolution helper.
3. Define the first `ResolvedGenerateRoute` shape with explicit provenance:
   default source, compatibility alias source, explicit override source, topology, and denial
   reason when resolution fails.
4. Revise the Gateway action-descriptor item (`0201`) so descriptors map to request/output schema
   fragments instead of current transport-only fields.
5. Revise the Runtime action-resolution item (`0204`) so the canonical durable intent is described
   as `request + output + source bindings + execution hints`, with current `output={modality,task}`
   treated as the lowering detail.
6. Revise replay/handoff items (`0202`, `0207`) so they persist bounded normalized request/output
   summaries and resolved-route snapshots rather than only action IDs and artifact provenance.

## Scope
- Cross-package contract definition and ADR update.
- Backward-compat mapping from current Core kwargs and current runtime transports.
- Shared route-resolution and override-denial rules.
- Gateway/Runtime/Core backlog alignment and validation expectations.

## Non-goals
- Do not copy Gateway action/workflow descriptors into Core.
- Do not add a new durable execution primitive beside `LLM_CALL`.
- Do not make workflow IDs the base capability vocabulary for atomic generation.
- Do not force direct Core users to consume Gateway replay/policy semantics.
- Do not treat current transport fields like `pending["media"]` as the long-term semantic API.
- Do not add a public route object inside `request` or `output` in this item; that remains a
  separate follow-up question only if the internal route contract proves insufficient.
- Do not let route keys or resolved-route records become the default thin-client vocabulary.
  They are lower-level implementation artifacts and should surface to users only through bounded
  summaries or explicit inspection flows.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0202_gateway_replayable_session_and_action_envelope.md`
- `0204_runtime_capability_intent_resolution_and_policy.md`
- `0205_multimodal_action_coverage_and_future_modality_extension.md`
- `0207_cross_client_replayable_action_handoff.md`
- `../0179_llm_agent_model_input_artifacts.md`
- `../../proposed/0208_abstractcore_lightweight_capability_surface_boundary.md`
- `../../planned/0147_gateway_per_principal_config_secrets_defaults.md`
- `../../completed/0139_unified_framework_capability_defaults.md`
- `../../completed/0172_explicit_multimodal_default_fallback_routing.md`

## Expected outcomes
- The framework gets one explicit lower-level multimodal contract instead of projecting current
  transport details outward.
- Gateway action/workflow descriptors become generated projections over Core and Runtime truth.
- Runtime replay can preserve capability intent honestly without inventing a second semantic layer.
- Direct Core users get a clearer path toward `generate(request, output)` while Gateway-first apps
  stay thin viewers/players/command-submitters over durable runs.
- Topology-specific route drift becomes a contract bug instead of an accepted implementation detail.
- The stack gains one clear internal temporary-override path, with any future public override
  surface intentionally deferred and kept narrow.
- Durable workflows and future super-agent planners get one stable route-truth substrate to
  consume through Gateway/Runtime summaries instead of inventing their own routing heuristics.

## Validation
- ADR text clearly explains the stack: Gateway descriptors -> Core request/output -> Runtime
  resolved-action record -> `LLM_CALL` lowering.
- Backlog and docs no longer disagree about whether `generate(..., output=...)` is the end-state or
  the compatibility baseline.

## Implementation note - 2026-06-15

The first Core/Runtime implementation wave is in:

- Core now has a public keyword `request=` path, an internal normalized `GenerateRequest`, and a
  shared call-scoped `ResolvedGenerateRoute`.
- capability defaults can carry an optional `reasoning` value for reasoning-capable text routes.
- Runtime now persists bounded `_runtime_resolved_action` summaries derived from Core route
  metadata and exports them through `history_bundle["resolved_actions"]`.

Gateway descriptor projection, cross-client replay envelopes, and client taxonomy cleanup remain
open follow-ups on top of that substrate.
- Cross-package tests added by follow-up items prove several typed Gateway actions normalize to the
  same request/output and `LLM_CALL` path across direct Core, local Runtime, remote Runtime, and
  server execution.
- Cross-package tests prove the same temporary modality override resolves to the same route object
  and the same effective execution across those topologies, or is rejected consistently.

## Progress checklist
- [ ] Define the canonical request/output vocabulary and structural inference rules.
- [ ] Define the shared per-call route object, merge rules, and temporary override contract.
- [ ] Define the backward-compat mapping from current Core kwargs and runtime transports.
- [ ] Define shared resolved-route and override-denial rules.
- [ ] Land the ADR boundary tying Gateway projection to Core/Runtime truth.
- [ ] Align `0201`, `0202`, `0204`, `0205`, `0207`, and `0179` with the contract.
- [ ] Use this contract as the prerequisite for broader client migrations.

## Guidance for the implementing agent
Keep the contract narrow. The point is not to re-create Gateway inside Core or to re-create Core
inside Runtime. Core should own the lightweight semantic vocabulary, Runtime should own the durable
record and lowering, and Gateway should own the high-level projection and policy filtering. Fail
closed on partial routes, silent output-route rewrites, and override paths that differ by topology.
Do not thread a mutable defaults/config blob through `generate(...)`; build one small per-call
route object and a redacted resolved-route record instead.
