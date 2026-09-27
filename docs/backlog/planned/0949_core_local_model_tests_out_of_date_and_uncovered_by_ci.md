# 0949 — AbstractCore local-model tests are out of date and invisible to CI

> Package: abstractcore
> Type: task
> Created: 2026-09-27
> Priority: normal
> Labels: tests, ci, huggingface, llama-cpp, next-wave

## Summary

Five AbstractCore tests fail on any machine that has torch / transformers / llama_cpp installed, and CI never
sees it because its `[test]` extra installs none of them (they skip). Four fail with
`TypeError: ... unexpected keyword argument 'reasoning_effort'`: the tests call provider internals with an old
signature. They fail identically on the released 2.16.1, so they are not a torch-version regression — but a
suite that hides failures is not a suite.

## Why

Found while staging abstractcore 2.17.0 (2026-09-27). The operator asked specifically to make sure the new
abstractvoice (torch ≥ 2.4 for Qwen3-TTS) breaks nothing: the voice worker resolved every install profile on
every OS with the new pins (identical lockfiles apart from abstractvoice; core already requires torch ≥ 2.6), and
these five failures are unrelated to torch versions — this item makes that verifiable in CI instead of by hand.

## Current code reality (abstractcore 2.17.0)

- `tests/huggingface/test_gguf_control_plane_plain_generate_reuse.py::test_warm_turn_loads_snapshot_instead_of_reprefilling`
- `tests/huggingface/test_transformers_cached_full_context_delta.py` (4 tests; `reasoning_effort` TypeError).
- CI (`.github/workflows/ci.yml`) installs `.[test]` only; 560 tests skip.

## Scope

### In scope

- Bring the five tests up to date with the provider code (no weakening; they must assert the same behaviour).
- A CI job with CPU torch + transformers (+ llama_cpp CPU wheel where available) running the local-model tests
  that need no downloads (tiny/random models only).

### Out of scope

- GPU/Metal CI.

## Acceptance criteria

- [ ] The five tests pass locally with the heavy extras; each goes RED when the behaviour it checks is removed.
- [ ] The new CI job runs them and is required before release.

## Receipts

- Core staging report 2026-09-27; voice worker compile logs `untracked/release-2026-09-27/voice/compile/`.
