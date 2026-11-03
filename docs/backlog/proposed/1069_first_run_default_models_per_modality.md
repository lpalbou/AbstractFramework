# 1069 — First-run guide: "Default models" per modality, recommended by VRAM/RAM, and a subscription path

> Package: abstractgateway (console wizard), abstractcore (recommendation data)
> Type: task
> Created: 2026-10-28
> Priority: high
> Labels: first-run, models, recommendations
> Status: gateway part implemented (AbstractGateway branch feat/first-run-default-models: the Default models step, Use recommended / Download / Choose per capability, Use recommended for all, the subscription path, the band table in first-run.md); the picks themselves move to AbstractCore in 1072

## Summary

Operator QA on the console setup wizard (OVH test instance, 2026-10-28). Shipped in gateway 0.18.0: the guide
opens right after the admin password is set, it is admin-only (members never see it or the Setup button), its
order is Welcome → Local engines → Default model → Apps → Done, Apps are proposed only once a default text model
exists, and LM Studio on Linux checks `libatomic1` first. NOT shipped (this item): the model step as one row per
MODALITY with a "Use recommended" that picks by detected VRAM/RAM, and a "Use a subscription" path.

## Why

Operator, verbatim scope: "Default models step: one row per modality in the framework's vocabulary (text, image,
video, voice out, voice in, music, 3d, embeddings, rankers) with input/output capabilities visible, a model
picker per row, and a 'Use recommended' button that picks by detected VRAM/RAM; also a 'Use a subscription' path
configuring OpenAI or Anthropic keys for text (stored in Core's provider profiles)."

## Scope

### In scope

- Wizard step "Default models": one row per modality (text, image, video, voice out, voice in, music, 3d,
  embeddings, rankers) showing the route's input/output capabilities, the current model, a picker (the Multimodal
  tab's catalog filtered to the route), and per-row "Use recommended" plus one "Use recommended for all".
- "Use a subscription": OpenAI or Anthropic key for text, stored as a Core provider profile (Providers tab's
  connection), then selected as the text default.
- The recommendation table lives in AbstractCore (the gateway holds no list of its own, first-run.md); the
  operator's starting table, to be adjusted with evidence (real downloads, fits, quality checks) and then written
  in the gateway docs:

| Modality | Rule (operator's proposal) |
|---|---|
| text | 24–64 GB: Qwen3.8 27B 4-bit (unsloth GGUF Q4_K_M; MLX on Apple). 16 GB: a quant that fits fully (Qwen3.8 27B UD Q3_K_XL, 14 GB) or the 8–14B class |
| image (t2i / i2i) | ≥ 12 GB: FLUX.2 [klein] 4B |
| voice out | Supertonic by default; Qwen3-TTS when ≥ 8 GB free and cloning is wanted |
| voice in | Whisper large-v3-turbo at ≥ 6 GB, else Whisper small |
| video | Wan 2.2 TI2V 5B at ≥ 16 GB, 14B at ≥ 32 GB, MiniMax H3 at ≥ 64 GB |

### Out of scope

- airelays (1071, proposal only).

## Acceptance criteria

- On the OVH instance (NVIDIA) and an Apple machine, "Use recommended for all" sets every row this computer can
  run and says why for the others; the table in the docs matches Core's data (a test pins it).
- The subscription path configures text with a real key end to end (chat answers).
