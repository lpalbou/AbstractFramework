# Completed: ADR Refresh For Install Profiles And Configuration Boundaries

## Metadata
- Created: 2026-05-08
- Status: Completed
- Completed: 2026-05-08

## Context

The unified install-profile and configuration-entrypoint investigation clarified a design that is
not yet represented cleanly in the framework ADR set:

- AbstractFramework has two operational entry points: AbstractCore and AbstractGateway.
- Install profiles choose dependency closure; they do not imply backend readiness.
- Configuration cascades by explicit handoff and precedence, not by silently copying every env var.
- Inbound auth/CORS/origin policy belongs to packages that expose HTTP servers.
- Outbound provider credentials and base URLs belong to Core or capability-package clients.

The current ADR set already contains most adjacent decisions: layered architecture, capability
plugins, Gateway control plane, deployment topologies, workflow routing, dependency minimization,
and package boundaries. The missing piece is a first-class ADR for install/config/security
boundaries.

## ADR Review Findings

Keep without conceptual change:

- `docs/adr/0001-layered-architecture.md` remains valid as the base dependency rule. It is already
  refined by ADR-0032.
- `abstractruntime/docs/adr/0001_layered_coupling_with_abstractcore.md` still supports the current
  direction: Runtime kernel stays dependency-light, Core integration is opt-in.
- `abstractruntime/docs/adr/0003_provenance_tamper_evident_hash_chain.md` is unrelated except for
  optional dependency discipline.
- Most memory/provenance/tool/runtime ADRs are compatible with the new profile work and do not
  need edits for this topic.

Add a new framework ADR:

- Add `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`.
- This should be the canonical decision for:
  - profile vocabulary: base, remote, server, apple, gpu, all-apple, all-gpu;
  - two entry points: `abstractcore` and `abstractgateway`;
  - root `abstractframework` as a curated install/docs hub, not a third config authority;
  - explicit config precedence;
  - separate Gateway auth, Core server auth, and outbound provider credentials;
  - capability readiness states.

Why a new ADR: ADR-0032 is already a broad dependency-boundary document. Adding install-profile
syntax, config precedence, and auth/CORS boundaries there would make it too large and harder to
apply during packaging work.

Update existing framework ADRs after ADR-0033 exists:

- `docs/adr/0032-package-dependency-boundaries-and-gateway-first-apps.md`
  - Keep as the package dependency map.
  - Add a link to ADR-0033.
  - Mention that dependency cascades are implemented by entry-point profiles, not by forcing fake
    extras onto every package.
  - Update the Gateway dependency tree once the base persona is chosen.

- `docs/adr/0028-capabilities-plugins-and-library-framework-modes.md`
  - Expand the title/scope from Audio/Voice/Vision to include Music as experimental.
  - Clarify that capability packages normally own outbound provider/backend config, not inbound
    Gateway/Core auth or browser origins.
  - Add readiness states: installed, registered, configured, ready, route_available, available.
  - Add the current distinction between production Core/Gateway routes and dev/example servers in
    Vision/Voice.

- `docs/adr/0021-deployment-topologies-and-supported-scenarios.md`
  - Add a clearer distinction between Core standalone server mode and Gateway deployment mode.
  - Add a role for capability backends/outbound providers.
  - State that Core server auth/origins matter only when the Core server is exposed or called as a
    separate service.
  - Reference Gateway server profiles: remote-light server, memory, and experimental GPU server.

