# 0925 — Retained reasoning in tool-call turns makes Qwen3.8 MLX loop on long runs (OPERATOR DECISION GATE)

- **Status:** proposed — OPERATOR DECISION GATE (never assignable): ADR-0026 (truncation policy) protects the current behaviour
- **Created:** 2026-09-26
- **Area:** abstractagent (`logic/react.py` `parse_response`, ~168–181), ADR-0026

## Summary
OPERATOR DECISION GATE. With MLX prompts rendered by the model's chat template (0922), the ReAct transcript keeps the model's reasoning
as the assistant turn's content whenever a turn has tool calls and no visible content (react.py:168–181, "UNBOUNDED by ADR-0026 … never
ours to slice"; a 1200-char cap was reverted on 2026-07-09 as an ADR violation). In the hermetic MLXP run-3 (`Jundot/Qwen3.8-27B-oQ4e-mtp`,
temperature 0.2), the model repeated a byte-identical 3,941-token reply at iterations 9–11 and iteration 12 was still generating after
19 minutes (351k tokens, cancelled). Replaying iteration 11 at provider level: with the messages as recorded the model starts by copying
its earlier reasoning; with that text moved to `reasoning_content` the output stayed byte-identical (2 seeds); with the reasoning dropped
from the tool-call turns the model wrote the digest. Runs 1 and 2 (shorter, 6–7 LLM calls) finished with a digest.

## What the replay showed (2026-09-26, after 0924 verified that sampling is applied)
Replaying run-3 iteration 11 with the reasoning kept in the assistant turns, no seed: at temperature 0.2, sample 1 copied the previous
13,799-char reasoning byte for byte and kept thinking to the 6,000-token cap; sample 2 was byte-identical to the gateway's loop reply
(3,941 tokens, same 3 calls). At temperature 0.7 both samples produced new text and new searches. So: when the prompt already contains
the model's earlier reasoning, a low temperature makes it copy that reasoning with near-certain tokens whatever the seed; the retention
is what sets the loop up, and the scheduled Observer task runs at 0.2. Token growth per run with retention: 99.8k → 135k → 351k.

## Options (the operator decides; none is a patch)
1. Keep faithful retention (ADR-0026 as written): accept the loop risk on long tool runs and the token growth; rely on prompt caching.
2. Scope the retention: keep reasoning only for the last N tool rounds of the current turn, or only when a turn had no visible content
   AND no tool calls. This is a bounded prompt-construction policy, not a silent truncation, but ADR-0026 must say so explicitly.
3. Let the chat template decide: send reasoning as `reasoning_content` (Qwen3.x templates keep it inside the current tool loop and drop
   it from earlier turns) — the replay shows this alone does not stop the loop on Qwen3.8.

## Validation (once decided)
The MLXP config-A run (untracked/missions-2026-09-25/MLXP evidence, gateway on a hermetic port) produces a digest 3/3 without a
byte-identical repeated reply; per-run tokens recorded.

## Related
0922, 0918, 0924; ADR-0026 (docs/adr/0026-truncation-policy-and-contract.md); abstractagent backlog 0033.
