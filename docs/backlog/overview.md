# AbstractFramework Backlog Overview

This root backlog is the framework-level planning ledger for cross-package work. Some older items
use legacy naming and duplicate numeric prefixes; new items should use four-digit global IDs and
the lifecycle folders described by the backlog process.

## Current Counts

- Planned: many legacy items plus active cross-package work.
- Proposed: legacy proposed items exist.
- Completed: historical completion ledger exists under `completed/`.
- Deprecated: not yet normalized at the root level.
- Recurrent: not yet normalized at the root level.

## Active Planned Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0142 | [Gateway tenant isolation and shared runtime design](planned/0142_gateway_tenant_isolation_and_shared_runtime.md) | Planned | Define and implement tenant-aware Gateway/Runtime isolation; current shared Gateway deployments are single-user or trusted-cohort only. |
| 0143 | [Shared Gateway per-principal runtime router](planned/0143_shared_gateway_per_principal_runtime_router.md) | In progress | Gateway principal auth, admin user CRUD, per-principal GatewayService routing, and Flow browser-session routing landed; broader app auth and route-family isolation remain open. |
| 0145-0153 | [Gateway control plane track](planned/gateway-control-plane/README.md) | Planned | Gateway-owned admin/account/config/workflow-permission control plane; starts with responsibility, RBAC, and browser-session contracts before broad UI/app migration. |
| 0164 | [Gateway Docker GHCR deployment track](planned/0164_gateway_docker_ghcr_deployment_track.md) | In progress | Align Gateway containers with ADR-0033/0034: `ghcr.io/lpalbou/abstractgateway` light/GPU tags, user-auth bootstrap, `/data` volume, PyPI-based image builds, and Docker docs. |
| 0166 | [Gateway local user-auth bootstrap UX](planned/0166_gateway_local_user_auth_bootstrap_ux.md) | In progress | Native `abstractgateway serve` should match Docker by creating/printing the `default/admin` browser-login token path when user auth is enabled. |
| 0167 | [Gateway provider connection setup console](planned/0167_gateway_provider_connection_setup_console.md) | In progress | Providers tab now owns endpoint URL/key setup with Test/Confirm modals; Defaults now maps capability routes only to configured provider connections and discovered models. |
| 0168 | [Abstract release root profile pin guard](planned/0168_release_skill_root_profile_pin_guard.md) | In progress | Tighten the `abstract-release` skill so partial lower-package releases cannot silently leave root pins/docs behind. |
| 0175 | [Multimodal capabilities track](planned/multimodal-capabilities/README.md) | Planned | Refine the Core capability taxonomy so speech, SFX/sound, and music understanding are distinct without breaking compatibility. Registry coverage for the initial audio-understanding models completed in 0174. |

## Gateway Control Plane Planned Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0145 | [Gateway admin console bootstrap](planned/gateway-control-plane/0145_gateway_admin_console_bootstrap.md) | In progress | Console v0 now serves `/console` with session sign-in, account/runtime summary, admin user management, optional email, create/delete confirmations, token rotation, and discovered provider/model defaults; richer runtime activity remains optional follow-up. |
| 0146 | [Gateway RBAC scope policy matrix](planned/gateway-control-plane/0146_gateway_rbac_scope_policy_matrix.md) | In progress | Central route-family policy gates operator/server-workspace/model-residency surfaces, runtime ids are tenant-unique, and the Alice/Bob matrix now covers runs, ledgers, artifacts, session artifacts, KG/session memory, private workflows, prompt-cache naming, runtime-scoped defaults, workspace helper denials, and discovery leak behavior. |
| 0147 | [Gateway per-principal config, secrets, and defaults](planned/gateway-control-plane/0147_gateway_per_principal_config_secrets_defaults.md) | In progress | Gateway-baseline plus per-user capability-default overlays and console UX landed; raw provider-secret storage/injection remains deliberately deferred pending a Core/Gateway secret boundary. |
| 0148 | [Gateway workflow registry ACLs](planned/gateway-control-plane/0148_gateway_workflow_registry_acl.md) | In progress | Immutable tenant catalog versions, admin default pointers, ACL APIs, explicit catalog scope, signed run-start/schedule policy, host-side catalog guards, ACL-aware catalog inspection, and discovery metadata landed; per-tool/workspace/secret policy intersection and UI remain. |
| 0150 | [Observer and Manager responsibility split](planned/gateway-control-plane/0150_observer_manager_responsibility_split.md) | Planned | Early containment audit to keep Observer focused on observability and admin/config ownership in Gateway/Gateway Console or later Manager surfaces. |
| 0153 | [Gateway browser session security contract](planned/gateway-control-plane/0153_gateway_browser_session_security_contract.md) | In progress | Gateway/Flow opaque browser sessions, CSRF, logout, token-rotation revocation, Code/Observer hosted proxy convergence, and HTTP/HTTPS/origin/expiry/logout/revocation cookie matrix tests landed. |

