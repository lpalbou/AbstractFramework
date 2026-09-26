# 0900 — Chat-turn latency regression seen in the M2 switch-v3 run (33–45 s vs 6–8 s)

> Package: abstractruntime, abstractcore, abstractgateway (unknown until bisected)
> Type: bug
> Created: 2026-09-26
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

- [ ] Root cause named with the commit (or setting) responsible.
- [ ] A rerun of the switch scenario on the release candidate trees with both chat runs ≤ 1.5× the v2 durations.

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
