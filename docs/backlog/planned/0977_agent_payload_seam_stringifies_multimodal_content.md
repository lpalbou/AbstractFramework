# 0977 — Agent payload seam turns multimodal message content into text

> Package: abstractagent
> Type: bug
> Created: 2026-09-28
> Priority: low
> Labels: agent, multimodal, payload, adr-0026

## Summary

`sanitize_transcript_messages` (abstractagent `adapters/transcripts.py`, the payload seam every agent loop uses) does `content_str = str(content)`. A message whose content is a part list (`[{"type":"text",...},{"type":"image_url",...}]`) is sent to the model as the Python repr of that list: the image reaches the model as base64 text, and a large image is then cut by the 200,000-character clamp (0961). Runtime 0.7.1 fixed the same class in the history window; the agent seam still has it.

## Why

Found while investigating 0961 for the operator (2026-09-28). The gateway accepts client-sent image transcripts on `/runs/start` (wave 2) and keeps them as parts; the agent loop then flattens them.

## Current code reality (2026-09-28)

- `abstractagent/src/abstractagent/adapters/transcripts.py:314` `content_str = "" if content is None else str(content)` (agent 0.3.17).
- abstractruntime 0.7.1 keeps list content as parts (`announce_dropped`, `estimate_message_tokens` with `MEDIA_PART_TYPES`).

## Scope

### In scope

- Keep list content as parts through the seam: filter and clamp only text parts, leave media parts byte-identical, keep empty-content checks correct for part lists.
- Tests: an image part survives the seam unchanged for ReAct, CodeAct, MemAct; the 200k clamp (or its 0961 replacement) applies to text parts only.

### Out of scope

- Provider-specific image conversion (core's ollama/anthropic history conversion is its own follow-up).

## Acceptance criteria

- [ ] A user message with an image part reaches the provider request as an image part, not text.
- [ ] Existing transcript tests stay green.

## Validation

Unit tests on `sanitize_transcript_messages` plus one end-to-end run through the gateway `/runs/start` with an image transcript and a fake provider.

## Investigation (2026-09-28, operator asked whether AbstractCore's vision fallback already covers this)

Evidence: `untracked/investigate-0977.md` (repro script, fake provider log).

- **Normal path is fine.** Every app sends images as artifact attachments (`context.attachments`), which reach AbstractCore as `generate(media=...)` (gateway `gateway.py:4318-4393` → agent `react_runtime.py:1912-1931` → runtime `effect_handlers.py:1965-1998`). A vision model gets the image natively; a text-only model gets a caption from the configured vision model (`openai_compatible_provider.py:1011-1048`, `local_handler.py:298-340`). Reproduced both.
- **The bug is real only on an unusual path:** a hand-built `/runs/start` whose `context.messages` holds image parts. No first-party app sends that shape and runtime replay never writes it. There, `transcripts.py:315` `str(content)` sends the list's Python repr (base64 included) as text to every model, and the vision fallback never runs (it only handles `media=`; core copies message image parts through unchanged, `openai_compatible_provider.py:1007-1008`).
- **The original fix idea is wrong:** keeping parts through the seam would hand a text-only model raw image parts with no caption.

## Revised fix

1. At the gateway boundary (`_normalize_run_context_media` / `_window_client_context_messages`), store each inline data-URL image part as a session artifact, add it to `context.attachments`, and refuse non-data image URLs with a 400. The image then takes the upload path, so the vision fallback applies.
2. At the agent seam, never stringify a list: join text parts and fail loudly on any remaining non-text part; clamp only text.
3. Acceptance: the repro's case B (parts on `/runs/start`) gives a vision model the image natively and a text-only model a caption.
