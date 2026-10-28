# 1066 — Every framework environment variable becomes a config setting; the variable stays only as an override

> Package: abstractgateway, abstractcore, abstractruntime (root: install docs)
> Type: task (cross-package)
> Created: 2026-10-28
> Priority: high
> Labels: config, env, settings, console, release-closing
> Links: AbstractGateway `src/abstractgateway/env_registry.py` (env-kill phase 0, operator dm#177/dm#194/dm#201) and
> `tests/test_gateway_env_registry.py` (orphan pin); AbstractCore 0826 (`abstractcore/docs/backlog/proposed/0826_behavior_env_to_config_migration.md`,
> behavior env -> config, vision/voice halves shipped); root [0992](0992_per_user_email_accounts_and_notifications.md) (email env retired), [032](../completed/032_gateway_default_model_from_config.md)
> (gateway default model from config); release-closing QA item (l) (`untracked/release-closing/QA.md`)

## Summary

The gateway, Core and Runtime read **304 environment-variable names** in the `ABSTRACTGATEWAY_*`, `ABSTRACTCORE_*`
and `ABSTRACTRUNTIME_*` prefixes from their source (tests excluded): **188 in abstractgateway** (includes the
`ABSTRACTCORE_*` names the gateway reads itself), **94 in abstractcore**, and **22 in abstractruntime**. Only 33
(gateway), 37 (core) and 5 (runtime) are already covered by a stored setting. The operator's shell on the Mac
exports 4 of these names. Two of them are read by nothing any more. This item makes each variable a natural setting
in the config file its package already owns, so a person sets it in the console, the TUI or `*-config set`. The
environment variable stays only as an override, and every surface that shows the setting says when it is in effect.

## Why

QA (l), 2026-10-28: "propose a remediation so each becomes a natural setting in the gateway/core config files with
the env var only as an override". Earlier rulings point the same way: dm#177 ("REMOVE ALL UNNECESSARY ENV VARIABLES,
THEY MUST ALL BE PROPERLY CONFIGURABLE ON THE GATEWAY/CONSOLE"), dm#194 (console config supersedes everything; a CLI
front door edits the same store), and dm#201 (cloud API keys stay env-inheritable). The gateway registry classifies
every name but migrated only part of them. Core migrated the vision and voice routes. Runtime has no config file at
all: its `RuntimeConfig` (`core/config.py`) holds limits only.

## What the operator's shell exports (names only, 2026-10-28)

| Exported name | Read by | Class | Remediation |
|---|---|---|---|
| `ABSTRACTGATEWAY_AUTH_TOKEN` | gateway `security/gateway_security.py:362` (+ CLI client default) | secret | Keep env or secret file; consoles show presence only. Document the token file (`abstractgateway-config bootstrap-admin`) as the default path. |
| `ABSTRACTGATEWAY_FLOWS_DIR` | gateway `config.py:342` | deployment (bundle dir) | `paths.flows_dir` in `runtime_config.json`; env overrides. |
| `ABSTRACTGATEWAY_MODEL` | **nothing** (only `scripts/lib/af_stack.sh` strips it from child envs) | dead | Remove from the shell. The default model is Core's `abstractcore.json` default (root 032). The boot env scanner should name it as "retired, ignored". |
| `ABSTRACTGATEWAY_PROVIDER` | **nothing** (same) | dead | Same. |

## The rule (to confirm, see Decision)

