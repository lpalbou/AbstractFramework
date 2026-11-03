# Tray runtime dependency repair — 2026-10-31

The operator's Appearance screenshot showed `No module named 'abstractavatar'` despite the prior
development-environment installation. The prior installed-package check targeted
`abstractassistant/.venv`; it did not establish availability in the running stack's environment.

## Actual runtime

- Running tray process: `untracked/deploy/root/.venv/bin/python -m abstractassistant.cli`.
- Parent: existing `bash scripts/start-local.sh` supervisor.
- `untracked/deploy/root/.venv` resolves to the framework's shared `.venv`.
- `untracked/deploy/root/abstractassistant` resolves to the source Assistant checkout.
- The shared environment initially had no `abstractavatar` package.

Installed the tested local `abstractavatar-0.1.0-py3-none-macosx_26_0_arm64.whl` into that exact
interpreter with `python -m pip install --no-deps`. No gateway/tray process was restarted and no
user preferences changed. No package was published.

## Verification

Using `untracked/deploy/root/.venv/bin/python`, with only the same Assistant source path used by
the local launcher (no renderer source/library override):

- `abstractavatar` loads from the shared environment's site-packages.
- The native catalog contains 44 designs.
- Actual `WindowPage` constructed in a missing-renderer condition recovers on `refresh()`, with
  44 enabled/selectable designs and the normal generated-on-device message.
- Actual Qt ActivityAvatar renders the installed native `watch-nebula` frame and releases its
  handle when hidden.

The existing Settings navigation calls the selected page's `refresh()`. Switching away from
Appearance and back reloads the catalog in the running app without restarting its gateway or
discarding the conversation.
