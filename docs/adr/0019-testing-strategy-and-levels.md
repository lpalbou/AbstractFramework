# ADR-0019: Testing Strategy and Levels (Basic → Intermediate → Full)

## Status
Accepted

## Dates
- Proposed: 2026-01-07
- Accepted: 2026-01-07

## Context
AbstractFramework is a durability-focused, multi-package ecosystem (Core/Runtime/Agent/Flow/Code). As the surface area grows (effects, waits, remote tool workers, remote run gateways), ad-hoc testing becomes risky:
- regressions can appear only after restarts (durability),
- correctness can depend on contract-level JSON-shapes (portability),
- “works on my machine” can hide network/security edge cases.

We already have many tests, but they are designed incrementally “as we go”. We need a shared, explicit testing philosophy that:
- keeps the default test suite fast and deterministic,
- still provides a path to high-confidence end-to-end validation,
- makes backlog completion reports more trustworthy (“what was actually tested?”).

## Decision
Adopt a 3-level testing model and enforce clear boundaries:

### Level A — Basic (Contract / Unit)
**Goal**: validate contracts and invariants quickly.

Rules:
- No external network.
- Deterministic; no time-based flakiness.
- Use in-memory stores or temp file stores as needed.
- Mock external providers when necessary (LLM/tool servers), but do not mock our own core logic.

Examples:
- JSON-safe persistence invariants (`RunState.vars`, event payload normalization).
- Effect handler contracts (inputs/outputs, wait states).
- Schema migration and serialization round-trips.

### Level B — Intermediate (Integration / Local)
**Goal**: validate real component integration without relying on external infra.

Rules:
- Still no external network dependency (localhost is acceptable when running in-process servers).
- Prefer real stores (file-backed) + restart simulation for durability.
- Prefer “real runtime tick loops” over mocked execution paths.

Examples:
- Start → wait → resume flows with file-backed stores, then reload and continue.
- AbstractFlow compiler/executor integration (VisualFlow → Runtime).
- Tool execution using a real local ToolExecutor (or an in-process MCP server stub).

### Level C — Full (End-to-end / Real Infra)
**Goal**: validate real-world deployments (providers, gateways, remote workers).

Rules:
- May require external network and credentials.
- Must be explicitly enabled (opt-in) to avoid flakiness in default CI.
- Should include timeouts, retries, and clear failure diagnostics.

Examples:
- Real provider call (OpenAI / LMStudio / Ollama / vLLM) + tool calling + tool execution.
- Remote run gateway: command submission + ledger replay across reconnect.
- Remote MCP worker over SSH/HTTPS with auth enabled.

## Conventions
### Pytest markers (recommended)
- `@pytest.mark.basic`
- `@pytest.mark.integration`
- `@pytest.mark.e2e`

Default CI should run:
- Basic + Integration

E2E should run only when:
- required env vars/credentials are present, or
- an explicit CI job is triggered.

### Test organization (recommended)
- `*/tests/` remains package-local
- Use either:
  - directory split: `tests/basic`, `tests/integration`, `tests/e2e`, or
  - marker-based split with clear naming (prefer directories if it stays clean).

### Durability-specific requirement
Any feature that touches:
- stores (RunStore/LedgerStore/ArtifactStore),
- waits/resume semantics,
- scheduler/eventing,
should have at least one **restart simulation** test at Level B (file-backed stores + reload).

## Consequences
### Positive
- Faster feedback loops without sacrificing realism.
- Higher confidence for durability and portability changes.
- Clearer completion reports and easier triage of failures.

### Negative
- Requires ongoing discipline (marking tests correctly, not “just adding another unclassified test”).
- Some E2E tests will remain inherently flaky unless infra is stable (we must treat them as opt-in).

### Neutral
- Does not prescribe a single CI system; only defines expectations and structure.

## Packages Affected
- All packages (Core/Runtime/Agent/Flow/Code and future packages).

## Backlog/reporting implications
Backlog completion reports should include:
- the **exact commands** run (e.g. `pytest -q ...`),
- which levels were executed,
- any skipped E2E tests and why (missing creds/infra).

## Related
- ADR-0018 (remote run gateway introduces new E2E needs): `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
- Security baseline (mirrors E2E requirements): `docs/backlog/completed/309-framework-run-gateway-security-and-auth.md`


