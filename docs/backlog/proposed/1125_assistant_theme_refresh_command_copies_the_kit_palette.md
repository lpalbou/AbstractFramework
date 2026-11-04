# 1125 — AbstractAssistant: the theme refresh command runs and copies the kit's palette file

> Package: abstractassistant
> Type: bug
> Created: 2026-11-04
> Priority: normal
> Labels: themes, ui-kit, desktop, maintenance

## Summary

`python -m abstractassistant.ui_themes --refresh <theme.css>`, the documented way to bring the desktop app's palettes
in line with AbstractUIC, does not work:
- It crashes with `NameError: name 'THEME_SPECS' is not defined`. The `if __name__ == "__main__":` block
  (`abstractassistant/ui_themes.py` l.437 on origin/main) runs before `THEME_SPECS` is assigned at the end of the module
  (l.451, "assigned last because the parsing helpers are defined below the loader").
- Even past the crash, `_refresh` only reports drift (`CHANGED` / `GONE` / `NEW` lines); it copies nothing. During the
  0.18.0 release the desktop palette file `abstractassistant/assets/uic-theme.css` had to be copied by hand from the
  ui-kit tag.

Recorded fact: the pip wheel does not ship `assets/uic-theme.css`. The package data is `assets/*.png` and
`assets/automation_controls.json` (`pyproject.toml` `[tool.setuptools.package-data]`). A pip install without an
`abstractuic` checkout beside it therefore uses the vendored snapshot in `ui_themes.py`. The refresh matters for the
packaged macOS .app, which copies the file in, and for checkouts.

## Why

The 0.18.0 palette refresh (the desktop palettes are now ui-kit 0.9.14's) was a hand copy, because the command does
not work. The next refresh should be one command that copies the file and says what it copied.

## Scope

### In scope

- The entry point runs after `THEME_SPECS` exists (the `__main__` block moves to the end of the module, or calls a
  function defined there).
- `--refresh <theme.css>` copies the kit's `theme.css` to `abstractassistant/assets/uic-theme.css`, then reports the
  copied file's SHA-256 and the drift against the vendored snapshot, as today.
- A test that the snapshot's palettes match the CSS.

### Out of scope

- Changing what the wheel ships, and the palette refresh itself (a release with a screenshot review).

## Acceptance criteria

- [ ] `python -m abstractassistant.ui_themes --refresh <path>` runs without a `NameError`, writes `assets/uic-theme.css`
      byte-identical to the given file and prints its SHA-256.
- [ ] A test runs the command on a temporary `theme.css` and a temporary assets folder, and checks the copy, the
      printed sha and the drift report. It fails if the command stops copying.
- [ ] A test checks each of the 21 palettes vendored in `ui_themes.py` against `assets/uic-theme.css`, so a stale
      snapshot fails CI.
- [ ] The docs that describe the refresh name the copy, and say the pip wheel does not carry the file.

## Receipts

- `untracked/council-2026-11-02/review-app-releases.md` (W-APPS lane note) and the comment on AbstractAssistant PR #53
  (root repository, untracked).
