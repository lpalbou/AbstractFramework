# 0920 — Gateway: the entity identity card matches history lines to door events by clock minute (flaky)

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractgateway (entities)

## Summary
`test_identity_card_composes_a_life` failed once on the 3.13 CI job of the 0.5.0 release (run 36233034955 attempt 1): the card
found 2 sleep moments where it expects 1. The identity card drops a history line when a door event of the same kind falls in the
same clock minute; the entity's automatic "asleep at birth" line only disappears when the entity is created and the door POST
happen within one minute, which a slow runner breaks. Timing flake, not a regression (attempt 2 green).

## Scope
Match history lines to door events by reason or sequence number instead of by minute (or make the test expect the birth
"asleep" moment). Evidence: untracked/missions-2026-09-25/RELEASE-LOG.md (Phase C).

## Validation
The test is deterministic under load (run it 10× concurrently as the console-tui fix did).
