# 1341 — Windows: commands run sandboxed under "Deny everything, allow listed workspaces" and under a read-only default

> Package: abstractcore (tools/sandbox.py, tools/sandbox_windows.py), abstractgateway (command_sandbox state, docs)
> Type: feature
> Created: 2026-11-24
> Priority: high
> Labels: windows, command-sandbox, security, workspaces

## Summary

On Windows, agents' commands run sandboxed only for runs set to "Allow everything, refuse listed workspaces"
with read & write by default (abstractcore 2.38.0, `windows-restricted-token`). For the two other workspace
shapes the command is still refused: "Deny everything, allow listed workspaces" (`posture: allowed_only`) and
"Allow everything, refuse listed workspaces" with read-only by default (`default_mode: ro`). macOS and Linux
(bubblewrap) sandbox all three. This item makes Windows enforce all three, so the gateway's command-sandbox
state on Windows is `sandboxed`, not `partial`.

## Why

Operator, 2026-11-24: "this MUST work on any OS, so while this was tested on OSx, this should work seemlessly
on windows and linux"; on the remaining gap: "so you completely failed and released codes that are not
working". A user who picks the stricter posture, or read-only by default, in Workspaces gets every command
refused on Windows with a sentence naming the posture, which is not "works on any OS".

## Current code reality (audited 2026-11-24, abstractcore 2.38.0, abstractgateway 0.23.0)

- `abstractcore/tools/sandbox.py`: `host_sandbox_kind("allowed_only")` returns `none` on win32
  (`WINDOWS_ALLOW_LIST_UNEXPRESSIBLE`); `build_sandbox` refuses `default_mode == "ro"`
  (`WINDOWS_READ_ONLY_UNEXPRESSIBLE`). `windows_rules(spec)` assumes a read & write world: only rows that change
  their surroundings become rules (`deny`, `carve`, `pass`, `ro`, `rw`, `read`).
- `abstractcore/tools/sandbox_windows.py`: the launcher builds a restricted token whose restricting SIDs MIRROR
  the user's identity (the user and every enabled group) plus one SID per rule, removes every privilege
  (traverse checking on), and writes per-rule access-list entries. Mirroring is what makes "everything the
  user can read stays readable": it cannot hide the user's data, and it grants the user's own write access
  everywhere.
- `abstractgateway/command_sandbox.py`: state `partial`, line "Commands sandboxed: Windows restricted token
  (Allow everything, refuse listed workspaces); otherwise commands refused".
