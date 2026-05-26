# 008 — Add AbstractMusic CLI + REPL (local generation)

## Summary

Add a small **`abstractmusic`** console entrypoint with:

- `abstractmusic t2m "<prompt>" --out out.wav`
- `abstractmusic repl` interactive loop

The CLI remains **local/in-process** (no external server) and keeps imports light for `--help`.

## Why

`abstractvoice` and `abstractvision` ship usable CLIs/REPLs. AbstractMusic should match that UX so users can generate audio without writing Python code.

## Scope

### In scope

- Add `abstractmusic.cli:main` + `python -m abstractmusic`.
- Wire `abstractmusic` as a `console_scripts` entry.
- Update `abstractmusic/README.md` with CLI examples.
- Add a minimal unit test ensuring CLI parser/help is import-safe (no model download).

---

## Report

### What changed

- Added `abstractmusic/src/abstractmusic/cli.py`:
  - `t2m` one-shot command outputs a WAV file
  - `repl` interactive prompt loop producing timestamped WAV files
  - heavy ML imports are deferred until generation (help is fast)
- Added `abstractmusic/src/abstractmusic/__main__.py` to support `python -m abstractmusic`.
- Added `abstractmusic` console script in `abstractmusic/pyproject.toml`:
  - `[project.scripts] abstractmusic = "abstractmusic.cli:main"`
- Updated `abstractmusic/README.md` with CLI/REPL usage examples.
- Added `abstractmusic/tests/test_cli_smoke.py` to validate `abstractmusic --help` exits cleanly.

### Tests executed

- `cd abstractmusic && pytest -q`

All passed.

