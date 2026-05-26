# ADR 002 — AbstractMusic generates locally in-process (Diffusers backend)

## Status

Accepted — 2026-02-12; profile boundary clarified 2026-05-08 by ADR-0033

## Context

Users expect symmetry across modality packages:

- `abstractvoice` generates audio locally (TTS/STT)
- `abstractvision` can generate locally (Diffusers / stable-diffusion.cpp)

For music generation, requiring an always-on external server (even if self-hosted) breaks the “install → generate” mental model and complicates local/offline workflows.

We also want to keep AbstractCore lightweight by default, so music generation must remain an **optional capability plugin**.

## Decision

- `abstractmusic` will provide **in-process local generation** as the default execution mode.
- Default backend will be **ACE-Step v1.5** (local, in-process), producing **WAV bytes**.
- An alternative backend will remain available via **Diffusers audio pipelines** (checkpoint-dependent capabilities and licensing).
- `abstractmusic` registers an AbstractCore capability plugin backend under `abstractcore.capabilities_plugins`, exposing:
  - `llm.music.t2m(prompt, ...) -> bytes | {"$artifact": ...}`

This decision applies to explicit AbstractMusic/local-profile use. It does not mean Music belongs
in remote-light AbstractCore or AbstractGateway defaults while its base install pulls local
Torch/Diffusers/ACE-Step dependencies.

## Rationale

- **Consistency**: matches the “local generation” pattern of AbstractVoice and the local backends of AbstractVision.
- **No mandatory daemon**: avoids requiring a long-running server process for basic usage.
- **Pluggability**: keeps open the option to add additional backends later (including ACE-Step) without changing the AbstractCore surface.

## Consequences

- Installing `abstractmusic` becomes heavier (torch + diffusers stack), similar to `abstractvision`.
- Model weights may still need to be downloaded (Hugging Face cache) the first time a model is used.
- MP3 output is not guaranteed without external codecs; WAV is the baseline.
- Gateway/Core remote-light profiles should keep Music opt-in until `abstractmusic` has a
  lightweight base split or a real remote music backend contract.

## Alternatives considered

- **ACE-Step API server as default**:
  - rejected as default due to mismatch with “install → generate locally” expectation; can remain an optional backend later.

## Related

- ADR-0033: `../0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- Proposed Music profile boundary:
  `../../backlog/proposed/2026-05-08_music_install_profile_boundary.md`