- What was measured on Windows 10 (19045), no admin, while building 2.38.0 (prototypes and their test matrices
  in `docs/backlog/evidence/1341_windows_sandbox_remaining_postures/`, findings in its README):
  - **Allow-list posture, restricted token with a small restricting set** (Users + Everyone + RESTRICTED +
    rule SIDs, Low integrity, private desktop): hides the user profile for free and all precedence cases pass,
    but folders at the root of a drive and other drives stay readable through `BUILTIN\Users`; at Medium
    integrity about 580 system folders are writable; Low integrity closes that but needs a Low label on every
    read & write row; Git Bash/MSYS2 programs abort, node child processes with piped stdio and Python
    `multiprocessing` fail (named pipes), schannel TLS fails.
  - **AppContainer**: a perfect allow-list for reading and schannel works, but deny entries for capability SIDs
    are ignored (nested refusals cannot be expressed), the NUL device is denied (`>nul`, `subprocess.DEVNULL`),
    pipes and `dir` fail.
  - **Read-only default**: no restricting-SID set gives "read everything, write only these rows" (the mirrored
    SIDs carry the user's write access; `WRITE_RESTRICTED` ignores deny-read for rule SIDs). Mirror + Low
    integrity + Low labels on the writable rows works (all 50 cases), but an integrity label is state of the
    folder shared by every run: a folder once labelled Low stays writable for later runs that list it
    read-only, and removing the label breaks a concurrent run.
  - `ALL APPLICATION PACKAGES` and other `S-1-15-*` SIDs are rejected as restricting SIDs (error 87).

## Scope

### In scope

- A design that enforces both shapes without admin rights, with no per-run state that can leak between runs,
  and with the nesting rule (most specific row wins; a refusal wins a tie; read-only beats read & write).
  Candidates to evaluate first, in this order:
  1. Read-only default: mirror token at Low integrity, with the Low label applied to the run's read & write
     rows for the life of the command only and guarded by a per-row SID entry (a write then needs BOTH the
     label and the rule SID), so a stale label grants nothing to another run.
  2. Allow-list posture: decide between (a) the small restricting set with its compatibility costs made
     visible in the docs, and (b) an elevated, one-time setup by the installer (dedicated sandbox account or
     firewall-style machine rules, as other agent sandboxes on Windows do), offered when the user picks the
     posture. (b) changes the "no admin" rule and needs the operator's decision.
- `host_sandbox_kind`, `build_sandbox`, `windows_rules` and the launcher for both shapes; the gateway state
  line and sentences; `docs/security.md` "On Windows"; tests in `tests/tools/test_sandbox_windows.py` for the
  three shapes (the macOS test's `POSTURES` matrix is the model); the runtime and gateway end-to-end tests.
- An adversarial review before release, as for 2.38.0.

### Out of scope

- Network isolation; confining a hostile program that asks another service of the session to act for it
  (documented limit on every platform under "Allow everything").

## Acceptance criteria

- [x] On Windows, with a run set to "Deny everything, allow listed workspaces", `execute_command` runs; a file
      in the user profile outside the allowed rows is unreadable, a read-only row is unwritable, a read & write
      row and the run's own folder are writable; refused rows nested in allowed ones are unreadable.
      (AbstractCore 2.39.0, lpalbou/AbstractCore#54: on `main` after the merge, CI run 45520469800, job
      "Windows command sandbox (restricted token)": `test_sandbox_windows: 592 collected, 592 passed, 0
      skipped, 0 failed`, and the real-host smoke on the runner's own profile and drives `real host: 3
      collected, 3 passed` (`tests/tools/test_sandbox_windows_real_host.py`, one case per shape, `allowed_only`
      included: a file in the profile's Documents is unreadable, a write outside the rows and to `HKCU` is
      refused, the row is writable). AbstractRuntime 0.21.0, lpalbou/AbstractRuntime#51: run 45525204097 on
      `main`, the same Windows job prints `abstractcore 2.39.0: every workspace shape sandboxed = True` and
      `sandbox tests: 12 collected, 10 passed, 2 skipped, 0 failed`; the two skips are the older-Core refusal
      test, "this AbstractCore enforces every shape on Windows". Through the gateway: PENDING: AbstractGateway
      0.24.0 (`tests/test_r12w2_e2e_command_sandbox.py`, the "Deny everything" scenario, on the gateway's
      Windows job of PR PENDING-GATEWAY-PR).)
- [x] On Windows, with "Allow everything, refuse listed workspaces" and read-only by default, `execute_command`
      runs; everything the user can read is readable except refused rows; only the read & write rows, the
      run's own folder and its temp folder are writable; a second run that lists a row read-only cannot write
      it while or after a first run had it read & write. (Same AbstractCore and AbstractRuntime jobs as above,
      shape `any_except_denied/ro`. The second-run guarantee is enforced by 256 bucket identifiers, with two
      documented exceptions, each for about one pair of folders in 256: a command of the second run already
      running when the folder first became read & write, and a lost list of labelled folders
      (abstractcore `abstractcore/tools/README.md`, *Command sandbox* > Windows, "Two runs and one folder";
      AbstractGateway `docs/security.md` "Two runs, one folder" on `release/0.24.0`). Through the gateway:
      PENDING: AbstractGateway 0.24.0.)
- [ ] `GET /api/gateway/discovery/tools` on Windows reports `command_sandbox.state: sandboxed`.
      PENDING: AbstractGateway 0.24.0 (state `sandboxed` read on `/api/gateway/discovery/tools` of an installed
      0.24.0 on Windows; root CI `scripts/tests/command_sandbox_smoke.py` then runs all three shapes, root PR
      PENDING-ROOT-PR). Today's released 0.23.0 on this machine reports `partial`.
- [ ] `cmd`, PowerShell, python, git (including Git Bash) and node/npm behave under each shape as documented;
      every program that cannot run is named in `docs/security.md`. **Not met as written.** cmd, PowerShell,
      python (`venv`, `pip install`), node and git (`init`, `add`, `commit`, `status`, `diff`, `log`, `branch`,
      `checkout`, https through its own TLS) are documented as working under every shape (abstractcore tools
      README; the real-host smoke runs cmd, PowerShell, python and git under all three; node is documented,
      not exercised by a test I could find). What does not run, as AbstractGateway `docs/security.md` "On
      Windows" > Limits names it on `release/0.24.0`: Git Bash and other MSYS2/Cygwin programs (`bash`, `sh`,
      Git's own `ssh-keygen`, and what git runs through its shell: `git clone` of a local folder or a
      `file://` address, hooks, `!` aliases) stop at start under the two stricter settings when a Git Bash
      window or another MSYS2 program is already running in the session (they start when none is); Windows'
      own `ssh-keygen` (`%SystemRoot%\System32\OpenSSH\ssh-keygen.exe`) writes the private key and then fails
      on the public one under every setting, the read & write default included, cause not identified (follow-up
      1345); Windows' built-in TLS (`curl.exe`, `Invoke-WebRequest`, .NET programs) is unavailable under every
      setting; Store app aliases under `WindowsApps` (the `python`, `pwsh`, `winget` stubs) do not start. So
      Git Bash does not "behave" under the stricter settings while another MSYS2 program runs; the programs
      that cannot run are named.
- [ ] CI `windows-sandbox` (abstractcore, abstractruntime) and the gateway's Windows job run the three shapes
      and fail on a skip. **Partly met.** AbstractCore's job fails on any skip (fewer than 60 cases, a skip or
      a failure exits) and its real-host step fails unless its 3 shape cases pass. AbstractRuntime's job
      accepts exactly the skips the installed Core explains (with 2.39.0: only the older-Core refusal test) and
      fails on any other skip or on fewer than 8 tests. The gateway's `model-host-windows` job on
      `release/0.24.0` runs `pytest tests/test_r12w2_command_sandbox.py tests/test_r12w2_e2e_command_sandbox.py`
      with no skip gate: a skipped shape there does not fail it. PENDING: AbstractGateway 0.24.0 (gateway PR
      PENDING-GATEWAY-PR: add the skip gate, or record that it is not added).

## Testing

- `python -m pytest tests/tools/test_sandbox_windows.py tests/tools/test_sandbox_spec.py` (abstractcore, Windows)
- `python -m pytest tests/test_r12_workspace_sandbox_windows.py` (abstractruntime, Windows)
- `python -m pytest tests/test_r12w2_e2e_command_sandbox.py tests/test_r12w2_command_sandbox.py` (abstractgateway, Windows)

## Receipts

- lpalbou/AbstractCore#53 (2.38.0: the first shape), lpalbou/AbstractGateway#115 (the `partial` state).
- Prototypes: `docs/backlog/evidence/1341_windows_sandbox_remaining_postures/`.
- Completed 2026-11-25. lpalbou/AbstractCore#54 (merged 2026-11-25, merge commit 3160eb5, tag v2.39.0 on it,
  PyPI `abstractcore` 2.39.0 uploaded 2026-11-25T01:09Z; `main` CI run 45520469800, Windows job 138890733539).
- lpalbou/AbstractRuntime#51 (merged 2026-11-25, merge commit 52858eb, tag v0.21.0 on it, PyPI
  `AbstractRuntime` 0.21.0 uploaded 2026-11-25T01:28Z; PR run 45524750402 and `main` run 45525204097, Windows
  jobs 138905198873 and 138906708489: "abstractcore 2.39.0: every workspace shape sandboxed = True").
- AbstractGateway 0.24.0: PENDING: AbstractGateway 0.24.0 (gateway PR PENDING-GATEWAY-PR; branch
  `release/0.24.0`, head d1420f8 on 2026-11-25, pins `abstractcore==2.39.0`, `AbstractRuntime==0.21.0`; a CI
  preview PR lpalbou/AbstractGateway#116 is marked "do not merge"). PyPI `abstractgateway` 0.24.0: PENDING.
- Root: AbstractFramework 0.14.4 pins gateway 0.24.0, core 2.39.0, runtime 0.21.0 (branch `release/0.14.4`;
  root PR PENDING-ROOT-PR). The installer's "Shell:" line names the tier of the installed gateway, and
  `scripts/tests/command_sandbox_smoke.py` runs the three shapes when the gateway reports `sandboxed`.
- Limits documented, not fixed: Git Bash/MSYS2 under the two stricter settings, Windows' own `ssh-keygen`
  (new proposed item 1345), Windows' TLS, Store app aliases.
