# Proposed: CPU Local Inference Install Profile

## Metadata
- Created: 2026-05-31
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- ADR impact: May revise existing ADR

## Context
The current root install profiles are Light, Apple, and GPU. Light is remote-first and avoids local
inference stacks. Apple and GPU add hardware-local inferencer stacks. Modern desktop CPUs can run
some models locally, so a fourth CPU profile may be useful for users without Apple Silicon or a
discrete GPU.

## Current code reality
- Root `pyproject.toml` exposes only `apple` and `gpu` extras.
- `docs/install.md` documents Light, Apple, and GPU only.
- AbstractCore can use endpoint servers that may themselves run on CPU, such as Ollama,
  llama.cpp, LM Studio, or LocalAI, through the Light profile.
- Local in-process CPU support is not clearly audited across `abstractvoice`, `abstractvision`,
  `abstractmusic`, `abstractcore`, `abstractruntime`, `abstractagent`, and `abstractgateway`.

## Problem or opportunity
Some users may want local inference on CPU-only machines. This can be especially plausible for
text, embeddings, small STT/TTS, or small llama.cpp/Ollama workflows. However, CPU-local image,
video, and music generation can be extremely slow, dependency-heavy, or unsupported depending on
backend.

## Proposed direction
Evaluate a fourth `cpu` install profile before adding it:

- `abstractframework[cpu]` would mean local CPU inferencers, not endpoint-only Light.
- Each package must define what CPU local inference means and which backends are included.
- Text/embedding CPU paths should be considered first.
- Vision, video, music, and voice CPU paths require explicit performance and dependency warnings.
- Docs must keep Light distinct from CPU: Light uses endpoints; CPU installs local inferencer
  dependencies.

## Why it might matter
A CPU profile could help users on strong desktop CPUs, servers without GPUs, or machines where
GPU/Apple stacks are unavailable. It could also provide a more predictable "offline but slow"
path for basic text and embeddings.

## Promotion criteria
- Package-by-package audit identifies safe CPU backend choices.
- Dry-run installs show no accidental CUDA/MLX dependency pull.
- At least one practical text/embedding workflow works locally on CPU.
- Docs can set honest expectations for latency, model size, and unsupported modalities.

## Validation ideas
- Add dependency tests asserting `abstractframework[cpu]` does not pull CUDA/MLX packages.
- Run a CPU-only smoke workflow for text generation and embeddings.
- Run or explicitly skip voice, vision, video, and music CPU smoke tests with documented reasons.
- Verify `abstractframework doctor` can detect and explain the CPU profile separately from Light.

## Non-goals
- Do not implement CPU profile as an alias for Light.
- Do not promise fast image/video/music generation on CPU.
- Do not add CPU dependencies that make the default Light install heavy.

## Guidance for future agents
Start with evidence. CPU-local can be valuable, but only if the user can predict what works and
what will be painfully slow.
