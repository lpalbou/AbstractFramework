# 032 — Gateway Default Model from AbstractCore Config

**Status**: Completed  
**Date**: 2026-02-14  
**Component**: abstractgateway

## Summary

Ensure Telegram (and other gateway-hosted workflows) use the global default provider/model configured via `abstractcore --config` when no explicit environment override or flow defaults exist.

## Reason

Users configure a default model in AbstractCore, but the gateway only used `ABSTRACTGATEWAY_PROVIDER/MODEL` or flow-level defaults. This caused Telegram to ignore `abstractcore --config` defaults. We now harmonize gateway defaults with AbstractCore’s configured defaults.

## Scope

### What we do
- Add a fallback in the gateway bundle host to use `abstractcore.config` global defaults when env + flow defaults are absent.

### What we don’t do
- No change to explicit env overrides (they remain highest priority).
- No change to workflow-specific provider/model defaults if they are set.

## Expected Outcomes
- Telegram and other gateway flows default to the model configured by `abstractcore --config`.

---

## Report

### Changes Implemented

**Gateway host fallback**
- When `ABSTRACTGATEWAY_PROVIDER/MODEL` are unset and flow defaults are missing, the gateway now reads:
  - `abstractcore.config.default_models.global_provider`
  - `abstractcore.config.default_models.global_model`
- Env overrides remain highest priority, flow defaults remain second priority.

**Bundles**
- Any bundle flows that omit provider/model now correctly inherit the gateway defaults.

### Verification Notes

- Reinstalled `abstractgateway` to pick up the fallback logic.

### Files Changed
- `abstractgateway/src/abstractgateway/hosts/bundle_host.py`
- `AGENTS.md`
