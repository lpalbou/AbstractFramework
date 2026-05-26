# 013 — AbstractMusic CLI: accept common flags after subcommands (`t2m`/`repl`)

## Summary

Fixed the `abstractmusic` CLI so common flags (ex: `--duration`, `--device`, `--dtype`, etc.) work when placed **after** the subcommand, matching typical CLI ergonomics and our documentation examples.

## Why

Python `argparse` subparsers do not accept top-level options placed after the subcommand by default. This caused commands like:

```bash
abstractmusic --backend acestep t2m "sci fi music" --duration 10 --out out.wav
```

to fail with `unrecognized arguments: --duration 10`, which breaks quickstart UX and is surprising to users.

---

## Report

### What changed

- **CLI parsing**: updated `abstractmusic/src/abstractmusic/cli.py`
  - Added a helper `_add_common_args(...)` and attached the same common flags to:
    - the top-level parser (with defaults from env)
    - each subcommand parser (`t2m`, `repl`) with `default=argparse.SUPPRESS`
  - Result: common flags can be placed **before or after** the subcommand.

- **Tests**: updated `abstractmusic/tests/test_cli_smoke.py`
  - Added `test_cli_allows_common_flags_after_subcommand()` to prevent regressions.

### Tests executed

- `cd abstractmusic && pytest -q`

### Outcome / UX

The following now parses correctly:

```bash
abstractmusic --backend acestep t2m "sci fi music" --duration 10 --out out.wav
```

