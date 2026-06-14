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

## Next Recommended Work

1. Investigate Observer wait handling as a replayable session chat/handoff instead of continuing to refine the narrow answer modal.
2. Design a first-class Session -> Turn -> Run/Subrun -> Artifact/Log hierarchy for Runtime Activity before adding more run-table complexity.
3. Complete the Observer/Manager responsibility split so high-trust admin/process controls stop competing with observability surfaces.
4. Add a Gateway run-stats endpoint if Activity queue counts must be exact across the whole runtime instead of the loaded run page.
5. Adopt `build_artifact_descriptor_payload(...)` in direct `abstractvision`, `abstractvoice`, and `abstractmusic` artifact writers that bypass the Runtime AbstractCore generated-media path.

## Active Planned Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0142 | [Gateway tenant isolation and shared runtime design](planned/0142_gateway_tenant_isolation_and_shared_runtime.md) | Planned | Define and implement tenant-aware Gateway/Runtime isolation; current shared Gateway deployments are single-user or trusted-cohort only. |
| 076 | [OpenAI Responses API integration](planned/076_openai_responses_api_integration.md) | Planned | Define a true Core Server `/v1/responses` contract, use native Responses transports where available, and require Core-owned first-class Responses adapters for MLX, HuggingFace, Anthropic, and non-native endpoint profiles. |
| 0143 | [Shared Gateway per-principal runtime router](planned/0143_shared_gateway_per_principal_runtime_router.md) | In progress | Gateway principal auth, admin user CRUD, per-principal GatewayService routing, and Flow browser-session routing landed; broader app auth and route-family isolation remain open. |
| 0145-0153 | [Gateway control plane track](planned/gateway-control-plane/README.md) | Planned | Gateway-owned admin/account/config/workflow-permission control plane; starts with responsibility, RBAC, and browser-session contracts before broad UI/app migration. |
| 0164 | [Gateway Docker GHCR deployment track](planned/0164_gateway_docker_ghcr_deployment_track.md) | In progress | Align Gateway containers with ADR-0033/0034: `ghcr.io/lpalbou/abstractgateway` light/GPU tags, user-auth bootstrap, `/data` volume, PyPI-based image builds, and Docker docs. |
| 0166 | [Gateway local user-auth bootstrap UX](planned/0166_gateway_local_user_auth_bootstrap_ux.md) | In progress | Native `abstractgateway serve` should match Docker by creating/printing the `default/admin` browser-login token path when user auth is enabled. |
| 0167 | [Gateway provider connection setup console](planned/0167_gateway_provider_connection_setup_console.md) | In progress | Providers tab now owns endpoint URL/key setup with Test/Confirm modals; Defaults now maps capability routes only to configured provider connections and discovered models. |
| 0168 | [Abstract release root profile pin guard](planned/0168_release_skill_root_profile_pin_guard.md) | In progress | Tighten the `abstract-release` skill so partial lower-package releases cannot silently leave root pins/docs behind. |
| 0179 | [LLM and Agent model input artifacts](planned/0179_llm_agent_model_input_artifacts.md) | Planned | Add first-class Flow model-input artifact-list authoring for LLM Call and Agent nodes, lowering ordered refs to Runtime media/context attachments while preserving Gateway artifact validation and Core route compatibility. |
| 0182-0186 | [VisualFlow recursion budget track](planned/visualflow-recursion-budget/README.md) | Planned | Runtime-enforced recursive Subflow budget defaulting to 3, Flow cycle detection and controls, Gateway observability, a separate same-flow feedback-loop budget, and ADR/docs/vocabulary cleanup. |
| 0200 | [Gateway experimental NVIDIA image publish fix](planned/0200_gateway_experimental_nvidia_image_publish_fix.md) | Planned | Repair the experimental NVIDIA Gateway image path so GHCR GPU tags publish for real instead of remaining best-effort release attempts. |

