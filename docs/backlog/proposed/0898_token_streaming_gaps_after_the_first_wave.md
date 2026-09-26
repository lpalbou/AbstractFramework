# 0898 — Token streaming: the paths that still do not stream

> Package: abstractruntime (llm_client.py, core/live_deltas.py); abstractcore (providers/streaming.py, server); abstractgateway (entity_chat.py, entity_loop.py)
> Type: improvement
> Created: 2026-09-26
> Priority: normal
> Labels: streaming, runtime, gateway, entity

## Summary

The 2026-09-26 wave added live token deltas (`llm.delta` / `llm.delta_end`) on the run SSE stream,
with every "no stream" outcome reported explicitly (`delta_end {reason:"unavailable", detail}`).
Several paths still run non-streamed, by design of the first wave: (1) remote core mode (the runtime
calls an AbstractCore server; detail `remote_core`); (2) entity chat turns; (3) the entity own-time
loop (no live tail client); (4) OpenAI-compatible servers that reject `stream_options` cannot report
usage while streaming, so streaming is refused for them (detail `usage_unavailable`; the call is
re-run non-streamed); (5) prompted tool calls emitted as a ```json fenced block were not withheld from
the live text (S-2 #9) — an abstractcore fix is in the uncommitted working tree. This item keeps the
list so each can be closed or ruled "never".

## Why

S-DESIGN: "Remote core (ABSTRACTCORE_SERVER_BASE_URL) and entity chat stay non-streaming". S report
S-2: "```json blocks not covered"; `usage_unavailable` via `_stream_options_unsupported`. REVIEW/11
P1-5 (parity gate) and P1-7 (no silent no-stream).

## Current code reality (2026-09-26; abstractruntime `bdebd0c` + staged edits; abstractcore `3c6e5ea` + uncommitted `providers/streaming.py`, `mlx_provider.py`; abstractgateway `1172686` + uncommitted S-gw)

- `abstractruntime/src/abstractruntime/core/live_deltas.py` l.70–74: reasons include
  `usage_unavailable`, `remote_core`.
- `llm_client.py` l.7444–7447 and l.8616–8655: `_stream_options_unsupported` → `usage_unavailable`,
  refusal latched per client.
- `llm_client.py` l.6766 `_STREAM_LANES_WITHOUT_PROMPT_CACHE_TELEMETRY = frozenset({"mlx"})`: MLX
  calls with a prompt-cache key run non-streamed (`prompt_cache_unavailable`) until MLX's streaming
  lane attaches cache telemetry — the uncommitted abstractcore `mlx_provider.py` diff targets this.
- `abstractcore/abstractcore/providers/streaming.py` l.93–103 (uncommitted): `json_fence_pattern`
  holds a ```json block that is a tool call.
- Gateway: `entity_chat.py`, `entity_loop.py` do not register a live-delta sink; the gateway
  `agents.streaming_default` never applies to schedules, bridges or the entity loop (CONTRACTS S-2 #6).

## Scope

### In scope

- Per path, decide stream or "never" and record it: remote core (stream through the core server's
  SSE), entity chat turns (entity UI consumer needed), entity own-time loop (likely "never": no viewer).
- `usage_unavailable`: find whether the affected servers report usage another way (final chunk,
  headers) so they can stream; otherwise keep the refusal.
- Confirm the ```json fence fix and the MLX telemetry fix land committed, with tests.

### Out of scope

- Client rendering changes (panel-chat, TUI, Assistant) beyond consuming the new paths.

## Dependencies

- S-core / S-gw commits in abstractcore and abstractgateway; 0900 (latency) before enabling more
  streaming by default.

## Expected outcomes

- Every non-streamed path is either streaming or a documented "never" with its reason visible to users.

## Acceptance criteria

- [ ] A table in the runtime docs ("Live token streaming") lists each path and its state.
- [ ] Test: a ```json tool-call block never reaches `llm.delta` text; a ```json answer without tools does.
- [ ] Test: MLX call with a prompt-cache key streams and the record keeps `metadata.prompt_cache`.

## Validation

- `python -P -m pytest abstractruntime/tests/test_live_token_deltas.py`
- abstractcore streaming unit tests (scratch HOME); hermetic gateway run with `_runtime.stream: true`.

## Evidence

- `untracked/missions-2026-09-25/S-DESIGN.md`
- `untracked/missions-2026-09-25/S/REPORT.md` (S-rt follow-up S-2, BLOCKER FOR MLX STREAMING)
- `untracked/missions-2026-09-25/REVIEW/11-streaming-design.md` (P1-5, P1-7, P2-11)
- `untracked/missions-2026-09-25/CONTRACTS.md` (S-2 #5–#9)

## ADR status

- ADR impact: None (the streaming contract lives in the package docs).

## Receipts

- None yet.

## Addendum (2026-09-26, after runtime ea9adbe)

- Harmony (gpt-oss) answers are routed per channel by the runtime (`final` streams as content, `analysis` as reasoning,
  `to=` tool calls held back). Remaining gap in abstractcore: `UnifiedStreamProcessor` holds everything from the first
  `<|channel|>` for harmony-marked architectures on lanes that pass raw harmony text through it, so on those lanes the answer
  still arrives in one piece at the end (servers that separate reasoning themselves, such as LM Studio, are unaffected).
  Evidence: untracked/missions-2026-09-25/S/REPORT.md ("S-rt ea9adbe"), REVIEW/17-streaming-clients-flow.md.
