# 0896 — Verify that ejecting an MLX model also frees its MTP drafter (needs a host with the companion checkpoint)

> Package: abstractcore (providers/mlx_provider.py MTP lane, mlx_residency.py); verification only
> Type: task
> Created: 2026-09-26
> Priority: normal
> Labels: memory, mlx, mtp, verification

## Summary

The clean-eject proof of 2026-09-25/26 (M1, M2) ran the operator's MTP model through the drafter-less
mlx-vlm lane, because the drafter companion `mlx-community/Qwen3.8-27B-MTP-4bit` is not in this host's
Hugging Face cache (only its `.locks` entry exists). Whether an eject also frees the drafter's weights
is therefore unverified. M2 added a unit-level drafter release test; a real-weights run is still
missing.

## Why

M1 F3 ("Freeing the drafter's memory on eject is therefore unverified"); M2 "Open: real MTP drafter
eject unverified (companion absent)".

## Current code reality (2026-09-26; abstractcore `3c6e5ea`)

- `abstractcore/abstractcore/assets/model_capabilities.json` l.4542: drafter
  `mlx-community/Qwen3.8-27B-MTP-4bit` for `Jundot/Qwen3.8-27B-oQ4e-mtp`.
- `ls ~/.cache/huggingface/hub | grep Qwen3.8-27B-MTP` → nothing on this host (2026-09-26).
- `describe_speculation_capabilities` reports `reason=mtp_head_not_cached` here; `_plan_mtp_lane`
  returns early without a speculation policy (M1 F3).

## Scope

### In scope

- On a host where the companion is cached (or after an operator-approved download into a scratch
  `HF_HOME`), run the M1 driver with a speculation policy enabled: load, generate with the drafter
  active (confirm in the log/diagnostics), eject, measure.

### Out of scope

- Downloading into the operator's shared cache without approval; MTP throughput work.

## Dependencies

- Operator approval for the companion download, or a host that has it.

## Expected outcomes

- A measured PASS/FAIL: IOAccelerator back to baseline (≤ 1.5 GB) after eject with the drafter loaded.

## Acceptance criteria

- [ ] Evidence folder with vmmap before/after, `/models/loaded` rows and the eject report, drafter
      confirmed loaded before the eject.
- [ ] If FAIL: a bug item in abstractcore with the holder chain.

## Validation

- `untracked/missions-2026-09-25/M1/run_m1.py --port <free>` with a scratch HOME and a speculation
  policy; `vmmap --summary <pid>`.

## Evidence

- `untracked/missions-2026-09-25/M1/REPORT.md` (F3)
- `untracked/missions-2026-09-25/M2/REPORT.md` (`cf8caae`, Open list)

## ADR status

- ADR impact: None.

## Receipts

- None yet.