## Gateway Control Plane Planned Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0145 | [Gateway admin console bootstrap](planned/gateway-control-plane/0145_gateway_admin_console_bootstrap.md) | In progress | Console v0 now serves `/console` with session sign-in, account/runtime summary, admin user management, optional email, create/delete confirmations, token rotation, and discovered provider/model defaults; richer runtime activity remains optional follow-up. |
| 0146 | [Gateway RBAC scope policy matrix](planned/gateway-control-plane/0146_gateway_rbac_scope_policy_matrix.md) | In progress | Central route-family policy gates operator/server-workspace/model-residency surfaces, runtime ids are tenant-unique, and the Alice/Bob matrix now covers runs, ledgers, artifacts, session artifacts, KG/session memory, private workflows, prompt-cache naming, runtime-scoped defaults, workspace helper denials, and discovery leak behavior. |
| 0147 | [Gateway per-principal config, secrets, and defaults](planned/gateway-control-plane/0147_gateway_per_principal_config_secrets_defaults.md) | In progress | Gateway-baseline plus per-user capability-default overlays and console UX landed; raw provider-secret storage/injection remains deliberately deferred pending a Core/Gateway secret boundary. |
| 0148 | [Gateway workflow registry ACLs](planned/gateway-control-plane/0148_gateway_workflow_registry_acl.md) | In progress | Immutable tenant catalog versions, admin default pointers, ACL APIs, explicit catalog scope, signed run-start/schedule policy, host-side catalog guards, ACL-aware catalog inspection, and discovery metadata landed; per-tool/workspace/secret policy intersection and UI remain. |
| 0150 | [Observer and Manager responsibility split](planned/gateway-control-plane/0150_observer_manager_responsibility_split.md) | Planned | Early containment audit to keep Observer focused on observability and admin/config ownership in Gateway/Gateway Console or later Manager surfaces. |
| 0153 | [Gateway browser session security contract](planned/gateway-control-plane/0153_gateway_browser_session_security_contract.md) | In progress | Gateway/Flow opaque browser sessions, CSRF, logout, token-rotation revocation, Code/Observer hosted proxy convergence, and HTTP/HTTPS/origin/expiry/logout/revocation cookie matrix tests landed. |

## VisualFlow Recursion Budget Planned Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0182 | [Runtime recursive subworkflow budget](planned/visualflow-recursion-budget/0182_runtime_recursive_subworkflow_budget.md) | Planned | Runtime owns recursive call detection at `START_SUBWORKFLOW`, with default 3 recursive calls and stable over-limit failure semantics. |
| 0183 | [Flow recursive Subflow analysis and controls](planned/visualflow-recursion-budget/0183_flow_recursive_subflow_analysis_and_controls.md) | Planned | AbstractFlow detects direct/mutual Subflow cycles, warns in preflight, and exposes synchronized recursive-call controls without enforcing execution. |
| 0184 | [Gateway recursion observability and runner coverage](planned/visualflow-recursion-budget/0184_gateway_recursion_observability_and_runner_coverage.md) | Planned | Gateway projects Runtime results, preserves ledger/history visibility, and tests no-stuck-parent behavior without owning enforcement. |
| 0185 | [VisualFlow feedback loop budget](planned/visualflow-recursion-budget/0185_visualflow_feedback_loop_budget.md) | Planned | Same-flow improvement loops get their own runtime-enforced feedback-cycle budget, separate from recursive Subflow calls and Agent iterations. |
| 0186 | [Recursion contract ADR, docs, and iteration vocabulary](planned/visualflow-recursion-budget/0186_recursion_contract_adr_docs_and_vocabulary.md) | Planned | Create or revise the durable ADR contract, document counting/defaults, and align labels such as Recursive Subflow calls, Agent loop iterations, and Feedback loop cycles. |

## Runtime Artifact Observability Completed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0198 | [Observer observability replay workbench](completed/runtime-artifact-observability/0198_observer_observability_replay_workbench.md) | Completed | Runtime history bundles now carry bounded replay artifact summaries and indexed best-effort session turns; Observer has a read-only Replay tab and Runtime Activity no longer exposes inline cancel controls. |
| 0197 | [Runtime artifact type OR filters and stable facets](completed/runtime-artifact-observability/0197_runtime_artifact_type_or_filter_facets.md) | Completed | Observer type chips now visibly combine with OR, selected results remain server-filtered, and chip counts come from the same non-type scope/search/date stats instead of the filtered result set. |
| 0194 | [Observer runtime activity monitor and wait actions](completed/runtime-artifact-observability/0194_observer_runtime_activity_monitor_and_wait_actions.md) | Completed | Runtime Activity now has explicit attention queues, a dense searchable/sortable run table, selected-run context/actions, direct cancel/stop, loaded-page count labeling, and offline/focus/responsive fixes. |
| 0193 | [Runtime artifact coredoc and explore skill](completed/runtime-artifact-observability/0193_runtime_artifact_coredoc_and_explore_skill.md) | Completed | Added Runtime artifact docs, root runtime-artifacts guide, package/root LLM updates, and a validated `runtime-explore` skill for bounded redacted investigations. |
| 0190 | [Media generation provenance and enrichment](completed/runtime-artifact-observability/0190_media_generation_provenance_and_enrichment.md) | Completed | Runtime/Gateway generated-media paths now store descriptors/structured metadata, preserve child projection provenance, redact sensitive metadata, and cover image/video/voice/music/transcript tests. |
| 0192 | [Observer canonical artifact explorer UI](completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md) | Completed | Observer Runtime Artifact Explorer now consumes Gateway envelopes/stats, separates Voice/Music/Sound/Unclassified audio, shows server-backed counts/pages, previews content, and surfaces provenance/actions with explicit legacy labels. |
| 0191 | [Gateway artifact envelope, query, and provider traces](completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md) | Completed | Gateway artifact search/list/detail now expose `artifact_envelope_v1`, exact stats/facets, bounded paging, access-action stats, action links, capability descriptors, and UI-safe `artifact_kind` filtering. |
| 0188 | [Artifact descriptor contract and ADR](completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md) | Completed | Added ADR-0036 and Runtime-owned `ArtifactDescriptor`/`ArtifactAccessStats` vocabulary with legacy projection and fallback labels. |
| 0189 | [Runtime artifact catalog and access stats](completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md) | Completed | Added descriptor-compatible Runtime metadata, explicit update/access APIs, exact counts/facets, filters, paging, and a repairable SQLite file-store catalog. |

