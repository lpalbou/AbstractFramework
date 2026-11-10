# 1192 — Local gate: `python -m pip` inside a job-created venv resolves to uv; any step mentioning "cargo publish" is skipped silently

> Package: AbstractFramework (root `scripts/ci_local.sh` / `scripts/ci_local.py`)
> Type: bug
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: release, ci-gate, adr-0050

## Summary

Two defects of the local CI gate found during the 2026-11-10 wave, both of which make the gate's verdict wrong without
saying so:

1. **`python -m pip` inside a venv the job creates.** A workflow step that does `python -m venv <dir>` then
   `<dir>/bin/python -m pip install dist/*.whl` fails inside the gate with "Error while finding module specification
   for '/Users/albou/.local/bin/uv'": the gate rewrites `pip` to uv, and the rewrite does not survive a venv created by
   the job's uv-managed Python. abstractvision's "Clean base wheel smoke" step failed on two heads for this reason
   (gate run `abstractvision-20261110-044528-2ac59b7b`); the same step passed by hand with real pip, and GitHub's
   runner uses real pip. The release was tagged on that evidence.
2. **Steps mentioning "cargo publish" are skipped.** The gate treats any step whose text contains `cargo publish` as a
   step that writes outside the machine and skips it, together with every job depending on it. abstractavatar's
   release `verify` job only *mentions* the words in an error message; the gate skipped verify, sdist and the wheel
   test silently, and a real wheel-test blocker (release.yml not copying `schema/`) was only found by hand
   (abstractavatar `a795a46`).

## Expected

- The pip rewrite applies inside job-created venvs too (or the gate installs real pip into them), so `python -m pip`
  behaves as on GitHub.
- A step is skipped only when it *runs* a publishing command (`cargo publish`, `twine upload`, `npm publish`, …) as a
  command, not when the words appear in a string; a skipped step is reported with its reason and fails the gate
  unless `--allow-skipped`.

## Validation

A fixture workflow with (a) a venv + `python -m pip` step and (b) a step whose error message contains "cargo publish":
(a) passes, (b) runs. Re-run `scripts/ci_local.sh abstractvision --release-tag v0.3.35` and
`scripts/ci_local.sh abstractavatar --release-tag v0.2.0`: every job runs.

## Current code reality (2026-11-10)

`scripts/ci_local.py` (read it): the pip rewrite and the "writes outside the machine" text filter. Evidence in
untracked/release-2026-11-07/RESUME.md (04:45, 05:30 entries) and audit-fable/.