1. **Setting first.** Every BEHAVIOR or DEPLOYMENT knob has a dotted key in its owner's file:
   - gateway: `<data_dir>/config/runtime_config.json`, through `abstractgateway-config get/set`, the console and the TUI;
   - core: `abstractcore.json`, through `abstractcore --config` and the gateway's Core config page;
   - runtime: a new `RuntimeSettings` filled by the host (the gateway's `runtime.*` section), never a file of its own.
2. **Env is an override, never a silent one.** When set, the variable wins for that process. `get`/`status`, the
   console field and the boot banner show `source: env (ABSTRACTX_Y)` next to the stored value. Today the precedence
   is split, and this item unifies it:
   - Core's `server.*`/`logging.*`: env wins.
   - Core's capability routes: config wins and env is a warned fallback.
   - Gateway rows: stored > env, except `ALLOWED_ORIGINS`.
   - Gateway triage LLM: env > the Core `maintenance` store.
3. **Kept as env only:** secrets (15 gateway, 1 core, 1 runtime internal hand-off) as env or secret file. Bootstrap
   names that locate the config itself also stay env (`ABSTRACTGATEWAY_DATA_DIR`, `ABSTRACTCORE_CONFIG_DIR/FILE`,
   bind host/port, store backend). So do the internal parent-to-child hand-offs (`*_SOURCE`, `ABSTRACTCORE_SERVER_BIND_HOST`,
   `ABSTRACTCORE_SERVER_TOKEN_SOURCE`, `ABSTRACTRUNTIME_ENDPOINT_PROFILE_JSON`). Diagnostic escape hatches also stay
   env (Core: 9, Runtime: 5), but each is listed in `status` when set.
4. **One registry per package**, enforced like the gateway's orphan pin. Core and Runtime gain the same test: a read in
   `src` that is not declared fails CI. Each row carries `superseded_by` (the setting key).

## Defects found while inventorying (fix in this item)

- Gateway `maintenance/backlog_exec_runner.py:1049` reads `ABSTRACTGATEWAY_ENABLE_PROCESS_MANAGER` straight from the
  environment. A process manager enabled in the console still refuses UAT deploys.
- Gateway `BACKLOG_EXECUTOR` defaults to `codex` in settings but to `none` in `BacklogExecRunnerConfig.from_env`
  (`backlog_exec_runner.py:911`).
- Gateway triage reads the unprefixed `ABSTRACT_TRIAGE_*` name first and the `ABSTRACTGATEWAY_TRIAGE_*` name second,
  the inverse of every other family.
- Gateway registry rows with no reader: `ABSTRACTGATEWAY_ALLOW_CLIENT_WORKSPACE_SCOPE`,
  `ABSTRACTGATEWAY_TRUST_CLIENT_WORKSPACE_SCOPE`. Dead code: `runtime_config._workspace_root_payload`.
- Runtime `identity/substrate.py:149-150` still honours `ABSTRACTGATEWAY_ENTITY_CHAT_PROVIDER/MODEL`, which the gateway
  retired in round 3. An entity's mind therefore resolves differently in the runtime CLIs.
- Runtime and gateway both read `ABSTRACTRUNTIME_GLOBAL_MEMORY_RUN_ID`. It needs one source.
- Runtime discovery reads `ABSTRACTCORE_{VOICE,AUDIO,VISION,MUSIC}_BACKEND` and ignores Core's own
  `capabilities_preferred_backends` setting.
- **Release-relevant:** Core `server/app.py:117` `ABSTRACTCORE_DEV_PREFER_SIBLINGS` defaults to **on**. A released
  server prepends `../abstractvision|abstractmusic|abstractvoice` checkouts to `sys.path` when they exist. It should
  default to off for wheels and stay a diagnostic env.

## Scope

### In scope

- Gateway: give every BEHAVIOR row of `env_registry.py` a `runtime_config.json` key and a `superseded_by`. The
  proposed keys are in the mapping table below; they agree with the registry's `console_path` areas. Add the console,
  TUI and CLI fields per area, the effective-source display, and the fixes above.
- Core: add the `abstractcore.json` sections from the table (server, downloads, jobs, generation.repetition,
  fetch_url, transformers, gguf, mlx, vision, embeddings, cli, paths). Add a declared env registry with the orphan
  test, and adopt the one precedence rule.
- Runtime: add `RuntimeSettings` (entity timeouts, limits, grounding fields, discovery timeout, memory global run
  id, code full-access policy, pdf font, prompt cache). The host fills it; env is only an override. Add the registry
  and the orphan test. Drop the `ABSTRACTGATEWAY_ENTITY_CHAT_*` rung.
- Root: `docs/install.md` and `docs/faq.md` say which variables remain (secrets, bootstrap) and that everything else
  is a setting. `scripts/lib/af_stack.sh` keeps stripping the retired names.

### Out of scope

- The `ABSTRACTVOICE_*`, `ABSTRACTVISION_*`, `ABSTRACTMUSIC_*`, `ABSTRACT_TELEGRAM_*` and `AGORA_*` families. Each has
  its owner; list them in that owner's registry.
- Provider API keys (`OPENAI_API_KEY`, ...), which stay env-inheritable per dm#201.

## Decision (operator)

QA (l) says "env var only as an override", meaning env wins when set. dm#194 says "console config supersedes
everything", meaning config wins and env is a fallback. Recommended: **env overrides, shown loudly**. A deployment
(systemd unit, container) must be able to pin a value, and the console must show that it is pinned and by which
variable rather than silently ignore an edit. If the operator keeps dm#194, flip rule 2. Either way it is one rule
for all three packages.

## Acceptance criteria

- [ ] Each package has a declared env registry and an orphan test that goes RED when a new `os.getenv` of the
      package's prefixes is added without a row. Mutation-checked.
- [ ] Every BEHAVIOR row has a setting key. `*-config get <key>` prints value, default, source (`config`/`env`/`default`)
      and, when overridden, the variable's name.
- [ ] The boot banner and `/api/health` list the overriding variables (names only) and the retired ones still
      exported (`ABSTRACTGATEWAY_MODEL`, `ABSTRACTGATEWAY_PROVIDER` on the operator's Mac today).
- [ ] The defects listed above are fixed, each with a test that is red before the fix.
- [ ] `ABSTRACTCORE_DEV_PREFER_SIBLINGS` defaults to off.
- [ ] Root install docs list the remaining env variables (secrets, bootstrap) and nothing else.

## Receipts

- Inventory taken 2026-10-28, read-only, from `main` of abstractgateway, abstractcore and abstractruntime (scratch:
  `untracked/release-closing/w10-env/{gateway,core,runtime}.md`). Each name was verified at its read site; spot checks:
  gateway `backlog_exec_runner.py:1049`, core `server/app.py:117`, runtime `effect_handlers.py:3491`.
- Exported names: `env | grep -o '^ABSTRACT[A-Z_]*'` (names only, no values recorded).

## Mapping table

Columns: name, read at (main site), meaning, default when unset, the setting that already covers it, proposed key.
"CD" = Core `capability_defaults.routes[...]`.

### AbstractGateway (188)

| name | read at | meaning | default when unset | already covered by | proposed config key |
|---|---|---|---|---|---|
| `ABSTRACTCORE_AUTH_TOKEN` | core_config.py:1452 (chain at :1449) | bearer for a remote Core server (4th in chain) | none | — | auth.core_server_token (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTCORE_DISCOVERY_MODEL_TIMEOUT_S` | routes/gateway.py:2449 | 4th name in provider-models timeout chain | 5 s (clamp 1-60) | — | discovery.provider_models_timeout_s (fold into) |
| `ABSTRACTCORE_DISCOVERY_TIMEOUT_S` | routes/gateway.py:2426 | 2nd name for discovery probe timeout | 1.5 s (clamp 0.2-10) | — | discovery.timeout_s (fold into) |
| `ABSTRACTCORE_IMAGE_MAX_BYTES` | routes/gateway.py:13607 | 2nd name for max image bytes | 20 MB (cap 200 MB) | — | limits.image_max_bytes (fold into) |
| `ABSTRACTCORE_PROVIDER_MODELS_TIMEOUT_S` | routes/gateway.py:2447 | 2nd name in provider-models timeout chain | 5 s (clamp 1-60) | — | discovery.provider_models_timeout_s (fold into) |
| `ABSTRACTCORE_SERVER_API_KEY` | core_config.py:1452 (chain at :1450) | bearer for a remote Core server (3rd in chain) | none | — | auth.core_server_token (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTCORE_SERVER_BASE_URL` | core_config.py:1441 (+core_config_migration.py:104, hosts/bundle_host.py:1959, routes/gateway.py:18339) | remote Core server = where the capability/config store lives (split-server) | unset = in-process Core store <data_dir>/config/abstractcore.json | — | server.core_base_url (bootstrap-only: keep env) (locates the config authority) |
| `ABSTRACTCORE_VISION_BACKEND` | routes/gateway.py:2513 (+:18270) | image backend #FALLBACK (3rd) | output.image route, else openai | abstractcore.json capability route output.image (provider) | vision.backend = the route (delete env) |
| `ABSTRACTCORE_VISION_MFLUX_MODEL` | routes/gateway.py:18278 | advertise an mlx-gen image model | none | capability route output.image (model) | vision.model = the route (delete env) |
| `ABSTRACTCORE_VISION_MODEL_ID` | routes/gateway.py:18277 | advertise an image model id | none | capability route output.image (model) | vision.model = the route (delete env) |
| `ABSTRACTCORE_VISION_UPSTREAM_MODEL_ID` | routes/gateway.py:18276 | advertise an openai-compatible image model | none | capability route output.image (model) | vision.model = the route (delete env) |
| `ABSTRACTGATEWAY_ABSTRACTCORE_SERVER_API_KEY` | core_config.py:1452 (chain at :1448; +config_cli.py:94) | bearer to remote Core server (2nd) | none | — | auth.core_server_token (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_ABSTRACTCORE_SERVER_AUTH_TOKEN` | core_config.py:1452 (chain at :1447; +config_cli.py:93) | bearer to remote Core server (1st) | none | — | auth.core_server_token (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_ADMIN_USES_DEFAULT_RUNTIME` | service.py:502 | admin runs in the root data plane, not a per-user one | on | — | auth.admin_uses_default_runtime (restart) |
| `ABSTRACTGATEWAY_AGORA_BRIDGE` | integrations/agora_bridge.py:144 | enable the agora bridge | off | — | agora.enabled (restart) |
| `ABSTRACTGATEWAY_AGORA_FLOOR_SLEEP_S` | integrations/agora_bridge.py:187 | min sleep between polls | 5 | — | agora.floor_sleep_s |
| `ABSTRACTGATEWAY_AGORA_POLL_WAIT_S` | integrations/agora_bridge.py:186 | long-poll wait | 25 | — | agora.poll_wait_s |
| `ABSTRACTGATEWAY_AGORA_RESIDENTS` | integrations/agora_bridge.py:146 | JSON list of residents (alias, mailbox, bundle) | [] (bridge idle) | — | agora.residents |
| `ABSTRACTGATEWAY_AGORA_STATE_PATH` | integrations/agora_bridge.py:181 | bridge cursor/state file | <data_dir>/agora_bridge_state.json | — | paths.agora_state (or drop: derive from data dir) |
| `ABSTRACTGATEWAY_ALLOWED_ORIGINS` | security/gateway_security.py:376 (+network_exposure.py:445) | browser origins allowed (CSV, '*' suffix) | http://localhost:*, http://127.0.0.1:* | runtime_config.json network.allowed_origins (stored origins ADDED; env = start-time override) | security.allowed_origins (exists as network.allowed_origins) |
| `ABSTRACTGATEWAY_APPS_HOST` | runtime_config.py:902 (resolve_apps_setting) | apps bind host (deprecated; loopback only) | 127.0.0.1 | runtime_config.json apps.host | apps.host (exists) |
| `ABSTRACTGATEWAY_APPS_NODE` | runtime_config.py:902 | Node.js for apps: auto|managed|system|path | auto | runtime_config.json apps.node | apps.node (exists) |
| `ABSTRACTGATEWAY_APPS_NPM_REGISTRY` | runtime_config.py:902 | npm registry/mirror | https://registry.npmjs.org | runtime_config.json apps.npm_registry | apps.npm_registry (exists) |
| `ABSTRACTGATEWAY_APPS_PORTS` | runtime_config.py:902 | port/range for apps | '' (app's port, else 3100-3199) | runtime_config.json apps.ports | apps.ports (exists) |
| `ABSTRACTGATEWAY_APPS_PYPI_URL` | runtime_config.py:902 | index for the managed Node.js build | https://pypi.org/pypi | runtime_config.json apps.pypi_url | apps.pypi_url (exists) |
| `ABSTRACTGATEWAY_AUDIT_LOG` | security/gateway_security.py:219 | write the security audit log | = security enabled (on) | — | logging.audit.enabled |
| `ABSTRACTGATEWAY_AUDIT_LOG_HEADERS` | security/gateway_security.py:245 | request headers recorded in audit | x-client-id,x-client-version,x-forwarded-for | — | logging.audit.headers |
| `ABSTRACTGATEWAY_AUDIT_LOG_MAX_BYTES` | security/gateway_security.py:226 | audit file rotate size | 50 MiB | — | logging.audit.max_bytes |
| `ABSTRACTGATEWAY_AUDIT_LOG_ROTATIONS` | security/gateway_security.py:236 | audit files kept | 10 (max 200) | — | logging.audit.rotations |
| `ABSTRACTGATEWAY_AUTH_MODE` | users.py:100 (+first_run.py:189) | user|legacy auth topology when USER_AUTH unset | unset | — | auth.user_auth (merge with USER_AUTH) |
| `ABSTRACTGATEWAY_AUTH_MODE_SOURCE` | first_run.py:135 | why user auth was switched on (loopback_default|network_setting) | unset | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_AUTH_TOKEN` | security/gateway_security.py:362 (+client default in models_engines_cli.py:220, network_exposure.py:2003) | static operator bearer token(s), CSV; CLI client token | none | — | auth.operator_tokens (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_AUTH_TOKENS` | security/gateway_security.py:363 | more operator tokens, CSV | none | — | auth.operator_tokens (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_AUTO_BOOTSTRAP_ADMIN` | cli.py:207 | =0 disables admin auto-create at serve | on | — | auth.bootstrap_admin |
| `ABSTRACTGATEWAY_AUTO_PUBLISH_SHIPPED` | shipped_catalog.py:50 | publish shipped bundles (docs-qa) at boot | on | — | server.auto_publish_shipped |
| `ABSTRACTGATEWAY_BACKLOG_ABSTRACTCODE_MODEL` | maintenance/backlog_exec_runner.py:1427 | model for the abstractcode executor | '' (abstractcode default) | — | backlog.abstractcode.model |
| `ABSTRACTGATEWAY_BACKLOG_ABSTRACTCODE_PROVIDER` | maintenance/backlog_exec_runner.py:1426 | provider for the abstractcode executor | '' | — | backlog.abstractcode.provider |
| `ABSTRACTGATEWAY_BACKLOG_ADVISOR_AGENT` | routes/gateway.py:26003 | bundle the backlog advisor runs | gateway default agent | — | backlog.advisor.agent |
| `ABSTRACTGATEWAY_BACKLOG_ADVISOR_ALLOW_WEB` | routes/gateway.py:25993 | give the advisor web tools | off | — | backlog.advisor.allow_web |
| `ABSTRACTGATEWAY_BACKLOG_AGENT_ALLOWED_PATHS` | routes/gateway.py:25779 | extra paths for backlog agent (lines/JSON) | none | — | backlog.agent.allowed_paths |
| `ABSTRACTGATEWAY_BACKLOG_AGENT_ALLOW_GATEWAY_DATA_DIR` | routes/gateway.py:25771 | add data dir to backlog agent paths | on | — | backlog.agent.allow_data_dir |
| `ABSTRACTGATEWAY_BACKLOG_CLAUDE_BIN` | maintenance/backlog_exec_runner.py:1550 | claude binary | claude | — | backlog.claude.bin |
| `ABSTRACTGATEWAY_BACKLOG_CLAUDE_PERMISSION_MODE` | maintenance/backlog_exec_runner.py:1551 | claude permission mode | '' | — | backlog.claude.permission_mode |
| `ABSTRACTGATEWAY_BACKLOG_CODEX_APPROVALS` | maintenance/backlog_exec_runner.py:930 | codex approvals policy | never | — | backlog.codex.approvals |
| `ABSTRACTGATEWAY_BACKLOG_CODEX_BIN` | maintenance/backlog_exec_runner.py:916 | codex binary | codex | — | backlog.codex.bin |
| `ABSTRACTGATEWAY_BACKLOG_CODEX_MODEL` | maintenance/backlog_exec_runner.py:917 | codex model (may embed effort) | gpt-5.2 | — | backlog.codex.model |
| `ABSTRACTGATEWAY_BACKLOG_CODEX_REASONING_EFFORT` | maintenance/backlog_exec_runner.py:919 | codex reasoning effort | inferred from model spec | — | backlog.codex.reasoning_effort |
| `ABSTRACTGATEWAY_BACKLOG_CODEX_SANDBOX` | maintenance/backlog_exec_runner.py:926 | codex sandbox | workspace-write | — | backlog.codex.sandbox |
| `ABSTRACTGATEWAY_BACKLOG_CURSOR_AGENT_BIN` | maintenance/backlog_exec_runner.py:1555 | cursor-agent binary | cursor-agent | — | backlog.cursor_agent.bin |
| `ABSTRACTGATEWAY_BACKLOG_CURSOR_AGENT_MODEL` | maintenance/backlog_exec_runner.py:1556 | cursor-agent model | '' | — | backlog.cursor_agent.model |
| `ABSTRACTGATEWAY_BACKLOG_EXECUTOR` | runtime_config.py:1031 via _resolve (:1685) (+backlog_exec_runner.py:911) | executor id (codex|claude|cursor-agent|abstractcode) | codex (settings) / none (runner from_env) | runtime_config.json executor | backlog.executor (exists as executor) |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_ALLOWED_MODELS` | routes/gateway.py:24988 | CSV of allowed per-task model overrides | unset = overrides refused | — | backlog.exec.allowed_models |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_MODE` | maintenance/backlog_exec_runner.py:341 | uat | inplace execution | uat | — | backlog.exec.mode |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_NOTIFY` | maintenance/backlog_exec_runner.py:912 | notify (telegram) on exec events | off | — | backlog.exec.notify |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_POLL_S` | maintenance/backlog_exec_runner.py:897 | exec queue poll | 2.0 | — | backlog.exec.poll_s |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER` | runtime_config.py:1264 via _legacy_env (:1448) | LEGACY exec-runner on/off: stored once, then ignored | off | runtime_config.json backlog_exec_runner (+ serve --exec-runner) | backlog.exec.runner (exists as backlog_exec_runner; delete env after import) |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_THREADS` | maintenance/backlog_exec_runner.py:905 | alias of BACKLOG_EXEC_WORKERS | 2 | — | backlog.exec.workers (fold into) |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_UAT_DIR` | maintenance/backlog_exec_runner.py:227 | UAT candidate root | <repo>/untracked/backlog_exec_uat | — | backlog.exec.uat_dir |
| `ABSTRACTGATEWAY_BACKLOG_EXEC_WORKERS` | maintenance/backlog_exec_runner.py:903 | parallel exec workers | 2 | — | backlog.exec.workers |
| `ABSTRACTGATEWAY_BACKLOG_ROOTS` | routes/gateway.py:22448 | explicit repo dirs whose backlogs are served (overrides discovery) | discovered under the backlog folder | — | backlog.roots |
| `ABSTRACTGATEWAY_BACKLOG_TELEGRAM_CHAT_ID` | maintenance/notifier.py:30 (2nd name) | telegram chat for backlog notices | none | — | backlog.telegram_chat_id |
| `ABSTRACTGATEWAY_BIND_HOST` | runtime_config.py:619 (+network_exposure.py:1308) | host `serve` bound (set by serve) | unset = treated non-loopback | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_BIND_PORT` | network_exposure.py:1312 | port `serve` bound (set by serve) | unset | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_BIND_SOURCE` | network_exposure.py:1309 | where host/port came from (set by serve) | unset | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_BOOTSTRAP_ADMIN` | cli.py:207 | =0 disables admin auto-create (alias) | on | — | auth.bootstrap_admin (fold into) |
| `ABSTRACTGATEWAY_BOOTSTRAP_ADMIN_TOKEN` | config_cli.py:267 | explicit bootstrap admin token | generated | — | auth.bootstrap_admin_token (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_BOOTSTRAP_ADMIN_TOKEN_FILE` | cli.py:213 | where the bootstrap admin token is written | <data_dir>/auth/bootstrap-admin-token | — | paths.bootstrap_admin_token_file (secret-file path: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_BOOTSTRAP_PRINT_TOKEN` | cli.py:223 | print admin token at serve (legacy of --print-token) | yes on loopback, else no | — | auth.print_bootstrap_token (or drop: flag exists) |
| `ABSTRACTGATEWAY_COMMAND_BATCH_LIMIT` | config.py:363 | runner commands per tick | 200 | — | server.runner.command_batch_limit (restart) |
| `ABSTRACTGATEWAY_CONSOLE_LOG_LEVEL` | cli.py:53 | log level (1st in chain) | ERROR | — | logging.level |
| `ABSTRACTGATEWAY_CONTAINER` | self_update.py:436 (+:417, tray_supervisor.py:137) | running in a container: no self-update, no tray | unset | — | none (bootstrap-only: keep env) (host fact set by the image) |
| `ABSTRACTGATEWAY_CSRF_COOKIE` | security/sessions.py:114 | CSRF cookie name | abstractgateway_csrf | — | auth.csrf_cookie |
| `ABSTRACTGATEWAY_CSRF_HEADER` | security/sessions.py:124 | CSRF header name | x-abstractgateway-csrf | — | auth.csrf_header |
| `ABSTRACTGATEWAY_DATA_DIR` | host_paths.py:175 (resolve_data_dir; +users.py:74, config.py:340, ~8 more) | gateway data root (holds config/) | ./runtime if present, else per-OS user data dir | — | none (bootstrap-only: keep env) (locates the config) |
| `ABSTRACTGATEWAY_DATA_DIR_SOURCE` | host_paths.py:142 | provenance of an exported DATA_DIR | unset | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_DB_PATH` | config.py:355 | sqlite run-store file (must be under data dir) | <data_dir>/gateway.sqlite3 | — | paths.db_path (restart) |
| `ABSTRACTGATEWAY_DECLARED_ADDRESS` | config.py:134 | canonical public address for entity handles | unset (no handles rendered) | — | server.declared_address |
| `ABSTRACTGATEWAY_DEV_READ_NO_AUTH` | security/gateway_security.py:374 | unauthenticated reads on loopback | off | — | dev.read_no_auth (security-inversion: config must not weaken auth) |
| `ABSTRACTGATEWAY_DISCOVERY_MAX_CONCURRENCY` | routes/gateway.py:12595 | concurrent discovery probes | 8 | — | discovery.max_concurrency |
| `ABSTRACTGATEWAY_DISCOVERY_MODEL_TIMEOUT_S` | routes/gateway.py:2448 | 3rd name in provider-models timeout chain | 5 s | — | discovery.provider_models_timeout_s (fold into) |
| `ABSTRACTGATEWAY_DISCOVERY_TIMEOUT_S` | routes/gateway.py:2425 | discovery probe timeout | 1.5 s (clamp 0.2-10) | — | discovery.timeout_s |
| `ABSTRACTGATEWAY_DOCS_CORPUS` | routes/gateway.py:1982 | docs corpus override for the Docs assistant | repo llms.txt, else wheel copy | — | paths.docs_corpus |
| `ABSTRACTGATEWAY_DRAFT_RUN_RETENTION_TTL_S` | run_retention.py:47 | draft run retention | 7 d | — | limits.draft_run_ttl_s |
| `ABSTRACTGATEWAY_DRAFT_RUN_TTL_S` | run_retention.py:47 | alias of DRAFT_RUN_RETENTION_TTL_S | 7 d | — | limits.draft_run_ttl_s (fold into) |
| `ABSTRACTGATEWAY_DRIVE_PRESSURE_THRESHOLD` | routes/entities.py:2480 | entity drive-pressure threshold | runtime DRIVE_PRESSURE_BOUND | — | entity.drive_pressure_threshold |
| `ABSTRACTGATEWAY_EAGER_REHYDRATE_MAX` | service.py:1520 | runs rehydrated at boot | 32 (0 disables) | — | server.eager_rehydrate_max (restart) |
| `ABSTRACTGATEWAY_ENABLE_PROCESS_MANAGER` | runtime_config.py:1031 via _resolve (:1673); ALSO direct env read maintenance/backlog_exec_runner.py:1049 | process manager (Services page) | off | runtime_config.json process_manager | backlog.process_manager (exists as process_manager; see note 4) |
| `ABSTRACTGATEWAY_ENTITY_CREATE_QUOTA` | config.py:106 | entities an account may create | 20 (<=0 none) | — | entity.create_quota |
| `ABSTRACTGATEWAY_ENTITY_MAX_ITERATIONS_CEILING` | config.py:79 | ceiling on entity max_iterations | 100 (<=0 none) | — | entity.max_iterations_ceiling |
| `ABSTRACTGATEWAY_ENTITY_SELF_REPAIR` | entity_repair.py:436 | self-repair sweeper on/off | on | — | entity.self_repair |
| `ABSTRACTGATEWAY_ENTITY_SELF_REPAIR_INTERVAL_S` | entity_repair.py:442 | sweeper cadence | 300 s | — | entity.self_repair_interval_s |
| `ABSTRACTGATEWAY_ENTITY_STAMP_SECRET` | entity_gate.py:257 | entity stamp HMAC secret override | auto file under <data_dir>/entities/ | — | entity.stamp_secret (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_FILE_INDEX_MAX_FILES` | routes/gateway.py:5274 | @file index cap | 50000 (min 1000) | — | limits.file_index_max_files |
| `ABSTRACTGATEWAY_FILE_INDEX_TTL_S` | routes/gateway.py:5268 | @file index cache TTL | 30 s (min 1) | — | limits.file_index_ttl_s |
| `ABSTRACTGATEWAY_FLOWS_DIR` | config.py:342 | workflow bundle dir | packaged flows/bundles | — | paths.flows_dir (restart) |
| `ABSTRACTGATEWAY_GPU_METRICS_PROVIDER` | host_metrics.py:213 | GPU metrics source (auto|off|...) | auto | — | server.gpu_metrics_provider |
| `ABSTRACTGATEWAY_GRACEFUL_SHUTDOWN_S` | cli.py:1402 | uvicorn graceful-shutdown timeout | 120 | — | server.graceful_shutdown_s |
| `ABSTRACTGATEWAY_IMAGE_MAX_BYTES` | routes/gateway.py:13607 | max image bytes accepted | 20 MB (cap 200 MB) | — | limits.image_max_bytes |
| `ABSTRACTGATEWAY_LOCKOUT_AFTER` | security/gateway_security.py:415 | failed auths before lockout | 10 | — | security.lockout.after |
| `ABSTRACTGATEWAY_LOCKOUT_BASE_S` | security/gateway_security.py:416 | lockout base backoff | 1.0 | — | security.lockout.base_s |
| `ABSTRACTGATEWAY_LOCKOUT_MAX_S` | security/gateway_security.py:417 | lockout max backoff | 60.0 | — | security.lockout.max_s |
| `ABSTRACTGATEWAY_LOG_LEVEL` | cli.py:53 | log level (2nd in chain) | ERROR | — | logging.level (fold into) |
| `ABSTRACTGATEWAY_MAX_ATTACHMENT_BYTES` | security/gateway_security.py:404 (+routes/gateway.py:4546, hosts/bundle_host.py:3262, workspace_policy.py:761) | max attachment | 25 MiB | — | limits.max_attachment_bytes |
| `ABSTRACTGATEWAY_MAX_BACKLOG_ATTACHMENT_BYTES` | routes/gateway.py:24621 | max backlog attachment | 25 MiB | — | limits.max_backlog_attachment_bytes |
| `ABSTRACTGATEWAY_MAX_BODY_BYTES` | security/gateway_security.py:401 | max request body | 10 MiB | — | limits.max_body_bytes |
| `ABSTRACTGATEWAY_MAX_BUNDLE_BYTES` | security/gateway_security.py:409 (+routes/gateway.py:8429) | max .flow bundle upload | 75 MiB | — | limits.max_bundle_bytes |
| `ABSTRACTGATEWAY_MAX_CHAT_THREAD_BYTES` | routes/gateway.py:12308 | max chat thread doc | 750000 | — | limits.max_chat_thread_bytes |
| `ABSTRACTGATEWAY_MAX_CONCURRENCY` | security/gateway_security.py:413 | concurrent requests | 64 | — | limits.max_concurrency |
| `ABSTRACTGATEWAY_MAX_SESSIONS` | security/sessions.py:434 | sessions kept | 1000 (10-10000) | — | auth.max_sessions |
| `ABSTRACTGATEWAY_MAX_SSE` | security/gateway_security.py:414 | concurrent SSE streams | 32 | — | limits.max_sse |
| `ABSTRACTGATEWAY_MAX_UPLOAD_BODY_BYTES` | security/gateway_security.py:402 | extra cap on upload bodies | 0 (no extra cap) | — | limits.max_upload_body_bytes |
| `ABSTRACTGATEWAY_MEMORY_BACKEND` | memory_store.py:126 | alias of MEMORY_STORE_BACKEND | lancedb | — | memory.backend (fold into) |
| `ABSTRACTGATEWAY_MEMORY_PATH` | memory_store.py:129 | alias of MEMORY_STORE_PATH | see MEMORY_STORE_PATH | — | memory.path (fold into) |
| `ABSTRACTGATEWAY_MEMORY_REQUIRE_VECTOR` | memory_store.py:142 | refuse a non-vector KG store | off | — | memory.require_vector |
| `ABSTRACTGATEWAY_MEMORY_STORE_BACKEND` | memory_store.py:125 | KG store: lancedb|sqlite|memory | lancedb | — | memory.backend (restart) |
| `ABSTRACTGATEWAY_MEMORY_STORE_PATH` | memory_store.py:129 | KG store path | <data_dir>/abstractmemory/kg (.sqlite3 for sqlite) | — | memory.path (restart) |
| `ABSTRACTGATEWAY_MULTI_USER` | users.py:95 (+first_run.py:188) | alias of USER_AUTH | off | — | auth.user_auth (fold into) |
| `ABSTRACTGATEWAY_NETWORK_EXPORTS` | network_exposure.py:173 | env names serve exported for the network setting | unset | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_POLL_S` | config.py:360 | runner poll interval | 0.25 s | — | server.runner.poll_s (restart) |
| `ABSTRACTGATEWAY_PROCESS_MANAGER_CONFIG` | maintenance/process_manager.py:563 | process specs JSON | built-in specs | — | paths.process_manager_config |
| `ABSTRACTGATEWAY_PROMPT_CACHE` | hosts/bundle_host.py:3257 | prompt caching for runs | on | — | server.prompt_cache |
| `ABSTRACTGATEWAY_PROTECT_READ` | security/gateway_security.py:372 | auth on read endpoints | on | — | security.protect_read (security-inversion carve-out) |
| `ABSTRACTGATEWAY_PROTECT_WRITE` | security/gateway_security.py:373 | auth on write endpoints | on | — | security.protect_write (security-inversion carve-out) |
| `ABSTRACTGATEWAY_PROVIDER_AUTOPROBE_TIMEOUT_S` | routes/gateway.py:16481 | local-provider autoprobe timeout | 1.5 s (clamp 0.2-5) | — | discovery.autoprobe_timeout_s |
| `ABSTRACTGATEWAY_PROVIDER_MODELS_TIMEOUT_S` | routes/gateway.py:2446 | provider model-list timeout (1st) | 5 s (clamp 1-60) | — | discovery.provider_models_timeout_s |
| `ABSTRACTGATEWAY_REMEMBER_SESSION_TTL_S` | routes/gateway.py:396 (+routes/apps.py:575) | 'remember me' session TTL | 30 d | — | auth.remember_session_ttl_s |
| `ABSTRACTGATEWAY_REPORT_BACKLOG_ASSETS_MAX_BYTES` | routes/gateway.py:21205 | bytes copied from a report to backlog | 25 MiB | — | backlog.report_assets_max_bytes |
| `ABSTRACTGATEWAY_REPORT_BACKLOG_ASSETS_MAX_FILES` | routes/gateway.py:21197 | files copied from a report to backlog | 8 | — | backlog.report_assets_max_files |
| `ABSTRACTGATEWAY_REPORT_COPY_ATTACHMENTS_TO_BACKLOG` | routes/gateway.py:21190 | copy report attachments into backlog | on | — | backlog.report_copy_attachments |
| `ABSTRACTGATEWAY_REQUEST_TIMING` | app.py:369 | log every request's duration | off | — | logging.request_timing |
| `ABSTRACTGATEWAY_RUNNER` | config.py:357 | run the tick loop in THIS process (CLI flips it per process) | on | — | none (bootstrap-only: keep env) (process role) |
| `ABSTRACTGATEWAY_RUNNER_LOCK_STALE_S` | runner.py:148 | runner lock considered stale after | 10 s | — | server.runner.lock_stale_s |
| `ABSTRACTGATEWAY_RUN_SCAN_LIMIT` | config.py:364 | runs scanned per tick | 200 | — | server.runner.run_scan_limit (restart) |
| `ABSTRACTGATEWAY_SECURITY` | security/gateway_security.py:359 (+first_run.py:180) | security middleware master switch | on | — | security.enabled (security-inversion carve-out) |
| `ABSTRACTGATEWAY_SERVICE` | tray_supervisor.py:161 | running as a Windows service: no tray | unset | — | none (bootstrap-only: keep env) (host fact set by the service wrapper) |
| `ABSTRACTGATEWAY_SESSIONS_FILE` | security/sessions.py:134 | session store file | <data_dir>/auth/sessions.json | — | paths.sessions_file |
| `ABSTRACTGATEWAY_SESSION_COOKIE` | security/sessions.py:109 | session cookie name | abstractgateway_session | — | auth.session_cookie |
| `ABSTRACTGATEWAY_SESSION_HEADER` | security/sessions.py:119 | session header name | x-abstractgateway-session | — | auth.session_header |
| `ABSTRACTGATEWAY_SESSION_SECRET` | security/sessions.py:148 | session signing secret | read/created at SESSION_SECRET_FILE | — | auth.session_secret (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_SESSION_SECRET_FILE` | security/sessions.py:141 | session secret file | <data_dir>/auth/session_secret | — | paths.session_secret_file (secret-file path: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_SESSION_TTL_S` | security/sessions.py:129 | session TTL | 8 h (60 s-7 d) | — | auth.session_ttl_s |
| `ABSTRACTGATEWAY_SILENCE_GPU_METRICS_ACCESS_LOG` | cli.py:1347 | drop GPU-metrics polls from access log | on | — | logging.silence_gpu_metrics_access_log |
| `ABSTRACTGATEWAY_SKILLS_SHELF` | skills_shelf.py:192 | skills registry folder | seeded shelf in data dir, else checkout | runtime_config.json skills.shelf | skills.shelf (exists) |
| `ABSTRACTGATEWAY_SLOW_REQUEST_MS` | app.py:363 | warn on requests slower than | 1000 ms | — | logging.slow_request_ms |
| `ABSTRACTGATEWAY_STOP_KILL_SWITCH_S` | runtime_config.py:1031 via _resolve (:1777) | kill a cancelled run's model call after N s (0 off) | 10 s | runtime_config.json stop_kill_switch_s | stop_kill_switch_s (exists) |
| `ABSTRACTGATEWAY_STORE_BACKEND` | config.py:354 | run store: file|sqlite | file | — | server.store_backend (restart) |
| `ABSTRACTGATEWAY_TICK_MAX_STEPS` | config.py:362 | steps per run per tick | 100 | — | server.runner.tick_max_steps (restart) |
| `ABSTRACTGATEWAY_TICK_WEDGE_AFTER_S` | runner.py:130 | report a tick as wedged after | 600 s | — | server.runner.tick_wedge_after_s |
| `ABSTRACTGATEWAY_TICK_WORKERS` | config.py:361 | tick worker threads | 4 | — | server.runner.tick_workers (restart) |
| `ABSTRACTGATEWAY_TOOL_MODE` | hosts/bundle_host.py:1885 (+routes/gateway.py:15662, integrations/telegram_bridge.py:1145) | tool execution posture: approval|local|passthrough|delegated | approval | — | security.tool_mode |
| `ABSTRACTGATEWAY_TRIAGE_ACTION_SECRET` | routes/triage.py:30 (+cli.py:1591) | HMAC key for triage action links | none | — | triage.action_secret (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_TRIAGE_DEFER_DAYS` | maintenance/triage.py:502 (2nd name) | defer duration for a triage item | 1 | — | triage.defer_days |
| `ABSTRACTGATEWAY_TRIAGE_LLM` | maintenance/llm_assist.py:100 (2nd name) | triage LLM on/off (env OVERRIDES store) | store value, else off | abstractcore.json maintenance.triage_llm_enabled | triage.llm.enabled = Core maintenance (delete env) |
| `ABSTRACTGATEWAY_TRIAGE_LLM_API_KEY` | maintenance/llm_assist.py:109 (2nd name) | triage LLM API key | none | — | triage.llm.api_key (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_TRIAGE_LLM_BASE_URL` | maintenance/llm_assist.py:104 (2nd name) | triage LLM base URL | store value | abstractcore.json maintenance.triage_llm_base_url | triage.llm.base_url = Core maintenance |
| `ABSTRACTGATEWAY_TRIAGE_LLM_MAX_TOKENS` | maintenance/llm_assist.py:125 (2nd name) | triage LLM output cap | store value, else none | abstractcore.json maintenance.triage_llm_max_tokens | triage.llm.max_tokens = Core maintenance |
| `ABSTRACTGATEWAY_TRIAGE_LLM_MODEL` | maintenance/llm_assist.py:105 (2nd name) | triage LLM model | store value | abstractcore.json maintenance.triage_llm_model | triage.llm.model = Core maintenance |
| `ABSTRACTGATEWAY_TRIAGE_LLM_TEMPERATURE` | maintenance/llm_assist.py:111 (2nd name) | triage LLM temperature | store, else 0.2 | abstractcore.json maintenance.triage_llm_temperature | triage.llm.temperature = Core maintenance |
| `ABSTRACTGATEWAY_TRIAGE_LLM_TIMEOUT_S` | maintenance/llm_assist.py:118 (2nd name) | triage LLM client timeout (<=0 none) | store, else 7200 s | abstractcore.json maintenance.triage_llm_timeout_s | triage.llm.timeout_s = Core maintenance |
| `ABSTRACTGATEWAY_TRIAGE_REPO_ROOT` | runtime_config.py:1264 via _legacy_env (:1402) | LEGACY backlog folder: stored once, then ignored | <data_dir>/backlog | runtime_config.json triage_repo_root (+ serve --backlog-root) | backlog.root (exists as triage_repo_root; delete env after import) |
| `ABSTRACTGATEWAY_TRIAGE_TELEGRAM_CHAT_ID` | maintenance/notifier.py:31 (2nd name) | fallback telegram chat for notices | none | — | triage.telegram_chat_id |
| `ABSTRACTGATEWAY_TRUST_PROXY` | security/gateway_security.py:418 (+network_exposure.py:446) | trust X-Forwarded-For from remote proxies | off | runtime_config.json network.trust_proxy (env used only when nothing stored) | security.trust_proxy (exists as network.trust_proxy) |
| `ABSTRACTGATEWAY_TUI_HANDOVER` | tui_signin.py:68 | one-time sign-in code: launcher script -> TUI | unset | — | none (bootstrap-only: internal handoff the gateway sets for itself/children; not operator input) |
| `ABSTRACTGATEWAY_URL` | models_engines_cli.py:215 (+apps_manager.py:2843, network_exposure.py:1847) | CLIENT-side gateway base URL for CLIs | serve record, else http://127.0.0.1:8080 | — | none (bootstrap-only: keep env) (client side, no data dir) |
| `ABSTRACTGATEWAY_USERS_FILE` | users.py:86 (+entity_accounts.py:28, entities.py:1279) | user registry file | <data_dir>/auth/users.json | — | paths.users_file |
| `ABSTRACTGATEWAY_USER_AUTH` | users.py:94 (+first_run.py:188) | per-user accounts on/off | off (serve on loopback sets 1) | — | auth.user_auth |
| `ABSTRACTGATEWAY_USER_AUTH_AUTO` | users.py:107 | user auth on if users.json exists | off | — | auth.user_auth_auto (or drop) |
| `ABSTRACTGATEWAY_VISION_BACKEND` | routes/gateway.py:18270 | image backend #FALLBACK for model list | output.image route, else '' | abstractcore.json capability route output.image (provider) | vision.backend = the route (delete env) |
| `ABSTRACTGATEWAY_VISION_MFLUX_MODEL` | routes/gateway.py:18279 | advertise an mlx-gen image model | none | capability route output.image (model) | vision.model = the route (delete env) |
| `ABSTRACTGATEWAY_VISION_MODEL_ID` | routes/gateway.py:18281 | advertise an image model id | none | capability route output.image (model) | vision.model = the route (delete env) |
| `ABSTRACTGATEWAY_VISUALFLOWS_DIR` | routes/gateway.py:2803 | VisualFlow JSON dir | <data_dir>/visualflows | — | paths.visualflows_dir |
| `ABSTRACTGATEWAY_VOICE_MAX_CONCURRENCY` | routes/gateway.py:12637 | concurrent TTS syntheses (503 past it) | 4 | — | voice.max_concurrency |
| `ABSTRACTGATEWAY_VOICE_REMOTE_BASE_URL` | routes/gateway.py:18337 | remote voice server URL (marks voice configured) | none | — | voice.remote_base_url |
| `ABSTRACTGATEWAY_VOICE_STT_ENGINE` | routes/gateway.py:2380 (_resolved_voice_engine) | STT engine #FALLBACK | input.voice route, else env | abstractcore.json capability route input.voice (provider) | voice.stt.engine = the route (delete env) |
| `ABSTRACTGATEWAY_VOICE_STT_MODEL` | routes/gateway.py:18418 (+:17739) | STT model #FALLBACK | input.voice route model | capability route input.voice (model) | voice.stt.model = the route (delete env) |
| `ABSTRACTGATEWAY_VOICE_TTS_ENGINE` | routes/gateway.py:2378 (_resolved_voice_engine) | TTS engine #FALLBACK | output.voice route, else env | abstractcore.json capability route output.voice (provider) | voice.tts.engine = the route (delete env) |
| `ABSTRACTGATEWAY_VOICE_TTS_MODEL` | routes/gateway.py:18376 (+:17334, :17686) | TTS model #FALLBACK | output.voice route model | capability route output.voice (model) | voice.tts.model = the route (delete env) |
| `ABSTRACTGATEWAY_VOICE_TTS_TIMEOUT_S` | routes/gateway.py:12571 | TTS deadline (504 past it; <=0 off) | 300 s | — | voice.tts_timeout_s |
| `ABSTRACTGATEWAY_VOICE_TTS_VOICES` | routes/gateway.py:16261 | extra voice ids to advertise (CSV) | none | — (route options.voice holds only the default voice) | voice.tts.extra_voices |
| `ABSTRACTGATEWAY_WORKFLOW_CATALOG_BUNDLES_DIR` | workflow_catalog.py:223 | catalog bundles dir | <data_dir>/workflow_catalog/bundles | — | paths.workflow_catalog_bundles_dir |
| `ABSTRACTGATEWAY_WORKFLOW_CATALOG_FILE` | workflow_catalog.py:215 | catalog file | <data_dir>/workflow_catalog.json | — | paths.workflow_catalog_file |
| `ABSTRACTGATEWAY_WORKFLOW_POLICY_SECRET` | workflow_catalog.py:239 | catalog policy HMAC secret | read/created at the secret file | — | security.workflow_policy_secret (secret: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_WORKFLOW_POLICY_SECRET_FILE` | workflow_catalog.py:231 | catalog policy secret file | <data_dir>/.workflow_policy_secret | — | paths.workflow_policy_secret_file (secret-file path: keep env/secret-file, never in a plain JSON) |
| `ABSTRACTGATEWAY_WORKFLOW_SOURCE` | service.py:786 (+config_cli.py:103) | workflow source (bundle is the only supported) | bundle | — | drop (single supported value) or server.workflow_source |
| `ABSTRACTGATEWAY_WORKSPACE_DIR` | workspace_policy.py:203 (legacy migration; +:606) | LEGACY shared workspace root, migrated once | none | runtime_config.json workspace_policy (GET/PUT /api/gateway/workspace/policy) | workspace_policy (exists; delete env after migration) |
| `ABSTRACTGATEWAY_WORKSPACE_MOUNTS` | runtime_config.py:597 (called from workspace_policy.py:409 migration) | LEGACY named mounts, migrated once | none | runtime_config.json workspace_policy | workspace_policy (exists; delete env after migration) |
| `ABSTRACTGATEWAY_WORKSPACE_ROOT` | workspace_policy.py:203 (+:606) | LEGACY alias of WORKSPACE_DIR | none | runtime_config.json workspace_policy | workspace_policy (exists; delete env after migration) |
| `ABSTRACTRUNTIME_GLOBAL_MEMORY_RUN_ID` | memory_store.py:74 | owner id of the global KG memory plane | global_memory | — | memory.global_owner_id (runtime-owned; read via runtime) |

### AbstractCore (94)

| Name | Read at | Meaning | Default when unset | Already covered by abstractcore.json | Proposed key |
|---|---|---|---|---|---|
| ABSTRACTCORE_ALLOW_ENGINE_INSTALL | config/engines.py:100; server/host_routes.py:68 | allow engine (pip) installs via jobs/HTTP | lib: module knob True; server: True only on loopback bind | no | server.allow_engine_install |
| ABSTRACTCORE_ALLOW_UNSAFE_UNLOAD_AFTER | server/app.py:9863 | permit `unload_after` on ollama (else 403) | false | no | server.allow_unsafe_unload_after |
| ABSTRACTCORE_AUTH_TOKEN | server/auth_policy.py:48; first_run.py:95 | server inbound bearer token | none -> first-run token file flow | server.auth_token (env wins) | (secret: keep env/secret-file); server.auth_token exists |
| ABSTRACTCORE_BLOC_KV_DEBUG | core/bloc_kv.py:637 | bloc-KV debug payloads | off | no | diagnostic: env only is fine (debug.bloc_kv) |
| ABSTRACTCORE_CALIBRATION_DIR | utils/context_calibration.py:43 | context-calibration cache dir | ~/.abstractcore/calibration | no | paths.calibration_dir |
| ABSTRACTCORE_CLI_COUNTRY | utils/cli.py:906 | CLI country code (2 letters) | locale-derived | no | cli.country (new group) |
| ABSTRACTCORE_CLI_KV_REFRESH_TOOLS_AT | utils/cli.py:878 | CLI: re-inject tool specs past N cached tokens | 50000 (<0 disables) | no | cli.kv_refresh_tools_at (new group) |
| ABSTRACTCORE_CONFIG_DIR | config/manager.py:611; host_jobs.py:350; model_catalog.py:1168 | config dir (also jobs/, cache/ root) | ~/.abstractcore/config | n/a | bootstrap: env only |
| ABSTRACTCORE_CONFIG_FILE | config/manager.py:608 | explicit config file path | <CONFIG_DIR>/abstractcore.json | n/a | bootstrap: env only |
| ABSTRACTCORE_CONSOLE_LOG_LEVEL | utils/structured_logging.py:70 | console log level (NONE disables) | logging.console_level (ERROR) | logging.console_level (env wins) | covered |
| ABSTRACTCORE_DEBUG | server/app.py:149 | server debug mode (= --debug) | false | no | diagnostic: env only is fine (debug.server) |
| ABSTRACTCORE_DEBUG_EXTRACTION | tools/common_tools.py:7968 | print traceback on fetch_url extraction failure | off | no | diagnostic: env only is fine |
| ABSTRACTCORE_DEV_PREFER_SIBLINGS | server/app.py:117 | prepend sibling repo checkouts to sys.path | **on ("1")** | no | diagnostic: env only is fine (debug.dev_prefer_siblings); see note 3 |
| ABSTRACTCORE_DOWNLOAD_STALL_S | config/host_jobs.py:139 | download stall threshold (s w/o bytes) | 15 | no | downloads.stall_s |
| ABSTRACTCORE_EMBEDDINGS_STRICT | embeddings/manager.py:379 | raise on embedding failure vs zero vectors | false | no (embeddings.* has no strict) | embeddings.strict |
| ABSTRACTCORE_FETCH_URL_ALLOW | tools/fetch_url_ssrf.py:43 | host[:port] CSV exempt from fetch_url SSRF block | empty | no | fetch_url.ssrf_allow |
| ABSTRACTCORE_FETCH_URL_PDF_NATIVE_MAX_BYTES | media/pdf_routing.py:347 | native-PDF route max bytes | 4 MiB (min 64 KiB) | no (gate is offline.allow_remote_pdf_extraction) | fetch_url.pdf_native.max_bytes |
| ABSTRACTCORE_FETCH_URL_PDF_NATIVE_MAX_PAGES | media/pdf_routing.py:346 | native-PDF route max pages | 4 | no | fetch_url.pdf_native.max_pages |
| ABSTRACTCORE_FETCH_URL_PDF_NATIVE_MODEL | media/pdf_routing.py:329 | model for native-PDF extraction | gpt-4.1-mini | no | fetch_url.pdf_native.model |
| ABSTRACTCORE_FETCH_URL_PDF_NATIVE_TIMEOUT_S | media/pdf_routing.py:348 | native-PDF call timeout | 120 (min 15) | no | fetch_url.pdf_native.timeout_s |
| ABSTRACTCORE_FILE_LOG_LEVEL | utils/structured_logging.py:78 | file log level (NONE disables) | logging.file_level (DEBUG) | logging.file_level (env wins) | covered |
| ABSTRACTCORE_GGUF_BOUNDARY_SNAPSHOT | providers/huggingface_provider.py:9309 | GGUF boundary-snapshot policy (0 = legacy full-prompt) | on | no | diagnostic: env only is fine (A/B escape hatch) |
| ABSTRACTCORE_GGUF_CONTROL_PLANE | providers/huggingface_provider.py:1365, 8924 | GGUF local control-plane render lane | on | no | diagnostic: env only is fine (escape hatch) |
| ABSTRACTCORE_GGUF_METAL_UNSAFE | providers/huggingface_provider.py:6137 | bypass Metal-after-torch safety guard | off | no | diagnostic: env only is fine |
| ABSTRACTCORE_GGUF_SNAPSHOT_BOUND | providers/huggingface_provider.py:3045 | max GGUF prompt-state snapshots kept | 2 | no | gguf.snapshot_bound |
| ABSTRACTCORE_HF_DEVICE | providers/huggingface_provider.py:1010 | transformers device (auto/cpu/mps/cuda) | auto | no | transformers.device |
| ABSTRACTCORE_HF_XET | config/model_materializer.py:3660 | allow hf_xet in download child | off (sets HF_HUB_DISABLE_XET=1) | no | downloads.hf_xet |
| ABSTRACTCORE_JOBS_DIR | config/host_jobs.py:347 | host-jobs persistence dir | <CONFIG_DIR>/jobs | no | jobs.dir |
| ABSTRACTCORE_JOBS_PERSIST | config/host_jobs.py:1453 | persist host jobs to disk | on | no | jobs.persist |
| ABSTRACTCORE_LMS_CLI | config/model_materializer.py:844 | LM Studio `lms` CLI path | `which lms`, then LM Studio default path | no | paths.lms_cli |
| ABSTRACTCORE_LOG_BASE_DIR | utils/structured_logging.py:86 | log dir | logging.log_base_dir (only if file_logging_enabled) | logging.log_base_dir (env wins; env bypasses file_logging_enabled) | covered |
| ABSTRACTCORE_MLX_MODEL_PATTERNS | providers/mlx_model_rules.py:294 (const :74) | patterns forcing MLX classification | none | no | mlx.force_mlx_patterns |
| ABSTRACTCORE_MLX_SHARE_MODELS | providers/mlx_provider.py:141 | share loaded MLX models across instances | on | no | mlx.share_loaded_models |
| ABSTRACTCORE_MPS_POOL_GUARD_STRIDE | providers/huggingface_provider.py:4544 | MPS pool-guard stride (A/B knob) | 8 | no | diagnostic: env only is fine |
| ABSTRACTCORE_MPS_POOL_RELEASE_GB | providers/huggingface_provider.py:4462 | release pooled MPS memory above N GiB | 4 (<=0 disables) | no | transformers.mps_pool_release_gb |
| ABSTRACTCORE_NON_MLX_MODEL_PATTERNS | providers/mlx_model_rules.py:292 (const :77) | patterns forcing non-MLX classification | none | no | mlx.force_non_mlx_patterns |
| ABSTRACTCORE_ONNX_VERBOSE | embeddings/manager.py:82 | show ONNX runtime warnings | 0 (suppressed) | no | diagnostic: env only is fine |
| ABSTRACTCORE_PROGRESS_MIN_INTERVAL_S | providers/generation_progress.py:157 (const :76) | min interval between text progress events | 0.5 | no | generation.progress_min_interval_s |
| ABSTRACTCORE_REPETITION_DETECT | core/degeneration.py:137 | repetition/degeneration detector on/off | on | no | generation.repetition.enabled |
| ABSTRACTCORE_REPETITION_MAX_CYCLE | core/degeneration.py:145 | detector max cycle tokens | 128 | no | generation.repetition.max_cycle |
| ABSTRACTCORE_REPETITION_MIN_CYCLE | core/degeneration.py:143 | detector min cycle tokens | 3 | no | generation.repetition.min_cycle |
| ABSTRACTCORE_REPETITION_MIN_LOOP_TOKENS | core/degeneration.py:149 | min loop tokens before abort | 512 | no | generation.repetition.min_loop_tokens |
| ABSTRACTCORE_REPETITION_REPEATS | core/degeneration.py:147 | repeats required to trip | 20 | no | generation.repetition.repeats |
| ABSTRACTCORE_SERVER_ALLOW_LOCAL_FILES | server/app.py:3721 | allow arbitrary local paths in HTTP requests | false | server.allow_local_files (env wins; config can only turn on) | covered |
| ABSTRACTCORE_SERVER_ALLOW_UNAUTHENTICATED | server/auth_policy.py:55; first_run.py:99 | run server without auth | false | server.allow_unauthenticated (env wins; config can only turn on) | covered |
| ABSTRACTCORE_SERVER_AUDIO_MAX_BYTES | server/audio_endpoints.py:994 | audio upload cap | 25 MiB | no | server.audio_max_bytes |
| ABSTRACTCORE_SERVER_BASE_URL_ALLOWLIST | server/app.py:3701; audio_endpoints.py:703; vision_endpoints.py:1566 | allowed request `base_url` hosts | empty (loopback only) | server.base_url_allowlist (env wins) | covered |
| ABSTRACTCORE_SERVER_BIND_HOST | server/host_routes.py:73 | recorded bind host (engine-install default) | unset -> treated non-loopback | n/a (written from --host by server) | internal hand-off: no key |
| ABSTRACTCORE_SERVER_CONTROL_PLANE_TIMEOUT_S | server/app.py:6437 | control-plane proxy client timeout | 7200 (0 = none) | no | server.control_plane_timeout_s |
| ABSTRACTCORE_SERVER_DISABLE_CENTRALIZED_CONFIG | server/app.py:187 | skip loading abstractcore.json in server | off | n/a | bootstrap: env only |
| ABSTRACTCORE_SERVER_MEDIA_ROOT | server/app.py:3710 | safe root for local media paths | none | server.media_root (env wins) | covered |
| ABSTRACTCORE_SERVER_PROTECT_DOCS | server/app.py:332 | require auth on /docs | off | no | server.protect_docs |
| ABSTRACTCORE_SERVER_SCENE3D_IMAGE_MAX_BYTES | server/scene3d_endpoints.py:53 | i23d source-image cap | 25 MiB | no | server.scene3d_image_max_bytes |
| ABSTRACTCORE_SERVER_TOKEN_SOURCE | server/first_run.py:111 | marker: token came from first-run file (enables claim) | unset | n/a (written by serve) | internal hand-off: no key |
| ABSTRACTCORE_SERVER_URL_FETCH_ALLOWLIST | server/app.py:9214, 9285 | server URL-fetch allowlist | empty | server.url_fetch_allowlist (env wins) | covered |
| ABSTRACTCORE_TRANSFORMERS_ATTN_IMPL | providers/huggingface_provider.py:6579 | force attn_implementation (e.g. eager) | transformers default | no | transformers.attn_implementation |
| ABSTRACTCORE_TRANSFORMERS_PREFILL_STEP | providers/huggingface_provider.py:4905 | chunked prefill step | 2048 (<=0 disables) | no | transformers.prefill_step |
| ABSTRACTCORE_TRANSFORMERS_SNAPSHOT_BOUND | providers/huggingface_provider.py:3759 | max transformers KV snapshots | 4 (capped by store entries) | no | transformers.snapshot_bound |
| ABSTRACTCORE_VISION_ALLOW_DOWNLOAD | server/vision_endpoints.py:3012 | diffusers lane may download weights | false | CD diffusers options.allow_download (config wins) | covered |
| ABSTRACTCORE_VISION_AUTO_RETRY_FP32 | server/vision_endpoints.py:3019 | diffusers retry in fp32 on failure | true | CD diffusers options.auto_retry_fp32 (config wins) | covered |
| ABSTRACTCORE_VISION_BACKEND | server/vision_endpoints.py:2173; catalog map :1634 | vision backend kind | auto | CD provider (config wins) | covered |
| ABSTRACTCORE_VISION_BACKEND_CACHE_MAX | server/vision_endpoints.py:1045 | max cached vision backends | 4 | no | vision.backend_cache_max |
| ABSTRACTCORE_VISION_DEVICE | server/vision_endpoints.py:3003 | diffusers device | auto | CD diffusers options.device (config wins) | covered |
| ABSTRACTCORE_VISION_HF_HUB_CACHE | capabilities/vision_catalog.py:41 | extra HF hub cache dir for vision catalog | after HF_HUB_CACHE(_DIR); else HF_HOME/hub, ~/.cache/huggingface/hub | no (cache.huggingface_cache_dir not consulted here) | vision.hf_hub_cache |
| ABSTRACTCORE_VISION_IMAGE_TO_VIDEO_MODE | server/vision_endpoints.py:3091 | proxy i2v request mode | multipart | CD proxy options.image_to_video_mode (config wins) | covered |
| ABSTRACTCORE_VISION_IMAGE_TO_VIDEO_PATH | server/vision_endpoints.py:3083 | proxy i2v path (alias) | /videos/edits | CD proxy options.image_to_video_path (config wins) | covered |
| ABSTRACTCORE_VISION_JOBS_MAX | server/vision_endpoints.py:706 | max concurrent vision jobs kept | 8 (1..64) | no | vision.jobs_max |
| ABSTRACTCORE_VISION_JOBS_TTL_S | server/vision_endpoints.py:715 | vision job TTL | 600 (10..86400) | no | vision.jobs_ttl_s |
| ABSTRACTCORE_VISION_MFLUX_ALLOW_DOWNLOAD | server/vision_endpoints.py:3043; catalog map :1646 | mflux lane may download | false | CD mlx-gen options.allow_download (config wins) | covered |
| ABSTRACTCORE_VISION_MFLUX_BASE_MODEL | server/vision_endpoints.py:3035; catalog map :1642 | mflux base model | none | CD mlx-gen options.base_model (config wins) | covered |
| ABSTRACTCORE_VISION_MFLUX_MODEL | server/vision_endpoints.py:2060; catalog map :1640 | mflux default model | falls to VISION_MODEL_ID | CD mlx-gen model (config wins) | covered |
| ABSTRACTCORE_VISION_MODEL_DIR | server/vision_endpoints.py:3038; capabilities/vision_catalog.py:88 | mflux model dir; also catalog local-model scan dir | none | CD mlx-gen options.model_dir (config wins) — catalog scan stays env-only | covered (partial; vision.models_dir for scan) |
| ABSTRACTCORE_VISION_MODEL_ID | server/vision_endpoints.py:2048, 3522; catalog map :1638 | diffusers default model id | none | CD diffusers model (config wins) | covered |
| ABSTRACTCORE_VISION_MODELS_DIR | capabilities/vision_catalog.py:87 | local diffusers model dirs for catalog | none | no | vision.models_dir |
| ABSTRACTCORE_VISION_MODELS_PATH | server/vision_endpoints.py:1650 (catalog env map, read at :1658) | plugin `vision_models_path` for catalog core | plugin default | no | vision.models_path |
| ABSTRACTCORE_VISION_SDCPP_BIN | server/vision_endpoints.py:3214 via f-string :2110 | sd-cli binary | sd-cli | CD sdcpp options.bin (config wins) | covered |
| ABSTRACTCORE_VISION_SDCPP_CLIP_G | server/vision_endpoints.py:3221 via :2110 | sdcpp clip_g component | none | CD sdcpp options.clip_g | covered |
| ABSTRACTCORE_VISION_SDCPP_CLIP_L | server/vision_endpoints.py:3220 via :2110 | sdcpp clip_l component | none | CD sdcpp options.clip_l | covered |
| ABSTRACTCORE_VISION_SDCPP_DIFFUSION_MODEL | server/vision_endpoints.py:2558 via :2110; catalog map :1654 | sdcpp diffusion model (component mode) | none | CD sdcpp options.diffusion_model | covered |
| ABSTRACTCORE_VISION_SDCPP_EXTRA_ARGS | server/vision_endpoints.py:3211 via :2110 | extra sd-cli args | none | CD sdcpp options.extra_args | covered |
| ABSTRACTCORE_VISION_SDCPP_LLM | server/vision_endpoints.py:3218 via :2110 | sdcpp llm component | none | CD sdcpp options.llm | covered |
| ABSTRACTCORE_VISION_SDCPP_LLM_VISION | server/vision_endpoints.py:3219 via :2110 | sdcpp llm_vision component | none | CD sdcpp options.llm_vision | covered |
| ABSTRACTCORE_VISION_SDCPP_MODEL | server/vision_endpoints.py:2553 via :2110; catalog map :1652 | sdcpp single-file model | none | CD sdcpp model (config wins, warns :2556) | covered |
| ABSTRACTCORE_VISION_SDCPP_T5XXL | server/vision_endpoints.py:3222 via :2110 | sdcpp t5xxl component | none | CD sdcpp options.t5xxl | covered |
| ABSTRACTCORE_VISION_SDCPP_VAE | server/vision_endpoints.py:3217 via :2110 | sdcpp vae component | none | CD sdcpp options.vae | covered |
| ABSTRACTCORE_VISION_TEXT_TO_VIDEO_PATH | server/vision_endpoints.py:3074 | proxy t2v path (alias) | /videos/generations | CD proxy options.text_to_video_path | covered |
| ABSTRACTCORE_VISION_TIMEOUT_S | server/vision_endpoints.py:1648 (catalog env map) | plugin `vision_timeout_s` for catalog core | plugin default | no | vision.timeout_s |
| ABSTRACTCORE_VISION_TORCH_DTYPE | server/vision_endpoints.py:3007 | diffusers torch dtype | backend auto | CD diffusers options.torch_dtype | covered |
| ABSTRACTCORE_VISION_UPSTREAM_IMAGES_EDITS_PATH | server/vision_endpoints.py:3065 | proxy image-edits path | /images/edits | CD proxy options.image_edits_path | covered |
| ABSTRACTCORE_VISION_UPSTREAM_IMAGES_GENERATIONS_PATH | server/vision_endpoints.py:3057 | proxy image-gen path | /images/generations | CD proxy options.image_generations_path | covered |
| ABSTRACTCORE_VISION_UPSTREAM_MODEL_ID | server/vision_endpoints.py:2087, 3516; catalog map :1637 | OpenAI-compatible proxy model id | none | CD openai_compatible_proxy model | covered |
| ABSTRACTCORE_VISION_UPSTREAM_VIDEOS_EDITS_PATH | server/vision_endpoints.py:3082 | proxy i2v path | /videos/edits | CD proxy options.image_to_video_path | covered |
| ABSTRACTCORE_VISION_UPSTREAM_VIDEOS_GENERATIONS_PATH | server/vision_endpoints.py:3073 | proxy t2v path | /videos/generations | CD proxy options.text_to_video_path | covered |
| ABSTRACTGATEWAY_DATA_DIR | tools/telegram_tools.py:61 (param default :344) | artifact store root for telegram send-artifact tool | fallback ABSTRACTFLOW_RUNTIME_DIR, else error | no | cross-package: gateway owns it; keep env (tool arg overrides) |

### AbstractRuntime (22)

| Name | Read at | Meaning | Default unset | Already covered by config? | Proposed home (env = override only) |
|---|---|---|---|---|---|
| ABSTRACTCORE_AUDIO_BACKEND | integrations/abstractcore/discovery_queries.py:734 (composed `f"ABSTRACTCORE_{cap.upper()}_BACKEND"`) | preferred capability backend id for `audio` in the runtime's discovery CapabilityRegistry | none (registry picks) | No for this path. Core has owner key `capabilities_preferred_backends` + abstractcore.json `audio.stt_backend_id`, but runtime discovery builds its own owner and ignores both | abstractcore.json `capabilities.preferred_backends.audio` (core-owned; runtime should read it via core, not env) |
| ABSTRACTCORE_MUSIC_BACKEND | discovery_queries.py:734 (composed) | same, `music` | none | No | abstractcore.json `capabilities.preferred_backends.music` |
| ABSTRACTCORE_VISION_BACKEND | discovery_queries.py:734 (composed) | same, `vision` (gateway and core server also read this name) | none | No | abstractcore.json `capabilities.preferred_backends.vision` |
| ABSTRACTCORE_VOICE_BACKEND | discovery_queries.py:734 (composed) | same, `voice` | none | No | abstractcore.json `capabilities.preferred_backends.voice` |
| ABSTRACTGATEWAY_ENTITY_CHAT_MODEL | identity/substrate.py:150 (const `SUBSTRATE_ENV_MODEL`, :33) | entity mind model, last rung before refusal (runtime identity CLIs) | none -> `SubstrateUnset` raised | Yes: CLI flags > `<home>/substrate.yaml` outrank it. Gateway registry says the gateway REMOVED this env in round 3 (env_registry.py:321); runtime still reads it, so the two halves have drifted | Drop the env rung (match gateway), or gateway text route as `runtime.entity.default_model` |
| ABSTRACTGATEWAY_ENTITY_CHAT_PROVIDER | identity/substrate.py:149 (const :32) | entity mind provider, same chain | none -> `SubstrateUnset` | Yes (same as above; same drift) | Drop, or `runtime.entity.default_provider` |
| ABSTRACTRUNTIME_CODE_FULL_ACCESS | visualflow_compiler/visual/code_executor.py:273 | host policy allowing `full_access` (unsandboxed) Code-node execution | off (sandbox only) | No (gateway passes per-request `permissions`, never the policy) | `runtime.code_execution.allow_full_access` (admin-only; security-sensitive, not a secret) |
| ABSTRACTRUNTIME_DISCOVERY_TIMEOUT_S | integrations/abstractcore/discovery_queries.py:41 | per-call budget for model/provider/voice/vision discovery probes | 5.0 s | Partial: per-call `timeout_s` arg wins; gateway passes it only on provider-model autoprobe (gateway.py:16518-16527); its own `ABSTRACTGATEWAY_DISCOVERY_TIMEOUT_S` (console_path `discovery`) is gateway-side only | `runtime.discovery.timeout_s` |
| ABSTRACTRUNTIME_ENDPOINT_PROFILE_JSON | identity/life.py:4276 | parent->child channel: host-resolved provider endpoint profile `{spec, profile}` for the spawned own-time loop | none (local config only) | N/A - internal IPC, written by life.py:1886 into the child env | Keep as internal IPC (or pass via stdin/file); never a config key. SECRET: payload may carry `api_key` |
| ABSTRACTRUNTIME_ENTITY_LLM_TIMEOUT_S | identity/life.py:94, identity/chat.py:139 | per-attempt total LLM timeout on interactive entity lanes; <=0 = none | 120 s | No | `runtime.entity.llm_timeout_s` |
| ABSTRACTRUNTIME_ENTITY_RETRY_BUDGET_S | identity/life.py:95, identity/chat.py:140 | wall-clock retry budget for the same lanes; <=0 = none | 180 s | No | `runtime.entity.retry_budget_s` |
| ABSTRACTRUNTIME_GLOBAL_MEMORY_RUN_ID | core/runtime.py:3649; integrations/abstractmemory/effect_handlers.py:118 | run id owning `scope="global"` memory spans (must match `_SAFE_RUN_ID_PATTERN`) | `global_memory` | No. Gateway reads the SAME env (memory_store.py:74; registry FOREIGN owner=runtime) | `runtime.memory.global_run_id` (deployment/topology; both readers must take it from one place) |
| ABSTRACTRUNTIME_GROUNDING_PROMPT_FIELDS | integrations/abstractcore/llm_client.py:1301 | comma list of grounding fields injected into the per-turn prompt envelope (local_datetime, timezone, country, user, display) | `local_datetime,display` | No | `runtime.grounding.prompt_fields` |
| ABSTRACTRUNTIME_LOCAL_IMAGE_SUBPROCESS | llm_client.py:2159 | run local image generation in a subprocess (off = in-process) | on | No | DIAGNOSTIC kill switch; keep env-only (or `runtime.media.local_image_subprocess`) |
| ABSTRACTRUNTIME_LOCAL_IMAGE_SUBPROCESS_SERIALIZE | llm_client.py:2332, 2379 | process-wide lock serializing local image generations (GPU contention) | on | No | DIAGNOSTIC; keep env-only |
| ABSTRACTRUNTIME_LOCAL_VIDEO_SUBPROCESS | llm_client.py:2214 | same for local video generation | on | No | DIAGNOSTIC; keep env-only |
| ABSTRACTRUNTIME_LOCAL_VIDEO_SUBPROCESS_SERIALIZE | llm_client.py:2514 | same lock for video | on | No | DIAGNOSTIC; keep env-only |
| ABSTRACTRUNTIME_MAX_ATTACHMENT_BYTES | integrations/abstractcore/effect_handlers.py:3491 | retention cap for tool-output artifacts/attachments | 50 MiB | Yes: `TOOL_CALLS.payload.max_attachment_bytes` > run var `_runtime.max_attachment_bytes` > env. Gateway fills the run var from `ABSTRACTGATEWAY_MAX_ATTACHMENT_BYTES` (bundle_host.py:3262; registry console_path `limits`) | `runtime.limits.max_attachment_bytes` (already effectively there via run var) |
| ABSTRACTRUNTIME_MAX_INLINE_BYTES | storage/offloading.py:30 (ledger offload); effect_handlers.py:4711 (tool output) | above this, values/tool outputs are offloaded to artifacts | 256 KiB | No (no run-var or param path) | `runtime.limits.max_inline_bytes` |
| ABSTRACTRUNTIME_PDF_FONT | documents/pdf.py:79 | TTF path tried first for Unicode PDF rendering | none (DejaVu via matplotlib, then system fonts) | No | `runtime.documents.pdf_font` (host/deployment; low priority) |
| ABSTRACTRUNTIME_PHASE_SPEC | identity/phase_spec.py:121, identity/phase_graph.py:227 (const `PHASE_SPEC_ENV`, phase_spec.py:38) | path to an entity-phases tunables JSON | vendored `identity/spec/entity_phases.vendored.json` | Yes: gateway operator copy `<data_dir>/config/entity_phases.json` outranks it (dm#177) | DIAGNOSTIC (docstring: "test/harness convenience"); keep env-only below config |
| ABSTRACTRUNTIME_PROMPT_CACHE | integrations/abstractcore/effect_handlers.py:1045 | process-wide default for session-scoped prompt-cache key derivation (tri-state) | on | Yes: run var `_runtime.prompt_cache` wins. Gateway fills it from `ABSTRACTGATEWAY_PROMPT_CACHE` (bundle_host.py:3254-3260; registry console_path `runtime.prompt_cache`), so this env is never consulted under the gateway | `runtime.prompt_cache` (exists as console_path; gateway's own source is still env) |

