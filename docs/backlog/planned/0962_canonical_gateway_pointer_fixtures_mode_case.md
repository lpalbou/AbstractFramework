# 0962 — Canonical gateway pointer fixtures gain a file-mode case

> Package: abstractuic (ui-kit/scripts/fixtures/gateway_pointer), copies in abstractassistant, abstractcode, abstractgateway console
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: contract, fixtures, gateway-pointer, security

## Summary

Every reader of `~/.abstractframework/gateway.json` now refuses a pointer that other users can write (kit, Assistant, AbstractCode, gateway console), but the shared fixture set has no case for it, so each reader tests the rule on its own. Add a mode case to the canonical set so one table drives every reader.

## Why

Ledger: "canonical kit fixtures may need a mode case (uic next release)" (code gate) and "uic next release: canonical gateway_pointer fixtures mode case".

## Current code reality (2026-09-28)

- `abstractuic/ui-kit/scripts/fixtures/gateway_pointer/` (v0.1.14): cases, malformed, non_loopback, valid, wrong_schema, CHECKSUMS.sha256; no mode case.
- Root `scripts/check_identity_sync.py` compares the copies byte for byte and checks CHECKSUMS lists every fixture.

## Scope

### In scope

- A mode case (group- or world-writable pointer refused) in `cases.json`, CHECKSUMS updated, copies re-vendored, each reader's test driven by it.

### Out of scope

- Changing the pointer format.

## Acceptance criteria

- [ ] All four readers run the mode case from the shared table; identity sync passes.

## Validation

`python scripts/check_identity_sync.py`; each reader's fixture test RED when its mode check is removed.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