## Active Proposed Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0144 | [User profile metadata for selective model grounding](proposed/0144_user_profile_context_grounding.md) | Proposed | Discuss first/last name, birth date, inferred country, provenance, and query-time selective context injection before implementation. |
| 0151 | [Runtime Explorer contract](proposed/gateway-control-plane/0151_runtime_explorer_contract.md) | Proposed | Reviewer consensus: start with a read-only Gateway envelope contract and Observer page for typed runtime resources; defer `abstractexplorer`, delete/export, raw workspace browsing, and admin cross-user exploration. |
| 0152 | [AbstractManager package extraction](proposed/gateway-control-plane/0152_abstractmanager_package_extraction.md) | Proposed | Revisit a separate `abstractmanager` package only after console/config/workflow ACL surfaces prove real maintenance or reuse pressure. |
| 0155 | [Hosted proxy shared helper extraction](proposed/gateway-control-plane/0155_hosted_proxy_shared_helper_extraction.md) | Proposed | Keep conformance tests now; extract a shared Node helper only if Code/Observer or future hosted apps drift again. |
| 0162-0163 | [Installer and setup track](proposed/installers/README.md) | Proposed | Prepare signed installer CI and evaluate a CPU-local profile after the extraction, generated manifest, doctor, and install chooser work landed. |
| 0169 | [Gateway Console route-specific default catalogs](proposed/0169_gateway_console_route_specific_default_catalogs.md) | Proposed | Decide the smallest Defaults-modal adapter for embeddings, image/video, voice, and music catalog filtering without moving URL/key setup out of Providers. |

## Installer And Setup Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0162 | [Signed installer CI and distribution](proposed/installers/0162_signed_installer_ci_and_distribution.md) | Proposed | Move from prototype builds to signed/notarized native installer artifacts with checksums and rollback/support logs. |
| 0163 | [CPU local inference install profile](proposed/installers/0163_cpu_local_inference_install_profile.md) | Proposed | Evaluate `abstractframework[cpu]` separately from Light; require package-by-package backend and dependency evidence before promotion. |

## Multimodal Capabilities Planned Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0175 | [Multimodal capability taxonomy and schema](planned/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md) | Planned | Add route-level audio input semantics for speech, sound/SFX, and music; preserve broad legacy booleans as compatibility views during migration. |

## Multimodal Capabilities Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0176 | [Multimodal model acquisition guidance](proposed/multimodal-capabilities/0176_multimodal_model_acquisition_guidance.md) | Proposed | Explore CLI/doctor and later console guidance for downloading/loading configured local models without conflating acquisition with defaults. |

## Recent Completed Work

