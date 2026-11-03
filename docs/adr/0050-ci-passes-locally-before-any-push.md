# ADR 0050: CI Passes Here Before Any Push

Status: Accepted — operator ruling 2026-11-03 ("it must succeed here before even attempting a push
on GH"; "CI/CD fail should be the exception, not the normal path").

## Context

In the 24 hours of the 2026-11-03 release wave, 22 workflow runs failed across six repositories
(`untracked/release-2026-11-03/ci-failures-24h.md`). None came from two green pull requests
interacting. They came from three habits:

1. **Pushing code that needs an unpublished sibling package** (10 runs). The workspace venv uses
   editable checkouts of every sibling, so a gateway change that imports a symbol only on a Core
   branch passes locally and fails on CI, which installs from PyPI. Four of those runs were
   re-pushes of a branch that was still red for the same reason.
2. **Timing assertions and readiness races** (9 runs; every one of the seven red `main` runs). A
   Core test timed a whole garbage-collection pass and required it under 0.5 s; on the job that
   loads torch and transformers it takes 0.53 s. Gateway tests connected after seeing a boot log
   line written before the port was open, and failed on the Python 3.10 and 3.11 shards that pull
   request checks never run.
3. **CI that nobody runs before pushing**: the push-to-`main` matrix (3.10–3.13, Windows, Rust,
   Docker) when pull requests run one version; dispatch-only suites (the Assistant's full iPhone UI
   suite, last run three weeks earlier); release-only steps (the sdist test that failed the Avatar
   0.1.1 publish); type checks that only `npm run build` performs.

A red run costs the operator an email, a reviewer a re-run, and the release a cycle. A red `main`
blocks everyone's next merge. The checks exist; they were not run where the change was made.

## Decision

1. **A push to GitHub happens only after the same checks have passed locally.** Before any
   `git push`, the author runs the repository's own workflow jobs, every step of every job, for the
   PR workflow **and** the push-to-`main` workflow: the same Python versions the matrix lists that
   exist on the machine, the same extras, the same services where they can run here, under a
   scratch `HOME` and a per-run temp directory. The root workspace provides this as
   `scripts/ci_local.sh <repo> [--job <name>] [--fresh-venv] [--allow-skipped]`
   (`docs/ci-local.md`): it reads the workflow files, so it cannot drift from CI; its exit code is
   the contract; a job it cannot run locally is printed as skipped with its reason, never silently.
   A matrix Python that is not installed locally is printed as skipped the same way. **Until the
   gate lands (backlog 1116), the by-hand procedure in the `abstract-release` skill
   (`references/release-process.md`, section 10) is the gate**: the author runs the job commands
   themselves. The pull request body lists the commands run and their results.
2. **Release branches run with `--fresh-venv`.** A fresh venv installs the package and its
   dependencies from the registries (`pip install -e ".[dev]"` from PyPI pins, `npm ci` from the
   lockfile), not from editable sibling checkouts, so "needs an unpublished sibling" fails here
   exactly as it fails on CI. Release workflows' own validate, build and sdist-test steps are part
   of the local run for a release branch.
3. **No pull request is opened red by design.** A branch whose CI needs a version that is not yet
   on its registry (a raised dependency floor, a smoke test installing the next release, an import
   of a sibling's unreleased symbol) stays local until that version is visible. Converting an
   already-open pull request to a draft stops nothing; the rule is to not push.
4. **A red `main` is an incident.** Whoever merged the change fixes or reverts within the hour and
   tells the operator. The fix is made at the source: a flaky test is repaired or quarantined with
   a named owner before the next merge, never re-run until green.
5. **No wall-clock assertions by default.** A test that means "did not block" or "finished" waits
   on an event, a condition or a response; a genuine performance bound runs only behind an explicit
   strict-timing switch that CI leaves off. Readiness means the server answers HTTP, never that a
   log line appeared.
6. **The checks a developer cannot see are a defect of the workflow, not an excuse.** When a
   suite runs only on `main`, only on dispatch, or only at release time, the repository's gate
   runs it when the paths it covers change.

## Consequences

- Pushing costs minutes instead of seconds; a full gate on Core or Gateway can take as long as
  the CI job it mirrors. That time is paid once by the author instead of by every reviewer and the
  operator's inbox.
- A branch waiting on an unpublished sibling has no visible pull request until the sibling is
  released; the release order (ADR 0032, the `abstract-release` skill) already requires the lower
  package first, this makes the wait visible as "not pushed" rather than as "red".
- Timing-sensitive tests lose their stopwatch; a real performance regression is caught by the
  strict-timing run, which is a deliberate check, not a side effect of the unit suite.
- Jobs that genuinely cannot run on the developer's machine (Windows, Docker, GPU) remain CI-only
  and are listed as skipped; `--allow-skipped` is an explicit acknowledgement, not a default.

## Enforcement

- Planned, backlog 1116: `scripts/ci_local.sh` and the opt-in `pre-push` hook
  (`scripts/install_hooks.sh`) refuse a push when a runnable job fails; `--no-verify` is the only
  override and is noted in the pull request. Until they land, the skill's by-hand procedure
  applies and the pull request body is the evidence.
- The `abstract-release` and `release` skills (AbstractSkill) carry the gate as a mandatory step
  before any push and the "no red-by-design pull request" rule in the per-package loop.
- Review: a pull request whose body does not list the local run is sent back; a pull request
  opened red by design is closed, its branch kept.
- Worker briefs in multi-agent waves quote this ADR; the coordinator reports any red `main` to the
  operator within the hour.

## Validation

- Planned, backlog 1116: the gate goes red locally on a commit known to have failed CI (the Core
  release branch with its changelog fragments left in; a gateway branch importing an unreleased
  Core symbol under `--fresh-venv`), and green on `origin/main` of Core, Gateway and UIC —
  recorded in `docs/ci-local.md` with timings.
- Planned, backlog 1116: Core's three garbage-collection timing tests, the gateway's
  boot-readiness tests and the Assistant's playhead assertion are event-based; on the loaded
  CI jobs they no longer depend on the runner's speed. Until then, the timing flakes that produced
  the seven red mains of 2026-11-03 are not caught by the gate on day one; only the flaky-test
  policy (rule 5) removes them.
- The operator's failure-email rate after a release wave is the measure: a failed run is an
  exception that names its cause, not a step of the process.

## Related

- Evidence: `untracked/release-2026-11-03/ci-failures-24h.md` (22 runs, categories, commands per
  repository); backlog 1102 (the wave's coordination record).
- ADR 0032 (package dependency boundaries and release order); the `abstract-release` skill's
  gates (adversarial review, merge only on all-green, registry visibility before a floor is raised).
- Gateway's existing strict-timing switch; Core gains one under this ADR.
