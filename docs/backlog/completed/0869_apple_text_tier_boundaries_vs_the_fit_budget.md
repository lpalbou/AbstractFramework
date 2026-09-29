# 0869 — Apple text-model tier boundaries vs the fit budget (128 GiB and 24 GiB Macs)

> Package: abstractcore (config/model_catalog.py); abstractgateway (first-run guide, tray)
> Type: task
> Created: 2026-09-25
> Priority: high
> Labels: decision-gate, models, catalog, apple-silicon
> Status: completed 2026-09-28. Operator ruling: the tiers stay as in 2.18.0; AbstractCore 2.19.0 (abstractcore `5cf2b6a`) aligns the fit estimate with the operator's 24 GB measurement; root 0.6.2 pins abstractcore 2.19.0

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

Operator ruling (2026-09-28, relayed by the lead): the tiers stay as they were in 2.18.0, below
24 GiB Qwen3.5 9B, 24 to under 128 GiB Qwen3.8 27B, 128 GiB and up Qwen3.8 Flash-Next. Option 2
(9B up to 32 GiB) and a 1.7B tier for 8 GB Macs are not adopted. Instead, AbstractCore 2.19.0
(`5cf2b6a`; core CHANGELOG `[2.19.0]`, `docs/recommended-models.md`) makes the fit estimate match
the operator's measurement on a 24 GB Mac mini: the default GPU memory limit is about 75% of RAM
(24 GB -> ~17.8 GB measured), MLX keeps a flat 2 GiB working reserve, and the highest limit it
suggests leaves macOS max(4 GiB, 12.5% of RAM). The command is printed and never run.

| Unified memory | Recommended text model | Verdict |
|---|---|---|
| below 24 GiB | Qwen3.5 9B | fits from 16 GB; "may not fit" on 8 GB |
| 24 to below 128 GiB | Qwen3.8 27B | on 24 GB: fits with a small context (about 1.1k tokens), about 34k tokens after `sudo sysctl iogpu.wired_limit_mb=20480`; fits from 32 GB |
| 128 GiB and above | Qwen3.8 Flash-Next | fits after raising the GPU memory limit: `sudo sysctl iogpu.wired_limit_mb=114688` (was 117760 with the RAM-minus-8-GiB rule) |

Existing routes are unchanged.

## Acceptance criteria

- [x] Ruling recorded (tiers unchanged; the fit estimate follows the 24 GB measurement).
- [x] `APPLE_TEXT_TIERS` per the ruling; a tier whose pick does not fit comfortably says so with
      the GPU-limit command (small context on 24 GB, `needs_gpu_limit` on 128 GB).
- [x] Released in an abstractcore patch (2.19.0); the root pin follows in root 0.6.2 (0982).
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
