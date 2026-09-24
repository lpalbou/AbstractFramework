# 0865 — Core model catalog tiers, MTP companions and offline-first loading (abstractcore 2.15.0 / 2.15.1)

> Package: abstractcore (with AbstractRuntime 0.4.34 for the cancel attribution)
> Type: feature
> Created: 2026-09-25
> Completed: 2026-09-24
> Priority: high
> Labels: models, catalog, offline, mlx, release-trace

## Summary

Completed record for unplanned major work (written for traceability on 2026-09-25). AbstractCore
now recommends a text model by the Mac's memory, downloads MTP companions with their base model,
loads cached models without touching the network, and keeps every Hugging Face offline switch out
of process-wide state.

## What landed (tags `v2.15.0` = `12528d3`, `v2.15.1` = `e91fe9b`)

- **Apple text tiers** (mission W1): `config/model_catalog.py` `APPLE_TEXT_TIERS` — below 24 GiB
  `mlx-community/Qwen3.5-9B-MLX-4bit`, 24–128 GiB `mlx-community/Qwen3.8-27B-4bit`, ≥ 128 GiB
  `mlx-community/Qwen3.8-Flash-Next-4bit`; a tier that does not fit stays with `fits: false` and a
  warning; MLX first on Macs; 90 8-bit catalog rows; `quant_class`.
- **MTP** (W2, CC): `MTP_RECOMMENDED = False` after the W2 NO-GO; MTP-preserving checkpoints never
  load through mlx-lm; the companion drafter downloads in the same job; `abstractcore models
  verify`.
- **Catalog UI** (X2): one card per model with quant/provider/capability filters; Hugging Face search
  as the same cards.
- **Offline-first** (S, U, V, EE): no import-time or process-wide `HF_HUB_OFFLINE` writes; cached
  models load from the snapshot directory with `local_files_only=True`; `ensure_hf_main_ref` +
  `abstractcore models repair-refs`; embeddings offline-first and a cache save that never writes
  empty; fetched PDFs never leave the machine without `offline.allow_remote_pdf_extraction`.
- **Downloads** (KK, 2.15.1): a download that stops on its own ends `failed` with a reason; cancels
  record `cancelled_by` / `cancelled_by_user`; the fit warning states the two totals it compared.

## Completion report

- Validation: orchestrator runs in `untracked/missions-2026-09-22/SUMMARY.md` — W1 141 passed / 1
  pre-existing failure; CC 67 + 8 tests, 15/15 mutants, a real 9B fresh-install run correct with
  MTP used; V 27 + 6 tests, 15/15 mutants; EE 77 targeted tests, mutants m1–m6 red; core
  `tests -m "not slow"` 4947 passed / 379 skipped / 7 failed + 1 collection error, all 8 also
  failing on the committed HEAD (fourth wave).
- Release evidence (`untracked/release-2026-09-24/STATUS.md`, `abstractcore-ledger.md`,
  `abstractcore-2.15.1-ledger.md`): PyPI 2.15.0 and 2.15.1 (wheel + sdist), GHCR
  `abstractcore-server:2.15.0` / `:2.15.1`, Release runs 36030399826 and 36055107695 green.
- Residual risks and follow-ups:
  - Tier boundaries vs the fit budget (Flash-Next on stock 128 GiB Macs, 27B on 24 GiB Macs) →
    decision gate 0869. The "9B below 32 GiB" change was deliberately left out of 2.15.1.
  - Default MLX model id `mlx-community/Qwen3-4B` does not exist → 0874.
  - `scripts/update_llms.py` SOURCES incomplete → 0882.
  - mlx-lm upstream patch-release request (`untracked/missionCC/mlx_lm_issue.md`) — operator
    action, no item.
  - `abstractcore[all]` still unresolvable (0850) and compiled packages still in the default
    extras (0861): both unchanged at 2.15.1.
- ADR state: no new ADR; offline behaviour is documented in one canonical section of the
  abstractcore docs (coredoc pass `194c312`).

## Receipts

- `untracked/missionS/`, `missionU/`, `missionV/`, `missionW1/`, `missionW2/`, `missionCC/`,
  `missionX2/`, `missionEE/`, `missionKK/` (local).
