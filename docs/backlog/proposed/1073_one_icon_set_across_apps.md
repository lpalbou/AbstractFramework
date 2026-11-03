# 1073: One icon set across apps (the kit's icon set covers every console glyph)

> Package: abstractuic (`@abstractframework/ui-kit` icons), then abstractgateway (console), the apps
> Type: task
> Created: 2026-10-29
> Priority: low
> Labels: ui-kit, icons, consistency
> Related: AbstractGateway PR #35 (first-run "Default models": `DM_ICONS` in console.py)

## Summary

The gateway console's first-run "Default models" step draws its capability badges with inline SVG
paths. Most come from the kit's 24-grid stroke-2 set, but two are not in it: `cube` (3D) and `rank`
(reranking). The step draws those two itself, in the same style. Every app should take its icons
from one set in the kit, so the same capability looks the same everywhere.

## Done when

- The kit exports `cube` and `rank` (and any other glyph an app draws inline today) in its icon set.
- The console's `DM_ICONS` and the apps read them from the kit, and none keep a private copy.
