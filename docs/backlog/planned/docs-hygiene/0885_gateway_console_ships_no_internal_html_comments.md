# 0885 — The gateway console must not ship internal HTML comments to browsers

> Package: abstractgateway (console.py, console_ui.py)
> Type: improvement
> Created: 2026-09-25
> Priority: low
> Labels: console, hygiene

## Summary

The console HTML is served from Python string templates that carry 35 HTML comments; several are
maintainer history ("charter refactor 2026-07-15", "operator ruling 2026-09-06", "FIRST-RUN WIZARD
(2026-09-23)", mission names). HTML comments are delivered to every browser that opens the console.
Code comments belong in the Python/JS source, not in the served markup.

## Current code reality (`v0.4.2`)

- `src/abstractgateway/console.py`: 35 `<!--` occurrences (e.g. l.1607, 1659, 2064, 2597, 2624).
- `console_ui.py`: 0 HTML comments (JS `//` comments inside `<script>` are also served; decide
  whether to strip those too).

## Scope

- Move explanatory comments out of served markup (Python comments next to the template, or a
  build-time strip); add a test that the served `/console` HTML contains no `<!--`.
- Out of scope: minifying the console.

## Acceptance criteria

- [ ] `GET /console` body contains no `<!--`, enforced by a test.

## Testing

- `grep -c "<!--" abstractgateway/src/abstractgateway/console.py`
- `python -m pytest abstractgateway/tests -q -k console`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractgateway row).
