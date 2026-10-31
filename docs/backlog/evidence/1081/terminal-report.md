# TUI avatar presentation — 1081

Implemented in AbstractTUI:

- Avatar uses the shared `Frame::rgba` compositing path with resolution-aware antialiasing.
- Theme material colors are precomputed into a 3 KiB packed palette. Production no longer retains
  the three legacy coverage lookup grids (96 KiB); test-only legacy sampling remains available.
- Default mosaic presentation follows terminal capabilities: quadrants for Unicode color,
  braille for monochrome, half blocks for legacy locale. `Avatar::mode` can explicitly select a
  family, including sextants where the font supports them.
- Transparent glyph colors are normalized without losing coverage, preventing default-white
  foreground artifacts. Empty margin text and styling remain untouched.
- `AvatarPointer::pressed(Point)` feeds bounded click attention without consuming events.
  The standalone avatar example forwards movement and pointer presses separately.
- Avatar API documentation describes RGBA composition, glyph-family choice and click attention.
- A per-instance render cache reuses both raster and mosaic on unchanged host repaints; its key
  covers style, pose, level, time, gaze, target dimensions, glyph family, theme and transparency.
  Placement/caption repaint does not rebuild the shared scene or resample pixels.
- Material palette construction stays in the theme layer, and generated RGBA decoding/compositing
  stays in the graphics layer, preserving the widget token-only color policy.

Files: `src/widgets/avatar.rs`, new `src/widgets/avatar_presentation_tests.rs`, private glyph-table
re-export in `src/gfx/mod.rs`, small Avatar-specific updates in `src/widgets/avatar_tests.rs`,
`examples/avatar.rs`, the Avatar subsection of `docs/api.md`, `src/theme/derive.rs` and
`src/gfx/bitmap.rs`.

Validation: seven new focused tests passed. The full Avatar suite passed 22/22 in 0.85 seconds, including actual
Driver/CaptureTerm gaze cadence, hidden/reduced-motion timer cleanup, all 44 styles at narrow/large
sizes, transparent underlay restoration and actual half-block edge rendering. The latter test is
pinned to HalfBlock so it keeps testing its historical glyph-family regression. The slow all-style
tonal-detail test constructs a shared Frame once per style and exercises RGBA directly; its
assertions remain opaque ground and >40 shades. The earlier suite before cache work passed 20/20
in 3.81 seconds (legacy per-pixel frame construction took 62.75 seconds). Both widget policy
lints and the material-theme test also pass. Diff checks pass.

The cache tests force complete Driver tree repaint five times and confirm actual procedural
sample count stays unchanged; audio, pose, design, theme, resize, real animation-clock ticks and
click gaze each invalidate, while hidden repaint performs no work. A separate test verifies
mode/transparency invalidation and stable raster/grid buffer addresses on cache hits.

Pixel protocols are deliberately not enabled automatically: `rect_signal` publishes an unclipped
layer-local rectangle, while current image placements are root-global and lack widget ownership,
effective clip and z-order. Automatically combining them could leak a Kitty image above a modal or
render a scrolled/cropped avatar outside its widget. Existing app-owned `Overlays::image` APIs
remain available, but general widget pixels need retained placement ownership/clip/occlusion work.
This is a follow-up, not a hidden fallback claimed as implemented pixel support.

For the final coredoc pass, retain/update the existing AbstractTUI package skill (an operable
framework with public APIs/examples); teach `.mode(...)` and `.pressed(...)` in its avatar recipe,
and regenerate `llms-full.txt` after both TUI selection and avatar documentation changes.

No package release, process restart, Watch/iPhone edit, or Git push was performed.
