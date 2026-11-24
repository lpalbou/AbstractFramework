# 1339 — The one-line installer delivers the Windows command sandbox (framework release pinning gateway 0.23.0)

> Package: framework (root pins, install manifest, installers), abstractgateway 0.23.0, abstractcore 2.38.0, abstractruntime 0.20.0
> Type: task
> Created: 2026-11-24
> Priority: high
> Labels: windows, release, installer, command-sandbox

## Summary

A person who installs AbstractFramework today with the one-line installer on Windows still sees "Refused: no
command sandbox on this host" on `execute_command` and `local_helper_start`, and agents' commands fail with
"unsupported platform (Windows)". The fix is published (abstractgateway 0.23.0, abstractcore 2.38.0,
abstractruntime 0.20.0, 2026-11-24) but the installers install the versions the framework release pins, and
AbstractFramework 0.14.2 pins gateway 0.22.0 / core 2.36.0 / runtime 0.19.7. This item is the framework
release that pins the published versions, so the one command gives every user the sandbox. The release needs
the operator's GO (AbstractFramework ADR 0051).

## Why

Operator, 2026-11-24: "this MUST work on any OS ... this should work seemlessly on windows and linux"; "the
users can be non technical people, so normally they have nothing to install or configure manually.. that's
why we have a one command line to install the framework"; after the package releases: "so you completely
failed and released codes that are not working".

The package releases alone do not reach users: only `install.ps1 -Pin latest` (an advanced path) installs
gateway 0.23.0. The default path must.

## Current code reality (audited 2026-11-24, root `main` at e3bc201)

- Root pins: `pyproject.toml` (gateway 0.22.0, core 2.36.0, runtime 0.19.7), `abstractframework/__init__.py`
  (`RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS`), `docs/installers/install-manifest.json`,
  `scripts/install.sh` (`AF_GATEWAY_PIN_DEFAULT`, `AF_FRAMEWORK_VERSION`, `AF_PY_MATRIX`, `AF_NPM_APPS`),
  `scripts/install.ps1` (`$AfGatewayPinDefault = '0.22.0'`, `$AfFrameworkVersion`, `$AfPyMatrix`).
- Published and verified from a clean install on Windows 10: abstractgateway 0.23.0, AbstractRuntime 0.20.0,
  abstractcore 2.38.0 (PyPI); @abstractframework/code 0.16.3 and @abstractframework/ui-kit 0.9.29 (npm).
- The operator's machine was upgraded with the fixed installer and `-Pin latest` on 2026-11-24: gateway 0.23.0
  healthy, start at login kept, `echo ok && pwd` runs sandboxed, the data folder and `.ssh` are denied.
- Local branch `windows-command-sandbox` (worktree `C:\abstractframework\worktrees\abstractframework-windows-sandbox`,
  commits 5a5a8f1 and 1195485, not pushed) holds: the `docs/install.md` Windows paragraph, the installer's
  version-aware "Shell:" summary line, and the installer fix of item 1340. This release ships that branch.

## Scope

### In scope

- Merge the branch `windows-command-sandbox` (after 1340's checks).
- Move every root pin to the published versions: gateway 0.23.0, core 2.38.0, runtime 0.20.0, code web 0.16.3
  (and any other package released since 0.14.2: run the release planner, `abstract-release` skill).
- Changelog, README release matrix, install docs, `llms.txt` / `llms-full.txt`; `scripts/tests/test_inventory.sh`.
- Release the framework version (operator GO), then verify the one-line install and the one-line upgrade on
  Windows, macOS and Linux.

### Out of scope

- The two workspace shapes Windows still refuses (item 1341).
- Rebuilding AbstractObserver on ui-kit 0.9.29 (do it if the planner lists it).

## Acceptance criteria

- [x] On a Windows machine with no AbstractFramework, the one-line installer (no flags) installs gateway 0.23.0
      or newer, and its summary reads "agents' shell commands run inside a Windows sandbox". (Root CI
      `Bootstrap smoke (windows-latest)` on a clean runner, the script run as the one-liner runs it.)
- [x] In that install, with the default workspace policy, an agent's `execute_command` succeeds with
      `sandbox.kind: windows-restricted-token` while a refused folder stays closed, and the gateway reports the
      sandbox line the tool cards render. (New CI step "Agents' commands run sandboxed (Windows)",
      `scripts/tests/command_sandbox_smoke.py`. Checked at the gateway's API, which every client renders; the
      card was not re-read by hand in AbstractCode web, the terminal clients and the Assistant.)
- [x] On an existing Windows install started at login, the one-line upgrade completes and the gateway is
      healthy afterwards with start at login still on (1340). (Real upgrade 0.22.0 -> 0.23.0 on the operator
      machine with `-Pin latest`; with no flags, the public one-liner's dry run on the same machine recognises
      the gateway and plans 0.14.3. The no-flags run itself was not repeated there: it restarts a gateway in
      use.)
- [x] The one-line install and upgrade still pass on macOS and Linux (root CI `bootstrap-smoke`).
- [x] Root pins, `RELEASE_VERSIONS`, the install manifest and both installers agree (`scripts/tests/test_inventory.sh`).

## Testing

- `bash scripts/tests/test_inventory.sh`
- `powershell -ExecutionPolicy ByPass -File scripts/install.ps1 -Print` (the plan names gateway 0.23.0)
- On Windows after the install: `abstractgateway service status`, then in the gateway's environment
  `python -m pytest tests/tools/test_sandbox_windows.py` from an abstractcore checkout at the installed version.

## Receipts

- PRs: lpalbou/AbstractCore#53, lpalbou/AbstractRuntime#50, lpalbou/AbstractGateway#115, lpalbou/AbstractUIC#68,
  lpalbou/AbstractCode#49 (all merged and released 2026-11-24).
- Install log of the operator machine's upgrade: `%LOCALAPPDATA%\AbstractGateway\logs\install-20261124-100322.log`.
- Root PR lpalbou/AbstractFramework#77 (Test and build, Bootstrap smoke on Ubuntu, macOS and Windows green),
  merge commit 999f9d6; `main` CI run 45489777851 green; tag v0.14.3; release run 45491351128 (test, build,
  PyPI publish green); PyPI `abstractframework` 0.14.3 requires `abstractgateway==0.23.0`,
  `abstractcore==2.38.0`, `AbstractRuntime==0.20.0`.
- `scripts/install.ps1` and `scripts/install.sh` served from `main` pin gateway 0.23.0 and framework 0.14.3
  (checked on raw.githubusercontent.com, 2026-11-24).
- Root PR lpalbou/AbstractFramework#78 (CI run 45493386171): on the fresh Windows install the gateway reports
  `kind: windows-restricted-token`, state `partial`; `echo sandbox-ok` succeeds inside it; the refused folder
  is unreadable.
- Not covered here: "Deny everything, allow listed workspaces" and a read-only default on Windows (1341), and
  git inside a run's own workspace folder under the default policy (found 2026-11-24, fixed with 1341).
