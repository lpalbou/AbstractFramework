# 0849 — Package test suites must not reach the operator's live stack

> Package: abstractframework (all packages)
> Type: task
> Created: 2026-09-18
> Priority: normal
> Labels: test-hygiene, operability

## Summary

Running a package's unit tests on a developer machine can mutate the running framework.
`abstractassistant`'s GUI tests build a real controller from `Config()`, which resolves the
gateway URL and token **from the environment**; with `ABSTRACTGATEWAY_AUTH_TOKEN` exported
and a gateway on `127.0.0.1:8080`, the suite connected to the live gateway and republished
the assistant's managed workflow — twice on 2026-09-17, each publish costing the operator a
~60 s gateway stall and every in-process prompt cache. `abstractassistant` is now guarded;
no other package is.

## Why

Measured, not hypothetical: two of the four gateway outages that day were caused by a test
run, identified by matching the audit log's `auth_token_fp` against the shell's exported
token. A suite that can silently reconfigure the machine it runs on is not a unit suite, and
the failure mode is invisible — the tests pass either way.

## Scope

### In scope

- Audit every package's test suite for the same shape: a test that constructs a client,
  controller, host or provider from environment-derived connection settings
  (`ABSTRACTGATEWAY_URL`, `ABSTRACTGATEWAY_AUTH_TOKEN`, `ABSTRACTFLOW_*`, `OPENAI_*`,
  `ANTHROPIC_*`, LM Studio / Ollama base URLs) and reaches a real service.
- Adopt the guard already in `abstractassistant/tests/conftest.py` as the framework pattern:
  scrub the connection environment before import, point the URL at a dead port, and refuse
  sockets to the known service ports and to every non-loopback host — with a test that
  exercises the refusal itself (`tests/basic/test_suite_cannot_reach_a_real_gateway.py`).
- Decide the policy for suites that legitimately need a live provider (abstractcore has
  several that call Anthropic/OpenAI/LM Studio): an explicit opt-in marker/env flag, so a
  plain `pytest` run can never bill an account or load a model, and so an adversarial
  reviewer running "the tests" does not do it by accident.
- Document the rule in the contributing/testing docs, and make the default `pytest`
  invocation in each README the hermetic one.

### Out of scope

- Changing what the assistant's reconcile does (abstractassistant 0850 / the revision gate
  already landed).
- Building a fake gateway fixture library (worth doing, but a separate item).

## Acceptance criteria

- [ ] For each package: `pytest` with the developer's normal environment exported makes zero
      network connections; verified by running the suite and confirming
      `runtime/audit_log.jsonl` does not grow (the method used to verify the assistant fix).
- [ ] Live-provider tests are opt-in and skipped by default, with the opt-in documented.
- [ ] Each package's testing docs state the rule.

## Receipts

- `abstractassistant/tests/conftest.py` + `tests/basic/test_suite_cannot_reach_a_real_gateway.py`
  (2026-09-17): after the guard, a full `tests/basic` run left the gateway audit log at
  exactly 28,806 lines, unchanged.
- `runtime/audit_log.jsonl` 2026-09-17 21:49 and 21:59: `PUT /api/gateway/visualflows/…`,
  `POST …/publish`, `POST …/promote` under the shell's exported admin token.

## Status update 2026-09-25 (post-release trace)

- Done for abstractcore (tests/conftest.py, released from 2.15.0) and abstractgateway (from 0.4.0
  tag / 0.4.1 release): per-test HOME/HF_HOME, socket guard (non-loopback + ports 8080/1234/11434/
  18850), `network` / `real_home` markers with mandatory reasons, gateway subprocess guard. Record:
  `completed/0866_test_isolation_in_abstractcore_and_abstractgateway.md` (missions DD, FF).
- Still open: AbstractRuntime (no guard; `_missing_weights_hint` launches `lms`), abstractagent (no
  `tests/conftest.py`), and the other packages. The item stays planned for them.
