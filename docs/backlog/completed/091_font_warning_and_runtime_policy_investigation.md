## Summary
- Remove Qt “Sans-serif” font alias warnings on startup.
- Investigate runtime tool defaults warning without code changes.

## Why
- Startup should be clean and deterministic; missing font aliases are noisy.
- Tool policy defaults should come from the runtime, not fall back due to import errors.

## Scope
- Replace `sans-serif` font fallback with `Sans Serif` in Qt styles.
- Identify why `ToolApprovalPolicy` is missing at runtime and document fix steps.

## Out of Scope
- AbstractRuntime code changes.
- Gateway backend changes.

## Dependencies
- Qt styles in `qt_bubble.py`, `toast_window.py`, `history_dialog.py`, `ui_styles.py`.
- Installed `abstractruntime` package version.

## Expected Outcomes
- No Qt font alias warning on startup.
- Clear root cause + remediation steps for runtime tool defaults warning.

## Plan
- Update style sheets to use a valid generic font family.
- Inspect installed `abstractruntime` and compare to repo version.
- Document fix steps.
- Run tests.

## Report
- **Font warning fix**: removed generic `sans-serif`/`Sans Serif` fallbacks and `-apple-system` to avoid Qt alias warnings; now using explicit macOS-safe fonts (`Helvetica Neue`, `Helvetica`, `Arial`).
- **Runtime defaults investigation**: the running environment imports `abstractruntime` from `/opt/anaconda3/lib/python3.12/site-packages/abstractruntime`, which does **not** export `ToolApprovalPolicy`; the repo version does. The warning is caused by a version mismatch on the Python path.
- **Remediation**: uninstall the old runtime package and install the repo version in editable mode:
  - `pip uninstall abstractruntime`
  - `pip install -e /Users/alboul/tmp/abstractframework/abstractruntime`
  - Verify with:
    - `python - <<'PY'\nimport abstractruntime, importlib\nm = importlib.import_module(\"abstractruntime.integrations.abstractcore.tool_executor\")\nprint(abstractruntime.__file__)\nprint(hasattr(m, \"ToolApprovalPolicy\"))\nPY`

## Tests
- `python -m pytest abstractassistant`
