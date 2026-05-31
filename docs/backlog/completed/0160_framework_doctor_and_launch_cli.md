# Proposed: Framework Doctor And Launch CLI

## Metadata
- Created: 2026-05-31
- Status: Completed
- Completed: 2026-05-31

## ADR status
- Governing ADRs: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- ADR impact: None

## Context
The root `abstractframework` package currently exposes helper functions for release profile and
installed package status, but no CLI. Installers and technical users both need the same readiness
checks and launch guidance.

## Current code reality
- `abstractframework/__init__.py` defines release pins, distribution mappings,
  `get_release_profile()`, `get_installed_packages()`, and `print_status()`.
- `pyproject.toml` exposes the `abstractframework` console script.
- `abstractframework.cli` implements `doctor` and `manifest`.
- Existing app launch behavior lives in package-specific commands and scripts, such as Gateway,
  Flow, Code, Observer, and local launcher scripts.
- `docs/install.md`, `docs/api.md`, and README references document `abstractframework doctor`.

## Problem or opportunity
Without a shared doctor/launch surface, GUI installers tend to reimplement checks and technical
users get inconsistent troubleshooting paths.

## Proposed direction
Add a small root CLI with two likely commands:

- `abstractframework doctor`: inspect installed versions, profile consistency, Python/Node
  prerequisites, Gateway/Flow readiness, local hardware availability, and common config problems.
- `abstractframework launch`: start or delegate to the default local Gateway/Flow experience once
  the install is healthy, using the same checks as the installer.

Start with `doctor`. Add `launch` only if it can delegate cleanly to existing package CLIs without
becoming another process manager.

## Why it might matter
The CLI becomes the shared support surface for users, installers, docs, and future updater flows.
It helps technical users self-diagnose and lets non-technical installer UI show reliable, familiar
failure messages.

## Promotion criteria
- Installer app needs reusable readiness checks.
- Support reports show install failures that could be diagnosed by a root command.
- The root package remains a meta-package but needs a small operational helper surface.

## Validation ideas
- Unit-test version/pin checks against `RELEASE_VERSIONS`.
- Run `abstractframework doctor` in a base install and in missing-dependency simulations.
- Verify the command does not import heavy local inference stacks unless explicitly checking them.
- If `launch` is added, verify it starts Gateway/Flow without leaking admin credentials to browser
  sessions.

## Non-goals
- Do not duplicate Gateway admin/user management.
- Do not make root `abstractframework` a long-running service.
- Do not replace package-specific CLIs.

## Guidance for future agents
Keep the CLI thin. It should orchestrate checks and delegate. If it starts to own app logic, move
that logic back to the relevant package or installer repo.

## Completion report
- Added `abstractframework doctor` with package pin checks, Python version checks, Node/npm probes,
  and Apple/GPU hardware indicators.
- Added JSON output support through `abstractframework doctor --json`.
- Added tests for the doctor report and manifest check command.
- Did not add `abstractframework launch`; the design still says launch should only be added if it
  can delegate cleanly without becoming a new process manager.
