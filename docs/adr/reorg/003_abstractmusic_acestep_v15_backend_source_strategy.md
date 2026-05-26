# ADR 003 — ACE‑Step v1.5 backend: source strategy (vendored vs runtime download)

## Status

Accepted — 2026-02-12; profile boundary clarified 2026-05-08 by ADR-0033

## Context

`abstractmusic` must run music generation **locally in-process** (no external server).  
ACE‑Step v1.5 is published as a Hugging Face checkpoint repo (`ACE-Step/Ace-Step1.5`) that includes:

- a custom Transformers model implementation (DiT) under the checkpoint subfolder
- a text encoder checkpoint (Qwen3 embedding)
- a VAE checkpoint (Diffusers `AutoencoderOobleck`)

This makes it possible to build a **minimal in-process pipeline** inside `abstractmusic` without depending on the upstream `ace-step/ACE-Step-1.5` application code (CLI/UI/server).

We need a strategy for how `abstractmusic` obtains that orchestration code while remaining:

- easy to install/use
- deterministic
- safe-by-default
- aligned with “no silent fallbacks”

## Options

### Option A — Vendor the HF custom Transformers modules into `abstractmusic`

Pros:
- Works offline after install (only model weights download remains).
- No runtime code download/trust prompts.
- Deterministic (we pin a snapshot of the HF weights/config).

Cons:
- Small repo bloat (a couple of `.py` files) and manual updates when upstream changes.

### Option B — Use Transformers `trust_remote_code=True`

Pros:
- No vendored code in repo (in theory).
- Easier updates by changing a pinned ref.

Cons:
- Requires network on first use.
- Executes downloaded code; requires explicit trust controls.
- **Not viable for ACE‑Step v1.5 as shipped**: Transformers only searches the repo root for custom modules, but ACE‑Step stores its custom modules inside the checkpoint subfolder (`acestep-v15-turbo/`), causing load failures.

## Decision

Implement a **native `abstractmusic` ACE-Step backend** that loads the required components directly from the Hugging Face repo and runs inference in-process.

The implementation ensures:

- model weights are stored in a user cache directory (never inside site-packages)
- any fallback is explicit (`#FALLBACK`)
- ACE‑Step custom model code is **vendored** (Apache-2.0) under `abstractmusic.vendor.*`, so we do **not** rely on `trust_remote_code`
- Transformers meta-init is handled explicitly: ACE‑Step runs quantizer setup during `__init__`, which is incompatible with `meta` tensors. The vendored model overrides `get_init_context(...)` to avoid meta initialization across Transformers v4/v5.
- The minimal quantizer implementation (MIT, derived from `vector-quantize-pytorch`) is vendored to avoid introducing an extra hard dependency (and transitive deps) into `abstractmusic`.
- revision pinning is supported for deterministic weights/config

## Consequences

- No vendoring of the upstream ACE-Step **application** repo is required for text-to-music generation.
- We vendor only the minimal HF custom Transformers modules needed to load the DiT checkpoint.
- `abstractmusic` provides configuration hooks for repo id, cache directory, revision pinning, and device/dtype selection.
- We will document Apple Silicon constraints and recommended flags (MPS, bf16 settings) per upstream.
- If AbstractMusic later splits its package profiles, ACE-Step belongs in an explicit local/heavy
  extra such as `abstractmusic[acestep]` or `abstractmusic[local]`, not in remote-light
  Gateway/Core defaults.

## Related

- ADR-0033: `../0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- ADR 002: `002_abstractmusic_inprocess_local_generation.md`
