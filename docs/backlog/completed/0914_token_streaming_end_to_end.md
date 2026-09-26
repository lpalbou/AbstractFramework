# 0914 — Token streaming end to end: runtime, core, gateway, panel-chat, Code web, Code TUI, Assistant

> Package: abstractruntime (live-delta lane); abstractagent (stream rider); abstractcore (streaming parity, MLX telemetry, tool/harmony/think handling); abstractgateway (live-delta hub, SSE, setting); @abstractframework/panel-chat 0.1.17 (abstractuic); abstractcode (web + TUI); abstractassistant
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: streaming, runtime, core, gateway, clients, mission-wave-2026-09-25, unreleased

## Summary

Completed record for track S of the 2026-09-25/26 wave (committed locally, not released; release
staged, waiting for the operator's go). Before the wave no token streaming existed anywhere — only
step-level ledger events. Now a run started with `_runtime.stream: true` (or on a gateway whose
`agents.streaming_default` is on) sends `llm.delta` / `llm.delta_end` frames on the existing run
stream, every client renders a live reply that the durable record replaces, and every case that
cannot stream says why instead of going silent. The durable ledger is byte-identical with streaming
on or off (apart from the `stream` flag and timings).

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`, track S): "token streaming end to
end" across runtime, gateway, panel-chat, code and assistant. Design: `S-DESIGN.md` (option A
in-memory hub, option B file sink for split mode), then CONTRACTS "S (final)" after REVIEW/11.

## What landed

- **Runtime** (abstractruntime `601425d`, `a0af9d0`, `b5f3821`, `079c0fc`, `bdebd0c`, `3eb99b0`,
  `ea9adbe`, `41ea691`, `b9827a8`, `879b6f4`): `Runtime.set_live_delta_sink`; `LiveDeltaEmitter`
  (first fragment immediate, 40 ms batches, sealed and flushed BEFORE the attempt's durable record);
  `parent_run_id` on frames; one `delta_end` per attempt; `reason: "unavailable"` + `detail`
  recorded in `_runtime_observability.stream_unavailable`; `<think>` split across fragments; harmony
  channel routing; usage refusal only when the provider flagged it and a stream lacked usage, with a
  re-probe every 10th call; `raw_response` / `prompt_cache` / `usage` kept on streamed records.
  abstractagent `0f3d90d`: delegated children inherit `_runtime.stream`.
- **Core** (abstractcore `8d59974`, `ad59c99`, `3778672`, `ff98aa2`, `4d9260b`, `7dddf90`, `807b026`,
  `ad29f0b`, `18b644e`, `9754270`, `7ad3e31`): every MLX lane ends a stream with one terminal chunk
  carrying `finish_reason` / `usage` / `prompt_cache` (MLX calls with a prompt-cache key were
  previously forced non-streamed); an unclosed tool call becomes `metadata.unparsed_tool_call`, never
  content; ```json blocks are tool calls only when they name an offered tool; harmony channels split
  while streaming and truncated gpt-oss replies are reasoning, not the answer, on both lanes;
  per-request provider copies start with cleared last-result state.
- **Thinking-stream root cause** (`9754270`, `7ad3e31`): `IncrementalThinkingTagStripper` held every
  chunk until it saw a think tag; Qwen3.x templates end the prompt with `<think>\n`, so only
  `</think>` ever arrived and the whole thinking phase was held. The stripper now opens in thinking
  mode when the prompt opened it; reasoning streams per chunk. Measured on the 27B model: first delta
  5.75 s → 0.49 s, final record identical. Same fix for the HF and GGUF lanes in `7ad3e31`.
- **Gateway** (abstractgateway `54a5cc0`, `7b71667`, `2dc4dde`, `0e3a353`, `59fce39`, `3d3eac3`,
  `038aa00`, `5628e9d`, `33f5c02`, `273902e`, `1b6b548`; console `e441a2c`, console-tui `c2bdd53`):
  hub keyed by data folder + root run with subtree subscriptions; one snapshot per open call on
  (re)connect; no cap; synthetic `delta_end` on run end, including runs ended straight in the store
  (kill switch, unresolvable workflow, tick exception); split-mode file sink (0600 in 0700
  `<data>/live/`, tailed, deleted at the end, startup sweep); frames carry no `id:` so
  `Last-Event-ID` stays the ledger cursor; `/runs/start` and `/runs/schedule` validate
  `_runtime.stream` (400 on non-boolean); setting `agents.streaming_default` with three doors;
  `capabilities.streaming` advertised; runtime floor as a named constant with a boot refusal.
- **Clients**: panel-chat 0.1.17 (abstractuic `d0a4357`, `7a5cd8e`; FINAL sha256 `a6411d52…53fd`):
  live bubble per call, closed on any terminal state, images as links by default. Code web
  (`ab4b0dd`, `83d1f6d`, `2baacf3`), Code TUI (`290fb49`, `bd480d1`, `74eaefc`, `488caf8`; `/stream`,
  `--stream on|off|default`, `exec --stream on`), Assistant (`3921c5a`, `04b7a0e`, `db9baeb`;
  `LiveMessageCard`, `assistant run --stream`). Shared rule in all three: Off always sends `false`,
  On only when the gateway advertises `streaming.deltas`, one "unsupported" note, malformed frames
  reported once and skipped.

## Completion report

- Tests: runtime 2508 → 2624 passed / 26 skipped (`test_live_token_deltas.py` 69 tests); agent 456;
  core providers+streaming+tools 2799 → 2928 passed (3 pre-existing media-contract failures); gateway
  2397 → 2401 passed (+20 hub, +14 stream); panel-chat 145 checks; Code web 254, TUI 815, Assistant
  887; deliberate breaks red in every repo (runtime 16, gateway 25, core 20 mutations).
- Hermetic (`S/gw-evidence`): Qwen3.5-4B 23 deltas, first at 0.25 s, live == final; reconnect → one
  snapshot, cursor right; split mode 21 deltas, file deleted at the end; stop → synthetic cancelled
  + done in 34 ms. Live MLX parity on Qwen1.5-0.5B: identical `prompt_cache` / usage / finish / text,
  cold and warm.
- E2E (`E2E/REPORT.md`): check 1 capability + setting; check 2 wire order (deltas → record →
  `delta_end` → done), reconnect snapshot with `Last-Event-ID` 74 → cursor 75, `stream:false` → 0
  deltas, `"true"` string → 400, tenancy (other user 404, 0 frames); checks 3–5 TUI, web and
  Assistant render live replies; check 6 streamed records keep `metadata.prompt_cache` (B2 TTFT
  0.67 s).
- Reviews: REVIEW/00 P0-4 (the only runtime "progress channel" is the durable ledger — needs a real
  transport) → S-DESIGN; REVIEW/11 GO-WITH-CHANGES (child runs invisible, frame order between hub and
  ledger, reconnect orphans, hub cleanup independent of `delta_end`); REVIEW/13 (orphaned bubbles on
  terminal/child runs), REVIEW/15 (stale same-version panel-chat repack; Off overridden by the gateway
  default), REVIEW/17, REVIEW/18 (```json answer swallowed as a tool call), REVIEW/19 (kill-switched
  runs leaked hub state and live files), REVIEW/20 (truncated harmony analysis presented as the
  answer), REVIEW/21, REVIEW/22 — every streaming finding closed; the last pass on each streaming commit is ACCEPT.
- Remaining non-streamed paths (remote core, entity chat, entity own-time loop, raw-text
  OpenAI-compatible servers with prompt-opened thinking) →
  [0898](../proposed/0898_token_streaming_gaps_after_the_first_wave.md).
- Release: publish exactly the FINAL panel-chat tarball, then relock Code web
  ([0899](0899_npm_relock_and_kit_floors_after_the_kit_publishes.md)); gateway requires
  the new runtime (named floor constant).
- ADR state: none; the streaming contract lives in the runtime and gateway docs ("Live token
  streaming").

## Receipts

- `untracked/missions-2026-09-25/S-DESIGN.md`, `CONTRACTS.md` (S, S-2, S-3), `S/REPORT.md`, `S/GW-REPORT.md` (+ `S/gw-evidence/`), `E2E/REPORT.md` (checks 1–6)
- `untracked/missions-2026-09-25/REVIEW/00-contracts-review.md` (P0-4), `11-streaming-design.md`, `13-panel-chat-live.md`, `15-code-web-streaming.md`, `17-streaming-clients-flow.md`, `18-g2-console-core-streaming.md`, `19-gateway-streaming.md`, `20-recheck-eject-core-g2.md`, `21-runtime-recheck.md`, `22-core-harmony-runtime-polish.md`
