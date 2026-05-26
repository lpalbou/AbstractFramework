# Backlog Item: 117_macos_installer_choice_alignment

## Task
Align the install-mode radio choices with the component checkbox layout.

## Summary
The install-mode radio buttons did not align with the checkbox rows. Update the layout so radio options match the checkbox spacing and typography.

## Reason
Consistent alignment improves scanability and visual polish.

## Scope
### In scope
- Adjust radio choice layout to use the same grid alignment pattern as checkboxes.

### Out of scope
- Changing component checkbox styles.
- Redesigning the choice content.

## Dependencies
- Installer CSS and layout.

## Expected Outcomes
- Radio options visually align with checkbox rows.

## Report
### Decision summary
- Adjusted the radio option layout to mirror the checkbox alignment.

### Implementation
- `src/app.css` now uses a two‑column grid for choices and aligns label text in a meta container.
- `src/index.html` wraps radio labels in a `.meta` container for consistent layout.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- Radio options now match checkbox alignment.
