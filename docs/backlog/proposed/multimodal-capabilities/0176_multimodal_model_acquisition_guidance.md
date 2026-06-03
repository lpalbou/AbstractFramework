# Proposed: Multimodal model acquisition guidance

## Metadata
- Created: 2026-06-02
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0033, ADR-0035
- ADR impact: None expected unless installer/profile policy changes.

## Context
Gateway Console now makes multimodal capability defaults visible and editable.
That is useful only after users have providers configured and, for local
execution, the needed models downloaded or loaded.

The user's current defaults are reasonable for a powerful Apple/local setup:

- `input.text`: LM Studio `qwen/qwen3.6-35b-a3b`
- `input.image`: covered by text
- `input.video`: covered or overrideable by text/video model
- `input.voice`: `faster-whisper` `large-v3`
- `output.image`: `mlx-gen` `AbstractFramework/ernie-image-turbo-4bit`
- `output.video`: `mlx-gen` `Wan-AI/Wan2.2-TI2V-5B-Diffusers`
- `output.voice`: `supertonic` `supertonic-3`
- `output.sound`: `stable-audio` SFX model
- `output.music`: `stable-audio-3` music model
- `embedding.text`: LM Studio embedding model

For a new user, however, installing and loading these models is still too
implicit.

## Current code reality
- Capability defaults do not install providers or download models.
- Gateway Console can configure provider connections and route defaults.
- Flow and Gateway can show residency/load status for some local media tasks,
  but model acquisition is provider/package-specific.
- Framework install profiles distinguish Light, Apple, and GPU; CPU local
  inference remains proposed in `0163_cpu_local_inference_install_profile.md`.
- `abstractframework doctor` and install manifest work exists, but it does not
  yet guide users through multimodal model acquisition by route.

## Problem or opportunity
Users need a guided way to go from "I want text/image/video/voice/music/SFX" to
"the required local or remote model is configured, downloaded if needed, and
smoke-tested".

## What we might do
Create a model acquisition and readiness layer that maps route defaults to
provider-specific setup actions.

## Why
Capability configuration is not enough. A new user should not need to know
which Hugging Face repository, LM Studio model, MLX model, Whisper model, or
Stable Audio package to install for each route.

## Requirements
- Keep model acquisition separate from capability defaults.
- Provide explicit user confirmation before downloading large local models.
- Show estimated size, hardware/profile compatibility, and expected runtime
  location.
- Support at least:
  - LM Studio / Ollama model presence checks.
  - Hugging Face / MLX model download hints.
  - AbstractVision / AbstractVoice / AbstractMusic package-backed local models.
  - Remote provider profiles that require no local download.
- Work from CLI first; Gateway Console can expose the same readiness actions
  later.
- Avoid making Qwen3-Omni 30B a hard default because it may exceed many
  machines' memory budgets.

## Suggested implementation
- Add a route/model recommendation manifest generated from package-owned
  metadata, not hand-maintained ad hoc UI strings.
- Extend `abstractframework doctor` or add `abstractframework models` to report:
  configured route, provider reachability, model discovered/loaded/downloaded
  state, and next action.
- Add provider-specific "how to acquire" hints rather than universal download
  commands when the provider owns installation.
- Add Gateway Console readiness badges and optional action links after the CLI
  contract is stable.

## Scope
- Proposed CLI/doctor/model-readiness design.
- Potential Gateway Console read-only readiness badges.
- Documentation for Light, Apple, GPU, and future CPU profiles.

## Non-goals
- Do not auto-install local inferencers in Light mode.
- Do not bundle large models into Python wheels or Docker images.
- Do not bypass provider tooling such as LM Studio's own model manager when it
  is the right operational surface.

## Promotion criteria
- At least one concrete user setup flow fails because model acquisition is
  confusing despite correct provider/default configuration.
- The route-specific capability taxonomy in `0175` lands or is close enough
  that readiness can depend on stable route names.
- Provider/package owners can expose enough metadata to avoid hard-coded,
  stale model download instructions.

## Validation ideas
- CLI dry-run against an empty machine/profile prints actionable next steps per
  route.
- CLI against the user's current Apple setup reports the configured models as
  available or explains exactly what is missing.
- Gateway Console can show readiness without storing extra state.

## Guidance for future agents
Keep this as onboarding/readiness, not defaults. Defaults say what route should
be used; acquisition says whether the selected provider/model is present and
how to make it present.
