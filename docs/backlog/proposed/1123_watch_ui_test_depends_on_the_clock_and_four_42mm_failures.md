# 1123 — Watch UI tests: one depends on the clock; four fail on the 42 mm simulator

> Package: abstractassistant
> Type: bug
> Created: 2026-11-04
> Priority: normal
> Labels: tests, flaky, watch, ui-tests, ci

## Summary

`AvatarConversationUITests.testAcceptedHumanGuidanceReturnsAfterLeavingAndReopeningTheConversation`
(`watch/apple/UITests/AvatarConversationUITests.swift` l.33 on abstractassistant `3d1a3ba`) passed until about 04:20 on
2026-11-04. Since about 05:00 it fails on every simulator, including origin/main `3d1a3ba` on a fresh simulator. The
"QC" conversation row is no longer found after opening Sessions. Nothing in the code changed in between, so the test
or one of its mock fixtures depends on the clock.

The same Watch UI pass (the Q6 lane, Series 11 42 mm simulator) has four other failing tests. They fail identically on
origin/main `3d1a3ba`, so they are older than the change that lane made:
- `AskStatusUITests.testANoteOnListeningEndsWhenTheOrbSpeaks` (`watch/apple/UITests/AskStatusUITests.swift` l.8)
- `OrbPageLayoutUITests.testTheOrbStaysWhereAFreshPagePutsIt` (`OrbPageLayoutUITests.swift` l.30)
- `VoiceButtonUITests.testHoldOnAFinishedVoicePlaysItFromTheStart` (`VoiceButtonUITests.swift` l.220)
- `VoiceButtonUITests.testNearMissesNeverStartListening` (`VoiceButtonUITests.swift` l.157)

## Why

A test that passes or fails by the hour cannot gate a release (root ADR 0050: red CI is the exception). The mock
mixes clocks: `MockGatewayClient.sampleRuns` dates its runs relative to now (`Date()` minus `minutesAgo`; the QC run is
12 minutes old, its older siblings whole days older). Other fixtures carry absolute dates (for example the Morning
digest automation's `2026-10-17T05:04:00Z` / `nextFireAt 2026-10-18T05:00:00Z`). A sessions list that groups or
filters by day, by a recent-activity window, or against one of those absolute dates can drop the "QC" row at some
hours and keep it at others.

## Scope

### In scope

- Name the cause: which fixture date or relative-time window (a day boundary, a "recent" cutoff, an absolute date
  compared with now) removes the "QC" row.
- Make the test deterministic: the mock and the app read one injected or frozen clock under `--mock` (a launch
  argument), so the fixture dates mean the same at any hour.
- The four 42 mm failures: the cause of each (layout at 42 mm, timing, or a stale expectation), then a fix or a
  documented size-specific skip with its reason.

### Out of scope

- Behaviour changes in the app beyond what the fix needs.

## Acceptance criteria

- [ ] The cause of the "QC" row disappearing is named in the fix, with the fixture or window involved.
- [ ] The test runs under a frozen or injected clock and passes at any hour. It is shown green with the clock set
      before and after the boundary that broke it (for example 04:00 and 06:00 local, and just after midnight UTC).
- [ ] Each of the four 42 mm tests listed above is green on the Series 11 42 mm simulator, or skipped there with the
      reason written in the test; the 46 mm and Ultra 49 mm results are unchanged.
- [ ] The Watch UI suite runs green twice in a row on a fresh simulator.

## Receipts

- Lane notes (root, untracked): `untracked/release-2026-11-03/q6-watch/pr-body.md` ("Found on the way" and the Watch
  UI results), `gate-8121ea2.log`, mutation logs and screenshots in the same folder.
