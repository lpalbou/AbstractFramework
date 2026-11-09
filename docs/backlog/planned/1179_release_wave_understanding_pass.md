# 1179 — Release wave: the understanding pass and the other local commits of 2026-11-07/08

> Package: AbstractMemory, AbstractRuntime, AbstractVoice, AbstractGateway, AbstractEntity, AbstractCode (web + TUI), AbstractFramework (root pins)
> Type: task
> Status: planned — paused
> Created: 2026-11-08
> Priority: P1
> Labels: release, understanding-pass, wave, paused, seat-framework

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go. Every publish below also needs its own
explicit go after a local redeploy and the operator's user test.

## Summary

Everything built for the understanding pass, plus the read-aloud repair, the Entity app rounds r21–r36 and the Code
TUI/web work, is committed LOCALLY on each repo's `main` and published nowhere. This item is the release sequence that
makes the pins resolve, the per-package inventory of what is unpublished, and the gates. Release record of the wave
goes to `completed/` when it closes, follow-ups as items.

## Why

The live gateway runs these commits from editable checkouts (restarted 13:30 on runtime `da03304`, gateway `2a68b105`,
memory `e74c29c`, voice `14a628c`); a clean `pip install abstractframework` still gets root 0.13.0's matrix. Until the
wave ships, an install and the operator's machine run different frameworks.

## Order (by the real dependency edges)

