# 0866 — Test suites isolated from the operator's home and network (abstractcore, abstractgateway)

> Package: abstractcore, abstractgateway
> Type: improvement
> Created: 2026-09-25
> Completed: 2026-09-24
> Priority: high
> Labels: test-hygiene, operability, release-trace

## Summary

Completed record for the abstractcore and abstractgateway slice of 0849 (which stays planned for
the other packages). Running either package's test suite on a developer machine can no longer
write to the operator's home, reach a live gateway/LM Studio/Ollama, or download from the network
unless a test is explicitly marked.

## What landed

- abstractcore (`tests/conftest.py`, shipped from tag `v2.15.0`) and abstractgateway
  (`tests/conftest.py`, present at `v0.4.1` and `v0.4.2`): per-test `HOME` / `HF_HOME` moved to a
  temporary directory; a socket guard refusing non-loopback hosts and the live ports
  8080 / 1234 / 11434 / 18850; `network` and `real_home` markers with mandatory reasons; ~30
  tests that reached live services fixed or marked (mission DD).
- abstractgateway: a subprocess guard (it caught a test running the operator's real `lms`), env
  reads declared, the `USER` read removed (wrong chown owner under sudo), XDG cache dir (mission FF).
- CONTRIBUTING sections in both repos describe the markers.

## Completion report

- Validation: full suites run with the REAL HOME left it untouched (nothing under
  `~/.abstractcore`, `~/.abstractcode`, `~/.cache/huggingface`, `~/Library/LaunchAgents`); guards
  refused nothing unexpected; 3/3 mutants (DD); gateway full suite 2147 passed / 0 failed (FF), 2235
  / 0 at the end of the fourth wave. Evidence: `untracked/missionDD/REPORT.md`,
  `full_suite_failures.md`, `untracked/missionFF/REPORT.md`.
- Product defects found by the isolation work and fixed in the same wave (mission EE): fetched
  PDFs uploaded to OpenAI when a key was set; the embeddings cache rewritten empty at exit.
- Residual: AbstractRuntime, abstractagent and the remaining packages have no equivalent guard
  (runtime also launches `lms` in `_missing_weights_hint`) → still 0849.
- ADR state: none written; 0849 records the policy question (opt-in marker for live-provider
  suites) and is the place to decide whether it becomes an ADR.

## Receipts

- `untracked/missionDD/`, `untracked/missionFF/`, `untracked/missionEE/` (local).
