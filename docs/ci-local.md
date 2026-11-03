# Local CI gate (`scripts/ci_local.sh`)

A push must be green on this machine before it reaches GitHub. `scripts/ci_local.sh` runs a
repository's GitHub Actions jobs for one commit on a Mac, from the repository's own workflow files,
so a push that would fail CI fails here first. A red CI run on GitHub is then the exception: a
flake, or a job this machine cannot run.

```bash
scripts/ci_local.sh abstractcore                    # HEAD of ./abstractcore, every job
scripts/ci_local.sh abstractgateway --job test      # one job (and the jobs it needs)
scripts/ci_local.sh abstractuic --ref origin/main --list   # what would run, without running it
scripts/ci_local.sh root                            # this repository
scripts/ci_local.sh abstractcore --jobs 1           # one job at a time
```

Jobs run in parallel: `--jobs N`, by default the smaller of the number of jobs and the physical
cores divided by 4, capped by free memory at 4 GiB a job (the chosen N is printed). Each job has
its own environment, `HOME`, `TMPDIR` and log, so they are independent; verdict lines print as jobs
finish and an ordered summary closes the run. Jobs listed in `SERIAL_JOBS` in `scripts/ci_local.py`
run alone, one at a time, after everything else, with the jobs that need them: AbstractCore's
local-model tests (one model process at a time) and the Gateway load test (its p99 gates need a
quiet machine).

`<repo>` is a repository directory of the workspace (`abstractcore`, `AbstractGateway`, ...), `root`
for this repository, or a path.

## The contract

- **Exit 0**: every job that could run here passed and no job was skipped, or some were skipped
  and `--allow-skipped` was given. **Exit 1**: a job failed, the gate met something it does not
  understand, the commit does not merge into the base, or a job was skipped without
  `--allow-skipped`. **Exit 2**: a usage error.
- One line per job: `PASS`, `FAIL` (the failing step, the log path and the log's last lines),
  `ERROR` (counts as a failure), `SKIPPED` (with the reason; GitHub still runs that job),
  `NOT-TRIGGERED` (the job's own `if:` is false, as on GitHub), `NOT-SELECTED` (left out by
  `--job` / `--python`). A last line gives the verdict, the time and the run directory.
- The workflow files are the only source of truth. Nothing is copied from them: a new step, a new
  matrix entry or a new job is run the next time the gate runs.

## Test tiers (`--tier light|full`, ADR 0051)

The pull request body states the tier and why; a reviewer may raise it.

- **Light** (`--tier light`): docs, copy, icons, CSS, one dropdown, a catalog or model entry, a
  changelog, or a pin bump with its pin tests. A light run may select few tests, never none.
  - One Python per matrix: 3.12, the version every repository's single-version jobs use (the
    first entry of a matrix without it). The entries it leaves out are printed
    (`tier light: skipped jobs ...`) and do not count as skipped jobs.
  - pytest keeps a test file when it changed, when its name holds the name of a changed file, or
    when it imports a changed module. The name rule is a substring match on the file stem:
    `model_host.py` keeps `test_model_host_portable.py`, `model_catalog.yaml` keeps
    `test_model_catalog.py`, and a short stem keeps more than it needs (`app.js` keeps
    `test_console_app.py`). The kept files and the reason for each are printed.
  - Every changed file that is not documentation (`.md`, `.txt`) and does not belong to an npm
    package or a crate must keep at least one test: a module, a YAML/JSON catalog, a template, a
    static JS/CSS file, a shell script. Otherwise the run is red before it starts:
    `no test covers <path>; use --tier full or add a test`.
  - A `conftest.py`, the package configuration (`pyproject.toml`, `setup.cfg`, `pytest.ini`,
    ...) or any non-Python file under `tests/` (a fixture) runs the whole suite.
  - Files in an npm package or a crate go to its own test step: `npm test` becomes
    `npx vitest related --run <the changed files>` when the test script is `vitest run` (vitest
    exits red when nothing relates), `npm --workspace <w> run test` for the workspaces with changed
    files in a monorepo (whole when a changed file is outside every workspace, other scripts run
    whole); `cargo test` becomes `cargo test -p <crate>` in a Cargo workspace, and is skipped when
    the crate has no change.
  - The run counts the tests it executed (pytest's kept tests, each npm / cargo test step that
    ran). Zero makes it red: `the run executed no test`. The one exception is a change made of
    documentation alone: no test runs, and the gate prints
    `tier light: documentation only (<n> file(s)): no test runs, every other step still runs`.
  - Every other step still runs: lint, type-check, build, pack.
