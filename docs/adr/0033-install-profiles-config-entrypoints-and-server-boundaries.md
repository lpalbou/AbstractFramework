# ADR-0033: Install Profiles, Config Entrypoints, and Server Boundaries

## Status
Accepted (2026-05-08)

## Dates
- Proposed: 2026-05-08
- Accepted: 2026-05-08

## Context

AbstractFramework now spans foundational LLM access, modality capabilities, durable workflow
execution, memory, thin clients, and deployment tooling. The package boundaries are clear in broad
terms, but installation and configuration have started to blur them:

- Gateway/Core/Vision/Voice are moving toward lightweight remote defaults.
- Music is currently local-heavy.
- Runtime and Semantics must stay dependency-light.
- Gateway needs to compose lower packages for deployment without absorbing their internals.
- Core and Gateway both expose HTTP servers in some topologies, so auth/CORS cannot be treated as
  a single global Gateway-only concern.

The project needs one decision that explains how dependency profiles, configuration entry points,
and server security boundaries fit together.

## Decision

### 1) Define two operational entry points

AbstractFramework has two primary operational entry points:

- `abstractcore`: direct developer/library entry point for LLM providers, tools, media handling,
  capability plugins, provider credentials, provider base URLs, global model defaults, and the
  standalone OpenAI-compatible Core server.
- `abstractgateway`: deployment/runtime entry point for durable runs, bundles, ledgers, artifacts,
  runner lifecycle, workspace policy, tool approvals, thin-client APIs, Gateway-level
  provider/model defaults, embeddings, memory, and capability readiness.

The root `abstractframework` package is a curated install/profile manifest and documentation hub.
It is not a third runtime configuration authority.

### 2) Unify profile vocabulary for Python installs

Use consistent profile names for Python package installs. A lower-level package may expose an empty
`apple`, `gpu`, `all-apple`, or `all-gpu` extra when it has no hardware-specific
dependencies; this keeps dependency cascades simple for aggregate installers without changing the
package's runtime responsibilities.

- `package`: the smallest useful install for that package's own role.
- `package[remote]`: hosted/API provider support when not already in base.
- `package[server]`: deployable HTTP/server profile for packages that host a server.
- `package[apple]`: native Apple local engines where the package owns such engines.
- `package[gpu]`: generic GPU local engines where the package owns such engines.
- `package[all-apple]`: aggregate native Apple stack, or a pass-through/no-op alias for packages
  with no Apple-specific dependencies.
- `package[all-gpu]`: aggregate GPU stack, or a pass-through/no-op alias for packages
  with no GPU-specific dependencies.

Keep `gpu` vendor-neutral only where that is technically honest; otherwise use an explicit profile
such as `server-nvidia` for Docker/container images or a future vendor-specific Python extra.

Python packaging uses bracket extras, for example `abstractgateway[server]`, not colon syntax.
Extras only add dependencies; they cannot turn a heavy base install back into a light one.

Docker is a separate deployment concern. Native Apple/MLX/Metal installs are supported through
Python extras on macOS; they are not expected to work inside a portable Docker image. Gateway keeps
two Docker strategies: a lightweight server image and an explicit NVIDIA server image.

### 3) Keep dependency cascades at entry-point profiles

Install profiles choose dependency closure. They do not imply that providers, models, memory,
capabilities, auth, or endpoints are configured and ready.

Recommended package roles:

- `abstractcore` stays light by default and exposes provider/server/capability/local-engine extras.
- `abstractgateway` chooses the deployment aggregate: HTTP, Runtime/Core/Agent, Vision, Voice,
  Music, Memory, and GPU/local profiles when explicitly requested. Because Gateway is the
  deployment composition root, `abstractgateway[apple]` and `abstractgateway[gpu]` are full native
  Python deployment profiles, equivalent in intent to `all-apple` and `all-gpu`.
- `abstractruntime` stays a durable kernel with optional Core integration; its Apple profiles only
  cascade to Core.
- `abstractagent` stays an agent behavior package; its Apple profiles only cascade to Core/Runtime.
- `abstractsemantics` stays a vocabulary/schema package; its Apple profiles are no-op compatibility
  aliases.
- `abstractmemory` owns storage/query contracts and optional backend extras such as LanceDB.
- `abstractvision` and `abstractvoice` own modality backends and plugin defaults.
- `abstractmusic` remains explicit/local-heavy until it has a remote-light base or remote backend.

### 4) Define configuration precedence

Configuration should cascade by explicit handoff and precedence, not by silently copying every
environment variable through the stack.

