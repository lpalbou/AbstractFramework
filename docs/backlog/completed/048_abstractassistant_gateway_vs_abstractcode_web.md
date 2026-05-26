# 048 — AbstractAssistant vs AbstractCode Web gateway refactor effort

## Summary

Investigate why AbstractAssistant gateway refactor still requires effort given
`abstractcode/web` already works on top of AbstractGateway, and explain the gap.

## Why

- Clarify reuse opportunities and remaining work.
- Align expectations on effort and scope.

## Scope

### In scope

- Inspect `abstractcode/web` gateway client + ledger streaming + wait handling.
- Compare with AbstractAssistant’s local-host execution model.
- Explain why effort remains and what can be reused.

### Out of scope

- Implementing the refactor.
- Changing gateway or UI code.
- Running tests (analysis only).

## Dependencies

- `abstractcode/web` gateway client + UI wiring.
- AbstractAssistant Qt UI + AgentHost integration.

## Expected Outcomes

- Clear explanation of the effort gap.
- Concrete reuse options (port client logic or embed web UI).

## Implementation Plan (analysis)

- Review gateway client + ledger streaming in `abstractcode/web`.
- Review AbstractAssistant’s local run loop and tool approval path.
- Map reuse vs rewrite surface areas.
- Summarize findings with evidence.

---

## Report

### Work completed

- Reviewed `abstractcode/web` gateway client and ledger-driven UI logic.
- Reviewed AbstractAssistant’s local execution path (`AgentHost.run_turn(...)`).
- Mapped reuse candidates and identified remaining rewrite areas.

### What `abstractcode/web` already provides (reuse)

- **Gateway client** for runs, ledger replay/streaming, commands, attachments, voice:
  - `web/src/lib/gateway_client.ts` includes `start_run`, `get_ledger`, `stream_ledger`, `submit_command`, `attachments_upload`, `attachments_ingest`, `audio_transcribe`, `voice_tts`.
- **Ledger-first rendering** and wait handling:
  - UI streams ledger events, resolves waits, and resumes via commands.
- **Attachment flow**:
  - Upload (browser file → artifact) and optional workspace ingest.
- **Voice flow**:
  - Push-to-talk audio upload + server transcription; server-side TTS playback.

### Why effort remains for AbstractAssistant

- **Different UI stack**: AbstractAssistant is a Qt/Python desktop app; `abstractcode/web` is React/TS. The gateway client and ledger parsing logic must be ported or embedded.
- **Different execution contract**: AbstractAssistant currently drives a **local** `AgentHost.run_turn(...)` generator. Gateway mode must replace this with **ledger streaming + durable commands**.
- **Session state model**: AbstractAssistant uses local session files (`session.json`, `sessions.json`) and local runtime stores. Gateway mode needs session_id + run list mapping, plus optional migration.
- **Voice UX depth**: AbstractAssistant supports full voice modes (continuous listening, hotkeys, local STT/TTS). Web PTT is simpler; gateway voice requires a new audio capture + upload loop and different latency expectations.

### Reuse options

- **Port the gateway client patterns** from `abstractcode/web` into a Python `GatewayClient` for Qt.
- **Embed the existing web UI** inside AbstractAssistant (WebView) to minimize re-implementation.
- **Hybrid**: keep native shell and embed a web panel for chat/ledger rendering.

### Tests

Not run (analysis only).
