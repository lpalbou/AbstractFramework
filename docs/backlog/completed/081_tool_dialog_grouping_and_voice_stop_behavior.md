## Summary
- Keep tray voice-stop actions from opening the chat bubble.
- Redesign the tools selector to be compact and grouped by tool section.
- Ensure tool selection and approval preferences stay in sync with sessions.

## Why
- Stopping speech should not change app visibility; it breaks user intent.
- The tools dialog is oversized and unstructured, making it hard to scan.
- Grouped tools improve discoverability and align with `abstractcode/web`.

## Scope
- Update tray click handling and any voice-stop paths to avoid auto-showing the UI.
- Compact the tools dialog (spacing, sizes) and group tools by section.
- Surface toolset metadata from discovery and infer groups when missing.

## Out of Scope
- Changing gateway server behavior or tool execution policy defaults.
- Redesigning the main chat UI or non-tools dialogs.
- Implementing new tool execution backends.

## Dependencies
- Tool discovery data from gateway or local default tool specs.
- Existing tool approval policy defaults from AbstractRuntime.

## Expected Outcomes
- Stopping voice never opens the chat bubble.
- Tools dialog is smaller, grouped, and faster to scan.
- Tool approval preferences remain tied to the current session.

## Plan
- Inspect tray click and voice-stop code paths for unintended UI show.
- Implement toolset grouping and compact styling in the tools dialog.
- Validate tool discovery surfaces toolset metadata and apply inference fallback.

## Report
- **Voice stop visibility**: single-click pause/resume now always returns without opening the bubble; the TTS double-click stop action no longer raises or shows the UI.
- **Tool dialog layout**: compacted spacing/button sizes and resized the dialog while grouping tools into sections (File system, Internet, System, Comms, SmartNote, Other).
- **Tool metadata**: tool discovery now carries `toolset` and `when_to_use` metadata (used for grouping and filter matching); missing toolsets are inferred from tool names.

## Tests
- `python -m pytest abstractassistant` (passed; warnings about tests returning non-None values).
