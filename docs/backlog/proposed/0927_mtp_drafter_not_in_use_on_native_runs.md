# 0927 — The MTP drafter was not in use on the instrumented native runs (`draft_model` False)

- **Status:** proposed (verify first)
- **Created:** 2026-09-26
- **Area:** abstractcore (native MLX lane, MTP/speculative decoding), abstractgateway (run parameters), abstractcode TUI (`/model` MTP step)

## Summary
While verifying sampling (0924) on `Jundot/Qwen3.8-27B-oQ4e-mtp` through the gateway (scheduled Observer digest, hermetic port) and at
provider level, every instrumented native-lane generation reported `draft_model = False`: the model's multi-token-prediction drafter was
not engaged and decoding was plain autoregressive. Either the runs did not request MTP (the TUI/gateway `mtp` parameter was not set for
the scheduled task, or the parameter does not reach the native lane), or the lane declined it (batching, thinking, sampler shape).

## Scope
1. Establish how MTP drafting is requested end to end (TUI `/model` MTP step → run vars → gateway → core native lane) and what the
   provider records when it is on (`metadata` should say so).
2. Reproduce with MTP explicitly on: measure tokens/s and acceptance rate vs off on the same prompt; confirm `draft_model` True.
3. If the scheduled task never turns it on, decide whether MTP should default on for `-mtp` builds.

## Validation
A provider-level and a gateway-level run with MTP on show `draft_model` True in the instrumentation and a tokens/s gain; metadata names it.

## Related
0924, 0922; abstractcode TUI 2eb59e4 (MTP step only for capable models); wave4 MTP NO-GO record (untracked missions 2026-09-24).
