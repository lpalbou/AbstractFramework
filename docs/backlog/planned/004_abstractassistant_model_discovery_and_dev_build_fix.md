# 004 — Fix AbstractAssistant model discovery (LMStudio/MLX) + harden dev build imports

## Summary

Improve the developer experience when running **AbstractAssistant** from a “multi-repo workspace” (multiple sibling repos in one folder) by:

- Preventing UI freezes when switching providers (notably **MLX**).
- Correctly discovering and displaying **LMStudio** available models (or showing an explicit warning + fallback when unreachable).
- Hardening the dev build environment so Python imports resolve to **editable installs** (not shadowed by sibling repo folders).

## Why

- Switching to **MLX** currently risks freezing the Qt UI because model discovery triggers heavy provider instantiation/model loading on the UI thread.
- LMStudio model dropdown can silently fall back to hardcoded defaults when the local server is not reachable or base URL is misconfigured, creating confusion.
- In a multi-repo workspace, Python’s default behavior of putting CWD on `sys.path` can shadow installed packages with same-named sibling directories.

## Scope

### In scope

- Refactor `abstractassistant` provider/model discovery to be **non-blocking** and **safe**.
- Add explicit, user-visible warnings when a fallback list is used (`#FALLBACK : reason`).
- Improve `scripts/build.sh` dev environment behavior so running tools from the workspace root is reliable.
- Add unit tests for model discovery behavior where feasible (LMStudio unreachable, MLX discovery must not load models).

### Out of scope

- Changing package import semantics via “monorepo hacks” inside individual repos (no cross-repo `sys.path` manipulation inside packages).
- Adding new providers beyond those already supported in AbstractCore.
- Shipping a full-blown provider configuration UI (base URLs/keys) inside AbstractAssistant (future work).

## Dependencies

- Python 3.11+ recommended (for `PYTHONSAFEPATH=1`); earlier versions require a fallback mechanism.
- AbstractCore provider registry (`abstractcore.providers.registry`) for model listing.
- Qt binding: PyQt5 or PySide2.

## Expected Outcomes

- Selecting **MLX** in AbstractAssistant never freezes the UI; models are discovered asynchronously.
- Selecting **LMStudio** shows the actual `/v1/models` list when reachable; otherwise shows a clear warning and a safe fallback list.
- Running from the workspace root after `source .venv/bin/activate` reliably imports editable-installed packages.

## Implementation Plan

- Update `abstractassistant/ui/provider_manager.py` to prefer **registry-based** model discovery and avoid heavy provider instantiation for discovery.
- Update `abstractassistant/ui/qt_bubble.py` to load models in a background `QThread`, with a cancellation token so stale results can’t override newer selections.
- Harden `scripts/build.sh` import verification and activation behavior across common shells.
- Add tests for provider manager discovery logic and regressions.

---

## Report

_To be completed after implementation and tests; then this item will be moved to `docs/backlog/completed/`._

