# Backlog: Gateway discovery caching to reduce API noise

## Summary
Cache gateway provider/model/tool discovery to prevent repeated calls and reduce gateway noise.

## Why
- Current UI refreshes can spam discovery endpoints.
- Reducing redundant calls improves responsiveness and lowers backend load.

## Scope
### In scope
- Add in‑process caching with TTL for providers, models, capabilities, and tools.
- Invalidate cache on explicit user refresh or config change.
- Surface cache age in debug logs (optional).

### Out of scope
- Persistent on‑disk cache.
- Cross‑process cache sharing.

## Dependencies
- Gateway discovery endpoints.
- UI refresh triggers in `QtChatBubble`.

## Expected outcomes
- Gateway logs show far fewer discovery requests.
- UI remains responsive with fresh data when requested.

## Full report
### What changed
- Added a TTL cache in `QtChatBubble` for gateway discovery (providers, models, model caps, tools).
- Discovery calls now hit the gateway only when the cache expires or is empty.

### Files touched
- `abstractassistant/ui/qt_bubble.py`

### Tests
- `python -m pytest abstractassistant/tests`

### Results
- Passed: 64
- Skipped: 7
- Warnings: 36 (existing warnings)
