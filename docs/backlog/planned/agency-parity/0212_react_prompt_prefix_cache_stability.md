# 0212 — ReAct Prompt-Prefix Cache Stability

**Status**: Planned
**Date**: 2026-07-07
**Priority**: Critical (speed + cost, every iteration, every provider)
**Components**: abstractagent (react_runtime, logic/react), abstractruntime (llm_client grounding), abstractgateway (cache default)

## Summary
Make the ReAct request prefix byte-stable across iterations so provider prompt caching (OpenAI
`prompt_cache_key`, Anthropic `cache_control`, local KV control planes) can actually hit. Today the
first bytes of the prompt change every cycle, guaranteeing ~0% prefix reuse even when caching is on,
and caching is off by default.

## ADR status
- Governing ADRs: ADR-0008 (token terminology), ADR-0026 (truncation — no lossy compaction to buy cache wins).
- ADR impact: None expected. May add a short note to a caching guide.

## Context / current code reality
Verified 2026-07-07:
- `abstractagent/logic/react.py:92` — the system prompt's **first line** is `f"Iteration: {iteration}/{max_iterations}"`. Byte 0 changes every cycle.
- `abstractagent/adapters/react_runtime.py:909-917` — the rendered scratchpad (`_render_cycles_for_system_prompt`, last 6 cycles) is **appended to the system prompt** every cycle. `planned/130_...` already documents this as defeating the stable-prefix principle.
- `abstractruntime/integrations/abstractcore/llm_client.py:806-823, 926-940` — `_runtime_grounding_prompt_envelope` re-injects `<runtime_metadata>{"local_datetime":"…":seconds}</runtime_metadata>` into the **last `user` message**, scanning backward (`:935-940`); in a tool loop the last user message is the task at **index 0**, so a fresh **seconds-resolution** timestamp lands at the very front of the message list on every call.
- `abstractruntime/integrations/abstractcore/effect_handlers.py:1476-1498` — the attachment index system message is **prepended** (`messages = injected + cleaned`) and rebuilt each call; every `read_file` registers a new attachment (`:2234-2323`), so file reads mutate the top of the conversation mid-session.
- Caching is **off by default** behind three opt-ins: `_runtime.prompt_cache` / `ABSTRACTRUNTIME_PROMPT_CACHE` (`effect_handlers.py:876-899`), `ABSTRACTGATEWAY_PROMPT_CACHE` (`bundle_host.py:1490-1493`), AbstractCode `/cache`.
- Prefix-safe already: tool specs are stable + change-detected via `toolset_id` (`react_runtime.py:157-161, 849-863`); `dedup_messages_view` never rewrites earlier messages (`session_attachments.py:387-508`).

## Problem
The cache prefix (system prompt + tools + leading messages) is mutated at byte 0 every iteration by
(a) the iteration counter, (b) the scratchpad block, (c) the per-second grounding timestamp injected
into message[0], (d) the prepended attachment index. Result: quadratic re-encode cost and higher
TTFT on long agentic runs. The framework already ships the cache machinery; the prompt assembly
defeats it.

## What we want to do
Keep the **stable prefix / dynamic suffix** discipline: static content (persona, rules, tools,
early conversation) stays byte-identical across cycles; volatile content (iteration counter,
scratchpad, grounding time) moves to the **tail** of the request. Then flip caching on by default.

## Requirements
1. **Iteration counter**: remove `Iteration: N/M` from the system prompt's first line. If the model
   still benefits from knowing loop position, inject it as a **trailing** ephemeral message (a
   final `system`/`user` turn appended last), mirroring how grounding is handled — so it is never
   part of the cached prefix. Consider whether it is needed at all (the model rarely needs it).
2. **Scratchpad**: do not append the rendered scratchpad to the system prompt (see 0213, which
   removes the need for it by keeping thought in the transcript). If any rolling summary remains, it
   goes at the tail, not the head.
3. **Grounding envelope**: keep it out of the cached prefix. Prefer a **trailing** grounding message
   over rewriting message[0]; if it must ride the last user turn, clamp the timestamp to a coarse
   resolution (e.g. minute or day) so within-session entropy is minimized. Preserve the language-
   safety behavior from the 2026-06-10 grounding fix (temporal-only default; no locale leakage).
4. **Attachment index**: append at the tail (or fold into the latest user turn) rather than
   prepend, so earlier messages stay byte-stable.
5. **Default caching on** where the derived `prompt_cache_key` is session-scoped and safe; keep the
   env/flag overrides.

