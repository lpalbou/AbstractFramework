# 0850 — Redesign the unresolvable `abstractcore[all]` extra

> Package: abstractcore (consumed by abstractframework)
> Type: task
> Created: 2026-09-23
> Priority: normal
> Labels: packaging, install-profiles

## Summary

`pip install "abstractcore[all]"` cannot be resolved on any platform (Linux or macOS, Python
3.10–3.13) for abstractcore 2.13.41 and 2.13.42. The extra bundles requirement sets that no
single environment can satisfy. The framework install profiles do not use it
(`abstractframework[apple|gpu]` go through `abstractgateway[apple|gpu]` →
`abstractcore[all-apple|all-gpu]`), so no release is blocked, but the extra is advertised and
fails for anyone who tries it.

## Why

Observed in the 2026-09-23 release wave (report `abstractcore-2.13.42.md`, point 2):

- `all` includes the MLX stack: mlx-vlm 0.7 needs `transformers>=5` and `llguidance>=1.7`.
- `all` includes vLLM: every vLLM release up to 0.19 needs `transformers<5` and `llguidance<0.8`.
- vLLM 0.30 would accept the newer stack, but it needs `openai>=2.25`, while `all` pins
  `openai>=1.0.0,<2.0.0`.

The conflict is structural (MLX-on-Apple vs vLLM-on-CUDA in one extra), not a NumPy or
Python-version issue.

## Current code reality

- `abstractcore/pyproject.toml` defines `all`, `all-apple`, `all-gpu`, `all-non-mlx`, `apple`
  (MLX only), `gpu` (vLLM only) and `full-dev`. A comment already warns that `all` "may not
  install everywhere".
- `all-apple` and `all-gpu` resolve on Python 3.10–3.13 with abstractcore 2.13.42 and
  abstractvoice 0.11.3.
- Root `abstractframework` 0.1.12 does not depend on `abstractcore[all]`.

## Scope

### In scope

- Pick one design and apply it in abstractcore:
  - drop vLLM (and other platform-exclusive engines) from `all`, so `all` means "everything
    that installs on any platform"; or
  - make `all` select `all-apple` on Darwin arm64 and `all-gpu` elsewhere with environment
    markers; or
  - remove `all` and point users at the platform profiles.
- Resolve the `openai<2` pin against the vLLM versions the `gpu` extras allow.
- Add a CI resolution check (uv dry-run) for every published aggregate extra on Linux and macOS,
  Python 3.10–3.13, so an unresolvable extra fails CI instead of users.
- Update abstractcore docs and llms files to describe the chosen semantics.

### Out of scope

- Renaming `all-apple` / `all-gpu` (tracked in 0852).
- Changing the root profiles.

## Acceptance criteria

- [ ] `uv pip compile` of `abstractcore[all]` (or its replacement) succeeds on
      `aarch64-apple-darwin` and `x86_64-manylinux_2_35`, Python 3.10–3.13.
- [ ] CI runs that resolution check for every aggregate extra.
- [ ] abstractcore CHANGELOG states the new meaning of `all` with a migration note.

## Receipts

- Release-wave evidence: `untracked/release-2026-09-23/abstractcore-2.13.42.md` (local).

## Status update 2026-09-25 (post-release trace)

Still open at abstractcore 2.15.1: `pyproject.toml` `all` still lists both `llama-cpp-python` and
`vllm>=0.6.0,<1.0.0` alongside the MLX stack. Neither 2026-09-24 wave touched the extras.
