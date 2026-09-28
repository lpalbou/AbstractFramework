# 0869 — Apple text-model tier boundaries vs the fit budget (128 GiB and 24 GiB Macs)

> Package: abstractcore (config/model_catalog.py); abstractgateway (first-run guide, tray)
> Type: task
> Created: 2026-09-25
> Priority: high
> Labels: decision-gate, models, catalog, apple-silicon
> Status: completed 2026-09-28. Answered by AbstractCore 2.18.1's fit rule (abstractcore `9026a04`, released in 2.18.1 `bd945f8`); root 0.6.2 pins abstractcore 2.18.1

## Summary

OPERATOR DECISION GATE (never assignable): the recommended text model on a Mac is chosen by
memory tier, and two tiers recommend a model the fit check itself says does not fit. Decide the
boundaries; the implementation after the ruling is a one-table change plus tests and a core patch.

## Why

Mission W1 (orchestrator-verified 2026-09-24 17:20): on a stock 128 GiB Mac the ≥ 128 tier picks
`mlx-community/Qwen3.8-Flash-Next-4bit`, which needs ~109.24 GiB against a usable 107.52 GiB (the
MTP twin 104.13 vs 102.14), and macOS's default GPU wired limit (~75 % of RAM unless raised with
`sysctl iogpu.wired_limit_mb`) makes it unlikely to load on a fresh machine. The 24 GiB Mac gets
`Qwen3.8-27B-4bit` with `fits: false` too (W1 probe `metal24 → 27B (fits False)`). The release
waves shipped the tiers unchanged, with a "may not fit" warning; the "9B below 32 GiB" change was
explicitly left out of abstractcore 2.15.1 pending this decision (STATUS patch wave).

## Current code reality (abstractcore `main`, 2026-09-25)

- `abstractcore/config/model_catalog.py` `APPLE_TEXT_TIERS`: `below_gib 24` → 9B, `below_gib 128`
  → 27B, `None` → Flash-Next. A tier that does not fit stays the tier with `fits: false` + a
  warning. `MTP_RECOMMENDED = False`.
- Tier tests: `tests/config/test_model_catalog.py`, gateway
  `tests/test_gateway_recommended_text_tiers.py`.

## Options to rule on

1. 128 GiB: keep Flash-Next with the warning (current) / move the boundary to ≥ 192 GiB (27B on
   128 GiB) / have the console offer to raise the wired limit (sudo, persistent machine change —
   operator-only by the workspace rules).
2. Low end: move the 9B boundary from 24 to 32 GiB (27B from 32 GiB) — the proposal on record.

## Resolution (2026-09-28)

The gate is answered by the rule AbstractCore 2.18.1 adopts, "recommendations must fit": each
Apple silicon tier starts at the first memory size Apple ships where its model fits macOS's default
GPU memory limit (core CHANGELOG `[2.18.1]`, `APPLE_TEXT_TIERS` in `config/model_catalog.py`):

| Unified memory | Recommended text model |
|---|---|
| below 16 GiB | Qwen3 1.7B 8-bit (new; the largest catalog text model that fits 8 GB) |
| 16 to below 32 GiB | Qwen3.5 9B (option 2 on record: the 9B boundary moves from 24 to 32 GiB) |
| 32 to below 128 GiB | Qwen3.8 27B |
| 128 GiB and above | Qwen3.8 Flash-Next, verdict `needs_gpu_limit` with the exact `sudo sysctl iogpu.wired_limit_mb=…` shown (option 1, keep the tier, with the command instead of a bare warning; the console never runs it) |

Existing routes are unchanged (`apply-recommended` reports the new pick as `kept` unless `--force`).
No verbatim operator quote was recorded in this item; the ruling was carried by the lead's
2026-09-28 cascade GO (core 2.18.1 -> gateway 0.7.2 -> root 0.6.2).

## Acceptance criteria

- [x] Ruling recorded (the fit rule above, via the 2026-09-28 cascade GO).
- [x] `APPLE_TEXT_TIERS` changed per the ruling; every tier's pick fits at its lower bound, and the
      128 GiB tier carries the GPU-limit command (`needs_gpu_limit`).
- [x] Released in an abstractcore patch (2.18.1); the root pin follows in root 0.6.2 (0982).
      The gateway's tier test reads core's table (`tests/test_gateway_recommended_text_tiers.py`),
      green on 2.18.0 and 2.18.1.

## Testing

- `python -m pytest abstractcore/tests/config/test_model_catalog.py -q`
- `python -m pytest abstractgateway/tests/test_gateway_recommended_text_tiers.py -q`

## ADR status

- Governing: ADR-0035 (capability routing defaults). ADR impact: None expected.

## Receipts

- `untracked/missionW1/REPORT.md`, `real_host_pick.txt`; `untracked/missions-2026-09-22/SUMMARY.md`
  (fourth wave, operator decision 2); 0865.