## Non-goals
- Do not satisfy any budget by dropping content (ADR-0026).
- Do not change tool-spec ordering (already stable) or the `toolset_id` mechanism.
- Do not remove grounding data from result metadata; only relocate the prompt envelope.

## Dependencies and related tasks
- `planned/130_react_scratchpad_prompt_flow_and_best_practice_review.md` (research this implements).
- Coordinate with **0213** (same file `react_runtime.py`; implement together).

## Expected outcomes
- The prompt prefix (system + tools + all-but-last message) is byte-identical between consecutive
  iterations of a tool loop (assert in a test).
- With caching enabled, cached-prefix token counts grow ~linearly, not quadratically, across a
  multi-iteration run.
- Caching is on by default; overrides still work.

## Validation
- Primary (structural, deterministic, endpoint-independent): capture two consecutive `LLM_CALL`
  payloads from a scripted 3-iteration ReAct run; assert the prefix is byte-identical up to the last
  message; assert the grounding/iteration entropy lands only in the trailing turn. This is the real
  proof that the harness is cache-friendly.
- Endpoint caveat (verified 2026-07-07): the local proxy `http://127.0.0.1:8317/v1` exposes a
  `usage.input_tokens_details.cached_tokens` field but does NOT reuse prompt-cache across stateless
  calls (a repeated identical 6k-token prefix returned `cached_tokens=0` twice). So cache HITS
  cannot be demonstrated on this endpoint; real cache savings accrue only on a caching-capable
  provider. Do not claim cache-hit numbers from this endpoint — use the structural prefix-stability
  proof instead. The token-reduction win from removing the duplicated scratchpad is 0213's to prove
  (fewer `input_tokens` per iteration), and IS measurable here.

## Progress checklist
- [x] Relocate iteration counter out of the system-prompt prefix.
- [x] Stop appending scratchpad to the system prompt (with 0213).
- [x] Relocate/clamp grounding envelope; preserve language-safety.
- [x] Append attachment index at tail.
- [x] Default caching on.
- [x] Prefix-stability unit test + LIVE evidence (2026-07-08):
      - OVH `gpt-oss-120b`, 12-call ReAct run, ledger payloads as ground truth: ONE distinct
        system prompt (2,155 bytes, no `Iteration:`), and after excluding the deliberate
        volatile tail every request's stable message list is an EXACT prefix of the next
        (12/12); per-call reuse 85–100%. Artifact retained (audit follow-up):
        `evidence/w1_ovh_prefix_stability_ledger.json`. PRECISION CORRECTION (2026-07-09): that
        run carried ZERO session attachments, so NO attachment-index (system-role) message ever
        rode its payloads (verified from the artifact: 0 system-role messages in `messages`) —
        this run therefore said NOTHING about OVH's tolerance of the tail index, and there is no
        tension with the incident: the 400 fired on the first run that DID carry attachments,
        on a stricter model (Qwen3.5 vs gpt-oss). Template strictness is per-model-endpoint.
      - OpenAI `gpt-5-mini` (real provider cache metrics): `prompt_tokens_details.cached_tokens`
        = 2048 on every call from iteration 2 onward — 60.9% of the run's total input tokens
        (8,192/13,455) served from cache. Prefix stability converts to actual cache hits.
      - Compatibility fix shipped en route: OVH hard-rejects the `prompt_cache_key` field
        (HTTP 400); the OpenAI-compatible provider now drops-and-retries once and stops sending
        it per instance (see CHANGELOG; unified caching strategy is a follow-up item).
      - NUANCE CORRECTED (2026-07-08, second live run): an earlier run showed `cached_tokens`
        plateauing at 2048 and this note blamed the volatile tail for capping deep-history
        reuse. A subsequent full-toolset run refutes that: `cached_tokens` GREW call-over-call
        (2560 → 2688 → 2816, tracking the growing stable history in OpenAI's documented
        128-token increments). Deep-history reuse works; the earlier plateau was block-boundary
        rounding on small per-call growth, not a structural cap. No tail-folding change needed.
        (OpenAI docs note ~15 requests/min per prefix+key before cache overflow — our
        session-scoped keys naturally stay under it; recorded in 0221 for fleet planning.)

## Guidance for the implementing agent
Re-read the grounding fix notes (root AGENTS.md, 2026-06-10) before touching `llm_client.py` — the
envelope's *position* is language-sensitive; keep temporal-only default and no locale leakage.
