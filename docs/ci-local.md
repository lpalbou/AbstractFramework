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
```

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
  parent's) and `RUNNER_TEMP`, under `~/Library/Caches/ci-local/runs/<repo>-<time>-<sha>/jobs/<job>/`.
  That directory is outside the workspace on purpose: code that looks up its parents for sibling
  checkouts (AbstractCore's theme sync finds `../abstractuic`) must not find the live ones, as on
  GitHub. The environment is clean: no token, no provider key, no `ABSTRACT*` variable from your
  shell, so nothing reaches the gateway you run on `:8080` or reads `~/.abstractcore`.
  `--sandbox` also runs every step under `sandbox-exec`, which refuses connections to
  `localhost:8080`, writes under your home directory outside the run and the download caches (uv,
  pip, npm, cargo, Playwright), and `~/.abstractcore` and the workspace's `runtime/`; it is off by
  default because macOS cannot nest `sandbox-exec`, so AbstractCore's own macOS sandbox tests fail
  under it. Rust jobs keep a target directory per job in `~/Library/Caches/ci-local/cargo-target/`,
  as `Swatinem/rust-cache` does on GitHub. The gate deletes nothing: run directories stay for the
  logs; remove old ones from `~/Library/Caches/ci-local/runs/` by hand.

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

## Rules

- No push without `scripts/ci_local.sh <repo>` green for the commit being pushed.
- A pull request whose CI is red by design (a dependency floor that is not on PyPI yet, a smoke that
  needs an unreleased version) is not opened: the branch stays local until the dependency is
  visible on its registry.
- A red main is an incident: whoever merged reverts or fixes it within the hour.

## Proof runs (2026-11-03, this Mac)

Runs of the first version of the gate, before the free disk ran out (the Core and Gateway runs on
`origin/main` were stopped at 1.9 GB free and are not complete). Each failure the gate itself
caused was fixed in the gate, not in the repositories.

| Run | Verdict | Time |
|---|---|---|
| AbstractUIC `origin/main` (e101804), all jobs: Test, build, and pack; Avatar browser check | GREEN, 2 pass | 1m47s |
| AbstractCore `37b7913` (release/2.33.0, red on GitHub: run 41571723950), `--job changelog` | RED, the same message as GitHub: "Release 2.33.0: changelog.d/ still holds 8 fragment(s)" | 0m02s |
| This repository, the gate's own branch, `--job test-build` | GREEN | 3m57s |
| A scratch repository with the pre-push hook: a good commit, then a bad one | pushed, then refused (the remote kept the good commit) | 0m02s, 0m01s |
| AbstractCore `origin/main` (de1f9c8), partial | changelog, build, docs, console-tui MSRV pass (1s, 12s, 16s, 37s); linux-sandbox SKIPPED (needs root) | stopped |
| AbstractGateway `origin/main` (0109bcb), partial | changes, changelog, build, docs, console-tui pass (1s, 1s, 13s, 47s, 4m32s); model-host-windows and docker SKIPPED | stopped |

What those partial runs found in the gate, and the fix: `ps` cannot run under `sandbox-exec` (now
outside it, and the sandbox is opt-in), macOS cannot nest `sandbox-exec` (AbstractCore's macOS sandbox
tests: `--sandbox` is now off by default), run directories inside the workspace let AbstractCore's
theme sync find the live `../abstractuic` (they moved to `~/Library/Caches/ci-local`), Gateway jobs
without `setup-node` had no Node (the newest local one is now on the `PATH`, as on the runner image),
and `uv` refused llama.cpp's macOS CPU wheel that pip installs (`UV_INSECURE_NO_ZIP_VALIDATION`). Two
failures are not explained yet: AbstractCore `test_zig_lists_imports_tests_and_only_top_level_constants`
on Python 3.9, and the console-tui `download_w_polls_the_job_to_a_completion_toast` timing test (run
while the Gateway suite loaded the machine).
