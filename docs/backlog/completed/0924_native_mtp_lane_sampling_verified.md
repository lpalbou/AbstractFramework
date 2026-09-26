# 0924 — Verified: temperature, top_p, top_k and seed reach the sampler on every MLX lane (no fix needed)

- **Status:** completed (verification record)
- **Created:** 2026-09-26
- **Completed:** 2026-09-26
- **Area:** abstractcore (MLX provider: mlx-lm lane, native lane, native batching runtime)

## Summary
Suspicion raised during the MLXP re-run (0922): four independent samples at temperature 0.2 (no seed, then seeds 11 and 12) from
`Jundot/Qwen3.8-27B-oQ4e-mtp` were byte-identical, which looked like the native MTP lane ignoring temperature/seed. Verified false.

## Evidence (untracked scratch `MLXP/samp`, arguments captured at the sampler)
- Code path: mlx-lm lane `_generate_core` → `_build_mlx_sampler` (mlx_lm `make_sampler`), seed → `mx.random.seed`; native lane
  (no runtime) → mlx_vlm `generate_step(temperature, top_p, top_k, seed)` (`ar.py:294-319`, positioned sampler when seeded); native
  batching runtime `NativeRequest` → `_run_exclusive` (`mlx_runtime.py:904`) → the same `generate_step`; a request with temperature > 0
  is never batched. Nothing is dropped.
- Identity table ("Write three unusual one-line story openings.", thinking off, 160 tokens): on all three lanes 4×T=1.0 no seed → 4
  distinct; 4×T=0.2 no seed → 4 distinct; seed 11 vs 11 → identical (3/3); seed 11 vs 12 → differ.
- The earlier identical samples came from the agent prompt that already contained the model's own reasoning: at T=0.2 the model copies
  it with near-certain tokens (0925).

## Side observation (not verified, see 0927)
In every instrumented native run `draft_model` was False: the MTP drafter was not in use and decoding was plain autoregressive.

## Related
0922, 0925, 0927.
