## Summary
- Remove the tiny tray-adjacent rectangle artifact shown when opening AbstractAssistant from macOS tray.

## Why
- The current workaround introduces a visual menu artifact (small rectangle) under the tray icon.
- UX requirement is clean tray interaction: ready-state click opens app with no extra popup artifacts.

## Scope
- Remove artifact-causing menu placeholder from macOS tray setup.
- Keep existing activation fallback behavior for ready-state open reliability.
- Validate with targeted tray fallback tests.

## Out of Scope
- Changes to run/speaking click semantics.
- Broader tray architecture rewrites.

## Dependencies
- `abstractassistant/abstractassistant/app.py`
- `abstractassistant/tests/basic/test_tray_context_menu_fallback.py`

## Expected Outcomes
- No tiny rectangle/menu artifact appears under tray icon.
- Fresh-launch ready-state click still opens app reliably.

## Plan
- Remove the dummy placeholder action from the macOS tray context menu.
- Keep `aboutToShow` fallback handler unchanged.
- Re-run tray fallback regression tests.

## Report
- **Root cause**: the tiny rectangle under the tray icon was the temporary placeholder menu entry used to force context-menu lifecycle callbacks on macOS.
- **Implementation**:
  - Removed the dummy disabled `QAction` from the darwin tray menu setup in `abstractassistant/app.py`.
  - Kept the existing `aboutToShow -> _qt_on_context_menu_show` fallback and activation timestamp guard unchanged.
- **Result**:
  - The tray keeps reliable ready-state open behavior.
  - The extra menu artifact source is removed.

## Tests
- `pytest -q abstractassistant/tests/basic/test_tray_context_menu_fallback.py` → **3 passed**
