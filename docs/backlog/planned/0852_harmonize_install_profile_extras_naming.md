# 0852 — Harmonize the install-profile extras on `apple` / `gpu`

> Package: abstractcore, abstractvoice, abstractvision, abstractmusic, AbstractMemory, abstract3d (dependents: abstractruntime, abstractagent, abstractgateway, abstractassistant, abstractframework)
> Type: task
> Created: 2026-09-23
> Priority: normal
> Labels: packaging, install-profiles, naming

## Summary

The full local-engine profile of a package is called `all-apple` / `all-gpu` in six packages
and `apple` / `gpu` in four others. The `all-` prefix reads like "install everything" while it
means "the local Apple / GPU engine profile". Rename the profile extras to plain `apple` /
`gpu` everywhere, in one release wave, keeping `all-apple` / `all-gpu` as deprecated aliases
for one release. Owner request, 2026-09-23; to be done after abstractframework 0.1.12, with no
extras change in that release.

## Why

Users and agents repeatedly ask for the wrong extra (for example `abstractruntime[all-apple]`,
which does not exist and makes pip install the package bare with only a warning;
`scripts/build.sh` documents one such case). One name for one concept removes that class of
mistake.

## Current code reality

Checked in the sibling `pyproject.toml` files at the 2026-09-23 released versions:

| Package (version) | `all-apple` / `all-gpu` today | `apple` / `gpu` today |
|---|---|---|
| abstractcore 2.13.42 | full local profile (torch, transformers, llama-cpp, MLX / vLLM, plugins …) | **different meaning**: `apple` = MLX only, `gpu` = vLLM only |
| abstractvoice 0.11.3 | full local voice profile | same content as `all-*` (duplicates) |
| abstractvision 0.3.29 | full local vision profile | same content as `all-*` (duplicates) |
| abstractmusic 0.1.15 | full local music profile | same content as `all-*` (duplicates) |
| AbstractMemory 0.3.0 | `lancedb` | **different**: empty |
| abstract3d 0.3.1 | depends on `abstractvision[all-apple|all-gpu]` | depends on `abstractvision[apple|gpu]` |
| AbstractRuntime 0.4.32 | — | `apple` → `abstractcore[all-apple]`, `gpu` → `abstractcore[all-gpu]` |
| abstractagent 0.3.13 | — | cascades to `abstractcore[all-*]` + `AbstractRuntime[apple|gpu]` |
| abstractgateway 0.2.30 | — | `AbstractRuntime[apple|gpu]`, `abstractagent[apple|gpu]`, `AbstractMemory[all-apple|all-gpu]` |
| abstractassistant 0.5.0 | — | `apple`, `gpu` |

abstractcamera has neither. The root `abstractframework` profiles are `apple` / `gpu` already.

## Scope

### In scope

- abstractcore: rename the MLX-only / vLLM-only extras first (for example `mlx` already exists;
  `vllm` already exists), then make `apple` / `gpu` the full profiles and keep `all-apple` /
  `all-gpu` as aliases. This is a behaviour change for anyone using `abstractcore[apple]` today
  and needs a CHANGELOG migration note.
- abstractvoice, abstractvision, abstractmusic: make `apple` / `gpu` canonical; keep `all-*` as
  aliases that point at them.
- AbstractMemory: make `apple` / `gpu` include `lancedb`; keep `all-*` aliases.
- abstract3d: depend on `abstractvision[apple|gpu]` only.
- Dependents move in the same wave: AbstractRuntime, abstractagent, abstractgateway,
  abstractassistant switch their floors to the canonical names (and raise floors to the renamed
  releases); the root `abstractframework` profiles follow with `==` pins.
- Docs, llms files and `scripts/build.sh` profile mapping updated in each package.
- Remove the aliases one release later (separate item).

### Out of scope

- The unresolvable `abstractcore[all]` (0850).

## Acceptance criteria

- [ ] Every listed package publishes `apple` / `gpu` as the full local profile; `all-apple` /
      `all-gpu` remain as aliases with a deprecation note.
- [ ] Dependents and the root profiles reference only the canonical names.
- [ ] uv dry-run resolution of the root `[apple]` (aarch64-apple-darwin, macOS 14) and `[gpu]`
      (x86_64-manylinux_2_35) profiles passes on Python 3.10–3.13 after the wave.

## Receipts

-
