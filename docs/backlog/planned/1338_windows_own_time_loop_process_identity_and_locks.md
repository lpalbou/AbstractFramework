# 1338 — Windows: an entity's own time starts, is seen running, and stops (process identity and locks)

> Package: abstractruntime (process probes, spawn, locks), abstractgateway (status read, liveness copy)
> Type: bug
> Created: 2026-11-22
> Priority: high
> Labels: windows, entities, own-time, lifecycle, stop

## Summary

On Windows an entity's own time (the personal phase, run by the own-time loop process) can never run: the loop
crashes at its boot, the status it leaves makes every later status read raise, the phase bar shows "His own time
is not running. Retry to start it.", and Retry meets the same error. Behind that first crash the whole
process-identity layer of the loop (is it alive, is it the same process, is it this home's loop, end it) and its
cross-process locks are POSIX-only. This item makes that layer one contract with a Windows implementation, and
makes an unreadable status say so instead of offering a Retry.

## Why

Operator, 2026-11-22 (Windows validation machine, entity `gandalf`): "Awake and reachable; his own time is not
running. · since 02:29 — His own time is not running. Retry to start it." / "i should always be able to give
personal time to an entity, what is the issue?"

The grant was fine (`phases.yaml`: `mode: until_revoked, granted_by: person:admin`, 01:29:20Z). The loop child
died five seconds later; `own_time.log` ends with:

```
life.py:4413 run -> read_loop_status:1918 -> _pid_alive_reaped:3288
    done, _status = os.waitpid(pid, os.WNOHANG)
AttributeError: module 'os' has no attribute 'WNOHANG'
```

## Current code reality (audited 2026-11-22 at abstractruntime 0.19.7 / abstractgateway 0.22.0, main)

1. `os.waitpid(pid, os.WNOHANG)` in `identity/life.py` (`_pid_alive_reaped`, `_pid_state`) and in the gateway's
   own copy (`entity_phase._pid_liveness`): `os.WNOHANG` does not exist on Windows; the AttributeError is not
   caught. A stale `loop_status` `{phase: starting, pid}` then makes every `read_loop_status` raise; the gateway
   folds that into `{running: false, phase: stopped}` (`entity_phase.gather`) and offers Retry
   (`_blocked` → `own_time_not_running`); the spawn path reads the same status and fails the same way.
2. `os.kill(pid, 0)` as a liveness probe (`_pid_alive`, `_pid_state`): on Windows signal 0 is `CTRL_C_EVENT`.
   Measured: from a console it "works" by accident; from a console-less process (the gateway runs under
   `pythonw`) it raises for a LIVE pid, so every live loop reads dead (a second loop on one home).
3. `ps` for the incarnation token (`_pid_start_time`, written at rest in `loop_status` as `pid_started_at` /
   `spawner_started_at`), the zombie check and the command line (`_pid_command`): no `ps` on Windows, so no
   token and no command line; `_verified_loop_incarnation` fails closed, so a Stop could never end a loop.
4. `freeze_loop` uses `signal.SIGKILL` (missing on Windows): it raises after the grant is revoked and the
   generation bumped, before `stopped` is written (a half-done Stop).
5. `_is_loop_invocation` splits the command line at its first space: wrong for an interpreter path with a space
   and for Windows' quoted command lines.
6. In a Windows virtual environment `sys.executable` is a launcher whose CHILD is the interpreter (measured:
   `Popen.pid` 23060, child `os.getpid()` 14040, `os.getppid()` 23060). `spawn_loop_process` records
   `proc.pid`, so the child's boot claim (`_foreign_live_loop`) sees a live reservation naming another process
   and refuses with LoopAlreadyRunning.
7. `fcntl.flock` is the cross-process exclusion of the home (home state lock, spawn lock, lifecycle write
   barrier, the task inbox append); without `fcntl` the code falls back to an in-process lock or to none, so on
   Windows the gateway and the loop do not exclude each other (two simultaneous starts both launch; a Stop's
   bump can land between a write's fence check and the write).

Evidence on this machine before the change: `tests/test_entity_life_loop.py::test_hard_stop_freezes_now_without_ceremony`
fails and leaks loop processes; `tests/test_stop_fence.py` cannot be collected (`import fcntl`).

## Decision (architect pass, 2026-11-22: two independent charters, both "Recommend With Reservations" for B)

Candidates compared: A in-place guards (rejected: turns a loud crash into "every live loop reads dead", and
cannot give a token or command line); **B one process module in abstractruntime, narrowed (chosen)**; C psutil
as a required dependency (rejected: a compiled dependency in the base install, changes the POSIX token at rest,
solves neither 6 nor 7); D liveness by a held OS lock (a later belt: Stop still needs pid, token and command
line; an inherited handle keeps "running" true); E a Windows Job Object per home (later hardening).

- `abstractruntime.utils.os_process`: `exists`, `reap`, `state` (alive / gone / unknown), `start_token`,
  `command`, `terminate`, `direct_python`. POSIX keeps `os.kill(pid, 0)`, `os.waitpid`, `ps` exactly; Windows
  asks the kernel through a process handle (ctypes, no dependency). `life.py` keeps its `_pid_*` names as thin
  delegates (the gateway and the tests import them).
- **Token spelling (written at rest, fixed):** POSIX unchanged (`ps -o lstart=` under `LC_ALL=C TZ=UTC`);
  Windows `win-filetime:<process creation time, 100 ns units>`. Tokens are compared for equality only; a token
  of the other spelling never matches (a home copied between machines reads "not that process").
- **Launcher (6):** the spawner starts the real interpreter (`sys._base_executable` + `__PYVENV_LAUNCHER__`,
  the route `multiprocessing` uses), so the recorded pid IS the loop's. Chosen over a second identity mechanism
  (a spawn id in argv) and over an ancestry rule in the boot claim: no new vocabulary at rest, and a Stop during
  `starting` ends the process that runs the loop.
- **Command line:** `NtQueryInformationProcess(ProcessCommandLineInformation)` + `CommandLineToArgvW`; the
  argument list is compared one argument at a time, the interpreter path is not read.
- **Stop on Windows:** `TerminateProcess` on a handle whose creation time is checked against the recorded
  token (no window for a reused pid).
- **Locks (7):** `abstractruntime.utils.file_lock` (`fcntl.flock` / `LockFileEx`, shared and exclusive, waiting
  without a limit), used by the home state lock, both spawn-lock sites, the write barrier and the task inbox.
- **Gateway:** `_pid_liveness` delegates to the runtime's probe; a status that cannot be read is
  `own_time_status_unreadable` with no Retry, and reconcile starts nothing over it.

## Scope

### In scope

- The decision above, in `abstractruntime` (branch `fix/windows-own-time-process-probes`) and `abstractgateway`
  (branch `fix/windows-own-time-status-error`), with tests that run on Windows, Linux and macOS.

### Out of scope

- The gateway's other `os.kill(pid, 0)` probes (`apps_manager`, `runner`, `runtime_config`, `split_mode`,
  `maintenance/process_manager`, `first_run`): follow-up, same module.
- The runtime's other `fcntl` sites (`email/inbox`, `storage/json_files`, `storage/lease`,
  `triggers/connections`) and the gateway's (`entity_phase` kill lock and record lock): follow-up.
