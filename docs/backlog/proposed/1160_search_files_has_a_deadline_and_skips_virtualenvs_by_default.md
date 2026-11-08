# 1160 — `search_files` skips virtualenvs by default and reports what it walked; the tools import order

> Package: AbstractCore (`abstractcore/tools/common_tools.py` `search_files`, `abstractcore/tools/abstractignore.py` defaults; the core agent's package, filed here for the owner)
> Type: defect + hardening
> Status: proposed
> Created: 2026-11-08
> Priority: P1 (operator incident 2026-11-08 03:31, Code web; runtime 1159 is the generic half)
> Labels: tools, search, performance

## Summary

A `search_files` over a workspace root can run for many minutes with no answer: the operator watched two
calls spin for eight minutes on 2026-11-08 while the gateway burned one core and the model waited. The
walk honoured the default ignore set (`.git`, `node_modules`, `.venv`, `venv`, `dist`, `build`, `target`)
and still ground through `untracked/review-gateway-100/venv-f65d/lib/python3.12/site-packages/pandas/tests/…`
(a review virtualenv with a non-standard name) and 13,486 gateway ledger files. The tool has `max_hits`
(stops when enough files match) but no deadline, so a pattern with few matches means a full walk.

## Scope

1. **No deadline, no interrupt** (operator 2026-11-08: "we don't want silly arbitrary interrupts"). Instead the
   result FOOTER states what the walk cost when it was large: `scanned 48,211 files in 7m 52s; 2 directories were
   the bulk (untracked/…, runtime/…); a .abstractignore or file_patterns would narrow it` — from a per-top-level
   directory file counter kept during the walk. The search always finishes.
2. **Defaults**: add `venv*/`, `.venv*/`, `site-packages/`, `.tox/`, `.nox/` to `_DEFAULT_IGNORE_LINES`
   (the walk already prunes by directory name, so these cost nothing).
3. **Import order**: `from abstractcore.tools.abstractignore import AbstractIgnore` in a fresh interpreter
   raises `ImportError: cannot import name 'get_model_capabilities' from partially initialized module
   'abstractcore.architectures'` (tools.__init__ → handler → architectures → utils → media → capabilities
   → architectures). Importing `abstractcore.architectures` first works. Found 2026-11-08 while testing the
   workspace `.abstractignore`; a small reorder of `tools/__init__.py` or a lazy import in `handler.py`.
4. Tests: a decoy tree of 50k empty files under `venv-x/` is not walked; a large walk's footer names the bulk
   directories; the fresh-interpreter import works.

## Related

- Runtime 1159 deprecated 2026-11-08 (no tool-call budget, operator ruling).
- UIC 1161 (the tool row shows the elapsed time while a call runs).
- The workspace `.abstractignore` added at the framework root on 2026-11-08 (prunes `untracked/`, `venv*/`,
  `.venv*/`, `site-packages/`, `/runtime`, `/outputs`) — the per-machine relief; this item is the fix.
