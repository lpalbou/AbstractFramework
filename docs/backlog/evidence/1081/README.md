# 1081 rendering evidence

Rendering review: **Approved** for the inspected local/source scope. The contextual interaction
implementation is tracked separately under 1082. Nothing in this receipt authorizes publication,
license changes, production restarts or Apple client modifications.

## Result and visual evidence

- [Focused designs](focused.png): Watch Halo, Wave, Hover, Rings and Eye, seven poses, 160 px.
- [Matched baseline](baseline-focused.png): same design/state framing before the change.
- [Theme comparison](themes.png): host palette ownership across warm/cool/monochrome themes.
- [Desktop Qt](desktop-focus.png): actual native library installed in the shared app environment.
- [Browser focus gallery](browser-focus.png) and [built Assistant preview](assistant-preview.png).
- [Independent final review](adversarial-review.md): rendering, scheduling, context and cache approved.
- [Core report](core-report.md), [terminal report](terminal-report.md),
  [native timing samples](native-timing.json), [artifact provenance](renderer-provenance.json).

The shared RGBA path retains overlapping light and shaded surfaces. Wave uses five ribbons and
a working spiral; Hover has a shaded body, visor, articulated arms, three plumes and floor glow;
Rings uses six icosahedral great circles; Eye has asymmetric lids and iris/pupil detail; Halo has
an uneven flowing corona. The source is still theme-driven and stateless. Three material ramps
do not recreate an independent rainbow palette or Watch's phase/history controller.

## Verified paths

- Core: 15 Rust tests, 12 Python tests plus 10 subtests, clippy, Rust 1.87 check, source archive
  and platform wheel installation, CLI and public Rust recipes. 378 native/Wasm frames across
  three sizes: maximum channel difference 1/255 (5 differing channels out of 7,483,392).
- Terminal: 22 Avatar tests, including actual Driver/CaptureTerm rendering, all styles, bounds,
  visibility/reduced motion, pointer attention, glyph families and transparent restoration.
  Cached theme palette is 3 KiB versus 96 KiB for the prior retained coverage grids.
  Five forced whole-tree repaints reuse the raster/mosaic; pose, level, time, gaze, theme,
  geometry, glyph family and transparency correctly invalidate the per-instance cache.
- UIC: full ui-kit test command passes; actual Chromium covers all 44 styles × seven poses,
  paged handle limits, static/error/reduced-motion behavior, gaze expiry, click attention,
  repeated unmount, context loss/recovery and quality/DPR resizing up to 512 px.
- Independent reviewer: 15 Rust tests plus aborted creation during module loading, failed
  palette cleanup, 16-handle exhaustion/recovery, real offscreen suspension, simulated document
  visibility, restoration and non-prevented host pointer actions pass.
- Assistant web: canonical compiled snapshot/source verification, production build, 62 unit
  tests and built-app fake-Gateway experience checks pass (actual audio envelopes, all 44
  designs, state previews, motion, responsive controls, approvals and Docs; zero JS errors).
- Desktop: the new wheel is installed in the **shared workspace `.venv` used by the launcher**.
  A fresh process compares 35 native focus-style/pose frames against the frozen artifact,
  then renders five real Qt widgets and verifies native disposal on hide.
- [Apple verification](apple-verification.json): all 569 previously recorded tracked Apple
  files have unchanged SHA-256 values. No Watch/iPhone implementation was modified.

## Measured limits

Matched native 160 px frame generation under concurrent local load: median **0.839 → 1.857 ms**,
maximum **1.271 → 5.393 ms**. The result is richer rendering, not a universal speed increase.

Chromium public Canvas draw calls (two warmups, seven measured speaking frames per case):

| Design | 128 px median ms | 256 px median ms | 512 px median ms |
|---|---:|---:|---:|
| Halo | 2.7 | 3.7 | 12.4 |
| Wave | 2.3 | 6.0 | 22.6 |
| Hover | 0.9 | 2.5 | 9.5 |
| Rings | 1.1 | 3.1 | 11.4 |
| Eye | 0.9 | 2.8 | 10.3 |

These measure synchronous generation/copy/Canvas submission on this Mac, not GPU scanout,
battery consumption or every operating system. High quality (512 px / up to 30 fps) is opt-in;
balanced defaults to at most 384 px / 24 active fps and 6 idle fps. A 128 CSS-pixel portrait at
2× density uses 256 backing pixels. Galleries default to economy. Missed deadlines are skipped.
Widget-owned Kitty/iTerm2/sixel placement remains proposed under 1085 because clipping/layer
custody is not yet adequate; TUI uses safe capability-selected mosaic presentation.

## What to try

- In Assistant Appearance, or Code account menu → **Companion settings** → **Appearance**,
  choose **Watch Halo**, **Watch Wave**,
  **Watch Hover**, **Watch Rings** or **Watch Eye**. Original similarly named shaded styles
  retain their identities. Compare listening, working and speaking, including silence.
- From `abstractuic/ui-kit`, run `npm run demo:avatars:build`, serve that directory locally,
  and open `examples/avatar_gallery.html`. Choose **Focus designs**, then Quality, Phase,
  Audio level and Light / dark. Economy is suitable for the multi-avatar grid.
- Native preview: `python -m abstractavatar render --style watch-hover --state speaking
  --level 0.6 --time 1.25 --size 256 --output /tmp/avatar-preview.png`.

The shared native wheel and built web assets are updated locally. An already running desktop
process retains its loaded native library until **Assistant-only restart**; the Gateway does
not need restarting. Source/package versions remain unpublished, with no new remote CI claim.