- Wire names (`killed_sigterm`, `escalated_to_sigkill`) and `start_new_session` (POSIX-only: whether a loop
  survives a gateway restart on Windows is unverified).
- psutil, lock-based liveness, Job Objects.

## Acceptance criteria

- [ ] On Windows, granting personal time to an entity starts its own-time loop; `GET /entities/{name}/life_state` reports phase `personal`, and `loop_status` names the loop's own pid with a `win-filetime:` token.
- [ ] On Windows, Stop ends that loop (`killed: true`) and nothing else; a Stop over a reused pid or another program is refused.
- [ ] `tests/test_entity_life_loop.py`, `tests/test_stop_fence.py`, `tests/test_os_process.py` pass on Windows and on Linux (the same tests that passed on Linux before still pass).
- [ ] Two simultaneous starts of one home launch one loop on Windows (`test_spawn_reservation_single_loop`).
- [ ] A status read that fails shows `own_time_status_unreadable` with its reason and no Retry; reconcile and Retry start nothing over it.
- [ ] After the fixed build is installed on the validation machine, one Retry starts gandalf's own time with the grant he already has (no hand edit of his home).

## Testing

- `cd abstractruntime && python -m pytest tests/test_os_process.py tests/test_entity_life_loop.py tests/test_stop_fence.py -q`
- `cd abstractgateway && python -m pytest tests/test_entity_phases_life_state.py tests/test_entity_phases_kill_switch.py -q`

## Receipts

