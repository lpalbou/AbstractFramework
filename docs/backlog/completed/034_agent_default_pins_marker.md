# 034 — Agent Default Pins Marker (__abstractcore_default__)

**Status**: Completed  
**Date**: 2026-02-14  
**Component**: abstractruntime

## Summary

Allow agent provider/model pins to default to the AbstractCore global default model unless explicitly overridden.

## Reason

Users want flows to expose provider/model pins while still inheriting `abstractcore --config` defaults. Removing pins or relying on implicit missing-value errors is confusing.

## Scope

### What we do
- Add an explicit default marker (`__abstractcore_default__`) for agent provider/model pins.
- Interpret the marker at runtime as “use AbstractCore global defaults.”
- Set Telegram agent pinDefaults to the marker so the flow defaults correctly but can be overridden.

### What we don’t do
- No changes to explicit overrides via pins or node config.
- No changes to gateway environment override precedence.

## Expected Outcomes
- Bundles can set `pinDefaults.provider/model="__abstractcore_default__"` to inherit AbstractCore defaults by default.
- Pins remain visible and configurable in the flow editor.

---

## Report

### Changes Implemented

**Runtime marker handling**
- Added a default-marker check for provider/model in the Visual Agent handler.
- `__abstractcore_default__` (and related aliases) are treated as “use AbstractCore defaults.”
- Missing provider/model still triggers `#FALLBACK` warnings; explicit markers do not.

### Verification

- Restarted the gateway and ran a bundle workflow with agent pinDefaults set to `__abstractcore_default__`.
- Confirmed `LLM_CALL` used the AbstractCore defaults without recording a missing-value `#FALLBACK`.

### Files Changed
- `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py`
- `AGENTS.md`
