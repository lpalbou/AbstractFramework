## Summary
- Rebuild bubble visibility state logic from actual Qt window state.
- Remove click‑based toggles for visibility decisions.

## Why
- Tray clicks were opening and closing the app due to toggle logic.
- Visibility must be derived from real widget state, not inferred clicks.

## Scope
- Add an explicit `BubbleVisibility` state derived from Qt widget state.
- Use that state in `show_chat_bubble` and tray click handlers.
- Remove duplicate visibility helpers.

## Out of Scope
- Changes to gateway APIs.
- Changes to voice playback logic.

## Dependencies
- `abstractassistant/app.py`
- Qt widget visibility APIs (`isVisible`, `isMinimized`, `windowState`)

## Expected Outcomes
- Tray click always opens/focuses the app, never closes it.
- “Shown/hidden” is computed from actual Qt state.

## Plan
- Implement visibility state derivation.
- Rewire tray click handlers and show logic to use it.
- Run tests.

## Report
- **Root cause**: `show_chat_bubble` had a `_run_is_active()` gate that refused to open the UI when a gateway run was still active. After double-click-stopping TTS, the run remained active, so subsequent clicks were blocked.
- **Fix**: completely rewrote the tray click state machine. `show_chat_bubble` now **never refuses to open**. Nothing gates it — not run state, not voice state. The rule is: click = show.
- **Visibility source of truth**: `BubbleVisibility` enum derived from live Qt widget state (`isVisible`, `isMinimized`, `windowState`).
- **Voice intercept**: tray clicks only short-circuit to pause/resume/stop when TTS is truly active; all other paths unconditionally show the app.
- **Removed**: run-active blocking, click-toggle hide behavior, duplicate visibility helpers.
- **Crash fix**: `handle_bubble_response` and `handle_bubble_error` were calling `hide_chat_bubble()` after every response/error, hiding the widget mid-processing (segfault on macOS). Now they are informational-only and never touch visibility.
- **Crash fix**: `handle_bubble_response` and `handle_bubble_error` were calling `hide_chat_bubble()` after every response/error, hiding the widget mid-processing (segfault on macOS). Now they are informational-only and never touch visibility.
- **Auto-hide after send removed**: `QTimer.singleShot(500, self.hide)` after starting a worker was hiding the bubble while tool approval dialogs were still expected, causing crashes when the dialog closed over a hidden widget.
- **Crash protection**: `on_agent_event`, `_handle_tool_request`, `_handle_ask_user`, and `_finalize_response` are now wrapped with try/except + stderr tracebacks so crashes are never silent.
- **faulthandler**: enabled at startup for native segfault tracebacks.
- **Global exception hooks**: `sys.excepthook` and `threading.excepthook` print full tracebacks to stderr before the process dies.
- **Font fix**: removed `SF Mono` from font stacks (not available in Qt on macOS); using `Menlo`, `Monaco`, `Consolas`.

## Tests
- `python -m pytest abstractassistant` — 73 passed