- Diagnosis 2026-11-22: `entities/gandalf/own_time.log` (the traceback above), `entities/gandalf/loop_status`
  stuck at `{"phase":"starting","pid":19344}`, about 80 identical AttributeErrors in `logs/gateway.log`.
- Baselines 2026-11-22: Windows, untouched tree: 72 passed, 1 failed, `test_stop_fence.py` not collectable;
  Linux (python:3.12-slim), untouched tree: 144 passed.

## Implementation report (2026-11-22, not merged, not released)

Built on two branches cut from main, each reviewed by two adversarial passes per commit (Windows correctness;
POSIX parity and integration):

- `abstractruntime` `fix/windows-own-time-process-probes`: `utils/os_process.py`, `utils/file_lock.py`,
  `identity/life.py`, `identity/lifecycle_fence.py`, `docs/entity-runtime.md`, tests `test_os_process.py`,
  `test_file_lock.py`, a real spawn -> claim -> Stop test in `test_stop_fence.py`.
- `abstractgateway` `fix/windows-own-time-status-error` (commit `89ca1f2c`): `entity_phase.py`,
  `entity_idle_sleep.py`, `entity_loop.py` (`stop_loop_if_running`), `routes/entities.py`.

Evidence (the same test files before and after):

| Where | Before | After |
|---|---|---|
| Runtime loop/stop tests, Windows | 72 passed, 1 failed; `test_stop_fence.py` not collectable; phases file 4 failed | all pass (2 skipped: POSIX-only by construction) |
| Runtime loop/stop tests, Linux (python:3.12-slim) | 144 + 58 passed | the same pass, plus the new tests |
| Gateway phase/stop tests (7 files), Windows | 39 failed, 81 passed | 5 failed, 116 passed; no test newly fails |

Found by the reviews and fixed in the same change: a Stop refused a loop whose home was named by another spelling
(8.3 short name); `OpenProcess` opens `pid+1..3` as `pid`; a Ctrl+C in the host's console ended the loop
(`start_new_session` does nothing on Windows); a blocking `LockFileEx` could not be interrupted; turning own
time off answered 500 over an unreadable status; the raw error text reached the versioned snapshot.

Still open (acceptance): the live check on the validation machine (install the fixed builds, one Retry on
gandalf). It needs a runtime release, the gateway's `AbstractRuntime==` pin moved to it, and a gateway build.

## Follow-ups (not in this item)

- The gateway's other `os.kill(pid, 0)` probes and `fcntl` sites (`entity_tasks.py:78` writes the task inbox
  without a lock on Windows; `entity_phase` kill lock and record lock): move them to `os_process` / `file_lock`.
- Five gateway tests in the seven files still fail on Windows as they did before; the one inspected
  (`test_an_unverifiable_loop_is_never_taken_for_dead`) simulates POSIX (`os.kill` patched to EPERM); the other
  four were not inspected.
- POSIX, pre-existing: `ps -o command=` is cut at 80 columns when `COLUMNS` is exported (procps), so a Stop can
  refuse a real loop there; the gateway's `apps_manager` already passes `-ww` for that reason.
- Wire names `killed_sigterm` / `escalated_to_sigkill` describe POSIX; on Windows the result's `signal` is
  `TerminateProcess`.

## Local install on the validation machine (2026-11-22)

The gateway tool environment there already ran local wheels built from the main checkouts with their uncommitted
host-pause work. The replacement wheels were therefore built from that state plus the fix branches (and the tray
quit fix, `fix/windows-tray-quit`): trees `C:\abstractframework\worktrees\abstractruntime-build` and
`abstractgateway-build`, wheels in `C:\abstractframework\worktrees\wheels`. Checked before the install: the built
wheels differ from the installed files only in the files the fixes touch (runtime: `identity/life.py`,
`identity/lifecycle_fence.py`, new `utils/os_process.py`, `utils/file_lock.py`; gateway: `entity_phase.py`,
`entity_idle_sleep.py`, `entity_loop.py`, `routes/entities.py`, `host_control.py`, `tray/app.py`,
`tray/events.py`); the combined trees pass the loop/stop suites (runtime 236 passed; gateway 72 passed, the 3
failures are among the 5 that fail on the untouched trees). Installed with `uv pip install --no-deps --reinstall`;
the replaced package folders are kept in `C:\abstractframework\worktrees\rollback-2026-11-22`. After the install
`read_loop_status` on gandalf's home answers `{phase: starting, running: false}` instead of raising. Start at login
is unchanged (on). The live check (gateway restart, Retry on gandalf) is still to do.
