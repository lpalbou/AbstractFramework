# 1121 — Kit voice picker: "Create a voice" folds below the picker, and plain labels

> Package: abstractuic (ui-kit)
> Type: task
> Created: 2026-11-04
> Priority: normal
> Labels: ui-kit, voice, end-user-copy, layout

## Summary

The ui-kit voice picker (`ui-kit/src/voice_settings.tsx`, ui-kit 0.9.14) has two problems an end user meets on every
page that reuses it, first seen on the Entity app's Identity page (abstractentity PR #17).
- The "Create a voice" panel sits between the picker and the page's Save action. People could not tell which button
  saves, and some read "Create voice" as a required step.
- The labels are jargon: "Speech provider", "Speech model", "Voice / profile", "Gateway default | Custom".

## Why

The review of Entity #17 (three personas: naive, intermediate and expert, each a Conditional Approval) traced both to
the kit, not to the page. Its asks for the kit:
- fold "Create a voice" into a collapsed section below the picker;
- use plainer labels than "Speech provider / Speech model / Voice / profile".

House rules: actions sit at the bottom of a screen, and end-user copy carries no jargon.

## Scope

### In scope

- `voice_settings.tsx`: the "Create a voice" panel renders collapsed, after the picker. A host page's own actions
  (Save) stay last on the page.
- Plain labels for the provider, model and voice fields and for the default/custom choice, written for someone who has
  never configured speech.
- The kit's tests and a kit release; consumers pick it up when they next take the kit (Entity, Assistant web, Code
  web, the gateway console).

### Out of scope

- The gateway's sentences shown verbatim on these pages (the "default voice" refusal, the "no voice yet" note).
- The Entity page's own copy asks from the same review (a sentence above Save, a gloss beside the trust number).

## Acceptance criteria

- [ ] On a page that reuses the picker, the page's Save button comes after the whole voice block. "Create a voice" is
      collapsed until opened and sits below the picker.
- [ ] No visible label reads "Speech provider", "Speech model" or "Voice / profile". A first-time user can say what
      each field chooses (checked by a naive-persona review of the new screens).
- [ ] Opening "Create a voice" and creating a voice still works as before (existing kit tests green, one test for the
      collapsed default).
- [ ] Screenshots at 400 px and on desktop, in a dark and a light theme, show the order picker → (collapsed) Create a
      voice → page actions.

## Receipts

- Review: `untracked/council-2026-11-02/review-entity-17.md` (root, untracked), findings 2 and the "hand the kit two
  asks" recommendation.
