# 1342 — Windows: defects found next to the command sandbox (to triage into items)

> Package: abstractgateway, abstractruntime, abstractcore, abstractcode, abstractobserver
> Type: bug
> Created: 2026-11-24
> Priority: normal
> Labels: windows, command-sandbox, triage

## Summary

Defects seen while building and deploying the Windows command sandbox (abstractcore 2.38.0, abstractruntime
0.20.0, abstractgateway 0.23.0) that were not fixed there. Each needs its own item once confirmed; they are
kept together here so none is lost.

## Why

They were reported to the operator on 2026-11-24 as "found but not fixed". None blocks commands under the
default workspace policy, but each is a visible Windows defect or a gap in the same feature.

## Current code reality (audited 2026-11-24)

1. **Windows credential folders are not in a run's built-in refusals.** `abstractgateway/run_workspace_guard.py`
   `apply_builtin_tool_deny` uses `BUILTIN_DENY_HOME_RELPATHS` only; `workspace_browse.py`
   `BUILTIN_DENY_HOME_RELPATHS_WINDOWS` (`AppData\Roaming\Microsoft\Credentials`,
   `AppData\Local\Microsoft\Credentials`, `AppData\Roaming\Microsoft\Protect`, `AppData\Roaming\gcloud`) is shown
   in the policy view but never reaches the run: file tools and the sandbox do not refuse those folders. Before
   adding them, check that the sandbox can write its entries there (they hold system-attributed files); a
   refusal that cannot be written stops every command (exit 126).
2. **The entity exec tool cannot start a program on Windows.** `abstractruntime/identity/tools.py` (around
   lines 1246 and 1312) splits the command with POSIX rules and passes an environment of PATH, HOME, LANG and
   TMPDIR only: without `SystemRoot`, `ComSpec` and `PATHEXT` a Windows process fails at start.
3. **`execute_command` describes itself with Unix examples only** (`abstractcore/tools/common_tools.py`,
   `ls -la`, `grep | head`), and the command runs through `cmd.exe` on Windows. A model then writes commands
   that only work where Git's tools are on PATH. Also: where `python` is only the Microsoft Store placeholder
   (`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`), `python ...` fails in a command, sandboxed ("Access is
   denied") or not ("Python was not found").
4. **`shell_exec` (the persistent shell) is POSIX-only** (`abstractcore/tools/shell_session.py`: `pty`); on
   Windows the only `bash` on PATH is often the WSL launcher, which would run outside a Windows sandbox. It is
   not offered on Windows today; decide whether Windows gets a persistent shell.
5. **AbstractCode web does not ask to sign in again when its session ends.** A password change ends the app's
   session; the Automations list then says "Sign in to the gateway to manage automations." (ui-kit 0.9.29,
   code web 0.16.3) but the conversation list stays stale and no sign-in prompt appears: the page has to be
   reopened from the console.
6. **AbstractObserver is not rebuilt on ui-kit 0.9.29**: it still words an ended session as "The gateway gave an
   unexpected answer" in its Automations page.
7. **Windows tests that fail on an untouched checkout**: abstractcore `tests/tools/test_shell_session.py`,
   `tests/test_install_scripts.py::test_install_sh_cut_mid_download_runs_nothing`; abstractcode web vitest (4
   tests) and its `npm run build` hash checks under CRLF checkouts.

## Scope

### In scope

- Confirm each point, then write one planned item per confirmed defect (or close it here with the reason).

### Out of scope

- The two workspace shapes Windows still refuses (1341), the framework release (1339), the installer (1340).

## Acceptance criteria

- [ ] Each of the seven points is either a planned item with its own acceptance criteria or recorded here as
      not a defect, with the evidence.

## Testing

- `python -m pytest tests/test_r12w2_e2e_command_sandbox.py` (abstractgateway, Windows; extend it with the
  Windows credential folders for point 1)