## Active Proposed Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0144 | [User profile metadata for selective model grounding](proposed/0144_user_profile_context_grounding.md) | Proposed | Discuss first/last name, birth date, inferred country, provenance, and query-time selective context injection before implementation. |
| 0151 | [Runtime Explorer contract](proposed/gateway-control-plane/0151_runtime_explorer_contract.md) | Proposed | Reviewer consensus: start with a read-only Gateway envelope contract and Observer page for typed runtime resources; defer `abstractexplorer`, delete/export, raw workspace browsing, and admin cross-user exploration. |
| 0152 | [AbstractManager package extraction](proposed/gateway-control-plane/0152_abstractmanager_package_extraction.md) | Proposed | Revisit a separate `abstractmanager` package only after console/config/workflow ACL surfaces prove real maintenance or reuse pressure. |
| 0155 | [Hosted proxy shared helper extraction](proposed/gateway-control-plane/0155_hosted_proxy_shared_helper_extraction.md) | Proposed | Keep conformance tests now; extract a shared Node helper only if Code/Observer or future hosted apps drift again. |
| 0162-0163 | [Installer and setup track](proposed/installers/README.md) | Proposed | Prepare signed installer CI and evaluate a CPU-local profile after the extraction, generated manifest, doctor, and install chooser work landed. |
| 0169 | [Gateway Console route-specific default catalogs](proposed/0169_gateway_console_route_specific_default_catalogs.md) | Proposed | Decide the smallest Defaults-modal adapter for embeddings, image/video, voice, and music catalog filtering without moving URL/key setup out of Providers. |
| 0181 | [Code node managed Python packages with simple authoring UX](proposed/0181_code_node_managed_python_packages_simplified_ux.md) | Proposed | Preserve the package-install architecture guardrails while making the user process simple: write imports, confirm package chips, prepare/test through Gateway, and run with Runtime/worker-managed provenance. |
| 0195-0196 | [Runtime artifact observability proposed track](proposed/runtime-artifact-observability/README.md) | Proposed | Parked follow-ups for wait handling via replayable session chat/handoff and first-class Session -> Turn -> Run hierarchy in Observer Runtime Activity. |

## Runtime Artifact Observability Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0195 | [Observer wait handling via session replay and chat handoff](proposed/runtime-artifact-observability/0195_observer_wait_replay_chat_session_handoff.md) | Proposed | Investigate whether waiting runs should be answered through a replayable session/chat context rather than a narrow modal. |
| 0196 | [Observer session-turn-runtime hierarchy](proposed/runtime-artifact-observability/0196_observer_session_turn_runtime_hierarchy.md) | Proposed | Investigate a first-class Session -> Turn -> Run/Subrun -> Artifact/Log hierarchy for Runtime Activity and artifact/log navigation. |

## Installer And Setup Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0162 | [Signed installer CI and distribution](proposed/installers/0162_signed_installer_ci_and_distribution.md) | Proposed | Move from prototype builds to signed/notarized native installer artifacts with checksums and rollback/support logs. |
| 0163 | [CPU local inference install profile](proposed/installers/0163_cpu_local_inference_install_profile.md) | Proposed | Evaluate `abstractframework[cpu]` separately from Light; require package-by-package backend and dependency evidence before promotion. |

## Multimodal Capabilities Completed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0175 | [Multimodal capability taxonomy and schema](completed/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md) | Completed | Added route-keyed `capability_routes`, JSON Schema validation, Core helper APIs, route-aware `/v1/models`, Runtime forwarding, Gateway Console route filters, and `input.music` default-route support; media-policy helper migration remains a follow-up. |

## Multimodal Capabilities Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0176 | [Multimodal model acquisition guidance](proposed/multimodal-capabilities/0176_multimodal_model_acquisition_guidance.md) | Proposed | Explore CLI/doctor and later console guidance for downloading/loading configured local models without conflating acquisition with defaults. |

## Recent Completed Work

