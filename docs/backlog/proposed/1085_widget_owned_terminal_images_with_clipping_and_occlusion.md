# 1085 — Widget-owned terminal images with clipping and occlusion

> Package: abstracttui, abstractcode
> Type: rendering capability proposal
> Created: 2026-10-31
> Status: Proposed
> Priority: medium
> Labels: images, clipping, terminal, avatars

## Summary and current code reality

TUI supports app-owned terminal images through Overlays::image and ImageHandle with a
Kitty/iTerm2/sixel/mosaic capability ladder. Widget rect signals are layer-local and do not
carry effective ancestor clipping or root coordinates. Image entries lack owning paint-layer
and occlusion metadata; protocol output is emitted through the presenter's global custody.
Automatically placing an Avatar image could therefore cover modals or escape a scroll pane.
Rendering work 1081 deliberately retains widget-safe mosaic output rather than expose an
unsafe root-only flag.

## Proposed outcome and scope

Provide retained widget-owned image placement tied to the paint tree, effective clip, screen
transform and layer visibility/z-order. Reuse existing image encoders/protocol capability
selection and cleanup; widgets must not write raw terminal control bytes. Define behavior for
overlapping modals, scrolling, crop, resize, hidden views and protocol-specific repaint.
Adopt this for avatars and other frame/media players only after the common contract is sound.

## Validation and promotion criteria

Real presenter tests for shifted/clipped/nonsquare image bounds, visible higher-z controls,
scroll removal, resize/move/unmount deletion, unsupported terminals and mosaic fallback.
Include Kitty placement layering and iTerm2/sixel redraw limitations rather than claiming
uniform capabilities. Promote when source-image ownership and per-protocol semantics have a
reviewed design. Non-goals: arbitrary terminal escapes or a second image custody system.

## Dependencies and ADR state

Follow-up to 1081. Existing TUI presenter/image boundaries apply; likely requires a TUI ADR
for retained widget-image ownership. No implementation is committed by this proposal.
