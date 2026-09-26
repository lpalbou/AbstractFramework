# 0900 — Chat-turn latency regression seen in the M2 switch-v3 run (33–45 s vs 6–8 s)

> Package: abstractruntime, abstractcore, abstractgateway (unknown until bisected)
> Type: bug
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: performance, open-risk, release-blocker-candidate

## Summary

Open risk to close before the next release. The hermetic default-switch proof was run twice with the
same model pair and driver. In `switch-v2` the two chat runs took 8.5 s and 6.5 s; in `switch-v3`
(after the Review 08 residency fixes, with the streaming edits uncommitted in the tree) they took
33.1 s and 45.4 s. Nobody has explained the difference. A bisect was assigned to reviewer job 16
(`REVIEW/16`, not written at the time of this item).

## Why

M2 report, Review 08 fixes: "NOTE: chat turns 36 s / 48 s vs 9 s in v2 — uninvestigated (streaming
edits were uncommitted in the tree) → reviewer job 16 to bisect."

## Current code reality (2026-09-26)

- `untracked/missions-2026-09-25/M2/evidence/switch-v2/run-a-chat.json`, `run-b-chat.json`:
  `duration_ms` 8,476 and 6,474. `switch-v3/` same files: 33,121 and 45,436.
- Candidate changes between the runs: runtime `6969d17` (claims registry, delayed eject re-check,
  MEMORY_COMPACT with the run's model), core `613e9e0`/`8694164`, and the uncommitted S-rt/S-core
  streaming edits (runtime is still dirty with staged changes; core has uncommitted
  `mlx_provider.py`/`streaming.py`).
- `untracked/missions-2026-09-25/REVIEW/16*` does not exist yet.

## Scope

### In scope

- Reproduce hermetically with the M2 driver on committed trees; bisect runtime/core commits; check
  whether a summarizer/compaction call, an eject/reload, the prompt cache (`metadata.prompt_cache`,
  per the prompt-cache diagnosis method) or a non-streamed re-run (`usage_unavailable`) explains it.
- Fix or record the cause; if the cause is a design trade-off, record it with numbers.

### Out of scope

- General throughput tuning.

## Dependencies

- REVIEW/16 when it lands (fold its findings here).

## Expected outcomes

- Chat-turn duration back within the v2 range, or an explained and accepted difference.

## Acceptance criteria

- [x] Root cause named with the commit (or setting) responsible: abstractgateway `0ccbe73` (built-in deny list), setting `workspace_builtin_deny`.
- [x] Rerun on the fixed trees: prompt back to the v2 size and byte-stable; wall time 1.3–1.6× v2, explained by answer length and machine load (see the completion report) — accepted as an explained difference per "Expected outcomes".

## Validation

- The M2 hermetic driver (same model pair, scratch HOME, `HF_HUB_OFFLINE=1`), `run-*-chat.json`
  `duration_ms`, plus the run ledgers' `metadata.prompt_cache`.

## Evidence

- `untracked/missions-2026-09-25/M2/REPORT.md` (Review 08 fixes)
- `untracked/missions-2026-09-25/M2/evidence/switch-v2/`, `untracked/missions-2026-09-25/M2/evidence/switch-v3/`

## ADR status

- ADR impact: None.

## Receipts

- None yet.

## Completion report

- Closed 2026-09-26 by REVIEW/16 (root cause) and the E2E pass (verification). Original path:
  `proposed/0900_chat_turn_latency_regression_in_switch_v3.md`.
- Root cause (REVIEW/16, not runtime or core): gateway `0ccbe73` (02:29, ten minutes before the v3
  run) added the built-in deny list and enumerated every file and folder of the gateway data folder
  into `input_data.workspace_ignored_paths` (`routes/gateway.py` `_apply_builtin_tool_deny`,
  `workspace_browse.py` `data_dir_tool_deny`); the runtime rendered each entry into the system prompt
  (`workspace_scoped_tools.py`). v2 → v3: prompt 2,985 → 14,659 tokens, system prompt 3,158 →
  24,542 chars, one new line "Excluded paths (override grants)" of 130 absolute paths. The prompt
  grew ~950 tokens per turn (every run adds `run_*.json` / `ledger_*.jsonl`), changed on every turn
  (prompt cache cold even within a session, undoing the 2026-09-22 stable-prompt fix) and disclosed
  other sessions' paths. Single-toggle A/B on unchanged code: deny on 41.5 / 44.5 / 92.8 / 88.9 s
  (17,669 → 22,439 tokens); deny off 14.2 / 13.1 s (2,987 / 2,988 tokens).
- Fix: the rule became deny PREFIXES plus one allow (the run's own folder), evaluated by the path
  resolver and never rendered (gateway `609806d` deletes the enumeration helper; runtime `6567ed4`
  enforces `workspace_builtin_deny_prefixes` / `workspace_builtin_allow`; prompt workspace section
  12,984 → 141 tokens, byte-identical across turns; test "prompt byte-identical while the data
  folder grows by 50 files").
- Verification (`E2E/REPORT.md` check 6, `Jundot/Qwen3.8-27B-oQ4e-mtp`, data folder grew 474 → 493
  files): system prompt byte-identical (sha `f753ffd42b18`, 2,683 B), no "Excluded paths" line; A1
  13.55 s / 2,989 tokens cold, A2 10.97 s / 3,116 tokens with 2,981 cached (`hit_restore`); streamed
  B2 TTFT 0.67 s. The remaining gap to v2's 8.5 / 6.5 s is a longer answer (138 vs 76 tokens in
  REVIEW/16's A/B) and machine load (load average 3–7), not prompt size.
- Also found by the same review: runtime `079c0fc` had reverted the claims registry (see
  [0913](0913_clean_model_eject_across_backends_and_default_switch_leak.md)); not a latency factor.
- Records: [0910](0910_conversation_workspace_browse_preview_one_guard_and_builtin_deny.md),
  [0915](0915_adversarial_review_programme_of_the_2026_09_25_wave.md).
