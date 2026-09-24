# 0872 — AbstractRuntime `MODELS_ENGINES_MIN_ABSTRACTCORE` still says 2.14.0

> Package: abstractruntime (integrations/abstractcore/config_facade.py)
> Type: bug
> Created: 2026-09-25
> Priority: low
> Labels: packaging, version-floor

## Summary

`config_facade.MODELS_ENGINES_MIN_ABSTRACTCORE = "2.14.0"` gates the models/engines facade, but
`host_job_cancel(job_id, *, by="api", user=None)` (AbstractRuntime 0.4.34) passes `by`/`user` to an
AbstractCore signature that exists only from 2.15.1. The package floor (`abstractcore>=2.15.1` in
pyproject) prevents the mismatch in a resolved install, but the in-code floor and its error message
("with abstractcore>=2.14.0") are wrong for anyone running against an editable or pinned older core.

## Current code reality (tag `v0.4.34` = `main` `696f386`)

- `src/abstractruntime/integrations/abstractcore/config_facade.py` l.634 (constant), l.643, l.703
  (message).
- `pyproject.toml` l.53/70/75 require `abstractcore…>=2.15.1`.

## Scope

- Raise the constant to 2.15.1 (or derive it from the package metadata so it cannot drift); add a
  test that the constant is not below the pyproject floor.
- Out of scope: other runtime changes.

## Acceptance criteria

- [ ] Constant ≥ the `abstractcore` floor in `pyproject.toml`, enforced by a test.
- [ ] Shipped in the next runtime patch (no dedicated release needed).

## Testing

- `grep -n MODELS_ENGINES_MIN_ABSTRACTCORE abstractruntime/src/abstractruntime/integrations/abstractcore/config_facade.py`
- `python -m pytest abstractruntime/tests/test_config_facade_models_engines.py -q`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractruntime row).
