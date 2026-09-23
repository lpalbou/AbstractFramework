# 0218 — Interactive Context-Budget Survival (design-first)

**Status**: Planned (design-first — do not implement lossy compaction without sign-off)
**Date**: 2026-07-07
**Priority**: High (long-session survival) / contentious mechanism
**Components**: abstractruntime (effect_handlers LLM_CALL, memory/compaction, core/runtime), abstractcore (exceptions, providers/ollama)

## Summary
Let long interactive ReAct sessions survive context growth **without silent lossy compaction**. The
maintainer is (rightly) wary that summarization loses context. This item's job is to design the
survival path around ADR-0026-compliant, provenance-preserving mechanisms first, and treat LLM
summarization as an explicit last resort only.

## ADR status
- Governing ADRs: ADR-0026 (truncation policy — binding), ADR-0007/0009 (active context vs stored memory, provenance).
- ADR impact: Likely a new/updated ADR on interactive context-budget strategy (eviction-to-artifact vs summarization ordering).

## Context / current code reality
Verified 2026-07-07:
- ReAct disables all input trimming by policy (`react_runtime.py:806-818`) — correct per ADR-0026
  (drop-oldest is forbidden in the loop).
- Real usage IS measured (`_limits.estimated_tokens_used`, `core/runtime.py:1521-1537`) and warned at
  80% (`check_limits`, `:1185-1224`) — but nothing consumes the warning inside the loop.
- Overflow has no typed error: no `ContextLengthExceededError` in `abstractcore/exceptions`;
  `validate_token_usage` (`core/interface.py:406`) is never called. API providers 400 → generic
  effect failure → `RunStatus.FAILED`. Ollama has no `num_ctx` management anywhere in abstractcore →
  **server-side silent truncation** (the one real ADR-0026 leak on the run path).
- `MEMORY_COMPACT` already archives older messages to the ArtifactStore, inserts a summary marker,
  preserves N recent, and **never re-summarizes prior summaries** (`memory/compaction.py:66-85`);
  spans are losslessly rehydratable (`memory/active_context.py:272-455`). `BasicSession.auto_compact`
  exists one layer down and is unused (`abstractcore/core/session.py:35-63, 201-203`).

## Problem
Long coding sessions grow until the provider 400s (fatal) or Ollama silently truncates (degraded,
no signal). The maintainer's concern: automatic summarization is inexact and loses context.

## What we want to do (design ordering, least-lossy first)
1. **Close the silent leak first (uncontentious):** set Ollama `num_ctx` from model capabilities so
   the server stops silently truncating; add a typed `ContextLengthExceededError` and map provider
   overflow 400s to it, so the loop can react instead of dying.
2. **Prefer rehydratable eviction over summarization:** when a budget threshold is crossed, evict the
   *oldest, largest, already-artifact-eligible* content (e.g. big tool outputs, file reads) to the
   ArtifactStore and replace it inline with an `open_attachment` handle + short marker (this is the
   `read_file` pattern applied to history). No semantic content is destroyed — the model can re-open
   it. This is a budget strategy, not truncation (ADR-0026 §"Arbitrary truncation vs memory budget").
3. **Summarization is last resort, explicit, provenance-bearing:** only if eviction cannot fit the
   budget, use `MEMORY_COMPACT` (spans, rehydratable, no summaries-of-summaries) — and never for
   critical-correctness content. Consider requiring opt-in for the summarization tier.
4. **Catch-and-retry:** on a caught overflow, apply eviction (then, if needed, opt-in compaction)
   and retry the LLM call once, mirroring the existing output-truncation retry
   (`effect_handlers.py:1625-1719`).

## Why design-first
The maintainer explicitly flagged compaction as lossy. The default must be the least-lossy viable
mechanism (num_ctx + eviction-to-artifact), with summarization gated behind explicit choice. Get
sign-off on the ordering before implementing the summarization tier.

## Non-goals
- No drop-oldest truncation.
- No automatic LLM summarization on by default without sign-off.
- Not the cross-run seeding/storage-growth problem (track separately).

## Dependencies and related tasks
- ADR-0026; `memory/compaction.py`, `memory/active_context.py`; the `read_file` offload pattern
  (`effect_handlers.py:3175-3285`) is the template for history eviction.

## Expected outcomes
- Ollama no longer silently truncates (num_ctx set); overflow surfaces as a typed, attributable error.
- A long session evicts large old content to artifacts (rehydratable) and keeps going, with markers.
- LLM summarization, if used at all, is explicit and provenance-bearing.

## Validation
- Unit: an overflow-inducing history triggers eviction-to-artifact + retry, not FAILED; evicted
  content is rehydratable via handle; Ollama call carries a correct `num_ctx`.
- Live (endpoint `http://127.0.0.1:8317/v1`): a session engineered to exceed the window; confirm it
  survives via eviction with no semantic loss (re-open proves content intact).

## Progress checklist
- [ ] Ollama `num_ctx` from capabilities.
- [ ] Typed `ContextLengthExceededError` + provider mapping.
- [ ] History eviction-to-artifact (rehydratable) + retry.
- [ ] Design sign-off before any default summarization tier.

## Guidance for the implementing agent
Do not enable lossy summarization by default. Lead with num_ctx + eviction-to-artifact. Bring the
summarization-ordering decision to the maintainer before implementing that tier.