- **Full** (`--tier full`, the default): anything in a code path shared across features,
  concurrency or lifecycle, schemas and contracts, and every release branch. The whole pull request
  and main job set, every matrix entry. `--tier light` with `--release-tag` is refused, and the
  pre-push hook always runs a `release/*` branch in full.

## What it runs

- **The commit, merged into the base.** The base branch (`--base`, default `main`) is fetched from
  the repository's GitHub remote, and the commit is merged into it the way GitHub merges a pull
  request; that tree is what CI tests and what main becomes. A commit that does not merge cleanly is
  red. Uncommitted changes are never tested. `--no-merge` tests the commit itself; `--base-sha`
  replays a pull request against an older base.
- **The strictest event per workflow** (`--event auto`, the default): a workflow that runs on a
  push to main runs as that push, with main's full matrix and every conditional job (Gateway's
  pull requests test Python 3.12 only; main tests 3.10 to 3.13, the Rust console and more). A
  workflow that runs only on pull requests (the changelog check, the Gateway load test) runs as the
  pull request, with its branch and path filters. `--event pull_request` or `--event push` runs one
  event only. `--release-tag v2.33.0` also runs the workflows that pushing that tag would run
  (release.yml's build and verify jobs; its publishing jobs need secrets and are skipped).
- **Every step of every job**, with the workflow's `env`, `defaults`, `if:` conditions, `needs`,
  job outputs, `$GITHUB_ENV` / `$GITHUB_OUTPUT` / `$GITHUB_PATH`, `continue-on-error` and
  `timeout-minutes`. `${{ }}` expressions are evaluated as GitHub evaluates them.
- **A fresh environment per job.** `actions/setup-python` gives each job a new virtual environment
  of the requested Python (every matrix version this machine has; `uv python install 3.X` adds one).
  The job's own `pip install` lines then install the package, so sibling packages come from PyPI
  exactly as on GitHub, never from the editable checkouts next door: a branch that needs an
  unpublished `abstractcore` or `abstractruntime` fails here. The `pip` commands run as `uv pip`
  (`--installer uv`, the default: packages are linked from uv's cache, so a fresh environment costs
  seconds and no disk); `--installer pip` runs pip itself. `actions/setup-node` uses the requested
  Node major from nvm or Homebrew; `dtolnay/rust-toolchain` the requested rustup toolchain and
  components. `actions/checkout` clones the tested commit with the step's `fetch-depth` and `path`,
  or clones another repository from GitHub (`repository:`, `ref:`).
- **Isolated.** Each job has its own scratch `HOME`, `TMPDIR` (pytest's temporary directories live
  there, one fresh base per job; a `--basetemp` in `PYTEST_ADDOPTS` is not used because nested
  pytest runs, such as the Assistant's offscreen harness test, would inherit it and wipe their
  parent's) and `RUNNER_TEMP`, under `~/Library/Caches/ci-gate/runs/<repo>-<time>-<sha>/jobs/<job>/`.
  That directory is outside the workspace on purpose: code that looks up its parents for sibling
  checkouts (AbstractCore's theme sync finds `../abstractuic`) must not find the live ones, as on
  GitHub. Its path holds no `local` either: AbstractCore's zig outline test checks that word
  is absent from output that prints its temporary path. The environment is clean: no token, no provider key, no `ABSTRACT*` variable from your
  shell, so nothing reaches the gateway you run on `:8080` or reads `~/.abstractcore`.
  `--sandbox` also runs every step under `sandbox-exec`, which refuses connections to
  `localhost:8080`, writes under your home directory outside the run and the download caches (uv,
  pip, npm, cargo, Playwright), and `~/.abstractcore` and the workspace's `runtime/`; it is off by
  default because macOS cannot nest `sandbox-exec`, so AbstractCore's own macOS sandbox tests fail
  under it. Rust jobs keep a target directory per job in the workspace's `untracked/ci-local/cargo-target/`,
  as `Swatinem/rust-cache` does on GitHub. The gate deletes nothing: run directories stay for the
  logs; remove old ones from `~/Library/Caches/ci-gate/runs/` by hand.

## What it cannot run (SKIPPED, with the reason)

- Jobs on Windows runners, and custom runner labels (`xcode-27`) unless `--runner-label xcode-27`
  says this Mac stands in for them.
- A step that needs root on a Linux runner: `sudo`, `apt-get` and `apt` are replaced by a stub that
  marks the job skipped (bubblewrap/Landlock sandbox jobs). A guarded call such as
  `command -v lsof || sudo apt-get install lsof` never reaches the stub when the tool is present.
- Docker build actions, `services:` and `container:` jobs, jobs that read `secrets.*` or use a
  deployment `environment:`, PowerShell / `cmd` steps that their `if:` does not exclude.
- A Python, Node or Rust toolchain this machine lacks (the reason names the install command).
- A job that `needs` a job that did not run in full.

An action the gate does not know (`uses:` other than checkout, setup-python, setup-node,
rust-toolchain, cache, rust-cache, upload-artifact and the Docker actions) is an `ERROR`: teach
`scripts/ci_local.py` the action rather than letting the gate pass without it.

## Differences from GitHub that remain

- Ubuntu jobs run on macOS: `RUNNER_OS` is `macOS`, `/bin/bash` is bash 3.2, Linux-only
  behaviour is not exercised and macOS-only tests (skipped on GitHub's Ubuntu) do run. A job without
  `setup-node` finds the newest local Node on its `PATH`, as the runner images carry one. Most checks are portable; the ones that are not are the SKIPPED
  root/sandbox jobs.
- `uv pip` resolves like pip (`UV_INDEX_STRATEGY=unsafe-best-match`), but it is not pip.
- Toolchains are this machine's: the local `stable` Rust may be older than GitHub's (clippy lints
  differ between releases); keep it current with `rustup update stable`.
- Timing-sensitive tests can pass here and flake on a loaded runner, and the reverse.

## The pre-push hook (opt-in)

`scripts/hooks/pre-push` runs the gate for every ref a `git push` sends and refuses the push when it
is red. It is never installed automatically; install it per repository from the workspace's main
checkout:

```bash
scripts/install_hooks.sh abstractcore abstractgateway abstractuic   # some repositories
scripts/install_hooks.sh --all                                      # every repository the gate covers
```

It writes `<repo>/.git/hooks/pre-push` and never replaces a hook it did not write. What it checks
for each pushed ref:

| Pushed ref | Gate run |
|---|---|
| `refs/heads/main` | `--event push --git-ref refs/heads/main`: the commit itself, as main's CI runs it |
| `refs/heads/release/X` | the merge into main (`--event auto`) plus `--release-tag vX` |
| any other branch | the merge into main (`--event auto`) |
| `refs/tags/<tag>` | `--event push --git-ref refs/tags/<tag>` |
| a deletion | nothing |

The hook passes `--allow-skipped`: the jobs this Mac cannot run are printed as SKIPPED and GitHub
runs them. Extra flags for one repository go in its git config, for example the Assistant's
iPhone suite: `git config ci-local.args "--runner-label xcode-27 --input full_ui_suite=true"`.
The only override is `git push --no-verify`; the red CI that follows is then yours to fix.

The first push to an empty remote is refused: there is no `main` to fetch and merge into. Push that
first commit with `git push --no-verify`, or run the gate by hand against a base you choose
(`scripts/ci_local.sh <repo> --base-sha <commit>`) first.

## Rules

- No push without `scripts/ci_local.sh <repo>` green for the commit being pushed.
- A pull request whose CI is red by design (a dependency floor that is not on PyPI yet, a smoke that
  needs an unreleased version) is not opened: the branch stays local until the dependency is
  visible on its registry.
- A red main is an incident: whoever merged reverts or fixes it within the hour.

## Proof runs (2026-11-03, this Mac: 18 physical cores, 128 GB)

| Run | Verdict | Wall time |
|---|---|---|
| AbstractUIC `origin/main` (e101804), all jobs | GREEN, 2 pass | 1m47s |
| AbstractCore `37b7913` (release/2.33.0, red on GitHub: run 41571723950), `--job changelog` | RED, GitHub's own message: "Release 2.33.0: changelog.d/ still holds 8 fragment(s)" | 0m02s |
| AbstractGateway `21c1f27` (fix/host-stop-interrupts-runs, red on GitHub: run 41563765646), `--event pull_request` | RED: the 4 shards fail on GitHub's `ImportError: cannot import name 'EffectInterrupted' from 'abstractruntime'` (PyPI holds 0.16.0) | 6m17s |
| This repository, this branch, `--job test-build` | GREEN | 8m40s (under load) |
| AbstractCore `origin/main` (447530e), full, default `--jobs 4` | RED: 10 pass, 1 skipped (linux-sandbox, needs root), 1 fail (below) | 14m53s |
| AbstractGateway `origin/main` (0109bcb), full, `--jobs 4`, 16 shards (3.10 to 3.13) | RED: 16 pass, 2 skipped (Windows, Docker), 5 shard failures (below) | 62m30s (beside a Core run) |
| Pre-push hook in a scratch repository: a good commit, then a bad one | the first pushed, the second refused (the remote kept the good commit) | 0m02s, 0m01s |

`--jobs`: AbstractCore's full run takes 14m53s with the default `--jobs 4` on a quiet machine. Its
jobs add up to about 34 minutes run one at a time; `--jobs 2` beside a Gateway run took 45m30s.

Light against full, the same commit:

| Commit | `--tier light` | `--tier full` |
|---|---|---|
| AbstractCore `ebc86d7` (PR #42: `providers/base.py`, a test, docs) | 1m46s: Python 3.12 only, 85 test files kept (the changed test, and the tests named after or importing `abstractcore.providers.base`), `cargo test` skipped (no change under `console-tui/`) | 14m53s (`origin/main`, default `--jobs`) |
| AbstractUIC `204bf84` (`ui-kit/` brand icons, CHANGELOG, docs) | 0m31s: `npm --workspace ui-kit run test` | 0m47s |
| AbstractUIC `67f867a` (`ui-kit/` and `ci.yml`) | 0m50s: whole (`ci.yml` is outside every workspace) | 0m51s |

The red runs on `origin/main`, test by test:

| Failure | Cause | Gate-caused? |
|---|---|---|
| Gateway `test_gateway_workflow_ownership_isolation.py::test_the_first_line_refuses_the_non_admin_at_sign_in`, shard 3 on every Python | the gateway finds `/Applications/Ollama.app` on this Mac and starts it; the suite's subprocess guard refuses the launch. GitHub's runner has no Ollama | No: the test is not hermetic on a Mac with Ollama installed (a Gateway fix) |
| Gateway `test_r12w2_command_sandbox.py::test_a_real_serve_audits_the_flag_at_boot`, 3.10 shard 2 | the readiness race already seen on GitHub (G9 of the failure catalogue: the audit line is written before the port is bound), more frequent under load | No, an existing flake |
| Core `test_shell_session.py::test_reopen_after_death_does_not_leak_master_fd` (3.9, 3.10 or the local-model job, one per run) | asserts `is_alive()` is false right after `kill -9`, before the shell is reaped | No, an existing race |
| Core `test_host_jobs_and_engines.py::test_cancel_kills_the_whole_process_tree_not_just_the_child` (once, under load) | reads the grandchild's pid file between its creation and its write | No, an existing race |
| Core `test_zig_lists_imports_tests_and_only_top_level_constants` (3.9, first version of the gate) | the test asserts the word `local` is absent from output that prints its temporary path, and the run directory was `untracked/ci-local/...` | Yes, fixed: runs live in `~/Library/Caches/ci-gate/`; it passes on every Python since |
| Core console-tui `download_w_polls_the_job_to_a_completion_toast` (once, while the Gateway suite loaded the machine) | the poll thread reached 100% before a frame showed 42% | No, a load-sensitive race; it passed in both later runs |

Fixed in the gate along the way: `ps` cannot run under `sandbox-exec` (the sandbox is now opt-in),
macOS cannot nest `sandbox-exec`, run directories inside the workspace let AbstractCore's theme sync
find the live `../abstractuic`, jobs without `setup-node` had no Node, uv refused a wheel pip
installs, and matrix entries of one job did not run in parallel.
