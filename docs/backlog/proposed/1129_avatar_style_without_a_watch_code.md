# 1129 — The avatar catalog's one style the Watch cannot draw (`iphone-weave`)

> Package: abstractavatar, abstractgateway
> Type: task
> Created: 2026-11-05
> Priority: normal
> Labels: avatar, identity, watch, catalog, adr-0052

## Summary

AbstractAvatar 0.1.1's catalog has 44 styles. One of them, `iphone-weave` ("Woven orb", catalog code 43, drawn by
`abstractassistant/phone/iphone/Sources/App/OrbWeave.swift`), has no Watch code: its row in `src/catalog.rs` carries an
empty watch code. So:
- the gateway's identity ladder refuses it as a chosen design (400, "cannot be drawn on the Watch", ADR 0052 §8);
- the recorded default never picks it (the default pool lists Watch designs only, ADR 0052 §2);
- the Entity app's picker already hides it (`identity_settings.tsx` keeps the designs with a non-empty `watchCode`).

Nothing is broken today, but the catalog does not say why the style is missing on the Watch, and a reader of the
catalog alone sees 44 styles an entity could wear.

## Decision to record (one of)

- **(a)** Give `iphone-weave` a Watch code in the next AbstractAvatar release, so all 44 styles can be worn by an entity.
- **(b)** Mark it phone-only in the catalog (a field every client reads), so the gateway refuses it with that reason and
  the Entity picker hides it by the field rather than by an empty code.

## Why

ADR 0052 makes the avatar design part of an entity's digital identity, drawn the same way everywhere. A catalog style that
some surfaces cannot draw needs to say so in the catalog itself, not only through an empty code that each client
interprets.

## Scope

### In scope

- The decision above, and the catalog change it needs (a Watch code, or a phone-only mark) in AbstractAvatar.
- The gateway's refusal reason and the Entity picker reading the same field.

### Out of scope

- New avatar styles; the Assistant's own (non-entity) design choice.

## Acceptance criteria

- [ ] Every catalog style either has a Watch code or is marked phone-only, and a catalog test fails if a style has
      neither.
- [ ] The Entity app's picker shows exactly the styles an entity may wear (all with a Watch code), checked by its test.
- [ ] The gateway's refusal for a phone-only style names that reason.

## Receipts

- AbstractAvatar `origin/main`: `catalog.json` (44 designs, `iphone-weave` code 43), `src/catalog.rs` (empty watch code);
  AbstractGateway `routes/entities.py` (the refusal ladder); AbstractEntity `src/identity_settings.tsx` (the filter).
