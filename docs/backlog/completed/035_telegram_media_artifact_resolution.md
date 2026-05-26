# 035 — Telegram Media Artifact Resolution

**Status**: Completed  
**Date**: 2026-02-14  
**Component**: abstractruntime + abstractcore

## Summary

Resolve artifact-backed attachments into usable media inputs and ensure LMStudio can answer Telegram image messages reliably.

## Reason

Telegram attachments arrive as artifact refs. Some OpenAI-compatible servers can behave inconsistently when **media + tool calling** are combined, leading to brittle “LLM must tool-call to reply” flows.

The durable fix is to:
- resolve artifact-backed media into file paths for AbstractCore’s media pipeline, and
- make outbound delivery workflow-owned (the workflow calls `send_telegram_message`), so the LLM does not need to tool-call.

## Scope

### What we do
- Resolve artifact-backed media to local file paths before LLM calls.
- Add test coverage for artifact media resolution.

### What we don’t do
- No changes to Telegram bridge payload shape.
- No changes to provider capability metadata.

## Expected Outcomes
- Telegram image attachments are analyzed and replied to.
- Outbound replies do not depend on LLM tool-calling reliability.

---

## Report

### Changes Implemented

**Artifact media resolution**
- LLM client resolves `{"$artifact": ...}`/`artifact_id` into local file paths before media processing.
- Added a unit test to ensure file paths are materialized for artifact-backed media.

### Verification

- Unit test: `pytest abstractruntime/tests/test_llm_client_media_artifacts.py -q`
- Simulated Telegram message with `sushi.png` attachment via `/api/gateway/attachments/upload` + `/api/gateway/commands`.
- Confirmed `send_telegram_message` executed and replied: “This is a picture of sushi.”

### Files Changed
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`
- `abstractruntime/tests/test_llm_client_media_artifacts.py`
- `AGENTS.md`