| ID | Item | Completed | Notes |
|----|------|-----------|-------|
| 0198 | [Observer observability replay workbench](completed/runtime-artifact-observability/0198_observer_observability_replay_workbench.md) | 2026-06-06 | Added bounded artifact summaries and indexed session-turn discovery to Runtime history bundles, plus an Observe Replay tab and monitor-only Runtime Activity actions. |
| 0199 | [AbstractFlow and AbstractAssistant vision LoRA and batch surface](completed/0199_abstractflow_and_abstractassistant_vision_lora_and_batch_surface.md) | 2026-06-14 | Flow now surfaces task-filtered provider/model discovery, `count`, ordered `seeds`, and stacked LoRA adapters in the media node authoring UI, while Assistant forwards the same route fields and adapter discovery through its Gateway thin-client path. |
| 0197 | [Runtime artifact type OR filters and stable facets](completed/runtime-artifact-observability/0197_runtime_artifact_type_or_filter_facets.md) | 2026-06-06 | Type chips now compose as OR, keep available counts visible from base facets, and Gateway regression coverage verifies mixed-kind artifact filters return a union. |
| 0194 | [Observer runtime activity monitor and wait actions](completed/runtime-artifact-observability/0194_observer_runtime_activity_monitor_and_wait_actions.md) | 2026-06-06 | Runtime Activity now separates operational supervision from artifact browsing with attention queues, readable waiting context, safe actions, honest loaded-page counts, and offline/focus/responsive fixes. |
| 0193 | [Runtime artifact coredoc and explore skill](completed/runtime-artifact-observability/0193_runtime_artifact_coredoc_and_explore_skill.md) | 2026-06-06 | Added cross-package artifact/retrieval docs, regenerated LLM docs, and validated the `runtime-explore` skill. |
| 0190 | [Media generation provenance and enrichment](completed/runtime-artifact-observability/0190_media_generation_provenance_and_enrichment.md) | 2026-06-06 | Added Runtime-owned descriptor payload helper, generated-media descriptors/metadata, Gateway projection preservation, STT descriptors, link sanitization, and media provenance tests. |
| 0192 | [Observer canonical artifact explorer UI](completed/runtime-artifact-observability/0192_observer_canonical_artifact_explorer_ui.md) | 2026-06-06 | Observer now uses Gateway-backed artifact envelopes/stats/pages, separates semantic media kinds from render formats, and exposes preview/provenance/action detail with focused tests/build/browser smoke validation. |
| 0191 | [Gateway artifact envelope, query, and provider traces](completed/runtime-artifact-observability/0191_gateway_artifact_envelope_query_and_provider_traces.md) | 2026-06-06 | Gateway now projects Runtime artifact descriptors into `artifact_envelope_v1`, exact stats/facets, bounded pages, access-action stats, and canonical/legacy-safe filters. |
| 0189 | [Runtime artifact catalog and access stats](completed/runtime-artifact-observability/0189_runtime_artifact_catalog_and_access_stats.md) | 2026-06-06 | Runtime artifact metadata now persists descriptors/access stats and supports exact counts, facets, filters, paging, and repairable file-store catalogs. |
| 0188 | [Artifact descriptor contract and ADR](completed/runtime-artifact-observability/0188_artifact_descriptor_contract_and_adr.md) | 2026-06-06 | Added ADR-0036 and the Runtime-owned artifact descriptor contract separating render kind, semantic kind, provenance, media facts, and legacy fallback labels. |
| 0187 | [Framework PDF profile pins](completed/0187_framework_pdf_profile_pins.md) | 2026-06-06 | Root Light, Apple, and GPU pins now consume Core/Runtime/Gateway versions with permissive PDF read/write support and regenerated installer manifest coverage. |
| 0180 | [AbstractFlow compact node pin disclosure](completed/0180_abstractflow_compact_node_pin_disclosure.md) | 2026-06-04 | Added a generic UI-only node pin disclosure policy, compact bottom chevron, focused Vitest coverage, lint/build validation, and browser QA for compact/expanded/connected optional pins. |
| 0178 | [Gateway and Flow reasoning control propagation](completed/0178_gateway_flow_reasoning_control.md) | 2026-06-03 | Added Gateway run-scoped `thinking`, Flow LLM/Agent controls and pins, Runtime VisualFlow propagation, AbstractAgent generation-param forwarding, docs, and focused Gateway/Runtime/Agent/Flow validation. |
| 0177 | [Flow route-aware provider and model selection](completed/0177_flow_route_aware_model_selection.md) | 2026-06-03 | Threaded Core/Gateway `capability_route` discovery into Flow selectors and Runtime Provider Models execution, including fail-closed invalid route handling, docs, and focused Runtime/Flow validation. |
| 0175 | [Multimodal capability taxonomy and schema](completed/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md) | 2026-06-03 | Added route-keyed model capability metadata and schema, Core route helpers, `/v1/models?capability_route=...`, Runtime/Gateway forwarding, Gateway Console route filters, docs, and focused cross-package tests. |
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