> Superseded 2026-11-09 by "Release matrix (draft 2026-11-09)" below: Core, Avatar, Agent, Skill, AbstractUIC,
> AbstractTUI, Observer, Flow and the Assistant web app join the wave, and the memory → runtime edge is weaker than
> stated here (the hard memory edge is the gateway's). Kept as the 2026-11-08 record.

1. **abstractmemory** (from 0.4.0): runtime requires `AbstractMemory>=0.4.0` (`abstractruntime/pyproject.toml`) and
   gateway `AbstractMemory[lancedb]>=0.4.0`; `open_home(task_queue=True)` and the gateway's
   `MemorySystem(task_queue=True)` need 0059/0060, and each repo's CI installs the previous package from PyPI. So
   memory publishes first and both floors rise to it.
2. **abstractruntime** (from 0.18.4; floor on the new memory) — in parallel with **abstractvoice** (from 0.20.1; no
   edge to memory or runtime).
3. **abstractgateway** (pyproject already 0.21.0; floors on the new runtime, memory and voice; the runtime floor equals
   `live_deltas.ABSTRACTRUNTIME_FLOOR`, a test keeps them equal).
4. **Apps**: abstractentity (from 0.11.2), abstractcode web and TUI.
5. **Root** `abstractframework`: `==` pins of the validated matrix, published only after the operator validates that
   exact matrix (ADR 0051).

The order relayed with the pause was "runtime → memory → voice → gateway"; the code puts memory before runtime (the
edge above). Confirm with the operator before the first cut.

## Unpublished on main (2026-11-08 15:00 Paris; counted with `git rev-list --count <last tag>..main`)

| Package | Last tag | Commits since | Load-bearing commits |
|---|---|---|---|
| abstractmemory | v0.4.0 | 9 | 0059 `3fbaf10`, 0060 `5997b68`, 0061 `09686e0`, no stored-text caps `8ac6df4` / `566f174`, card lessons `cc1ed75`, read-time provenance `e74c29c` |
| abstractruntime | v0.18.4 | 41 | cognition profile `1468f965` + `376cd6e`, restored look-back `e53ee30`, tool results whole as home artifacts `d217d93` (1145), unreachable endpoint parks the step `15e4a01` / `da03304` / `ed7d605` (1168), stored text whole `27beba0` / `79e0379` / `d419ec1` |
| abstractvoice | v0.20.1 | 14 | read-aloud repair `0d1ce0a`, `abec249`, `88e0f11`, `14a628c`, docs `94eb777` (`untracked/tts-failure-2026-11-08/REPORT.md`); round-18 spoken language and clone retry |
| abstractgateway | v0.20.2 | 80 | cognition-profile route `c7c9bc70` / `56aa6219` / `3b42be73`, stored understanding `1b3832b7` / `fa75c70a` / `79f47c5b`, capability clients `5df15719`, session kinds `514d6175` (1166), entity artifacts `d1d9656f` (1145) |
| abstractentity | v0.11.2 | 74 | rounds r21–r36 `58de504` … `f7967fb` (20 commits, incl. Settings → Mind `4f5a975` / `60770af`) |
| abstractcode | web-v0.15.6 | 36 | Code TUI `dcbd5ce`; web 0.15.17–0.15.19 (local builds) |
| root | v0.13.0 | 36 | pyproject at 0.13.1, no `v0.13.1` tag (held); pins today gateway 0.20.2, runtime 0.18.2, memory 0.4.0, voice 0.20.1 |

The understanding drain ([1171](understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md)) is not on
main yet; the operator decides whether the wave waits for it or ships without it (gateway main already opens homes
with `task_queue=True`, so tasks queue up until the drain lands).

## Scope

### In scope

- The sequence above, version bumps, CHANGELOGs, coredoc + llms regeneration per package, floors with the
  install-profile pin tests, registry visibility checks, the root clean-venv install.
- Release mechanics per repo: root and gateway publish on an annotated tag on `main`; AbstractRuntime only through
  `workflow_dispatch` on `main` (its PyPI environment rejects tags); wait for each PyPI listing before the next push.

### Out of scope

New features mid-wave (no base-package change during the candidate test); the website (gated, the operator publishes).

## Acceptance criteria

- [ ] The operator's explicit go for this wave, then for each publish.
- [ ] Per repo: `scripts/ci_local.sh` green before any push (ADR 0050); an adversarial review with real screenshots for
      every UI change; no red-by-design PR.
- [ ] Local redeploy of the exact candidate matrix and the operator's user tests (a user-level test list handed over)
      before any publish; the operator says "satisfied".
- [ ] Every package visible on its registry at its version; floors raised with pin tests; root published last with
      `==` pins of the validated matrix; `pip install abstractframework` in a clean venv passes.
- [ ] Release record in `completed/` with tags → commits and the registry check; follow-ups filed as items.

## Testing

- `./scripts/status.sh` (every repo on main, clean, 0 ahead / 0 behind after the pushes)
- `./scripts/build.sh`
- `scripts/ci_local.sh` (each repo)

## Release matrix (draft 2026-11-09)

Read-only audit, observed 2026-11-09 13:17 Paris. Sources: every repo's `main` HEAD and manifests, local and remote
tags (`git ls-remote`), PyPI JSON, `npm view`, the crates.io API, the release workflows and the publishing
environments' deployment policies (`gh api`), and the planner (`abstract_release_plan.py --registry --backlog`).
"Unpushed" counts compare with the CACHED `origin/main` (nothing was fetched). Other sessions were committing during
the audit (Code `1d9c652` 13:13, Entity `e3d6739` / `d4b582e` 13:14, Flow `95bb1d0`, Agent `c83f4d0`): re-run the
planner before the first cut. Codex finish review §C (`untracked/finish-plan-2026-11-09/CODEX-PLAN.md`) was checked
claim by claim (table at the end).

Local gate for every row: root `scripts/ci_local.sh <repo> --tier full --release-tag <tag>` (no package repo has its
own copy; the gate tests committed refs only, from a clone).

### Packages in the wave

| Package (registry) | Manifest now | Published | Since last tag | Proposed | Why this number | Trigger (env policy) |
|---|---|---|---|---|---|---|
| abstractavatar crate + Python (crates.io, PyPI) | 0.2.0 (`Cargo.toml`, `pyproject.toml`) | 0.1.1 / 0.1.1 | 12 since v0.1.1 (8 unpushed): 17 designs retired with a resolve fallback, seven ready designs, `retired()` / `resolve_style` | **0.2.0** | pending number; new API | crate: local `cargo publish` from tag v0.2.0 (no workflow); Python: tag v0.2.0 or dispatch `-f version -f publish=true -f publish_confirmation` (`pypi`: no policy) |
| abstractvoice (PyPI) | 0.20.1 (`_version.py`) | 0.20.1 | 14 (all unpushed): read-aloud repair (Markdown read as words, Qwen3-TTS end of speech, runaway guard), round-18 spoken language (`abstractvoice.stt.languages`, `transcribe_detailed`, `language=None` = auto), clone retry | **0.21.0** | new public module and API | tag v0.21.0 or dispatch `-f version` (main, `v*.*.*`) |
| AbstractMemory (PyPI) | 0.4.0 | 0.4.0 | 12 (10 unpushed): 0059 understanding versions, 0060 task queue, 0061 ripple, stored text whole, read-time provenance, diary lessons on the card, `retitle`, `rekey_world_model` | **0.5.0** | new public types (`UnderstandingVersion`, `MemorySystem(task_queue=)`) | tag v0.5.0 (main, `v*.*.*`) |
| abstractskill (PyPI) | 0.3.11 | 0.3.10 | 1: bundles the abstractcore skill (root 1180) | **0.3.11** | pending number | tag v0.3.11 (main, `v*`) |
| @abstractframework/ui-kit + panel-chat (npm; AbstractUIC tag) | ui-kit 0.9.26, panel-chat 0.9.9, root `package.json` 0.10.17 | 0.9.19 / 0.9.1 (last tag v0.10.8) | ui-kit 13, panel-chat 17 (31 repo commits unpushed): `IterationLimitField`, read-aloud player fixes, `EntityCard attention="marker"`, @ mentions and "who answered", reconnects; app-server and monitor-* unchanged | **ui-kit 0.9.26, panel-chat 0.9.9, tag v0.10.17** | pending numbers; additive exports. The kit stays on 0.9.x patches: every app pins `^0.9.x`, a 0.10.0 would fall outside every range | tag v0.10.17 (npm: main, `v*`) |
| abstracttui (+ graph, mermaid) (crates.io) | 0.7.1; graph/mermaid 0.6.0 | 0.7.1; 0.6.0 | 9 (5 unpushed): @ mention chips, chat row author, modal pointer defaults, ready avatar designs | **0.8.0; graph 0.7.0, mermaid 0.7.0** | `ChatMessage` gained the public field `authored_by` (b06ba9a): struct literals break, a minor in 0.x. The extensions are workspace members with `abstracttui = { version = "0.7", path = "../.." }`: at 0.8.0 the workspace stops resolving until they say "0.8", and a new dependency needs new versions (precedent `c287eb3` at 0.7.0) | tag v0.8.0 or dispatch `-f publish=true`; `publish-family` publishes graph then mermaid (`crates-io`: no policy) |
| abstractcore (+ console crate) (PyPI, crates.io, GHCR) | 2.35.0 (`utils/version.py`); console 0.8.1 | 2.34.0; console 0.8.1 | 18 (all pushed): 2.35.0 capability lineups, round-18 transcription language facts, `EndpointUnreachableError` (503 envelope, pickling), MCP handshake for strict servers, embeddings residency race, tool parameter descriptions; 3 fragments in `changelog.d/` | **2.35.0** (0884 says 2.35.1) | 2.35.0 was bumped on main (`e4e1a6f3`, CHANGELOG `[2.35.0] - 2026-11-07`) but never tagged, released or published (no v2.35.0 tag local or remote, no release run, PyPI latest 2.34.0). A new public exception type is a minor over 2.34.0; 0884's 2.35.1 assumes 2.35.0 shipped. Console unchanged | tag v2.35.0 (main, `v*.*.*`) |
| AbstractRuntime (PyPI) | 0.18.4 | 0.18.4 | 50 (all unpushed): cognition profile, restored look-back, own time, stored text whole (ADR 0054), tool results as home artifacts (1145), visit attachments, unreachable endpoint parks the step (1168), turn authors, `repeat_of`, skills readable (1180), iteration budget 50 (`DEFAULT_MAX_ITERATIONS`), visitor at the door (`4978eda`); 16 tracked fragments | **0.19.0** | new public modules and constants | dispatch: `gh workflow run release.yml --ref main -f version=0.19.0 -f publish=true -f publish_confirmation=publish-abstractruntime-0.19.0` (main, `v*.*.*`) |
| abstractagent (PyPI) | 0.6.0 | 0.6.0 | 2 (unpushed): defaults read the runtime's `DEFAULT_MAX_ITERATIONS` (50, was 20); a delegated sub-agent inherits its parent's limit exactly | **0.6.1** | default values, no type change (0.7.0 if the operator counts the new default as a minor) | tag v0.6.1 (main, `v*.*.*`) |
| abstractgateway (+ gateway-console crate) (PyPI, crates.io, GHCR) | 0.21.0 (`pyproject`, `__init__`, `app.py:133`); console 0.18.1 | 0.20.2; console 0.18.0 | 92 (all unpushed; 0.20.3 `1304f728` and the 0.21.0 candidate were never published): MTP backstop, keyless endpoints, key-destination rule, entity tile, Markdown e-mails, Tailscale HTTPS, cognition-profile route, stored understanding, visit attachments, session kinds (1166), entity artifacts (1145), @ mentions, iteration default 50, keep-awake setting, a visit never fails (`81a92233`); 16 fragments. Console: 7 commits | **0.21.0; console 0.18.1** | pending numbers | tag v0.21.0; release.yml also publishes the console when its version is new (main, `v*`) |
| @abstractframework/entity (npm) | 0.11.2 | 0.11.2 | 82 (55 unpushed): rounds r21–r36, Settings → Mind, ledger and graph rounds, mentions, phase bar (`9ec60aa`), visit lane (`e07f930`), Stop always available (`e3d6739`), world cards from provenance (`d4b582e`) | **0.12.0** | new screens and controls | tag v0.12.0 (npm: no policy) |
| @abstractframework/code (npm, `web/`) | 0.15.21 | 0.15.6 | 37 touching `web/` (0.15.7–0.15.21 were local builds): Stop rounds, reconnect (1163), sidebar rows, mentions, Iteration limit, kit ranges `1d9c652` | **0.15.21** | pending number (Codex: keep). Features since 0.15.6 would justify 0.16.0; operator's call | tag `web-v0.15.21` (npm: main, `v*`, `web-v*`) |
| abstractcode crate (crates.io, `tui/`) | 0.14.0 | 0.14.0 | 6 touching `tui/`: automation panels, @ mention chips and authors | **0.15.0** | new features on abstracttui 0.8.0 | tag v0.15.0 only (`crates-io`: tag `v*`; a dispatch is refused) |
| @abstractframework/assistant web (npm, `web/`) | 0.1.3 | 0.1.3 | 3 touching `web/`: @ mentions + who answered, automation titles whole | **0.2.0** | new feature | tag `web-v0.2.0` (npm: tag `web-v*` only) |
| @abstractframework/observer (npm) | 0.13.0 | 0.12.4 | 12 (unpushed): Board redesign and review fixes, kit entity cards | **0.13.0** | pending number | tag v0.13.0 (npm: main, `v*`) |
| @abstractframework/flow (npm) | 0.14.1 | 0.14.1 | 1 (`95bb1d0`, today 13:09): agent iteration default 50 from one constant | **0.14.2** | default value | tag v0.14.2 or dispatch `-f version` (npm: main, `v*`) |
| abstractframework root (PyPI) | 0.13.1 (never published; draft PR #74 "HOLD", stale PR #70 release/0.12.1) | 0.13.0 | 46 | **0.14.0** | a new minor matrix | tag v0.14.0 after the operator's GO (main, `v*`) |

Not released (no source change since the last tag): abstractvision (1 backlog commit), abstractsemantics (harness
cleanup and research docs), abstractnote (1 backlog commit), abstractmusic, abstractcamera, abstract3d,
@abstractframework/continuum, @abstractframework/note, app-server and monitor-*, abstractcore-console, and
abstractassistant's Python package, iPhone and watch lanes (only `web/` and backlog changed since v0.18.3).

### Floors that must move

| Dependent (where) | Now | Becomes | Kind | Evidence |
|---|---|---|---|---|
| abstractcore `pyproject.toml` | `abstractvoice>=0.20.0` (+ `[apple]`, `[gpu]`) | `>=0.21.0` | recommended (Core is cut anyway) | 2.35.0's transcription language facts call voice's `transcribe_detailed` (`capabilities/registry.py:1562`, getattr fallback: older voice works and reports `detected_language: None`); it also lets the gateway raise its own voice floor (gateway test line 108) |
| AbstractRuntime `pyproject.toml` | `abstractcore>=2.34.0` (+ `[apple]`, `[gpu]`) | `>=2.35.0` | HARD | `integrations/abstractcore/effect_handlers.py:38` imports `EndpointUnreachableError` by name (no fallback by design, root 1168); the class is absent from v2.34.0 (added `44897db3`). Runtime main does not import against any published Core |
| AbstractRuntime | `AbstractMemory>=0.4.0` | `>=0.5.0` | recommended | tracked runtime code calls no new memory API (retitle, rekey, task_queue, `UnderstandingVersion`: 0 hits); only the untracked drain needs `task_queue`. Memory publishes first, so the raise is free |
| abstractagent `pyproject.toml` | `abstractruntime>=0.17.0` (+ `[apple]`, `[gpu]`) | `>=0.19.0` | HARD | `69a6014` imports `abstractruntime.core.vars.DEFAULT_MAX_ITERATIONS` (absent from 0.18.4) |
| abstractgateway `pyproject.toml` ×3 + `live_deltas.py:122` `ABSTRACTRUNTIME_FLOOR` | `AbstractRuntime>=0.18.1` | `0.19.0` everywhere | HARD | `runtime_config.py:1702` imports `DEFAULT_MAX_ITERATIONS` at module load; `entity_cognition_profile.py:74` imports `identity.cognition_profile` |
| abstractgateway | `AbstractMemory[lancedb]>=0.4.0`, `[all-apple]`, `[all-gpu]` | `>=0.5.0` | HARD | `entities.py:378` `MemorySystem(..., task_queue=True)`: 0.4.0's constructor has no `task_queue` (TypeError) |
| abstractgateway | `abstractcore>=2.34.0`, `abstractcore[embeddings]>=2.34.0` | `>=2.35.0` | HARD (test) | `tests/test_gateway_install_profiles.py:86`: the runtime's core floor must not exceed the gateway's |
| abstractgateway | `abstractavatar>=0.1.1` | `>=0.2.0` | HARD for the feature | `b8dff9ee`: identity looks call `abstractavatar.retired()` / `resolve_style`; on 0.1.1 the listing answers 503 "too old" and those tests fail in CI (it installs from PyPI) |
| abstractgateway | `abstractagent>=0.6.0` ×3 | `>=0.6.1` | recommended | the "50 everywhere" ruling: the gateway default (`b1a46871`) vs agent 0.6.0's copied 20 |
| abstractgateway | `abstractskill>=0.3.4` | `>=0.3.11` | recommended | root 1180: the abstractcore skill registered on a fresh install comes from skill 0.3.11's bundle |
| abstractgateway | `abstractvoice>=0.20.0` | `>=0.21.0` | optional, only with Core's raise | test line 108: Core's voice floor must be at least the gateway's |
| `tests/test_gateway_install_profiles.py` | literals at lines 50–54, 149, 159–169 | follow every row above, same commit | HARD | they pin the floors as strings |
| abstracttui `Cargo.toml` | `abstractavatar = "0.1.0"` (optional) | stay `^0.1`, or `0.2` | decision | `d742fce`: on 0.2 a test fails until the fixed allowlist is deleted (a code change) |
| abstractcode `Cargo.toml:13–17`, `tui/Cargo.toml:114` | TEMP `[patch.crates-io] abstracttui = { path = "../abstracttui" }`; `abstracttui = "0.7.1"` | patch removed; `"0.8.0"`; `Cargo.lock` relocked | HARD | the TEMP comment says "remove at release" |
| abstractcore-console, abstractgateway-console | `abstracttui = "0.7.1"` | unchanged | none | not affected; each keeps one abstracttui |

### Lockfiles and vendored copies

| Where | Declares now | Lock now | Built and deployed on | At release |
|---|---|---|---|---|
| Code web `web/package.json:51–52` | ui-kit `^0.9.26`, panel-chat `^0.9.9` (`1d9c652`, today) | ui-kit 0.9.19, panel-chat 0.9.1 (`web/package-lock.json:84`) | node_modules 0.9.26 / 0.9.9 | relock after the UIC publish (`check:lock` red until then; a clean `npm ci` cannot build: `settings_panel.tsx:3` imports `IterationLimitField`); re-sync `src/vendor/abstractchat` from the PUBLISHED panel-chat tarball (hash file in the folder) |
| Entity `package.json:50`, `:55` | panel-chat `file:vendor/abstractframework-panel-chat-0.9.9.tgz` + `bundleDependencies`; ui-kit `^0.9.16` | 0.9.16 / file: | 0.9.26 / 0.9.9 | panel-chat `^0.9.9`, drop `bundleDependencies` and `vendor/`, ui-kit `^0.9.26` (lock = what was tested), relock |
| Assistant web `web/package.json:62–63` | panel-chat `^0.8.2` (excludes every 0.9.x), ui-kit `^0.9.16` | 0.8.2 / 0.9.16 | 0.9.9 / 0.9.25 | `^0.9.9` / `^0.9.26`, relock; re-sync `src/vendor/abstractchat` from the published tarball (today from UIC `aab7240`, the same hashes as Code's copy) |
| Observer `package.json:48–49` | panel-chat `^0.8.2`, ui-kit `^0.9.18` | 0.8.2 / 0.9.19 | 0.9.9 / 0.9.26 | ui-kit `^0.9.26` (`mission_control.tsx:1456` passes `attention="marker"`, ui-kit ≥ 0.9.25), relock |
| Flow | panel-chat `^0.8.1`, ui-kit `^0.9.19` | 0.8.1 / 0.9.19 | 0.9.9 / 0.9.26 | uses no newer kit export; releases from its lock as is (decision: relock or not) |
| AbstractUIC root `package-lock.json` | — | ui-kit entry 0.9.25 → 0.9.26 UNCOMMITTED | — | commit it in the release PR |
| Gateway console islands `console_islands.py:16` | `kit_version` 0.9.19 | published | — | unchanged (no newer kit export used) |

Several different local packs carry the same numbers: panel-chat 0.9.9 was packed at `2e6738e` and again after
`aab7240` (mentions) without a bump; ui-kit 0.9.26 at `0b8c1f8` and changed again at `4cc6fa9`. Publishing those
numbers is legal (neither is on npm), but every consumer must be relocked from the registry and every vendored copy
re-hashed against the published tarball; 0.9.27 / 0.9.10 would retire the ambiguity (operator's call).

### Sequence

0. **Before any cut:** the confirmations below answered; the scope sweep on the record for each base package (the
   planner lists planned items: Core 65, Runtime 72, Gateway 87, Voice 29, Memory 16); every dependent DRAFTED locally
   with its floor, lock and pin-test change (branches stay local until the floor is visible, ADR 0050).
1. **Tier 0, in parallel (no edges between them):** abstractavatar crate 0.2.0 then its Python package 0.2.0;
   abstractvoice 0.21.0; AbstractMemory 0.5.0; abstractskill 0.3.11; AbstractUIC v0.10.17 (ui-kit 0.9.26, panel-chat
   0.9.9); abstracttui 0.8.0 with graph 0.7.0 and mermaid 0.7.0.
2. **abstractcore 2.35.0**, voice floor 0.21.0 (after voice is visible).
3. **AbstractRuntime 0.19.0**, core ≥ 2.35.0 and memory ≥ 0.5.0 (after both are visible).
4. **abstractagent 0.6.1**, runtime ≥ 0.19.0.
5. **abstractgateway 0.21.0** with gateway-console 0.18.1: runtime, memory, core, agent, avatar, skill (and voice)
   floors, `ABSTRACTRUNTIME_FLOOR` and the pin tests in one commit, after all of them are visible.
6. **Apps, in parallel**, after AbstractUIC is visible and the gateway is published (no registry edge to the gateway,
   but they call its 0.21.0 routes): Entity 0.12.0, Code web 0.15.21, Code crate 0.15.0 (after abstracttui 0.8.0),
   Assistant web 0.2.0, Observer 0.13.0, Flow 0.14.2.
7. **Candidate, then the operator:** everything above published and visible, the stack redeployed locally at exactly
   these versions, the website rebuilt locally, the change report; the operator's user test and GO; then root 0.14.0.

### Root 0.14.0 `==` pins (proposed)

- Python: abstractgateway 0.21.0, abstractassistant 0.18.3 (latest published; main still pins 0.18.1), abstractcore
  2.35.0, AbstractRuntime 0.19.0, abstractagent 0.6.1, abstractskill 0.3.11, AbstractMemory 0.5.0, abstractsemantics
  0.0.5, abstractvoice 0.21.0, abstractvision 0.3.34, abstractmusic 0.1.17, abstract3d 0.3.2, abstractcamera 0.2.1,
  abstractavatar 0.2.0, abstractnote 0.3.1; `[apple]` / `[gpu]`: gateway 0.21.0, assistant 0.18.3.
- `NPM_RELEASE_VERSIONS`: flow 0.14.2, code 0.15.21, observer 0.13.0, continuum 0.8.1, entity 0.12.0, note 0.3.1.
  `NPM_LIBRARY_RELEASE_VERSIONS`: app-server 0.1.13, ui-kit 0.9.26, panel-chat 0.9.9, monitor-active-memory 0.2.2,
  monitor-flow / gpu / memory 0.1.10. The Assistant web app is in neither list nor in `scripts/lib/packages.txt`
  (planner inventory gap).
- `CRATE_RELEASE_VERSIONS`: abstractgateway-console 0.18.1, abstractcore-console 0.8.1, abstractcode 0.15.0,
  abstracttui 0.8.0, abstractavatar 0.2.0, abstracttui-graph 0.7.0, abstracttui-mermaid 0.7.0.
- With them: `RELEASE_VERSIONS`, `docs/installers/install-manifest.json`, `scripts/install.sh` / `install.ps1`, the
  install docs, `scripts/tests/test_inventory.sh`.

### Gates per step

- Before each cut: the local gate above green; an adversarial review (real screenshots for UI); real weights or a real
  gateway for engines and routes; one dated changelog section per version (Core and Gateway: `scripts/changelog.py
  assemble` over their fragments; Code's 15 unpublished `web 0.15.7`–`0.15.21` sections, Observer's "Unreleased (local build)" and UIC's
  0.10.9–0.10.17 folded); llms files regenerated; local redeploy, the operator's user test and his explicit go.
- After each publish: the release run green, then `pypi_visibility_gate.py --wait 900 <spec>` before any dependent
  raises its floor; then the dependent's gate again (it installs the new floor from the registry).
- Root: only after the candidate and the operator's GO; a clean-venv `pip install abstractframework` passes; until
  then the installer still resolves root 0.13.0's matrix.

### Blockers

1. **Runtime main cannot import against any published Core** (`EndpointUnreachableError`): Core 2.35.0 (or 2.35.1)
   must be published first. AbstractCore backlog 0884's version number is wrong (see the Core row).
2. **Gateway main needs four unpublished packages:** memory 0.5.0 (`task_queue`), runtime 0.19.0
   (`DEFAULT_MAX_ITERATIONS`, cognition profile), Core 2.35.0 (test line 86), avatar 0.2.0 (identity looks). Agent main
   needs runtime 0.19.0.
3. **Entity's phase bar has no backend.** Entity main calls `PUT /entities/{name}/life_state/toggles` and
   `POST /entities/{name}/lifecycle` (`phase_bar_source.ts`), which gateway main does not serve, and no longer calls
   `loop/start` / `loop/stop`. Shipped on gateway 0.21.0 as is, every phase control is off. Either the phase backend
   lands in Runtime and Gateway before their cuts (Codex: finish the phase change before cutting Runtime) or the
   phase bar waits. This scope decision comes before step 3.
4. **Lockfiles name versions the builds do not use** (table above): Code web cannot build from its lock; Assistant
   web's range excludes panel-chat 0.9.x; Entity installs panel-chat from a tarball; UIC's lock change is uncommitted.
5. **Code's TEMP crates.io patch and abstracttui's extensions** (`Cargo.toml:13–17`; extension path dependencies on
   "0.7").
6. **The paused drain in AbstractRuntime must stay out:** `identity/understanding.py`,
   `tests/test_understanding_drain.py` and `changelog.d/understanding-drain.md` are untracked and not ignored. CI
   release runs and `ci_local.sh` use committed refs only, and no tracked file imports the drain, so they stay out
   there. Three local paths pull them in: `scripts/changelog.py assemble` reads `changelog.d/` from disk
   (`rglob`), so run in this checkout it would fold the drain's entry into 0.19.0 and DELETE the untracked file; a
   local `python -m build` / `pip wheel .` (hatchling, `packages = ["src/abstractruntime"]`, untracked files
   included) would ship `understanding.py`; a local `pytest` collects the drain's test. Assemble and build only in a
   clean clone of the committed ref.
7. **Nothing of this wave is on GitHub yet** in Voice, Memory, Runtime, Gateway, Entity, Code, UIC, TUI, Observer,
   Agent, Avatar, Skill, Assistant, Flow (cached counts above): every repo goes through its PR and gate before a tag.

### Open confirmations (needs the operator)

1. **Commits on `main` not from the main two sessions, needs operator confirmation to ship:** AbstractRuntime
   `4978eda`, AbstractGateway `81a92233`, AbstractEntity `e07f930` ("a visit never fails", all 2026-11-09 12:11:28,
   root [1184](../completed/1184_a_visit_never_fails_on_a_busy_entity.md) "OPERATOR REVIEW PENDING"). Landed during
   this audit, session not established from git: AbstractFlow `95bb1d0` (13:09) and AbstractAgent `c83f4d0` (13:11);
   Code `1d9c652` and Entity `e3d6739` / `d4b582e` (13:13–13:14) follow the Codex finish plan.
2. Core 2.35.0 (recommended: the pending, never-published number) or 2.35.1 (0884).
3. Scope: the phase backend (blocker 3); the drain (1171) stays out; Codex A.2's regex title fallback
   (`identity/reflection.py:328`, `identity/digest.py:47`) ships as is or is replaced first.
4. Kit numbers: 0.9.26 / 0.9.9 as pending, or 0.9.27 / 0.9.10.
5. abstracttui on abstractavatar `^0.1` (no change) or `0.2` (allowlist deleted first).
6. Core's voice floor to 0.21.0 (recommended), which allows the gateway's.
7. Root 0.14.0 instead of the never-published 0.13.1; close draft PR #74 and stale PR #70; add the Assistant web app
   to the root npm lists and `packages.txt`, or not.

### Codex §C, verified

| Claim | Verdict |
|---|---|
| Runtime imports `EndpointUnreachableError` directly; Core release needed | TRUE (`effect_handlers.py:38`); but 2.35.0 itself was never published, so "2.35.1" is not required |
| Voice → Core; Memory independent | TRUE only if Core raises its voice floor (recommended); Core's code tolerates the old voice |
| Memory 0.5.0, Runtime 0.19.0, Voice 0.21.0, Entity 0.12.0, Code TUI 0.15.0 | AGREED |
| AbstractTUI 0.8.0 for `b06ba9a`'s public-struct change | TRUE (`ChatMessage.authored_by`); MISSED: graph and mermaid must move to 0.7.0 |
| Gateway 0.21.0, panel-chat 0.9.9, UI-kit 0.9.26, Code web 0.15.21 unpublished | TRUE (registries checked); same-version local packs differ |
| Code web locks UI-kit 0.9.19 but imports `IterationLimitField` | TRUE (`package-lock.json:84`); ranges raised since (`1d9c652`), lock not yet |
| Entity bundles an unpublished panel-chat tarball | TRUE, plus `bundleDependencies` (`package.json:55`) |
| Code TEMP patch, 0.7.1 → 0.8.0 | TRUE (`Cargo.toml:13–17`, `tui/Cargo.toml:114`) |
| Raising the gateway's voice floor alone fails test line 108 | TRUE; line 86 likewise forces the gateway's Core floor to follow the runtime's |
| Not in §C | Avatar 0.2.0, Agent 0.6.1, Skill 0.3.11, Observer 0.13.0, Flow 0.14.2, Assistant web 0.2.0 and gateway-console 0.18.1 belong to the wave; the Entity phase bar has no gateway route |

## Receipts

- Release mechanics: the `abstract-release` and `release` skills; previous record [1132](../completed/1132_final_stable_release.md).
- Track: [understanding-pass](understanding-pass/README.md).
