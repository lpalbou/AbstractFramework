# 0881 — AbstractAssistant's Linux input dependency needs wheels (`evdev` via `pynput`)

> Package: abstractassistant (pyproject.toml); abstractframework (root install matrix)
> Type: bug
> Created: 2026-09-25
> Priority: normal
> Labels: install, linux, packaging, wheels

## Summary

`abstractassistant` depends on `pynput>=1.7.7`; on Linux `pynput` depends on `evdev`, which PyPI
ships as an sdist only, so a Linux install of the root profiles that pull the Assistant needs a C
compiler and kernel headers. The root dry-run matrix of 0.3.0 and 0.3.1 lists it as a pre-existing
gap (identical on 0.2.1).

## Current code reality

- `abstractassistant/pyproject.toml` l.48 `"pynput>=1.7.7"` (no platform marker).
- Root release ledgers: "linux evdev sdist via abstractassistant→pynput".

## Scope

- Pick one: a platform marker plus a Linux input backend that ships wheels (or `evdev-binary`), an
  optional `hotkeys` extra, or dropping the global hotkey on Linux; the owner decides.
- Release abstractassistant, then move the root pin in a floor-pinned root patch.
- Out of scope: the other sdists in the matrix (0861 covers the compiled engines).

## Acceptance criteria

- [ ] `uv pip install --dry-run --only-binary :all: abstractassistant` resolves on Linux x86_64 and
      aarch64, Python 3.10–3.13.
- [ ] Root dry-run matrix no longer lists the `evdev` gap.

## Testing

- `uv pip install --dry-run --python-platform x86_64-unknown-linux-gnu --only-binary :all: abstractassistant`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/release-2026-09-24/STATUS.md` (root 0.3.0 row, owner follow-ups); 0861.
