# 0977 — Agent payload seam turns multimodal message content into text

> Package: abstractagent
> Type: bug
> Created: 2026-09-28
> Priority: high
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
