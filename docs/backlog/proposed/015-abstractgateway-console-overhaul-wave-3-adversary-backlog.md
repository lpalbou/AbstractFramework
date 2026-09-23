# 015-abstractgateway: [TASK] Console overhaul wave 3 — remaining adversary findings

> Package: abstractgateway
> Type: task
> Created: 2026-07-14 14:20:00 +0200
> Priority: P2
> Labels: seat-gateway, console, ux-debt

## Progress (2026-07-21 — laurent ruled the card active; gateway shipped the wave)

Shipped (pinned by `tests/test_gateway_console_wave3.py`, 6 tests; console
suites 25 green):
- Inline-SVG icon registry: page-wide `ICONS` map (24x24 stroke,
  currentColor) + boot hydration over unicode-fallback spans; lock chip and
  state-warn emoji replaced; every remaining glyph site carries its
  hydration class (pinned).
- Chip unification: ONE shape recipe over pill/badge/state-pill/entity-chip/
  entity-warn-pill/entity-live-badge; families keep only state-color deltas;
  class names preserved (ruled).
- Re-embed relocation: Lifecycle -> Substrate subtab behind a danger-zone
  `<details>` disclosure (element ids unchanged; JS wiring intact).
- Loading rows: shared `tableLoadingRow()` on runs, data-homes, and the
  entities roster (runtimes already had one from wave 2).
- Radius normalization: all radii on the 4/8/10/999 token scale; documented
  exceptions pinned (50%, inherit, pc-chat-item 12px — the shared uic
  transcript recipe stays the kit's pen).
- Create staging: the dry-run's warnings now ride the CONFIRM dialog
  (reviewed BEFORE the irreversible birth); the existing
  validate -> confirm -> create flow already staged the rest.
- Steer modal: verified already shipped pre-wave (themed input modal).
- Cross-repo flags POSTED to uic (commons c3976): the `.af-dialogue`
  canonical transcript recipe, and the light-theme accent decision
  (#e94560 -> teal proposal) — both are uic's pen (themes are vendored with
  a drift pin; a local edit would fork the kit), laurent's eyeball flagged.

Deliberately not done (engineering calls, on the record):
- `.btn-*` class-rename migration: the SEMANTIC (ghost row-actions, tinted
  danger, interaction states, one-primary-per-section weight) shipped in
  wave 2 via element+`.actions` rules; a pure rename churns 100+ markup
  sites for zero pixel change.
- Runtime drill-in growth (per-runtime data-homes slice + config subtab):
  a real feature slice, not polish — needs its own card/claim.

## Summary

Waves 1+2 of the console overhaul (operator order 2026-07-14 12:24) shipped
the structural redesign and the adversary P0s. Four fable5 briefs (usability,
aesthetics, layout-IA, progressive disclosure) produced a longer tail of
P1/P2 findings worth landing as a follow-up wave; this card holds them so
they survive the session.

## Why

The operator ordered "a complete overhaul"; the briefs contain measured,
line-cited fixes beyond what shipped. Each is small; together they finish
the visual/system coherence the briefs defend.

## Scope

### In scope (from the four briefs)

- Button system migration: `.btn`/`.btn-primary`/`.btn-secondary`/`.btn-quiet`/
  `.btn-icon` classes with one-primary-per-section discipline; row actions
  become quiet icon buttons with hover-time danger color (aesthetics P0-1
  full shape; wave 2 shipped the tinted-danger + interaction-states half).
- Inline-SVG icon registry: promote the sandbox `svgIcon()` to a page-wide
  `ICONS` map (24x24 stroke, currentColor); replace ambiguous unicode glyphs
  (one glyph = one verb: x only closes, trash only destroys); fix emoji
  rendering (U+2699/U+26A0 need VS15; lock chip -> SVG).
- Chip unification: one `.chip` recipe (the kit's measured AA color-mix
  derivation) mapped over state-pill/badge/entity-chip/entity-live-badge/
  entity-warn-pill; class names and state words preserved (ruled).
- Light-theme accent decision: `theme-light --accent: #e94560` shares the
  danger hue family — proposal `#0f766e` (teal-700, verify >= 4.5:1);
  retire `--cyan` onto accent mixes. Needs a quick operator eyeball since
  it changes the light brand hue.
- Re-embed block relocation: Lifecycle -> Substrate subtab behind a
  danger-zone disclosure (disclosure P0-3 second half; the prefill removal
  already shipped in wave 2).
- Entity-create staging: split the modal into steps (identity -> validate ->
  mind -> review) with the dry-run at the step boundary (disclosure b).
- Steer prompt: replace `window.prompt` with a small modal (usability P2-4).
- Loading rows + refresh busy states on the five tables (usability P2-1/2).
- Runtime drill-in growth: per-runtime data-homes slice + config subtab
  (IA layout; needs nothing new server-side beyond what shipped).
- Radius/spacing normalization to the token scale (aesthetics P1-5, 4/8/10/999).
- Cross-repo flag to uic: promote a shared `.af-dialogue` transcript CSS API
  (three console chat surfaces now share pc-chat-item classes; the kit owns
  the canonical recipe — usability P2-7).

### Out of scope

- Providers & Multimodal structural changes (operator-ruled OK).
- Renaming `THEME_SPECS` ids or `entity-live-badge phase-*` classes
  (persisted/ruled contracts).

## Acceptance criteria

- [ ] Each in-scope item lands with markup-pin or render tests
- [ ] Light-theme accent decision taken with the operator (one eyeball)
- [ ] uic cross-repo flag posted (dialogue CSS API)

## Receipts

- Briefs: four fable5 subagent reports, 2026-07-14 (usability, aesthetics,
  layout-IA, disclosure) — summarized in the wave-2 SHIP
- Waves 1+2: commons c2168 + the wave-2 SHIP following it
