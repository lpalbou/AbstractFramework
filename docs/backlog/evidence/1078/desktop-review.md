# AbstractAvatar desktop Assistant integration

Desktop worker scope: Python/Qt palette, local preferences, Appearance controls, optional packaging,
relevant public documentation and tests. No web, Watch or iPhone files edited. No commits, release,
production gateway requests or persistent processes created.

## Implemented

- Optional `avatar_enabled` (false), `avatar_style` (`halo`) and `avatar_animated` (true) preferences.
  Stable keys are normalized without importing native code. They round-trip with other preferences
  and do not enter runtime/run scope.
- `abstractassistant/ui/avatar.py::ActivityAvatar` presents owned RGBA8 frames from the shared
  AbstractAvatar native library. No private geometry implementation, inference, network or ambient
  library-path search. The package is imported only when used.
- A 96 px portrait appears below the palette header when enabled. Existing geometry/reflow leaves
  transcript and composer separate; the menu-bar icon and click behavior are unchanged.
- Actual error, speech playback, recording/listening, pending waits, tool work and run activity
  select all seven shared states. Speech/microphone levels and transient Ready pointer gaze are
  host-fed. Theme anchors derive from the app's semantic palette.
- Appearance contains the enabled switch, authoritative catalog design picker and motion switch.
  Missing native support has an explicit actionable message and cannot silently substitute an orb.
- Cadence is bounded at 2 fps Ready, 6 fps Waiting and 12 fps active. Meter/pointer bursts cannot
  bypass the frame budget. Motion-off freezes time/level and owns no animation clock; state changes
  still redraw. Hidden/disabled widgets stop clocks and release their handle. Qt destruction closes
  the native owner; image bytes are copied into Qt ownership.
- Optional `[avatar]` extra depends on `abstractavatar>=0.1.0`. A PyInstaller hook collects the
  installed optional native library. Base import/launch does not require it.

## Files

- `abstractassistant/abstractassistant/ui/avatar.py` (new adapter)
- `abstractassistant/abstractassistant/app.py` (small host integration)
- `abstractassistant/abstractassistant/preferences.py`
- `abstractassistant/abstractassistant/ui/settings/pages.py`
- `abstractassistant/pyproject.toml`
- `abstractassistant/packaging/macos/hooks/hook-abstractavatar.py`
- `abstractassistant/tests/basic/test_activity_avatar.py`
- `abstractassistant/README.md`, `CHANGELOG.md`, `docs/settings.md`, `docs/getting-started.md`
- `abstractassistant/llms-full.txt` regenerated with the existing generator

Other modified web/backlog files in the shared repo belong to concurrent workers and were left intact.

## Independent verification

Combined relevant selection: **231 passed**, four dependency deprecation warnings, 3.43 s.
This includes real native frames for all seven states and an actual AssistantPalette construction,
layout and tool-state change. The shared library's catalog had 44 entries at that check.

Command (from framework root):

```sh
PYTHONPATH=/Users/albou/tmp/abstractframework/abstractavatar/python \
ABSTRACTAVATAR_TEST_LIBRARY=/Users/albou/tmp/abstractframework/abstractavatar/target/release/libabstractavatar.dylib \
ABSTRACTAVATAR_CAPTURE_DIR=/tmp/abstractavatar-desktop QT_QPA_PLATFORM=offscreen \
abstractassistant/.venv/bin/python -m pytest -q \
  abstractassistant/tests/basic/test_activity_avatar.py \
  abstractassistant/tests/basic/test_assistant_palette.py \
  abstractassistant/tests/basic/test_run_lifecycle_fixes.py \
  abstractassistant/tests/basic/test_voice_mode.py \
  abstractassistant/tests/basic/test_hold_to_talk.py \
  abstractassistant/tests/basic/test_run_scope_preferences.py \
  abstractassistant/tests/basic/test_tray_voice_meter.py \
  abstractassistant/tests/basic/test_settings_pages.py \
  abstractassistant/tests/basic/test_design_polish.py \
  abstractassistant/tests/basic/test_window_defaults.py --disable-warnings
```

The source-path environment is test-only; the application itself imports the installed package
and accepts no sibling-source or machine-cache fallback. Native integration was tested with the
core worker's built binary; final wheel installation proof belongs to shared-core/package review.

Screenshot: `/tmp/abstractavatar-desktop/assistant-desktop.png`, inspected with view_image. It shows
the actual palette with watch-ocean, a native portrait under the header and separate transcript and
composer. Screenshot state is synthetic local activity; no live run or real audio was started.

`git diff --check` passed. Python modules compiled. llms-full generator completed.

An earlier isolated broad selection (before the new test module retained QApplication) had
140 passes and 3 deleted-Qt-wrapper failures in existing stat-detail/status tests; an isolated
three-node rerun had two passes and the same deleted _ChipHover failure. Holding QApplication
through the new widget fixture yielded the clean 231-test combined run. No unrelated stat-detail
source or existing test fixture was patched.

## Limits and review focus

- No full platform test matrix, signed macOS bundle or actual system-tray interaction was executed.
  Tray behavior is protected by existing tests and its implementation was left unchanged.
- The renderer is synchronous at 96 px with bounded host cadence; geometry fidelity/full-catalog
  performance and native/Wasm parity are shared-core review scope.
- Motion-off is an explicit user preference; no claim of automatic macOS accessibility preference
  synchronization is made.
- The optional-dependency release remains coordinated with AbstractAvatar publication. No version
  was published by this worker.

Ready for the designated adversarial reviewer. Residual package/build/platform proof must be
integrated by the coordinator before final approval.