- `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
  - Keep the control-plane decision.
  - Refine the security baseline so Gateway bearer auth/origin policy is explicitly separate from
    Core server auth and provider API keys.
  - Clarify that Gateway direct media routes are Gateway-owned HTTP/artifact contracts with
    Core/Vision/Voice-owned backend configuration.

- `docs/adr/0031-workflow-llm-routing-overrides-provider-model-and-base-url.md`
  - Keep `provider`/`model` first.
  - Add the new security rule: `base_url` is host policy, must be allowlisted where user-controlled,
    and must not carry provider secrets in workflow JSON.
  - Note that Core server uses a dedicated provider-key override header for upstream provider keys.

- `docs/adr/0029-permissive-dependency-and-licensing-policy.md`
  - Accept or refresh it during profile work.
  - Add that remote-light defaults and local-engine extras are the packaging expression of
    dependency minimization.
  - Reconcile "local-first" language with the new two-entrypoint model: direct local experiences
    remain supported, but server/default installs should not pull local engines by surprise.

Update package ADRs after package profile decisions are accepted:

- `abstractvoice/docs/adr/0001-local_assistant_out_of_box.md`
  - This is the highest-risk package ADR mismatch.
  - It currently says bare `pip install abstractvoice` should include local assistant dependencies
    such as faster-whisper. That conflicts with a remote-light base install.
  - Either revise it to say local assistant works out of the box with `abstractvoice[voice]` /
    `abstractvoice[local]`, or explicitly decide that bare AbstractVoice remains local-heavy.
  - The recommended direction is to revise/supersede it, keeping public `VoiceManager()` local-first
    while making the AbstractCore plugin remote-first for server installs.

- `docs/adr/reorg/002_abstractmusic_inprocess_local_generation.md`
  - Keep accepted for direct/local AbstractMusic.
  - Add a clarifying note that local-first Music is not included in remote-light Gateway/Core
    defaults until Music has a lightweight remote-capable base.

- `docs/adr/reorg/003_abstractmusic_acestep_v15_backend_source_strategy.md`
  - Keep accepted.
  - Link it from any future Music profile split because it explains why ACE-Step remains a heavy
    local extra.

- `abstractruntime/docs/adr/0002_execution_modes_local_remote_hybrid.md`
  - Optional small update: clarify that "remote AbstractCore server" implies explicit Core server
    auth/config, not Gateway token inheritance.

Do not remove ADRs:

- Superseded ADRs should remain as historical records.
- The `docs/adr/reorg/` files should not be deleted just because some are short; they preserve
  product decisions for Music, SmartNote, Assistant, and installer work.
- ADR-0032 should not be deleted or replaced. It should be complemented by ADR-0033.

## Recommended Roadmap

1. Promote or draft ADR-0033 first.
2. Refresh ADR-0032, ADR-0028, ADR-0021, ADR-0018, ADR-0031, and ADR-0029 to point to ADR-0033.
3. Resolve the AbstractVoice ADR-0001 mismatch before changing Voice packaging.
4. Add small clarifying notes to Music and Runtime package ADRs when their proposed package-profile
   items are promoted.
5. Update `docs/adr/README.md` last so the index reflects the accepted final ADR set.

## Promotion Criteria

Promote this item when maintainers choose:

- bare `abstractgateway` persona: minimal runner/CLI or remote-light server;
- whether bare `abstractcore` includes official hosted provider SDKs or keeps them in
  `abstractcore[remote]`;
- whether bare `abstractvoice` is remote-light or local assistant heavy;
- whether `abstractgateway[server]` includes memory by default or keeps `abstractgateway[memory]`
  separate.

## Validation Ideas

- ADR index links resolve.
- ADR-0033 does not contradict ADR-0001, ADR-0021, ADR-0028, ADR-0031, or ADR-0032.
- Package ADRs no longer promise heavy local dependencies in default installs unless the package
  owners intentionally choose that base persona.
- Backlog proposed items link to the ADR that owns each strategic decision.

## Completion Report

- Completed: 2026-05-08

### Summary

Implemented the ADR refresh for install profiles, configuration entry points, and server-boundary
security.

Added a new accepted framework ADR:

- `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`

This ADR now owns the canonical decisions for:

- two operational entry points: `abstractcore` and `abstractgateway`;
- profile vocabulary and bracket-extra syntax;
- dependency cascades through entry-point profiles rather than fake package symmetry;
- configuration precedence from request/run values down to package defaults;
- separate Gateway auth, Core server auth, and outbound provider credentials;
- readiness states for capabilities and thin-client gating.

Refreshed framework ADRs:

- `docs/adr/0032-package-dependency-boundaries-and-gateway-first-apps.md`
  - Kept it as the dependency-boundary and gateway-first app ADR.
  - Added ADR-0033 as the owner of install/config/security rules.
  - Clarified Gateway server and memory profile dependency expectations.
- `docs/adr/0028-capabilities-plugins-and-library-framework-modes.md`
  - Expanded the scope to include Music as experimental.
  - Added server/security boundary language for Core/Gateway versus capability packages.
  - Added readiness-state terminology.
- `docs/adr/0021-deployment-topologies-and-supported-scenarios.md`
  - Added Core server and capability backend roles.
  - Clarified Gateway deployment profiles and explicit Gateway-to-Core handoff.
- `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
  - Refined the security baseline so Gateway auth/origins are separate from Core server auth and
    provider API keys.
  - Clarified direct media routes as Gateway contracts with Core/capability backend config.
