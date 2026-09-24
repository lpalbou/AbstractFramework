# 0869 — Apple text-model tier boundaries vs the fit budget (128 GiB and 24 GiB Macs)

> Package: abstractcore (config/model_catalog.py); abstractgateway (first-run guide, tray)
> Type: task
> Created: 2026-09-25
> Priority: high
> Labels: decision-gate, models, catalog, apple-silicon

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

## Acceptance criteria

- [ ] Operator ruling recorded here (quote it verbatim).
- [ ] `APPLE_TEXT_TIERS` changed per the ruling; every tier's pick `fits` on a stock machine of the
      tier's lower bound, or the ruling explicitly accepts a warning.
- [ ] Released in an abstractcore patch; root pin follows in a floor-pinned root patch.

## Testing

- `python -m pytest abstractcore/tests/config/test_model_catalog.py -q`
- `python -m pytest abstractgateway/tests/test_gateway_recommended_text_tiers.py -q`

## ADR status

- Governing: ADR-0035 (capability routing defaults). ADR impact: None expected.

## Receipts

- `untracked/missionW1/REPORT.md`, `real_host_pick.txt`; `untracked/missions-2026-09-22/SUMMARY.md`
  (fourth wave, operator decision 2); 0865.
