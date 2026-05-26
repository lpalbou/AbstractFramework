## Backlog Item: 115_macos_installer_finish_and_nav

### Task
Remove duplicate Back/Next controls in the setup step and add a Finish action to exit the installer.

### Summary
The setup screen shows two sets of navigation controls and lacks a way to exit the installer. Hide the outer wizard nav during setup, keep a single Back/Next for setup sub-steps, and show a Finish button.

### Reason
Duplicate navigation is confusing, and users need a clear way to complete the flow and exit the installer.

### Scope
#### In scope
- Hide the main wizard nav while in the setup step.
- Always show a Finish button in setup.

#### Out of scope
- Changing setup sub-step content.
- Modifying install logic.

### Dependencies
- Installer wizard UI state.

### Expected Outcomes
- Only one Back/Next pair is visible in setup.
- Finish exits the installer.

### Status
Completed. Full report is in `docs/backlog/completed/115_macos_installer_finish_and_nav.md`.
