# 0947 — 128 GiB tier: the fit estimate ignores a raised GPU memory limit

> Package: abstractcore, abstractgateway
> Type: task
> Created: 2026-09-27
> Priority: normal
> Labels: catalog, fit, apple-silicon, tiers, next-wave

## Summary

On 128 GiB Macs the recommended text model (`mlx-community/Qwen3.8-Flash-Next-4bit`) is judged `too_large` by
AbstractCore's own fit estimate (needs about 109 GiB; usable about 102 GiB from Metal's recommended working
set), yet it is the tier's recommendation and "Download all" fetches it (~111 GB). The operator runs it
successfully — with more memory given to the GPU. The estimate should know about (and the consoles should
explain) the raised GPU wired limit, instead of contradicting the recommendation.

## Why

Operator, 2026-09-27: "i am using it right now but you may need to increase the memory available to gpu."

## Current code reality (abstractcore 2.17.0)

- Fit ceiling on Apple silicon comes from `metal_recommended` (about 107.5 GiB ceiling / 102.1 GiB usable on an
  M5 Max 128 GiB) or 75% of RAM as fallback (`abstractcore/utils/host_profile.py`, `_FALLBACK_CEILING_FRACTION`).
- The GPU wired limit can be raised by the user (`sysctl iogpu.wired_limit_mb=<MB>`, admin, resets at reboot);
  nothing in the framework reads it or explains it.
- Tier choice: `abstractcore/config/model_catalog.py` text tiers (see backlog 0869 for tier boundaries).

## Scope

### In scope

- Read the effective wired limit on macOS (`sysctl iogpu.wired_limit_mb`, 0 = default) and use it as the
  ceiling when set; report the basis in the fit notes.
- When a recommended model only fits with a raised limit: verdict `tight` (or a new explicit
  `needs_gpu_limit`) with the exact command and the value to set, shown by both consoles in the model step;
  never a silent `too_large` next to a recommendation.
- Decide with the operator whether the installer/console may offer to set it (it needs admin; never done
  silently).

### Out of scope

- Changing the 128 GiB tier's model (the operator keeps it).

## Acceptance criteria

- [ ] With the default limit: the recommendation and its fit agree (`tight`/`needs_gpu_limit` + instruction).
- [ ] With a raised limit: `fits`, basis "iogpu.wired_limit_mb".
- [ ] Tests per host (patched sysctl); both consoles render the instruction.

## Receipts

- Adversarial review 1 (untracked/parity/REVIEW-1.md, minor list); core route worker report (6c64508).
