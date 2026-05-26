# ADR-0031: Workflow LLM routing overrides (`provider`/`model` first, `base_url` advanced)

## Status
Proposed (2026-02-08)

## Dates
- Proposed: 2026-02-08
- Accepted: (TBD)
- Updated: 2026-05-08 (aligned with ADR-0033)

## Context
Workflows (including specialized-agent workflows) are executed by hosts (`abstractcode`, `abstractflow`, `abstractgateway`) on top of `abstractruntime`.

Today:
- `provider` and `model` are first-class workflow/run inputs across hosts.
- `base_url` support exists in the stack, but with topology-specific behavior:
  - local runtime: per-call `base_url` is intentionally stripped (provider-construction concern),
  - remote/hybrid runtime: per-call `base_url` is forwarded to AbstractCore server request body.

This creates an architecture question: should workflows expose `base_url` like `provider`/`model`, or should it remain an advanced host/runtime routing concern.

Related references:
- ADR-0014 (runtime authority over execution policy)
- ADR-0015 (execution targets + optional LLM routing data including `base_url`)
- AbstractRuntime integration docs (`remote` vs `local` `base_url` behavior)

## Decision
### 1) Keep `provider` and `model` as the workflow-level override contract
`provider`/`model` remain the canonical, portable routing inputs for workflow nodes and host contracts.

### 2) Treat `base_url` as an advanced routing override, not a required workflow contract field
`base_url` is optional and host-controlled. It should not be required by workflow interface contracts (e.g. `abstractcode.agent.v1`) and should not be assumed present by workflow logic.

### 3) Topology-specific behavior is explicit
- **Local runtime**: `base_url` is resolved during provider construction (or via provider env defaults). Per-call override is not guaranteed.
- **Remote/hybrid runtime**: per-call `base_url` may be honored (forwarded to AbstractCore server) for dynamic OpenAI-compatible routing.

### 4) Security and policy boundary
Hosts that expose `base_url` must treat it as a sensitive routing surface:
- optional allowlist / policy validation,
- clear separation from workflow JSON portability concerns,
- no secret-bearing URLs persisted in workflow definitions.
- no use of Gateway bearer tokens as provider credentials.

When routing through a standalone AbstractCore server:

- Core server `Authorization` is the Core server auth channel when server auth is enabled.
- Per-request upstream provider-key overrides must use the dedicated Core provider-key override
  mechanism.
- Request body/query-string provider keys should remain disabled.
- Non-loopback or user-provided `base_url` values must be governed by host/Core allowlists to
  prevent provider-key exfiltration.

### 5) Observability and cache identity
When `base_url` materially changes endpoint behavior, hosts/runtime should surface effective routing metadata and avoid accidental cache collisions across endpoints.

## Consequences
### Positive
- Preserves workflow portability and simple contracts (`provider`/`model`).
- Supports advanced deployment needs (OpenAI-compatible endpoint override, multi-tenant routing).
- Aligns with runtime topology semantics already implemented.

### Negative
- Routing capabilities differ by topology (local vs remote/hybrid), which must be documented clearly.
- Hosts need explicit UX/policy choices for exposing `base_url`.

### Neutral
- Existing `provider`/`model` workflows remain compatible.
- This ADR does not mandate a single UX; it sets architecture boundaries.

## Packages Affected
- `abstractruntime` (routing semantics + metadata + cache identity policy)
- `abstractcode` (CLI/web settings UX for advanced `base_url`)
- `abstractflow` (host-run UX/policy stance; optional advanced routing)
- `abstractgateway` (control-plane policy if exposing run-level endpoint override)
- `abstractcore` (provider/server behavior already supports `base_url`)

## Related
- `docs/adr/0014-runtime-authority-timeouts.md`
- `docs/adr/0015-execution-targets-and-remote-tool-workers.md`
- `abstractruntime/docs/integrations/abstractcore.md`
- `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
