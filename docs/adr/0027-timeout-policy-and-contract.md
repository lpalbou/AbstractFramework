# ADR-0027: Timeout Policy and Contract (CRITICAL)

## Status
Accepted (2026-01-26)

## Dates
- Proposed: 2026-01-26
- Accepted: 2026-01-26

## Context

In an agentic runtime, **timeouts are lossy**:
- they can abort an LLM call mid-generation (client disconnect), producing partial / misleading outputs,
- they can deadlock or stall subworkflows (e.g., background KG ingestion),
- they create hard-to-debug “it sometimes fails” behavior when the timeout is implicit or hidden.

We observed this concretely with local LM Studio calls timing out after a client-side threshold (`1200s`),
causing the server to log “Client disconnected” and the UI/runtime to surface an opaque failure.

We need a framework-wide policy that makes timeouts:
- explicit,
- observable (and attributable),
- and not silently enforced at low values.

This ADR is the timeout analogue of ADR-0026 (Truncation Policy).

## Definitions

### Timeout (what this ADR governs)
Any mechanism that aborts an operation after a duration, including:
- HTTP client timeouts for LLM providers (LM Studio / OpenAI-compatible / Ollama / etc),
- tool execution timeouts (host-side),
- proxy/server request timeouts (gateway, web server).

### Silent timeout (forbidden)
A timeout that:
- happens without a warning/error surfaced to the operator/user, or
- is surfaced without enough information to diagnose (duration + responsible component).

## Decision

### 1) Silent timeouts are forbidden (framework-wide)
If a timeout occurs, the system MUST emit a warning/error that includes:
- the duration (e.g., `timed out after 1200s`),
- the responsible component (package/module), and
- the configured source when possible (env var / config key).

### 2) Default timeouts must be conservative (high) for correctness-critical paths
For correctness-critical paths (LLM calls, memory ingestion, provenance creation):
- do not use low default timeouts,
- prefer **no client-side timeout** for local providers, or a very high safeguard (e.g., 2h).

### 3) Timeouts are allowed only as explicit safeguards (not hidden “performance knobs”)
Timeouts can be useful, but only when:
- explicitly configured by an operator/developer,
- clearly documented,
- and easy to audit in code.

### 4) Code hygiene: every timeout site must be tagged
All timeout sites must be tagged in code with the literal marker:

`#[WARNING:TIMEOUT]`

Rationale:
- easy to spot in reviews,
- easy to grep for audits,
- prevents accidental low timeouts creeping in.

## Consequences

### Positive
- Fewer “mystery failures” on long-running generations.
- Better observability when requests legitimately take a long time (large prompts, slow prompt processing).
- Faster debugging: timeouts become attributable, not folklore.

### Negative
- Some operations may hang longer if the provider/server becomes unresponsive; this is mitigated by:
  - high-but-finite safeguards where appropriate (e.g., 2h),
  - and explicit operator configuration.

## Implementation Notes

Recommended defaults (v1):
- Global HTTP default timeout: 2h (`7200s`) OR allow configuring `0 = unlimited`.
- Local LM Studio provider: default to `timeout=None` (no client timeout) unless explicitly overridden.

## Related
- ADR-0026: Truncation Policy and Contract
- `docs/guides/truncation-mechanisms.md`
