# ADR-0030: Security test fixtures and isolation (no real sensitive paths)

## Status
Proposed

## Dates
- Proposed: 2026-02-02
- Accepted: TBD

## Context
During the 2026-02-02 incident investigation, several backlog items appeared with titles containing `../etc/passwd …`. While the root cause was a **test artifact**, the specific fixture (`/etc/passwd`) amplified suspicion and created unnecessary incident load.

We need security regression tests for:
- path traversal inputs (e.g., `../..`),
- filename/path sanitization,
- and “write-to-repo” bridges (e.g., auto-bridging bug/feature reports into `docs/backlog/`).

But we also need to avoid:
- referencing real OS-sensitive paths (e.g., `/etc/passwd`, `~/.ssh/id_rsa`) in tests and user-visible artifacts,
- any test that can mutate a developer’s real repo state by accident (especially when env vars like `*_TRIAGE_REPO_ROOT` are set).

## Decision
1. **Use synthetic placeholders** for security fixtures that would otherwise reference real sensitive paths:
   - Prefer `../SENSITIVE_FILE` or `../../../SENSITIVE_FILE` over `../etc/passwd`.
2. **Do not create tests that attempt to access/modify OS files**. Tests may validate rejection/sanitization of a string payload, but must not depend on the presence of any real file.
3. **Isolate tests from developer repo state by default**:
   - Tests must not write to `docs/backlog/*` unless the test explicitly creates and uses a temporary repo root.
   - Tests should defensively clear `ABSTRACTGATEWAY_TRIAGE_REPO_ROOT` / `ABSTRACT_TRIAGE_REPO_ROOT` unless explicitly set.
   - Tests should defensively clear durable host settings that can point at a developer’s real runtime DB:
     - `ABSTRACTGATEWAY_DB_PATH`
     - `ABSTRACTGATEWAY_STORE_BACKEND`
   - Tests should provide safe temporary defaults for:
     - `ABSTRACTGATEWAY_DATA_DIR`
     - `ABSTRACTGATEWAY_FLOWS_DIR`

## Consequences

### Positive
- Reduces false-positive “intrusion” signals caused by test data leaking into user-visible artifacts.
- Keeps regression coverage for traversal/sanitization without referencing real system files.
- Prevents accidental mutation of a developer’s real repo backlog during test runs.

### Negative
- Slightly less “realistic” fixtures (but still covers the same classes of bugs).

### Neutral
- Encourages a consistent naming convention for security test payloads across packages.

## Packages Affected
- `abstractgateway`
- `abstractruntime`
- (potentially) any package that has sanitization/security regression fixtures

## Related
- Incident report: `untracked/2026-02-02_backlog-items-689-692-etc-passwd-investigation.md`
- Backlog: `docs/backlog/completed/693-abstractgateway-prevent-integration-tests-from-leaking-autobridge-into-real-repo-v0.md`
- Backlog: `docs/backlog/planned/694-abstractgateway-durable-audit-log-for-mutating-endpoints-v0.md`
- Backlog: `docs/backlog/planned/695-framework-secure-gateway-dev-defaults-and-ngrok-exposure-guardrails-v0.md`
