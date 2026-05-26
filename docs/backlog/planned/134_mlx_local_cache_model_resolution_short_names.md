# 134 — MLX Local Cache Model Resolution For Short Names

**Status**: Planned  
**Date**: 2026-03-25  
**Priority**: High  
**Components**: abstractcore, docs

## Summary

Fix local MLX model resolution so a user can select a cached model by its bare local model name, not only by a full `org/model` repo id.

The resolver must inspect both local cache roots already used by the framework:

- `~/.cache/huggingface/hub`
- `~/.lmstudio/models/*/*`

This is specifically a correctness issue for CLI entrypoints such as:

```bash
abstractcode --provider mlx --model gpt-oss-120b-MXFP4-Q8 --prompt-cache on
```

when the model is already cached locally under:

```text
~/.lmstudio/models/mlx-community/gpt-oss-120b-MXFP4-Q8
```

## Why

- `MLXProvider.list_available_models()` already discovers many locally cached MLX models by scanning LM Studio and Hugging Face caches.
- The actual MLX loader path still expects a full `org/model` identifier for cache resolution.
- That creates a broken UX:
  - discovery says the model is available
  - loading by the visible short name fails
- The fix should live in the shared cache-resolution layer, not as a one-off CLI hack.

## Scope

### In scope

- Extend shared local cache-resolution helpers in `abstractcore.utils.model_cache`.
- Make MLX local model loading accept unique bare names from local cache roots.
- Keep resolution safe in ambiguous cases.
- Improve MLX local model listing if needed so it does not advertise obviously unloadable GGUF directories as MLX models.
- Add focused regression tests.
- Update `abstractcore` documentation.

### Out of scope

- Automatic downloads.
- Changing provider auto-detection rules in `create_llm(...)`.
- Non-local remote provider routing.

## Strategies considered

### Strategy A — Patch only `MLXProvider._load_model()`

Pros:
- Small diff.

Cons:
- Duplicates cache-lookup rules outside the shared utility layer.
- Leaves future loaders with the same bug shape.

Decision:
- Reject.

### Strategy B — Extend shared cache-resolution helpers to support unique bare names

Pros:
- Keeps cache discovery and cache resolution aligned.
- Makes the fix reusable by provider code without adding CLI-specific behavior.
- Lets us define one safe ambiguity policy.

Cons:
- Requires careful behavior for duplicate names across orgs.

Decision:
- Chosen.

### Strategy C — Auto-pick the first matching cache entry across all orgs

Pros:
- Simplest implementation.

Cons:
- Unsafe and non-deterministic when multiple orgs publish the same repo basename.
- Hard to explain to users.

Decision:
- Reject.

## Design intent

### Resolution rules

For a model identifier with `org/model`, preserve the current exact-resolution behavior.

For a bare model name:

1. Search the configured LM Studio model directories for exact case-insensitive basename matches.
2. Search the configured Hugging Face hub caches for exact case-insensitive repo basename matches.
3. If there is exactly one match, use it.
4. If there are multiple matches, prefer a unique match from explicit preferred orgs when the caller supplies them.
5. If ambiguity remains, do not guess.

### MLX-specific expectations

- Prefer `mlx-community` and `lmstudio-community` when bare-name resolution is ambiguous.
- Do not treat GGUF-only directories as valid MLX targets.

## Acceptance criteria

- The reported MLX CLI scenario resolves a cached LM Studio model by bare name.
- Bare-name lookup also works for uniquely matching Hugging Face cached MLX repos.
- Ambiguous bare names do not silently pick an arbitrary repo.
- Focused tests cover both LM Studio and Hugging Face cache roots.
- `abstractcore` docs explain the supported local naming forms.

## Notes for implementation

- Do not revert unrelated in-flight edits in sibling repositories.
- Keep the resolver cache-only; no network calls.
- Keep the implementation explicit and predictable; prefer “not found / ambiguous” over silent guessing.