- `docs/adr/0031-workflow-llm-routing-overrides-provider-model-and-base-url.md`
  - Strengthened the `base_url` security boundary and provider-key override language.
- `docs/adr/0029-permissive-dependency-and-licensing-policy.md`
  - Added install-profile-based dependency minimization.
  - Reconciled local-capable integrations with remote-light server defaults.
- `docs/adr/README.md`
  - Added ADR-0033 to the index.
  - Updated ADR-0028 status/title and package references.

Refreshed package ADRs:

- `abstractruntime/docs/adr/0002_execution_modes_local_remote_hybrid.md`
  - Clarified that remote AbstractCore server mode uses explicit Core server auth/config and does
    not inherit Gateway tokens.
- `abstractvoice/docs/adr/0001-local_assistant_out_of_box.md`
  - Resolved the major mismatch by scoping local assistant out-of-box behavior to local voice
    profiles such as `abstractvoice[voice]` / `abstractvoice[local]`, unless maintainers
    intentionally keep bare `abstractvoice` local-heavy.
  - Preserved public direct-library local-first semantics where local engines are installed.
- `docs/adr/reorg/002_abstractmusic_inprocess_local_generation.md`
  - Clarified that local-first Music applies to explicit Music/local-profile use, not remote-light
    Gateway/Core defaults.
- `docs/adr/reorg/003_abstractmusic_acestep_v15_backend_source_strategy.md`
  - Clarified that ACE-Step belongs in an explicit heavy local extra if Music profiles are split.

### Decisions Made

- Created ADR-0033 as an accepted ADR instead of only adding notes to ADR-0032. This keeps the
  package dependency map separate from install/config/security policy.
- Did not remove any ADRs. Superseded and short ADRs preserve useful history.
- Did not change unrelated dirty files already present in the workspace.
- Did not update backlog overview tables because this task specifically requested transferring
  this proposed item to completed and updating ADRs.

### Validation

- Read the relevant ADR set before editing:
  - root `docs/adr/`;
  - `abstractruntime/docs/adr/`;
  - `abstractvoice/docs/adr/`.
- Kept edits scoped to ADR files and this backlog completion file.
- Added ADR-0033 links from the ADRs that now depend on it.
- Verified the ADR README index includes the new ADR.

### Residual Risks And Follow-Ups

- Package metadata still needs implementation work to match the ADRs, especially:
  - choosing the bare `abstractgateway` persona;
  - deciding whether bare `abstractcore` includes hosted provider SDKs;
  - deciding whether bare `abstractvoice` becomes remote-light or remains local-heavy;
  - adding/validating Gateway `server`, `memory`, and GPU profiles.
- Core server CORS/origin policy still needs implementation hardening. ADR-0033 defines the
  boundary; it does not implement the server middleware/config changes.
- Gateway capability readiness must still be implemented/tested against the new state vocabulary.
- Music still needs a package split before it can participate in remote-light defaults.
