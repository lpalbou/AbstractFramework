# 1072 — AbstractCore: the operator's recommendation bands (NVIDIA and processor hosts first)

> Package: abstractcore (`config/recommendations.py`, `capability_defaults.RECOMMENDED_MODELS`, `model_catalog`)
> Type: task
> Created: 2026-10-29
> Priority: high
> Labels: recommendations, first-run, models, core
> Related: 1069 (the gateway's "Default models" step, which shows AbstractCore's picks), AbstractGateway docs/first-run.md (the band table, Today vs Target)

## Summary

The gateway's first-run guide now lists one row per capability and applies AbstractCore's per-host pick
(`recommended_models(host)`). The operator's table (2026-10-28) differs from today's picks on NVIDIA and
processor hosts. AbstractCore owns the picks (the gateway holds no list), so the table lands here, each pick
measured on real hardware first ("adjust with evidence").

## The operator's table (verbatim intent) and what it needs in AbstractCore

| Capability | Rule | Needs |
|---|---|---|
| Text | 24–64 GB: Qwen3.8 27B 4-bit (unsloth GGUF Q4_K_M, or MLX on Apple); 16 GB: Qwen3.8 27B UD Q3_K_XL (14 GB) or the 8–14B class | catalog artifacts `huggingface unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_M` (16.5 GB) and `:UD-Q3_K_XL` (13.1 GB) (repo checked 2026-10-29); `recommended_text_model()` bands for CUDA by VRAM |
| Image (t2i/i2i) | ≥ 12 GB: FLUX.2 klein 4B | already so; check the 12 GB floor on CUDA (16 GB measured with offload) |
| Voice out | Supertonic by default; Qwen3-TTS when ≥ 8 GB free and clones are wanted | Qwen3-TTS as the cloning recommendation (AbstractVoice ships it) |
| Voice in | Whisper large-v3-turbo at ≥ 6 GB, else small | today Whisper base; turbo exists in the catalog (`mobiuslabsgmbh/faster-whisper-large-v3-turbo`, `mlx-community/whisper-large-v3-turbo`) |
| Video | Wan 2.2 TI2V 5B ≥ 16 GB, 14B ≥ 32 GB, MiniMax H3 ≥ 64 GB | today Apple-only (MLX-Gen); CUDA needs a Diffusers Wan backend in AbstractVision (`Wan-AI/Wan2.2-TI2V-5B-Diffusers`, `Wan-AI/Wan2.2-T2V-A14B-Diffusers`) and MiniMax H3 support (`MiniMaxAI/MiniMax-H3`) |

## Acceptance

- `abstractcore models recommendations --json` answers the table on the reference machines; the generated
  `docs/recommended-models.md` and the gateway's first-run.md "Today" column match it (a test pins the gateway
  table to Core's matrix once adopted).
- Each new pick measured on the OVH NVIDIA box (16 GB Quadro RTX 5000) and on a Mac: load, one generation, peak memory.
