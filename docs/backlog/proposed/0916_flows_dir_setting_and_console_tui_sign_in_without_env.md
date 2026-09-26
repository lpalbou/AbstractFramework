# 0916 — Serve your own flow bundles and sign in to the console TUI without environment variables

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractgateway (settings, console-tui)

## Summary
Two remaining places where the documented way to configure something is an environment variable: the flows directory
(`ABSTRACTGATEWAY_FLOWS_DIR`, no launch flag and no stored setting) and the console TUI sign-in (its README documents
`ABSTRACTGATEWAY_AUTH_TOKEN` as the preferred way). The operator's rule: configuration is a launch flag plus a stored setting
that the consoles can edit; environment variables are at most a reported legacy fallback.

## Why
Found by the root coredoc pass (untracked/missions-2026-09-25/CD/REPORT.md, root row): the root docs still have to mention
these variables because no flag or setting exists.

## Current code reality
Flows directory precedence lives in `abstractgateway/src/abstractgateway/config.py` (~340-345): `ABSTRACTGATEWAY_FLOWS_DIR`,
then `ABSTRACTFRAMEWORK_WORKFLOWS_DIR`, then `ABSTRACTFLOW_FLOWS_DIR`, then the shipped bundles. The console TUI reads the
token from the environment or a flag (`console-tui/README.md`); the gateway's own TUI hand-over mints one-time tokens for
AbstractCode (`apps_manager.py mint_tui_handover`) but not for the console TUI.

## Scope / non-goals
Add `flows.dir` as a stored setting + `serve --flows-dir` flag (three doors, source word reported, env as legacy fallback);
give the console TUI a sign-in path that does not need the token in the environment (the same one-time hand-over the
Assistant and AbstractCode use, or a stored session file with 0600 mode). Not in scope: changing bundle discovery semantics.

## Validation
Settings read reports `flows.dir` with `source`; `serve --flows-dir` wins over the stored value; the console TUI signs in
from a launcher without any token in `env`; docs updated by the coredoc skill.
