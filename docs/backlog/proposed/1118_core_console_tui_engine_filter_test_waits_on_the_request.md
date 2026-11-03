# 1118 — AbstractCore console TUI: the engine-filter test waits on the request, not on the screen

> Package: abstractcore (console-tui crate `abstractcore-console`, `console-tui/tests/headless_ui.rs`)
> Type: bug
> Created: 2026-11-03
> Priority: normal
> Labels: tests, flaky, console-tui, ci

## Summary

`models_engine_e_cycles_through_seen_engines` (`console-tui/tests/headless_ui.rs` l.3658 on abstractcore `dcde7ccc`)
is flaky. It opens the Models tab with the fixture catalog, presses `e`, waits until the screen shows
"engine ollama", checks that no non-ollama artifact is listed, and then asserts that the mock backend received
`catalog q= engine=ollama fits=false`. The screen can show the new filter before that catalog request reaches the
mock, so the last assertion sometimes runs too early.

## Why

It failed once in the local release gate for abstractcore 2.34.0 (job "Test console-tui crate" of `release.yml`,
run dir `~/Library/Caches/ci-gate/runs/abstractcore-20261103-225929-9b24e976`):
`assertion failed: h.mock.called("catalog q= engine=ollama fits=false")`, while the same crate passed in the
`ci.yml` console-tui job of the same run and when the job was re-run alone. The crate had no change in that
release. A flaky test turns a good release red (root ADR 0050: red CI is the exception).

## Scope

### In scope

- Wait on the request rather than on the screen: settle until the mock has seen
  `catalog q= engine=ollama fits=false` (a bounded wait like `settle_until`, failing with what was seen), then check the
  screen.
- Look for the same pattern (a screen wait followed by an immediate `mock.called(...)` assertion) in the other
  Models-tab tests of `headless_ui.rs`, for example `models_fits_only_f_toggles_the_backend_filter`, and apply the same
  rule where it holds.

### Out of scope

- Changing the console's request or rendering order.

## Acceptance criteria

- [ ] The test passes 200 times in a row under load (for example beside a running Core test job).
- [ ] With the request removed from the engine-filter path, the test still fails (it checks the request, not only
  the label).

## Receipts

- Release PR AbstractCore #50 (gate section); log `untracked/release-2026-11-03/w3/gate-rel-2.34.0-9b24e976.log` and
  re-run `w3/gate-rel-2.34.0-9b24e976-rerun-console-tui.log` (root repository, not tracked).