| ID | Item | Completed | Notes |
|----|------|-----------|-------|
| 0174 | [Audio understanding model registry coverage](completed/0174_audio_understanding_model_registry.md) | 2026-06-02 | Added source-backed Core registry entries and route hints for Qwen3-Omni Captioner/Instruct, Qwen2.5-Omni, Qwen2-Audio, Audio Flamingo 3, and MOSS-Audio; Qwen3.6 remains audio false; Qwen3.6 MTP GGUF variants no longer overclaim image/video; schema, alias, lookup, and duplicate-key checks passed. |
| 0173 | [Core provider endpoint profiles](completed/0173_core_provider_endpoint_profiles.md) | 2026-06-02 | Added Core-owned single-principal provider endpoint profiles, `abstractcore config set-provider/providers/models/test-provider/delete-provider`, `endpoint:*` registry/factory and embedding-manager resolution, OVH-style docs, and redacted CLI output. |
| 0172 | [Explicit multimodal default fallback routing](completed/0172_explicit_multimodal_default_fallback_routing.md) | 2026-06-02 | Made `input.voice` and explicit/covered `input.video` the fallback gates, removed Flow default editing from Model Residency, allowed blank LLM/Agent pins to use Gateway defaults, added Auto provider switch-back options, and validated Core/Gateway/Runtime/Flow behavior. |
| 0171 | [Gateway Console sandbox client grounding and media attachments](completed/0171_gateway_console_sandbox_client_grounding_and_media.md) | 2026-06-01 | Added browser-local prompt grounding for Console Sandbox text tests, fixed artifact-backed image uploads through Gateway/Runtime/Core into native OpenAI-compatible `image_url` payloads, and documented the prompt-only untrusted metadata boundary. |
| 0170 | [Core and Gateway capability-default config convergence](completed/0170_core_gateway_capability_defaults_config_convergence.md) | 2026-06-01 | Added scoped Core config files and `abstractcore config` defaults commands; Gateway baseline/user defaults now write runtime-scoped Core config only. |
| 0165 | [AbstractFlow web-only product migration](completed/0165_abstractflow_web_only_product_migration.md) | 2026-05-31 | Flattened AbstractFlow into the root npm web package, removed Python package/backend/tests, moved examples to `examples/flows`, removed Python Flow from root pip profiles, and updated launch/docs/release paths. |
| 0161 | [Three-path public install guide](completed/0161_three_path_public_install_guide.md) | 2026-05-31 | Added `docs/install.md`, linked it from user docs, and clarified that Light is remote-first rather than reduced-functionality. |
| 0160 | [Framework doctor and manifest CLI](completed/0160_framework_doctor_and_launch_cli.md) | 2026-05-31 | Added the `abstractframework` console script with `doctor` and `manifest` commands; launch remains deferred unless it can delegate cleanly. |
| 0159 | [Generated install manifest contract](completed/0159_generated_install_manifest_contract.md) | 2026-05-31 | Added manifest generator, checked-in JSON/schema, CLI drift check, and tests tying the manifest to root pins. |
| 0158 | [Installer repository extraction](completed/0158_installer_repository_extraction.md) | 2026-05-31 | Moved installer prototypes to `https://github.com/lpalbou/AbstractInstallers` and removed the tracked root `abstractinstallers/` tree. |
| 0157 | [Gateway provider endpoint profiles](completed/0157_gateway_provider_endpoint_profiles.md) | 2026-05-31 | Added Gateway-owned provider endpoint profiles with descriptions, write-only API keys, virtual `endpoint:*` providers in discovery, Runtime resolution, local dynamic provider construction, console UI with model discovery, and tests. |
| 0156 | [Retained runtime admin lifecycle](completed/0156_retained_runtime_admin_lifecycle.md) | 2026-05-30 | Added admin-only retained runtime list/transfer/purge routes, Gateway Console actions, scoped purge deletion, transfer semantics, and regression tests. |
| 0154 | [Multi-user security release blockers](completed/0154_multi_user_security_release_blockers.md) | 2026-05-30 | Added retained-runtime reservations, Code/Observer hosted URL guards, published launcher user bootstrap, and `.DS_Store` cleanup. |
| 0149 | [Cross-app Gateway auth and defaults convergence](completed/0149_cross_app_gateway_auth_defaults_convergence.md) | 2026-05-30 | Per-app hosted/local auth/default matrix completed; Flow, Code Web, and Observer use hosted browser-session proxy auth; shared auth/default component intentionally deferred until duplication creates real pressure. |
| 0141 | [Flow browser-session Gateway auth](completed/0141_flow_browser_session_gateway_auth.md) | 2026-05-30 | Initial Flow browser sign-in removed server/admin ambient browser auth; 0153 now supersedes raw token cookies with opaque Gateway browser sessions. |
| 0140 | [Abstract Release Skill](completed/0140_abstract_release_skill.md) | 2026-05-24 | Added a read-only framework release orchestration skill with package discovery, release-wave planning, dependency-floor review, root profile pin drift checks, PyPI visibility gates, and approval/traceability guidance. |
| 0139 | [Unified Framework Capability Defaults](completed/0139_unified_framework_capability_defaults.md) | 2026-05-24 | Core-owned routing defaults for input/output/embedding/rerank, Gateway control-plane access, atomic provider/model resolution, catalog-backed Flow defaults UI, and qwen3.6 text default. |

## Operating Notes

- Use `docs/adr/` for durable architecture policy.
- Use this backlog for execution traceability, validation evidence, and follow-up state.
- New backlog item filenames should use `NNNN_<slug>.md`; date-prefixed legacy files should not be copied for new work.
