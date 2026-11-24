# Evidence for 1341: Windows sandbox prototypes for the two remaining workspace shapes

Prototypes written on 2026-11-24 (Windows 10 build 19045, no admin rights) while building the Windows command
sandbox released in abstractcore 2.38.0. They are NOT the released code (`abstractcore/tools/sandbox_windows.py`
is); they explore the two shapes 2.38.0 still refuses. Each prototype is standard library + ctypes and writes
access-list entries only on the folders it is given: run them on scratch folders only.

| File | What it is |
|---|---|
| `allow_list_prototype.py` | Launcher for "Deny everything, allow listed workspaces": restricted token with a small restricting set (Users, Everyone, RESTRICTED, rule SIDs, a per-launch SID), Low integrity, a private desktop, a kill-on-close job; also an AppContainer mode |
| `allow_list_test_matrix.py` | Its experiments (base SID sets, precedence of nested rules, writable places, registry, process access, tools) |
| `read_only_default_prototype.py` | Launcher and rule application for "Allow everything, refuse listed workspaces": mirror token, integrity labels, `access_check` |
| `read_only_default_tests.py` | Its experiments (read & write default, the four read-only-default variants B1..B4, escape probes) |

## What they established

Allow-list posture (restricted token, no mirror):
- Working base set: `BUILTIN\Users` + `Everyone` + `RESTRICTED` + rule SIDs. `ALL APPLICATION PACKAGES` and any
  `S-1-15-*` SID are rejected by `CreateRestrictedToken` (error 87). Without `Everyone` the NUL device is
  denied; without `RESTRICTED` PowerShell cannot read the registry; a private desktop replaces the logon SID.
- The user profile is unreadable with no entry written (its access list names the user only).
- Not hidden: folders at the root of a drive, other drives, `C:\ProgramData` (readable through `Users`). A deny
  row closes a root folder the user owns; system-owned ones cannot take it.
- Writes: at Medium integrity about 580 folders and 16 HKLM keys are writable; at Low integrity almost none,
  but each read & write row then needs a permanent Low label.
- Breaks: MSYS2/Cygwin programs (Git Bash, git hooks), node child processes with piped stdio and Python
  `multiprocessing` (named pipes with the default descriptor), schannel TLS, Store app aliases, PATH entries
  inside the profile.
- Held: nested-rule precedence in every case; no access to other processes of the user; registry writes,
  `schtasks`, WMI process creation and COM ShellWindows denied.

AppContainer:
- Reading is a perfect allow-list and schannel works; but deny entries for capability SIDs are ignored (no
  nested refusals), the NUL device is denied, `dir` and pipes fail, and it needs a registered profile.

Read-only default under "Allow everything":
- B1 (mirror + Low integrity + Low labels on writable rows): correct for one run; a label is state of the
  folder, so a folder labelled for one run stays writable for a later run that lists it read-only, and removing
  it breaks a concurrent run. Leaves `%LOCALAPPDATA%Low`, `Favorites`, `HKCU\Software\AppDataLow` writable.
- B2 (no integrity level, restricting set without the user): loses read of the profile, leaks writes.
- B3 (`WRITE_RESTRICTED`): writes limited correctly; deny-read for a rule SID is ignored.
- B4 (`WRITE_RESTRICTED` + Low integrity; refused rows labelled Medium with no-read-up): correct for one run,
  closes B1's leaks, same shared-label problem for refused and writable rows.

Common to every restricted token: schannel TLS fails (`curl.exe`, `Invoke-WebRequest`, .NET); programs with
their own TLS work.
