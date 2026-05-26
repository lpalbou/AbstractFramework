# 033 — Agent Default Model From AbstractCore Config

**Status**: Completed  
**Date**: 2026-02-14  
**Component**: abstractruntime (Visual Agent node)

## Summary

Allow Visual Agent nodes to use the global default provider/model from `abstractcore --config` when no provider/model is explicitly configured on the node.

## Reason

Telegram and other event-driven flows rely on Visual Agent nodes. Removing pinned provider/model values should not break execution; the system must respect AbstractCore’s global default model when node-level defaults are absent.

## Scope

### What we do
- Add a runtime fallback in the Visual Agent node handler to load provider/model from AbstractCore global defaults.
- Record a `#FALLBACK` warning in the run for visibility.

### What we don’t do
- No changes to explicit node-level provider/model values.
- No changes to gateway env override precedence.

## Expected Outcomes
- Event-driven agents run when node provider/model are unset.
- Defaults match `abstractcore --config` global model.

---

## Report

### Changes Implemented

**Visual Agent handler fallback**
- When provider/model are missing, the agent node now attempts to load defaults from AbstractCore config (`default_models.global_provider/global_model`).
- A `#FALLBACK` warning is recorded in `_flow_warnings` on the run.

### Verification

- Restarted `abstractgateway` with updated runtime.
- Ran a bundle workflow containing a Visual Agent node with no provider/model configured and confirmed:
  - LLM_CALL used the AbstractCore defaults (`default_models.global_provider/global_model`).
  - A `#FALLBACK` warning was recorded in `_flow_warnings` (missing-value fallback visibility).

### Files Changed
- `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py`
- `AGENTS.md`
