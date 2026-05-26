# 006 — Clarify AbstractMusic docs: LLM host vs music backend (avoid “GPT generates music” confusion)

## Summary

Tighten documentation/examples so it’s unambiguous that `llm.music.t2m(...)` is implemented by the **AbstractMusic capability plugin** (ACE-Step backend), not by the selected LLM model/provider.

## Why

Examples using `create_llm("openai", model="gpt-4o-mini", ...)` can be misread as “GPT-4o generates music”.
We want to prevent misconceptions and align user expectations with the capability plugin architecture.

## Scope

### In scope

- Update `abstractmusic/README.md` and framework docs to:
  - use a provider/model example that doesn’t imply native music generation
  - add explicit comments clarifying that the LLM is only a host object for `.music`
  - clarify why v0 uses ACE-Step’s API server by default

### Out of scope

- Implementing an in-process ACE-Step backend (heavy deps + Python pinning).

---

## Report

### Changes made

- Updated music examples to use `ollama/qwen3:4b-instruct` and added explicit comments:
  - `abstractmusic/README.md`
  - `docs/guide/capability-plugins.md`
  - `docs/getting-started.md` (Path 7a)
- Clarified in `abstractmusic/README.md` that v0 uses ACE-Step’s official API server (`acestep-api`) by default.

### Verification

- No code-path changes; documentation-only updates.