Recommended precedence:

1. explicit request/run values, when the host policy permits them;
2. Gateway deployment config/env for runtime hosting concerns;
3. AbstractCore persisted config/env for provider credentials, provider base URLs, model defaults,
   and Core media defaults;
4. capability package config/env for Vision, Voice, Music, and other backend details;
5. package defaults, with explicit `#FALLBACK` warnings when behavior changes.

`abstractgateway-config` may call or guide `abstractcore --config` / `abstractcore-config`, and it
may generate or pass Core server settings when it manages a deployment. It must not silently
reinterpret `ABSTRACTGATEWAY_*` values as Core or capability-package configuration.

### 5) Separate inbound server security from outbound provider credentials

Auth/CORS/origin policy belongs to the inbound HTTP boundary being exposed:

- Gateway auth and allowed origins protect Gateway HTTP/SSE routes and thin clients.
- Core server auth and allowed origins protect the standalone Core server when it is exposed
  directly or called as a separate service.
- Capability packages normally run as libraries/plugins or outbound clients. They consume provider
  credentials, base URLs, model ids, timeout settings, cache paths, devices, and backend flags.
  They do not inherit Gateway/Core bearer tokens or browser origin policy unless they intentionally
  expose their own production server.

Gateway auth is not a master key for lower packages:

- `ABSTRACTGATEWAY_AUTH_TOKEN` / `ABSTRACTGATEWAY_AUTH_TOKENS` protect Gateway.
- `ABSTRACTCORE_SERVER_API_KEY` protects the Core server.
- Provider credentials such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
  `OPENAI_COMPATIBLE_API_KEY`, OpenRouter keys, and Portkey keys are outbound provider secrets.
- Per-request upstream provider-key overrides for the Core server use the Core provider-key
  override channel, not the Gateway auth token.

When Gateway embeds Core in-process, only the Gateway server boundary is exposed to clients. When
Gateway calls a standalone Core server, the Gateway-to-Core connection must be explicit: Core
server URL, Core server auth token, Core base URL allowlists, and provider-key behavior are Core
server configuration.

### 6) Standardize readiness reporting

Discovery and setup checks must distinguish these states:

- `installed`: package import exists.
- `registered`: plugin/backend registered.
- `configured`: required env/config exists.
- `ready`: cheap non-generating preflight passes, or no preflight is needed.
- `route_available`: HTTP route exists.
- `available`: route exists, backend is ready, and policy permits use.

Thin clients must not enable image, audio, music, embeddings, or memory controls merely because a
package is installed.

## Consequences

### Positive

- Provides a clear install/config vocabulary for every package without erasing boundaries.
- Gives Core and Gateway clean, separate entry-point responsibilities.
- Prevents Gateway from becoming a dumping ground for provider/capability internals.
- Preserves light installs for Runtime, Semantics, and capability packages where possible.
- Makes server security boundaries explicit enough for Docker, installers, and thin clients.

### Negative

- Requires packaging cleanup across root, Core, Gateway, Vision, Voice, Memory, and Music.
- Requires config UX work: `abstractgateway-config`, Core config hardening, and readiness preflight.
- Some existing ADRs/docs that promised local-first base installs need refinement.

### Neutral

- Direct local use remains valid. This ADR changes default dependency/profile discipline, not the
  legitimacy of local engines.
- Gateway can still offer one-command profiles; the profile must be explicit about what it installs
  and what still needs configuration.

## Packages Affected

- `abstractframework`
- `abstractcore`
- `abstractgateway`
- `abstractruntime`
- `abstractagent`
- `abstractsemantics`
- `abstractmemory`
- `abstractvision`
- `abstractvoice`
- `abstractmusic`
- higher-level apps and installers that choose Gateway/Core profiles

## Related

- ADR-0001: `docs/adr/0001-layered-architecture.md`
- ADR-0018: `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
- ADR-0021: `docs/adr/0021-deployment-topologies-and-supported-scenarios.md`
- ADR-0028: `docs/adr/0028-capabilities-plugins-and-library-framework-modes.md`
- ADR-0029: `docs/adr/0029-permissive-dependency-and-licensing-policy.md`
- ADR-0031: `docs/adr/0031-workflow-llm-routing-overrides-provider-model-and-base-url.md`
- ADR-0032: `docs/adr/0032-package-dependency-boundaries-and-gateway-first-apps.md`
- Proposed backlog: `docs/backlog/proposed/2026-05-08_unified_install_profiles_and_config_entrypoints.md`
