# AbstractFramework Backlog Overview

This root backlog is the framework-level planning ledger for cross-package work. Some older items
use legacy naming and duplicate numeric prefixes; new items should use four-digit global IDs and
the lifecycle folders described by the backlog process.

## Current Counts

On-disk item files on 2026-09-26 (recursive, topic tracks included; README, overview, template and
`evidence/` files excluded). The legacy part of the backlog still breaks the one-ID-one-item rule,
so these are file counts, not unique IDs: see [Hygiene Findings](#hygiene-findings) and 0889.

| State | Files | Notes |
|---|---|---|
| Planned | 117 | 74 flat + tracks: agency-parity 11, app-surfaces 6, docs-hygiene 7, multimodal-capability-projection 8, gateway-control-plane 6, visualflow-recursion-budget 5. Includes 24 stale copies of completed items (0889). |
| Proposed | 36 | 28 flat (0905 included) + tracks installers 2, gateway-control-plane 3, runtime-artifact-observability 2, multimodal-capabilities 1. |
| Completed | 234 | 224 flat + tracks runtime-artifact-observability 9, multimodal-capabilities 1. Includes 0906–0915 and the moves of 0875 and 0900 (2026-09-26). |
| Deprecated | 0 | |
| Recurrent | 2 | [`recurrent/`](recurrent/README.md): backlog/ADR hygiene, post-completion follow-up triage. |

Not counted: `fable-opinions/agency_deep_dive_and_codex_comparison.md` (analysis, unindexed; 0889).

## Next Recommended Work

**Release state (2026-09-26): the 2026-09-25/26 mission wave is committed locally in every repo and
the release is STAGED, waiting for the operator's go** (nothing tagged, pushed or published; see
[Staged Release](#staged-release-2026-09-2526-wave-not-published)). Release steps that belong to that
wave: [0890](planned/0890_wire_bundled_flow_interface_pins_and_rebuild_gateway_bundles.md) (wire the
remaining bundled-flow pins, then rebuild the gateway's deep-research bundle and its contract test)
and [0899](planned/0899_npm_relock_and_kit_floors_after_the_kit_publishes.md) (publish the FINAL kit
tarballs, relock the npm apps, raise the app-server floor). [0900](completed/0900_chat_turn_latency_regression_in_switch_v3.md)
(latency regression) is CLOSED: root cause and fix recorded by REVIEW/16, verified by the E2E pass.

Release follow-ups (after the 2026-09-24 waves; see [Release Trace](#release-trace)):

1. Owner actions and decision gates: sign and notarize the Mac installer
   ([0868](planned/0868_sign_and_notarize_the_mac_installer.md)); rotate the leaked agora keys
   ([0851](planned/0851_rotate_agora_keys_leaked_in_sibling_repo_histories.md)); rule on the Apple
   text tiers ([0869](planned/0869_apple_text_tier_boundaries_vs_the_fit_budget.md)) and on the
   gateway roles ([0870](planned/0870_operator_rulings_for_gateway_roles_0862.md)); crates.io
   trusted publishing ([0857](planned/0857_crates_io_trusted_publishing_for_console_crates.md)).
2. Public-surface leaks first: the gateway docs site publishes `docs/backlog/**`
   ([0884](planned/docs-hygiene/0884_gateway_docs_site_excludes_the_backlog.md)); the console ships
   maintainer HTML comments ([0885](planned/docs-hygiene/0885_gateway_console_ships_no_internal_html_comments.md)).
3. Next abstractcore patch: default MLX id ([0874](planned/0874_core_default_mlx_model_id_names_a_missing_repo.md)) and
   llms sources ([0882](planned/docs-hygiene/0882_core_llms_sources_cover_every_user_page.md)) — both
   already committed on local `main`, unreleased — plus the tier ruling (0869).
4. One-click completeness: console TUI release binaries
   ([0876](planned/app-surfaces/0876_gateway_console_tui_release_binaries.md)); the Assistant
   sign-in handover is done ([0875](completed/0875_assistant_one_time_sign_in_handover.md), 2026-09-26,
   unreleased); the `allow_engine_install` switch the UI already points at
   ([0858](planned/0858_console_toggle_for_allow_engine_install.md)), Linux `evdev`
   ([0881](planned/app-surfaces/0881_assistant_linux_input_dependency_with_wheels.md)), compiled
   packages out of the default extras ([0861](planned/0861_compiled_packages_out_of_the_default_extras.md)).
5. Release tooling: planner scratch discovery ([0871](planned/0871_release_planner_must_skip_scratch_trees.md)),
   ADR-0034 order ([0860](planned/0860_adr_0034_release_order_from_the_inventory_tiers.md)), test
   isolation for the remaining packages ([0849](planned/0849_test_suites_must_not_reach_the_operators_live_stack.md)),
   backlog normalization ([0889](planned/0889_normalize_the_legacy_root_backlog.md)).
6. Wave 2026-09-25/26 (missions; completed records 0906–0915): release steps 0890 and 0899 (above);
   security follow-up [0892](proposed/0892_gateway_tool_deny_list_gaps_and_launch_folder_trust_for_non_admins.md)
   (two of its three gaps closed 2026-09-26; still open: shell confinement 0232, `.netrc`/`.docker`,
   operator ruling on launch-folder trust for remote non-admins); operator gate
   [0904](proposed/0904_refresh_the_audit_only_seat_missions.md) (stale "AUDIT ONLY" seat texts); a
   review of the gateway commits after REVIEW/19 (`3d3eac3` … `288f29f`) is not on disk (see 0915);
   the rest are proposed (0891, 0893–0898, 0901–0903, 0905). Evidence: `untracked/missions-2026-09-25/`.

Longer-running architecture work (unchanged since before the waves):

1. Finish the second wave of the Core/Runtime route substrate: direct Core, local Runtime, remote Runtime, and Core server must consume the same resolved-route semantics and denial rules.
2. Lock the Gateway action-descriptor contract over the implemented Core `request/output` and Runtime `resolved_actions` substrate instead of letting clients keep private capability taxonomies.
3. Formalize the replayable Gateway session/action envelope on top of Runtime `history_bundle` and `resolved_actions` so capability-aware runs stay explainable across lightweight apps.
4. Align Gateway-first apps and Flow authoring on the same durable action/replay handoff instead of app-local multimodal routers, semantic caches, or transport-specific heuristics.
5. Close current coverage gaps such as `generate_sound` and define the extension rules for future modalities like `scene3d`, characters, and environments, while keeping workflows as the product layer and AbstractCore as the lighter non-durable entrypoint.

## Active Planned Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0851 | [Rotate agora API keys leaked in sibling repo histories](planned/0851_rotate_agora_keys_leaked_in_sibling_repo_histories.md) | Planned (operator decision gate) | Seven sibling repos pushed `.cursor/mcp.json` with agora keys; rotate them and decide per repo on history rewrite. High priority. |
| 0850 | [Redesign the unresolvable `abstractcore[all]` extra](planned/0850_abstractcore_all_extra_is_unresolvable.md) | Planned (not started; still open in abstractcore 2.15.1) | MLX (transformers>=5, llguidance>=1.7) and vLLM <=0.19 (transformers<5) cannot share one extra; vLLM 0.30 needs openai>=2.25 vs the `openai<2` pin. Root profiles unaffected. |
| 0852 | [Harmonize install-profile extras on `apple` / `gpu`](planned/0852_harmonize_install_profile_extras_naming.md) | Planned (not started; the 0.2.0 wave kept the existing extras) | After 0.1.12: rename `all-apple`/`all-gpu` to `apple`/`gpu` in core, voice, vision, music, memory, 3d with one-release aliases; dependents and root move in the same wave. |
| 0856 | [Validate the Windows bootstrap and gateway service on real machines](planned/0856_validate_windows_bootstrap_on_real_machines.md) | Planned (not started; 0.3.x changed `install.ps1` with read review only) | `install.ps1` has CI (`windows-latest`, `-NoService`) and container parse/dry-run evidence only; validate PS 5.1/7 on Windows 10 22H2 and 11 (x64/ARM64), the Startup service entry, winget installs, NTFS token permissions. |
| 0857 | [crates.io trusted publishing for the console crates](planned/0857_crates_io_trusted_publishing_for_console_crates.md) | Planned (still open: 0.8.0 token-published 2026-09-24) | `abstractcore-console` 0.2.0 and `abstractgateway-console` 0.7.0 / 0.8.0 were published with a local token; configure OIDC trusted publishing in both release workflows. |
| 0858 | [Console toggle for `allow_engine_install`](planned/0858_console_toggle_for_allow_engine_install.md) | Planned (still open in gateway 0.4.2) | Only `POST /admin/runtime-config` changes it, yet console and network texts already point users at "Settings → allow_engine_install"; add the audited admin switch in the web and terminal consoles. |
| 0859 | [Launcher port defaults match the stack map](planned/0859_launcher_port_defaults_match_the_stack_map.md) | Planned | `apps_common.sh` / `gateway-flow*.sh` defaults differ from the stack map the gateway adopted in 0.4.1; `local_pythonpath` is stale; then retire the gateway's legacy probe ports 3000/3007. |
| 0860 | [ADR-0034: release order from the inventory tiers](planned/0860_adr_0034_release_order_from_the_inventory_tiers.md) | Planned | The ADR's hand-written order is stale (core and runtime in one tier; the 2026-09-24 patch wave had to run core → runtime → gateway → root); `scripts/lib/packages.txt` + `deps.sh` are authoritative. |
| 0861 | [Compiled packages out of the default `all-apple` / `all-gpu` extras](planned/0861_compiled_packages_out_of_the_default_extras.md) | Planned | `llama-cpp-python`, `stable-diffusion-cpp-python`, `aec-audio-processing` are source-only on PyPI; the pip route needs a compiler until they become opt-in (later wave, owner decision 2026-09-24). |
| 0848 | [Supervisor must not blame model inference for a blocked gateway](planned/0848_supervisor_must_not_blame_inference_for_a_blocked_gateway.md) | Planned (not started) | The unhealthy banner asserts a cause it cannot observe; it was wrong 4/4 on 2026-09-17 (the cause was a workflow publish rebuilding the host on the event loop). Point at `runtime/audit_log.jsonl` and the ledgers. |
| 0849 | [Test suites must not reach the operator's live stack](planned/0849_test_suites_must_not_reach_the_operators_live_stack.md) | Planned (abstractassistant, abstractcore, abstractgateway guarded; runtime, agent and the rest open) | An assistant GUI test republished the live gateway's managed workflow twice, costing two ~60 s stalls. Core and gateway slice done 2026-09-24 ([0866](completed/0866_test_isolation_in_abstractcore_and_abstractgateway.md)); audit the remaining packages. |
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
| 0201-0207,0209-0210 | [Multimodal capability projection and workflow-callability track](planned/multimodal-capability-projection/README.md) | In progress | The first Core/Runtime substrate wave is landed: Core `request=` + resolved-route metadata and Runtime `resolved_actions` export. Gateway descriptors, replay envelopes, and client adoption still remain. |
| 0212-0222 | [Agency parity track (Codex-0.89 gaps)](planned/agency-parity/README.md) | In progress | Implemented + tested: 0212 (prefix-cache stability), 0213 (context fidelity/thought retention), 0214 (parallel read-only tools), 0216 (edit_file safety + CRLF/dash-line follow-ups), 0217 (verifier + update_plan + inject_guidance + default RetryPolicy), 039 (arg coercion + PEP-563 schema-type fix), 0215 engine + generalized output offload, 0220 (persistent-shell tools — opt-in, approval-gated, live-verified on OVH gpt-oss-120b). LIVE evidence recorded 2026-07-08 (track README "Live evidence"): prefix stability 12/12 + OpenAI cached_tokens 60.9%, thought retention, 2.09× parallel tools, verifier live catch, edit_file traps 3/3. Remaining: 0218 (design-first context-budget survival), 0219 (retrieval/project memory — owned elsewhere), unified prompt-caching strategy (0221). ADR-0026 binding: no lossy truncation in the loop. |
| 0232 | [Sandbox `execute_command` and fix workspace path containment](planned/0232_execute_command_sandboxing_and_workspace_path_containment.md) | Planned | P0 security. `execute_command` is raw `sh -c` with the full inherited environment and no filesystem containment, so a `write_file` refused by `workspace_only` succeeds via shell heredoc (observed live 2026-07-30); `~/.abstractcode/gateway.json` and `~/.codex/auth.json` are readable, subsuming the `fetch_url` approval gate. Path containment is string-based, so case-variant and Unicode-NFD denylist bypasses work on APFS and `workspace_allowed_paths` pointing at the workspaces base exposes 1,746 sibling workspaces. Proposes fail-loud workspace clamping, identity-based (`st_dev`,`st_ino`) containment with `openat`+`O_NOFOLLOW`, per-invocation OS sandbox (sandbox-exec/bubblewrap) with container fallback, environment scrubbing, and approval tiering that forbids auto-approving `execute_command` while unsandboxed. |
| 0868 | [Sign and notarize the Mac installer](planned/0868_sign_and_notarize_the_mac_installer.md) | Planned (owner action: Developer ID) | The `.pkg` on releases v0.3.0/v0.3.1 is unsigned; sign, notarize, staple, replace the asset, then update the nine doc places that teach **Open Anyway**. |
| 0869 | [Apple text tier boundaries vs the fit budget](planned/0869_apple_text_tier_boundaries_vs_the_fit_budget.md) | Planned (operator decision gate) | Flash-Next on stock 128 GiB Macs and 27B on 24 GiB Macs fail the fit check they ship with; rule on the boundaries (9B below 32 GiB proposed). |
| 0870 | [Operator rulings for gateway roles (0862)](planned/0870_operator_rulings_for_gateway_roles_0862.md) | Planned (operator decision gate) | Viewer role? Members configure their own entities? Require or prompt for a member account off localhost? |
| 0871 | [Release planner must skip scratch trees](planned/0871_release_planner_must_skip_scratch_trees.md) | Planned | `abstract_release_plan.py` walks `untracked/`, worktrees and runtime workspaces; scratch package copies can pollute a plan. |
| 0872 | [Runtime `MODELS_ENGINES_MIN_ABSTRACTCORE` floor](planned/0872_runtime_models_engines_floor_matches_the_cancel_signature.md) | Planned | Constant says 2.14.0; the 0.4.34 cancel signature needs 2.15.1 (pyproject floor already 2.15.1). |
| 0873 | [Root launchers stop exporting legacy backlog env](planned/0873_root_launchers_stop_exporting_legacy_backlog_env.md) | Planned | `ABSTRACTGATEWAY_TRIAGE_REPO_ROOT` / `BACKLOG_EXEC_RUNNER` are stored settings since gateway 0.4.1; Continuum labels the exports "environment (legacy)". |
| 0874 | [Core default MLX model id names a missing repo](planned/0874_core_default_mlx_model_id_names_a_missing_repo.md) | Planned (fix committed on local core `main`, unreleased) | `mlx-community/Qwen3-4B` does not exist; `…-4bit` does. |
| 0889 | [Normalize the legacy root backlog](planned/0889_normalize_the_legacy_root_backlog.md) | Planned | 24 stale planned copies of completed items, 231 non-`NNNN_` filenames, reused IDs; blocks reliable counts. |
| 0890 | [Wire bundled-flow interface pins, then rebuild the gateway bundles](planned/0890_wire_bundled_flow_interface_pins_and_rebuild_gateway_bundles.md) | Planned (release step; still open 2026-09-26: `KNOWN_GAPS` non-empty) | entity-chat/goodbye `success`/`meta`, multiagent-coding `passed` read as null; gateway `deep-research@0.1.7` predates the `prompt`/`success` wiring and its contract test pins the old outputs. |
| 0899 | [npm relock and kit floors after the kit publishes](planned/0899_npm_relock_and_kit_floors_after_the_kit_publishes.md) | Planned (release step) | Code web lock pins ui-kit 0.1.10 / panel-chat 0.1.16 vs `^0.1.12` / `^0.1.17` (`npm ci` fails); observer/entity/continuum to `app-server ^0.1.10`; grep-prove the published builds. Crates.io stays 0857. |
| 0876-0881 | [App surfaces track](planned/app-surfaces/README.md) | Planned | Seams between the gateway's apps manager and each app (console TUI binaries, Continuum flags/seat/dev port, Entity dead variable, Linux `evdev`). 0875 completed 2026-09-26. |
| 0882-0888 | [Docs hygiene track](planned/docs-hygiene/README.md) | Planned | Code-vs-docs conflicts and publishing gaps from the 2026-09-25 coredoc pass. |

## App Surfaces Planned Track

Track README: [planned/app-surfaces/README.md](planned/app-surfaces/README.md). 0875 moved to
[completed](completed/0875_assistant_one_time_sign_in_handover.md) on 2026-09-26.

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0876 | [Gateway console TUI release binaries](planned/app-surfaces/0876_gateway_console_tui_release_binaries.md) | Planned | crates.io only today; add binaries + `SHA256SUMS` like abstractcode so the console installs it in one click. |
| 0877 | [Continuum server settings as launch flags](planned/app-surfaces/0877_continuum_server_settings_as_launch_flags.md) | Planned | Env-only configuration; `--help` incomplete. |
| 0878 | [Continuum hub seat default is a personal name](planned/app-surfaces/0878_continuum_hub_seat_default_is_a_personal_name.md) | Planned | Default seat `laurent`. |
| 0879 | [App dev ports match the stack map](planned/app-surfaces/0879_app_dev_ports_match_the_stack_map.md) | Planned | Continuum dev on 3003 (Code's port, `--strictPort`), Entity dev on 3007. |
| 0880 | [Entity `ABSTRACTENTITY_OBSERVER_URL` is dead](planned/app-surfaces/0880_entity_observer_url_is_a_dead_variable.md) | Planned | Injected by the server and root launchers, read by nothing. |
| 0881 | [Assistant Linux input dependency with wheels](planned/app-surfaces/0881_assistant_linux_input_dependency_with_wheels.md) | Planned | `pynput` → `evdev` sdist on Linux; pre-existing gap in the root install matrix. |

## Docs Hygiene Planned Track

Track README: [planned/docs-hygiene/README.md](planned/docs-hygiene/README.md).

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0882 | [Core llms sources cover every user page](planned/docs-hygiene/0882_core_llms_sources_cover_every_user_page.md) | Planned (fix committed on local core `main`, unreleased) | 20 user pages were missing from `llms-full.txt` at 2.15.1. |
| 0883 | [Root llms-full generator file list](planned/docs-hygiene/0883_root_llms_full_generator_file_list.md) | Planned | Lacks troubleshooting, inlines 35 backlog/research files, no `--check`. |
| 0884 | [Gateway docs site excludes the backlog](planned/docs-hygiene/0884_gateway_docs_site_excludes_the_backlog.md) | Planned | `mkdocs.yml` has no `exclude_docs`; `docs/backlog/**` is public. |
| 0885 | [Gateway console ships no internal HTML comments](planned/docs-hygiene/0885_gateway_console_ships_no_internal_html_comments.md) | Planned | 35 comments in served console markup, some maintainer history. |
| 0886 | [Docs sites redeploy on main](planned/docs-hygiene/0886_docs_sites_redeploy_on_main.md) | Planned | Core site stale since 2026-05-27 (no deploy job); runtime/gateway deploy on tags only. |
| 0887 | [CHANGELOG histories without maintainer narrative](planned/docs-hygiene/0887_changelog_histories_without_maintainer_narrative.md) | Planned | ui-kit 0.1.9 history and Entity pre-release CHANGELOG. |
| 0888 | [Runtime ROADMAP is stale](planned/docs-hygiene/0888_runtime_roadmap_is_stale.md) | Planned | Says v0.4.2; dead backlog link. |

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

## Multimodal Capability Projection Planned Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0210 | [Core request/output contract and Gateway projection alignment](planned/multimodal-capability-projection/0210_core_request_output_contract_and_gateway_projection_alignment.md) | In progress | First-wave Core `request=` support, Core resolved-route metadata, reasoning-capable route defaults, and Runtime resolved-action export are landed; Gateway projection work remains. |
| 0201 | [Gateway action descriptor contract](planned/multimodal-capability-projection/0201_gateway_action_descriptor_contract.md) | Planned | Create the versioned Gateway-owned typed action contract and lock the durable boundary between Gateway actions, Core lower-level request/output semantics, tools, workflows, and canonical Runtime intent. |
| 0202 | [Gateway replayable session and action envelope](planned/multimodal-capability-projection/0202_gateway_replayable_session_and_action_envelope.md) | In progress | Runtime now exports `resolved_actions`; Gateway still needs to project the full portable decision/session envelope over that substrate. |
| 0207 | [Cross-client replayable action handoff](planned/multimodal-capability-projection/0207_cross_client_replayable_action_handoff.md) | Planned | Align live and replay consumers on the same bounded action handoff instead of forcing each lightweight app to reconstruct capability decisions locally. |
| 0203 | [Flow action descriptor alignment](planned/multimodal-capability-projection/0203_flow_action_descriptor_alignment.md) | Planned | Keep typed Flow media nodes but source availability, preflight, and task metadata from the shared action contract. |
| 0204 | [Runtime capability intent resolution and policy](planned/multimodal-capability-projection/0204_runtime_capability_intent_resolution_and_policy.md) | In progress | Runtime now derives and exports bounded resolved-action records from Core route metadata; broader action-policy and Gateway-fed action resolution remain. |
| 0205 | [Multimodal action coverage and future modality extension](planned/multimodal-capability-projection/0205_multimodal_action_coverage_and_future_modality_extension.md) | Planned | Close coverage gaps such as `generate_sound`, define route-backed truth rules like `voice_clone`, and set the extension rule for `scene3d` and later families. |
| 0209 | [Super-agent workflow-first adoption over the shared action/route substrate](planned/multimodal-capability-projection/0209_super_agent_workflow_adoption_over_shared_action_route_contract.md) | Planned | Align specialized orchestrator workflows with the shared action/route substrate while keeping `basic-agent` a simple baseline and avoiding private workflow-local routing logic. |

## Agency Parity Planned Track

Close flagship ReAct agent-loop gaps vs a Codex-CLI-0.89-class harness (quality + speed). ADR-0026 is
binding: no lossy truncation inside the loop. Source analysis:
`fable-opinions/agency_deep_dive_and_codex_comparison.md`.

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0212 | [ReAct prompt-prefix cache stability](planned/agency-parity/0212_react_prompt_prefix_cache_stability.md) | Done (tested) | Iteration/scratchpad/grounding moved out of the cached prefix; caching default-on. A/B: system prompt byte-stable across iterations (was growing). |
| 0213 | [ReAct context fidelity + thought retention](planned/agency-parity/0213_react_context_fidelity_thought_retention_dedup.md) | Done (tested) | Reasoning kept in the transcript; scratchpad no longer double-carried into the system prompt; ADR-0026 tags added. |
| 0214 | [Parallel read-only tool execution](planned/agency-parity/0214_parallel_readonly_tool_execution.md) | Done (tested) | Concurrent read-only batches (bounded pool), side-effects strictly sequential/ordered; timing proof. |
| 0215 | [Persistent exec session + output offload](planned/agency-parity/0215_persistent_exec_session_and_output_offload.md) | Done (engine + offload) | PTY shell engine (cwd/env/stdin/exit-code, hardened) + generalized output offload: stdout+stderr on any exit code, any tool's large string output, 50 MB retention cap, explicit >cap push-back notice (never silent). Tool exposure split to 0220. |
| 0216 | [edit_file safety + patch robustness](planned/agency-parity/0216_edit_file_safety_and_patch_robustness.md) | Done (tested) | Default single replacement + ambiguity fail; context-anchored diff; JSON/YAML parse-refuse. 33 tests. Follow-ups resolved 2026-07-08: CRLF preservation (dominant-style restore, mixed-endings note) + `-- `-deletion-line diff parse. +12 tests. |
| 0217 | [ReAct verifier/plan/steering/retry](planned/agency-parity/0217_react_verifier_plan_steering_and_retry.md) | Done (tested) | CodeAct verifier + update_plan wired into ReAct; gateway inject_guidance command; default RetryPolicy (llm=3, tools=1). |
| 0218 | [Interactive context-budget survival](planned/agency-parity/0218_interactive_context_budget_survival.md) | Planned (design-first) | num_ctx + typed overflow + eviction-to-artifact before any lossy summarization. |
| 0219 | [ReAct retrieval + project memory](planned/agency-parity/0219_react_retrieval_and_project_memory.md) | Planned (record only) | abstractmemory-backed recall + AGENTS.md loading; owned elsewhere. |
| 0220 | [Persistent shell tool exposure](planned/agency-parity/0220_persistent_shell_tool_exposure.md) | Done (tested + live) | `shell_exec`/`shell_write_stdin`/`shell_close`: opt-in (`ABSTRACT_ENABLE_SHELL_TOOLS`), approval-gated, run-id namespaced, terminal-hook teardown incl. cancel, non-durable with explicit new-session notice. 14 tests + live OVH gpt-oss-120b venv proof; A/B showed the one-shot arm silently polluting the wrong environment. |
| 0222 | [Mid-loop steering + soft interrupt](planned/agency-parity/0222_mid_loop_steering_and_soft_interrupt.md) | Design converged (TOP priority) | Type into a running loop + redirect/stop without cancel. 2 adversarial reviews folded (single-writer sidecar + vars watermark + in-loop drain hook + tree fan-out + wait semantics); Codex 1:1 verified; 21 required tests listed; hot-file handshake posted to runtime/gateway (commons 82). |
| 0221 | [Unified prompt-caching strategy](planned/agency-parity/0221_unified_prompt_caching_strategy.md) | Wave 1 done (live-verified) | Anthropic top-level cache_control was an ACTIVE cost increase (full-prompt write premium every call, zero reads — live-falsified); now an explicit breakpoint on the system head (write→read verified) + normalized `cached_input_tokens`/`cache_write_tokens` across Anthropic/OpenAI/compatible. Mechanism = provider class; registry = tuning values; endpoint quirks = profiles. Waves 2-3 planned. |
| 039 | [Tool argument type coercion](planned/039_tool_argument_type_coercion.md) | Done (tested) | Centralized schema-aware coercion at dispatch + PEP-563 schema-type inference fix. Both registry and runtime paths share it. |

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
| 0206 | [Micro-model gating and hierarchical multimodal planning](proposed/0206_micro_model_gating_and_hierarchical_multimodal_planning.md) | Proposed | Preserve the idea of deterministic pre-gates plus cheap classifiers and richer coordinators, but defer it until the shared action/policy contract is real enough to support stable gating inputs. |
| 0208 | [AbstractCore lightweight capability surface boundary](proposed/0208_abstractcore_lightweight_capability_surface_boundary.md) | Proposed | Preserve the Gateway/Core entrypoint split by keeping Gateway actions durable/high-level and only promoting a narrower Core-side discovery contract if direct Core demand proves it is needed. |
| 0211 | [Public generate route override surface](proposed/0211_public_generate_route_override_surface.md) | Proposed | Keep structured temporary route overrides deferred until the internal resolved-route contract, topology parity, and Gateway policy ceilings are stable; if promoted later, prefer a separate advanced override surface over nesting route objects inside `request` or `output`. |
| 0230 | [Spatial memory: rooms and objects as entity recall anchors](proposed/0230_spatial_memory_rooms_for_entities.md) | Proposed | Maintainer proposal (team vote): give each summoned entity an inhabitable space it can populate with valued objects/texts/sounds; wandering/passing objects becomes a place/object recall channel (like the participants channel), fighting inward loops and giving human-like rootedness. Layer 1 = object-anchor graph channel (2D/no 3D); later layers use meshvault/abstract3d/abstractvision/abstractmusic. Non-goal: anchors never become authoritative memory or identity. |
| 0891 | [Flow: runtime-resolved handles as pins](proposed/0891_flow_runtime_resolved_handles_as_pins.md) | Proposed (pointer) | Root pointer to abstractflow `docs/backlog/proposed/0157`; 336 undrawable edges in 24 flows; "N hidden" badge is the interim. |
| 0892 | [Gateway tool deny list gaps; launch-folder trust for remote non-admins](proposed/0892_gateway_tool_deny_list_gaps_and_launch_folder_trust_for_non_admins.md) | Proposed (operator ruling needed) | Snapshot and schedule gaps closed 2026-09-26 (prefix rule, one guard `288f29f`); still open: shell not confined (0232), `.netrc`/`.docker`, trust default on for non-admins (REVIEW/09 B2). |
| 0893 | [Same-machine locality behind a reverse proxy](proposed/0893_same_machine_locality_behind_a_reverse_proxy.md) | Proposed | App-proxied requests are never local in trust-proxy mode; TUI treats a same-host LAN URL as remote until the first run; add a pre-run verdict route. |
| 0894 | [Migrate Flow and Code web proxies onto app-server](proposed/0894_migrate_flow_and_code_web_proxies_onto_app_server.md) | Proposed | Needs WebSocket proxying, pre-login token check, status shape in app-server; Flow vite dev proxy lacks the forwarding headers. Realises 0155's trigger. |
| 0895 | [MLX idle/TTL unload](proposed/0895_mlx_idle_ttl_unload.md) | Proposed (operator decision) | `ttl_s`/`keep_alive` now reported unsupported; no unloader exists. |
| 0896 | [Verify MTP drafter eject](proposed/0896_verify_mtp_drafter_eject_on_a_host_with_the_companion.md) | Proposed | Companion `mlx-community/Qwen3.8-27B-MTP-4bit` not cached on this host; eject with a loaded drafter unmeasured. |
| 0897 | [Standalone Local LLM clients register residency claims](proposed/0897_standalone_local_llm_clients_register_residency_claims.md) | Proposed | Only `MultiLocalAbstractCoreLLMClient` registers; another client's switch can eject a standalone client's model. |
| 0898 | [Token streaming: paths that still do not stream](proposed/0898_token_streaming_gaps_after_the_first_wave.md) | Proposed | Remote core, entity chat, entity own-time loop, `usage_unavailable` servers, raw-text servers with prompt-opened thinking; the ```json and MLX telemetry fixes are committed (status note 2026-09-26). |
| 0901 | [Code web: delete the legacy `src/ui/app.tsx`](proposed/0901_code_web_delete_the_legacy_ui_app.md) | Proposed | 6,382 dead lines plus helpers only it uses; entry renders `workspace/app`. |
| 0902 | [abstractskill pin history, wheel test, refresh pin](proposed/0902_abstractskill_bundle_pin_history_wheel_test_and_refresh_pin.md) | Proposed | Digest can change without a version bump; no wheel-content CI check; `entity-self-knowledge` pin stale. |
| 0903 | [Identity sync check in the release checklist](proposed/0903_identity_sync_check_in_the_release_checklist.md) | Proposed | `scripts/check_identity_sync.py` is monorepo-only and run by no CI; make it a recurrent release gate. |
| 0904 | [Refresh the "AUDIT ONLY" seat missions](proposed/0904_refresh_the_audit_only_seat_missions.md) | Proposed (operator decision gate) | Nine CLAUDE.md seat texts contradict the implementation work every agent was given. |
| 0905 | [AbstractCore public docstrings carry session history](proposed/0905_core_public_docstrings_carry_session_history.md) | Proposed | ~63 `help()`-visible docstrings still cite thread ids and "operator directive" wording (REVIEW/22 a′); mission names/dates already removed (`a0f0377`). |
| 0862 | [Gateway roles: admin, member (and maybe viewer), with admin-authorised choices](proposed/0862_gateway_roles_members_and_admin_authorised_choices.md) | Proposed (operator decisions pending: gate [0870](planned/0870_operator_rulings_for_gateway_roles_0862.md)) | Named roles and a gateway-wide provider/model allow/deny list that members choose within; clamp member `tool_policy` and workspace self-service; per-role route contract test; prompt for a daily-use member account when network mode leaves localhost (not at first run); member invite links. The two authorization defects it recorded (token-only session login; `PROTECT_READ=0` reads as admin) are fixed in gateway 0.4.1. |

## Runtime Artifact Observability Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0195 | [Observer wait handling via session replay and chat handoff](proposed/runtime-artifact-observability/0195_observer_wait_replay_chat_session_handoff.md) | Proposed | Investigate whether waiting runs should be answered through a replayable session/chat context rather than a narrow modal. |
| 0196 | [Observer session-turn-runtime hierarchy](proposed/runtime-artifact-observability/0196_observer_session_turn_runtime_hierarchy.md) | Proposed | Investigate a first-class Session -> Turn -> Run/Subrun -> Artifact/Log hierarchy for Runtime Activity and artifact/log navigation. |

## Installer And Setup Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0162 | [Signed installer CI and distribution](proposed/installers/0162_signed_installer_ci_and_distribution.md) | Proposed (macOS `.pkg` signing promoted as 0868; superseded by ADR-0038 for the bootstrap; still relevant to signed native apps only) | Move from prototype builds to signed/notarized native installer artifacts with checksums and rollback/support logs. |
| 0163 | [CPU local inference install profile](proposed/installers/0163_cpu_local_inference_install_profile.md) | Proposed | Evaluate `abstractframework[cpu]` separately from Light; require package-by-package backend and dependency evidence before promotion. |

## Multimodal Capabilities Completed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0175 | [Multimodal capability taxonomy and schema](completed/multimodal-capabilities/0175_multimodal_capability_taxonomy_schema.md) | Completed | Added route-keyed `capability_routes`, JSON Schema validation, Core helper APIs, route-aware `/v1/models`, Runtime forwarding, Gateway Console route filters, and `input.music` default-route support; media-policy helper migration remains a follow-up. |

## Multimodal Capabilities Proposed Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0176 | [Multimodal model acquisition guidance](proposed/multimodal-capabilities/0176_multimodal_model_acquisition_guidance.md) | Proposed | Explore CLI/doctor and later console guidance for downloading/loading configured local models without conflating acquisition with defaults. |

## Release Trace

Released on 2026-09-24 (two waves) and verified again on 2026-09-25 by the backlog trace (PyPI,
npm, crates.io APIs; GitHub releases). Record: [0867](completed/0867_release_waves_2026_09_24_and_coredoc_pass.md).

| Package | Version(s) | Tag → commit | Registry |
|---|---|---|---|
| abstractcore | 2.15.0, 2.15.1 | `v2.15.0` → `12528d3`, `v2.15.1` → `e91fe9b` | PyPI; GHCR `abstractcore-server:2.15.0` / `:2.15.1` |
| AbstractRuntime | 0.4.34 | `v0.4.34` → `a2e0e94` | PyPI (workflow_dispatch from `main`) |
| abstractgateway | 0.4.1, 0.4.2 (`v0.4.0` tag has no artifacts) | `v0.4.1` → `1075cde`, `v0.4.2` → `4b08b95` | PyPI; GHCR `abstractgateway:0.4.2` / `:latest` / `:0.4.2-gpu` |
| abstractgateway-console (crate) | 0.8.0 | — | crates.io (local token; 0857) |
| @abstractframework/ui-kit | 0.1.11 | `v0.1.11` → `ccd9184` | npm |
| @abstractframework/continuum | 0.3.0 | `v0.3.0` → `8e89b8c` | npm (CI, provenance) |
| @abstractframework/entity | 0.2.0 | `v0.2.0` → `d8ea226` | npm (CI, provenance) |
| abstractframework (root) | 0.3.0, 0.3.1 | `v0.3.0` → `0565c43`, `v0.3.1` → `cb29dda` | PyPI; GitHub releases with `AbstractFramework-Installer.pkg` (unsigned; 0868) |

Root 0.3.1 pins abstractcore 2.15.1, abstractgateway 0.4.2, AbstractRuntime 0.4.34. Docs pass
2026-09-25 (docs-only `main` commits): runtime `696f386`, core `194c312`, gateway `3312bfe`, root
`cfb4926`, continuum `7bc4616`, entity `f3b5a11`, uic `9a307b3`.

## Staged Release (2026-09-25/26 wave, not published)

Nothing below is tagged, pushed or published. Plan: `untracked/missions-2026-09-25/STAGING.md`
(draft for the operator's personal check; no release without the operator's explicit per-release
go). Proposed order, each step's pins resolving on the previous ones: abstractskill 0.3.0 →
abstractcore 2.16.0 → AbstractRuntime 0.5.0 (workflow_dispatch from `main`) → abstractagent 0.3.14 →
ui-kit 0.1.12 / app-server 0.1.10 / panel-chat 0.1.17 (FINAL tarball sha256 `1e84bbf7…`,
`6586583f…`, `a6411d52…`) → abstractgateway 0.5.0 + console crate → flow 0.3.21 → abstractcode
crate 0.6.0 / web 0.5.0 (after the 0899 relock) → observer / entity / continuum patches →
abstractassistant 0.6.0 → abstractframework 0.4.0. Pre-release steps: 0890, 0899,
`scripts/check_identity_sync.py`, the floors named in STAGING, a yank decision for abstractcore
2.15.3, and rewriting the local unpushed release commits (runtime 0.4.36, gateway 0.4.4, root 0.3.3)
to the proposed versions. Completed records: 0906–0915 (below).

## Recent Completed Work

| ID | Item | Completed | Notes |
|----|------|-----------|-------|
| 0915 | [Adversarial review programme of the 2026-09-25/26 wave](completed/0915_adversarial_review_programme_of_the_2026_09_25_wave.md) | 2026-09-26 | 23 reviews (REVIEW/00–22) + E2E 23/23; the defects that mattered (gateway secrets served, proxied browsers counted local, argv hand-over, shelf corruption, locked models ejected, latency root cause, reverted fixes, silent edge loss). |
| 0914 | [Token streaming end to end](completed/0914_token_streaming_end_to_end.md) | 2026-09-26 | `llm.delta`/`llm.delta_end` on the run stream from runtime to panel-chat, Code web/TUI and Assistant; MLX telemetry parity; thinking-stream root cause (first delta 5.75 s → 0.49 s). Unreleased. |
| 0913 | [Clean model eject across backends and the default-switch leak](completed/0913_clean_model_eject_across_backends_and_default_switch_leak.md) | 2026-09-26 | MLX/HF/GGUF/embeddings eject, switch ejects before the new default loads, lock-aware ejects, memory basis in console/tray; M1 17.6 GB → 3 MB. Unreleased. |
| 0912 | [Code TUI: MTP in `/model`, `/files`, `/about`, gateway default, help](completed/0912_code_tui_mtp_in_model_files_about_gateway_default_help.md) | 2026-09-26 | TUI 763 → 815 tests; truthful `--help` defaults. Unreleased. |
| 0911 | [Assistant: hand-over, overlap fix, window defaults, workflow selector, raw-HTML fix](completed/0911_assistant_handover_overlap_window_defaults_workflow_selector_raw_html.md) | 2026-09-26 | 0600 hand-over file, transcript cross-write fixed, 650/28 defaults, raw HTML off. Closes 0875. Unreleased. |
| 0910 | [Conversation workspace browse/preview, one guard, built-in deny](completed/0910_conversation_workspace_browse_preview_one_guard_and_builtin_deny.md) | 2026-09-26 | Files in Code web and TUI; data folder never served; one guard on every run start (`288f29f`). Unreleased. |
| 0909 | [Default agent workflow](completed/0909_default_agent_workflow_gateway_setting_and_clients.md) | 2026-09-26 | `agents.default_workflow.<interface>`, `@default` resolved on the server, three doors, no client fallback. Unreleased. |
| 0908 | [Framework identity, About screens, forwarded-address rule](completed/0908_framework_identity_about_screens_and_proxy_forwarded_address.md) | 2026-09-26 | One descriptor, About in every app, `gatewayVersionRows`; proxies overwrite `X-Forwarded-For` + app-proxy marker. Unreleased. |
| 0907 | [Skills shipped with abstractskill, seeded by the gateway](completed/0907_skills_shipped_with_abstractskill_and_seeded_by_the_gateway.md) | 2026-09-26 | abstractskill 0.3.0 `seed_registry` (locked, never overwrites operator edits); gateway seeds at start. Unreleased. |
| 0906 | [Flow interface pins, edge preservation, deep-research wiring](completed/0906_flow_interface_pins_edge_preservation_and_deep_research_wiring.md) | 2026-09-26 | Load→save lost 336 edges in 24 flows, now 0; deep-research reads `prompt`. Unreleased. |
| 0900 | [Chat-turn latency regression in switch-v3](completed/0900_chat_turn_latency_regression_in_switch_v3.md) | 2026-09-26 | Moved from `proposed/`. Root cause gateway `0ccbe73` (data folder enumerated into the system prompt); fixed as deny prefixes; E2E prompt byte-identical, 2,989 tokens. |
| 0875 | [Assistant one-time sign-in handover](completed/0875_assistant_one_time_sign_in_handover.md) | 2026-09-26 | Moved from `planned/app-surfaces/`. Desktop hand-over file + loopback-only redeem; record 0911. Unreleased. |
| 0867 | [Release waves of 2026-09-24 and the 2026-09-25 docs pass](completed/0867_release_waves_2026_09_24_and_coredoc_pass.md) | 2026-09-25 | Trace of root 0.3.0 and patch 0.3.1 (versions, tags, registries, incidents) plus the coredoc commits; follow-ups 0868–0888. |
| 0866 | [Test isolation in abstractcore and abstractgateway](completed/0866_test_isolation_in_abstractcore_and_abstractgateway.md) | 2026-09-24 | HOME/HF_HOME per test, socket + subprocess guards, `network`/`real_home` markers; full suites leave the real home untouched. Slice of 0849. |
| 0865 | [Core catalog tiers, MTP companions and offline-first loading](completed/0865_core_catalog_tiers_companions_and_offline_first_loading.md) | 2026-09-24 | abstractcore 2.15.0/2.15.1: Apple memory tiers, companion downloads, `models verify`, no process-wide HF offline writes, cancel attribution. |
| 0864 | [Gateway engines, apps, tray and network settings](completed/0864_gateway_engines_apps_tray_and_network_settings.md) | 2026-09-24 | abstractgateway 0.4.1/0.4.2: engines without a terminal, gateway-managed apps with signed-in open, Network setting, tray control centre, settings instead of env vars. |
| 0863 | [First-run console and one-action Mac installer](completed/0863_first_run_console_and_one_action_mac_installer.md) | 2026-09-24 | Root 0.3.0/0.3.1: `.pkg` + `.command` + uninstaller, full-page setup guide; fresh install 76 s to a signed-in console. |
| 0233 | [Real run cancellation: abort in-flight LLM calls](completed/0233_real_run_cancellation_abort_in_flight_llm_calls.md) | 2026-09-23 | Closed by the 2026-09-25 trace (was still planned): core 2.13.41 `cancel_event`, runtime 0.4.32 cancel reaches the effect, gateway 0.2.30 kill switch; decode stops within one token. |
| 0855 | [One-line install, first-run console and model/engine management](completed/0855_one_line_install_and_model_management_wave.md) | 2026-09-23 | Root 0.2.0: uv-based `install.sh`/`install.ps1` defaulting to gateway 0.3.0 (service + claim link), doctor probes, manifest v2, `CRATE_RELEASE_VERSIONS`, 30-package inventory with `abstractcore-console`, docs; pins core 2.14.0, runtime 0.4.33, gateway 0.3.0. |
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

## Hygiene Findings

Scan of 2026-09-25 (details and fix plan in [0889](planned/0889_normalize_the_legacy_root_backlog.md)):

- 24 filenames exist in both `planned/` and `completed/` (035, 036, 041, 042, 043, 102–120): the
  planned copies are stale.
- 231 item files lack a four-digit `NNNN_` prefix (three-digit legacy names, hub-era
  `NNN-<package>-…` names, `2026-05-08_*` date prefixes in `proposed/` and `completed/`).
- Reused IDs, e.g. `001`–`018` (legacy and hub-era), `0212`–`0214` (`planned/agency-parity/` and
  `proposed/`).
- `planned/agency-parity/` holds items marked "Done (tested)" without completion moves.
- `scripts/gen_llms_full.py` inlines this overview and ~30 backlog items into the root
  `llms-full.txt`, which therefore goes stale on every backlog edit (0883); it was not regenerated
  by this trace (docs outside `docs/backlog/` are out of its scope).
- ADR candidates flagged, not written: "no environment-variable instructions in user-facing text;
  every setting has web, terminal and CLI doors" (applied across gateway 0.4.1, see 0864).

Scan of 2026-09-26 (after 0906–0915):

- Every file created or moved on 2026-09-26 (0890–0915, 0875, 0900) has a unique four-digit `NNNN_`
  prefix and no date; no four-digit ID is reused; no new file appears in two lifecycle folders. The
  legacy violations above are unchanged (0889).
- Backlog behind the code: the 2026-09-25 patch wave (root `v0.3.2` / local 0.3.3, abstractcore
  `v2.15.2` / `v2.15.3`, AbstractRuntime `v0.4.35`, gateway 0.4.3 images) has no release record, and
  planned items look fixed by it without being closed: 0874 (core `cb2c160`, in `v2.15.2`), 0872 and
  0888 (runtime `fc2a27d`, in `v0.4.35`; the constant is now 2.15.3), 0884 (gateway `c197b86`
  `exclude_docs: backlog/`, on `main`, not yet deployed). Verify against the registries and close
  them in the next release trace; not closed here (outside this wave).

## Planning Notes

- 2026-09-25 post-release trace: closed 0233 (shipped 2026-09-23, never moved); recorded 0863–0867
  for the 2026-09-24 waves; created 0868–0889 (two topic tracks: app-surfaces, docs-hygiene);
  refreshed 0849, 0850, 0855, 0856, 0857, 0858, 0859, 0860, 0861, 0862, 0162 with dated status
  notes; added `recurrent/` with the two minimum process tasks. Counts above replaced the previous
  qualitative placeholders.

- 2026-09-26 follow-up triage of the 2026-09-25/26 mission wave (`untracked/missions-2026-09-25/`:
  PLAN, CONTRACTS, S-DESIGN, track reports, REVIEW/00–15): created 0890–0904 (two planned release
  steps, thirteen proposed). 0894 realises the trigger of 0155 (three copies of the proxy forwarding
  rules); fold 0155 into 0894 when promoting. REVIEW/16 (latency bisect) had not landed; fold it into
  0900. The wave's own completion record is written at release time, not here.

- 2026-09-26 (second pass, after the wave): completed records 0906–0915 written for the ten tracks
  of the 2026-09-25/26 mission wave; 0875 (planned/app-surfaces) and 0900 (proposed) moved to
  `completed/`; status notes appended to 0892 and 0898; counts recounted on disk (0905 included).
  **The release is staged and waits for the operator's go** (Staged Release section); 0890 and 0899
  stay planned as its release steps.

## Operating Notes

- Use `docs/adr/` for durable architecture policy.
- Use this backlog for execution traceability, validation evidence, and follow-up state.
- New backlog item filenames should use `NNNN_<slug>.md`; date-prefixed legacy files should not be copied for new work.
- Run the [recurrent passes](recurrent/README.md) after every release wave; the `abstract-release`
  process expects a backlog trace (release record in `completed/`, follow-ups as items).
