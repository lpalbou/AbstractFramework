# Backlog Item: 112_macos_installer_full_step_wizard

## Task
Convert the entire macOS installer into a step-by-step wizard (one card at a time).

## Summary
Users should not scroll a long page. Convert install mode, components, location, install, and setup into wizard steps with Back/Next navigation while keeping the install button and progress in the install step.

## Reason
The current single-page UI is overwhelming and contradicts the requested guided installer experience.

## Scope
### In scope
- Show only one primary step at a time.
- Add Back/Next navigation for install steps.
- Keep install progress + logs within the Install step.

### Out of scope
- Redesigning the underlying installation logic.
- Changing the component manifest or dependency graph.

## Dependencies
- Existing installer UI and event flow.

## Expected Outcomes
- The installer displays one step/card at a time.
- Navigation works reliably across install phases.

## Report
### Decision summary
- Implemented an outer wizard controller to show one install step at a time and added Back/Next navigation across the entire installer.

### Implementation
- `src/index.html` wraps each major panel as a `wizard-step` and adds a wizard navigation bar.
- `src/app.css` adds wizard step visibility rules and navigation styling.
- `src/app.js` manages wizard state, navigation, and locks step 5 until installation completes.

### Tests
- `cargo tauri build` (release) in `abstractinstallers/abstractframework-macos/src-tauri`.

### Results
- The installer now presents one step at a time with Back/Next.

### Follow-ups
- Validate navigation flow on small screens and ensure install/progress lock behavior is clear.
