# 1179 — Release wave: the understanding pass and the other local commits of 2026-11-07/08

> Package: AbstractMemory, AbstractRuntime, AbstractVoice, AbstractGateway, AbstractEntity, AbstractCode (web + TUI), AbstractFramework (root pins)
> Type: task
> Status: planned — in preparation (development resumed 2026-11-09 13:10; every publish waits for the operator's explicit go; refresh 2026-11-10)
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

## Refresh 2026-11-10 (supersedes the 2026-11-09 draft on the points below)

Hygiene pass of 2026-11-10, built on the read-only audit `untracked/release-2026-11-07/audit-fable/PACKAGES.md`
(observed 2026-11-09 19:10–19:38; its section (e) lists where the code contradicts the draft), the running log
`untracked/release-2026-11-07/RESUME.md` (entries to 2026-11-10 00:25) and `ROADMAP-2026-11-09-2010.md` (sections
F–H), each commit checked against its repo's log at about 00:05 on 2026-11-10. The sections above stay as the
2026-11-09 record; where they disagree with this section, this section wins. The room was still committing while this
was written (runtime `5ee8049` at 00:01, agent `5052f8a` at 23:59): re-run the planner
(`abstract_release_plan.py --registry --backlog`) before the first cut. Status line refreshed: development resumed on
2026-11-09 13:10 ("do your best to finish the current work"), so the 2026-11-08 pause no longer holds; every publish
still waits for the operator's explicit go.

### What changed since the draft

| Draft said (2026-11-09 13:17) | Now | Evidence |
|---|---|---|
| Runtime → Memory floor "recommended" (no new memory API in tracked runtime code) | **HARD**, and the floor is now memory **`4074406`** or later | runtime `4eefddb` (16:23) calls `task_queue=True` and the authoring verbs (`declare_pending`, `retitle`, `rewrite_digest`); since the Stop fence, runtime `098cd4b` passes the fence to memory's `commit_guard` (memory `4074406`, 23:10). Memory 0.5.0 must contain `4074406` |
| Blocker 3: Entity's phase bar has no backend | **closed in code** | gateway `GET /{name}/life_state`, `PUT /{name}/life_state/toggles`, `POST /{name}/lifecycle` (`routes/entities.py`, contract v3: gateway `8681a9be`, Entity `0848c19`, spec v25); the operator tested the live stack on 2026-11-09 evening; his findings were fixed in the app (Entity `b2d6207`, `a35e8f1`, `2c9a7ba`) and in runtime `b6d50d3` / gateway `5c2f5db7`, `26101378` |
| Blocker 6: the paused drain is untracked inside the runtime tree | **gone** | runtime `git status` clean; a different, tracked drain (`identity/authoring.py` `drain_authoring`) ships and the gateway imports it (`entity_authoring.py:33`, gateway `a749e4e5`); 1171 carries the note |
| Kit 0.9.26 / 0.9.9 (or 0.9.27 / 0.9.10) | **ui-kit 0.9.27, panel-chat 0.9.11** | AbstractUIC `7d557cd` (22:37) committed ui-kit 0.9.27 / panel-chat 0.9.10 / root `package.json` 0.10.18 and relocked; then `4bee00d` (23:28, reply notices as badges) changed panel-chat after its bump, so panel-chat ships as **0.9.11** (bump not committed yet; ui-kit unchanged by `4bee00d`). No AbstractUIC tag exists past v0.10.8; tag the cut that carries 0.9.11 |
| Core 2.35.0 after voice is visible, voice floor 0.21.0 | **Core first and alone**, voice floor stays `>=0.20.0` | ROADMAP F/H D3 (R1: published 2.34.0 quarantines valid configs and runs on defaults; 187 copies on this machine) |
| Memory in tier 0 | **Memory only after the Stop decision** | the fence touches `MemorySystem` (`4074406`); ROADMAP H D1 |
| Apps after AbstractUIC is visible | **Apps after the gateway is visible** | their phase bar and mentions call 0.21.0 routes; publishing earlier breaks npx users (ROADMAP F step 6, G S2) |

### Candidates and fences (heads as observed 2026-11-10 ~00:05)

| Package | Candidate | State | Gate / open |
|---|---|---|---|
| abstractcore 2.35.0 | **`8b970550`** (pushed) | `7fe2aeaf` … `fe145749` config loader, then the operator's 22:15 decision ("NO quarantine logic at all"): `6c79e36b` an unparseable settings file stops the load with its path and error, `2084b646` the server refuses to start on it; `fdb5eeb3` console theme copy from ui-kit 0.9.27 (`KIT_THEME_FLOOR` 0.9.27: a vendored copy with a provenance test, `tests/test_console_web.py:183-190`, not a registry edge); `8b970550` fragments restored (5 in `changelog.d/`) | local gate green on `8b970550` (RESUME 23:40); cut = one changelog-assemble commit (no source), then tag `v2.35.0`; waits for the operator's go |
| abstractvoice 0.21.0 | **`2b98d1e`** (pushed) | `26b5d8d` release prep (version, changelog, docs, llms), `721d31f` `aec-audio-processing` on macOS and Windows only (no Linux wheel; the `[gpu]` install failed on Ubuntu), `2b98d1e` `transformers<5.21` on the platform profiles and the `qwen3-tts` extra | local gate green (RESUME 23:15); tag waits for the operator's go. Next release: [voice backlog 0069](../../../abstractvoice/docs/backlog/proposed/0069_port_qwen3_tts_speech_tokenizer_to_transformers_5_21_mimi.md) (port the vendored Qwen3-TTS tokenizer to the 5.21 Mimi split). Open with the operator: the `[gpu]` profile runs Supertonic/Piper on CPU on NVIDIA |
| Stop fence, runtime half | `66d3220` (fence primitive, required on every state writer), `86666af` (spawn reservation, boot refusal, fenced night), `098cd4b` (`open_home(fence=)`: memory `commit_guard`, diary, artifacts, effect table), `2c9b673` (`ChatSession.fence`); Fable review fixes `1573f8e` (F1), `0b7b9b5` (F2), `5ee8049` (F3) | built, not live | 36 tests, 47 mutants red, suite 4831 passed at `2c9b673` (RESUME 23:55); Fable review `untracked/entity-phases-2026-11-08/review/FABLE-REVIEW-fence-runtime.md` |
| Stop fence, memory half | `4074406` `commit_guard` (one integer compare before every COMMIT) | built | sets the runtime's memory floor |
| Stop fence, gateway half | in progress (W-gwfence: the 11 runtime signatures, Codex gateway-3 F2/F4/F5/F8/F12 and F3/F6/F7/F9) | **not landed** | **no gateway restart until it lands** (RESUME 23:55, 00:15). Already on gateway main: `34674984` (a Stop during a sleep's final stage records no completed night), `3be0f167` (idle sleep admitted atomically, one home per sweep), `dea1bcba` (only a full pass is the last maintenance) |
| abstractagent 0.6.1 | 5 commits since v0.6.0, two new tonight: `ff1c4d1` (the agent stays out of a message addressed to entities, with gateway `c26d38a2`), `5052f8a` (tests open the home with its fence) | built | runtime `>=0.19.0` stays HARD (the tests need `open_entity_runtime(fence=)`) |

Decisions the operator made after the draft and that are built (scope IN): fresh-install iteration limit 50 seeded once
(gateway `fa8286e2`, D2); a gateway restart is not a Stop, own time resumes where the grant is armed (gateway
`dddc0726`, D5); helper servers live until the conversation ends (runtime `85a536b`, gateway `00481f64`); the session
agent stays silent for a message addressed to entities (gateway `c26d38a2`, agent `ff1c4d1`, runtime `f2d9628`);
reply notices beside the reply (runtime `09cbad7`, gateway `f1e730ab`, kit `4bee00d`, Entity `d666337`).

### Counts (since the last tag; "unpushed" = not on `origin/main`; counted 2026-11-10 ~00:05)

| Package | Draft | 2026-11-09 19:38 (PACKAGES (a)) | Now |
|---|---|---|---|
| AbstractMemory (v0.4.0) | 12 | 26 | 28 (26 unpushed) |
| AbstractRuntime (v0.18.4) | 50 | 94 | 108 at `5ee8049` (all unpushed); 67 changelog fragments |
| abstractgateway (v0.20.2) | 92 | 134 | 150 (all unpushed); 42 fragments |
| AbstractEntity (v0.11.2) | 82 | 90 | 96 (69 unpushed) |
| Code web (web-v0.15.6, `web/` only) | 37 | 40 | 41 |
| Assistant web (web-v0.1.3, `web/` only) | 3 | 5 | 8 |
| abstractagent (v0.6.0) | 2 | 3 | 5 (all unpushed) |
| AbstractUIC (v0.10.8) | 31 | 33 | 37 (all unpushed) |
| abstractcore (v2.34.0) | 18 | 20 | 25 (all pushed); 5 fragments |
| abstractvoice (v0.20.1) | 14 | 14 | 17 (all pushed) |
| abstractskill (v0.3.10) | 1 | 1 | 2 (both unpushed) |
| root (v0.13.0) | 46 | 55 | 56 + this pass |


### Floors that changed against the table above

- AbstractRuntime → AbstractMemory: **`>=0.5.0`, HARD**, and 0.5.0 must contain memory `4074406` (fence) — so memory
  is cut after the fence lands, never before.
- abstractgateway → AbstractMemory: `>=0.5.0`, HARD (unchanged), and 0.5.0 must contain `f310865` (`sleep_pass(…,
  cancelled=)`, used by gateway `34674984`) and `26503e3` (`records_since_maintenance(after=)`).
- abstractgateway → AbstractRuntime: `0.19.0` everywhere (unchanged); the gateway's new seams since the draft also
  include the fence signatures (pending) and `read_job_queue`, `TurnCancelled`, `home_state_lock`. The friendly
  `ABSTRACTRUNTIME_FLOOR` check cannot fire for 0.19.0 (`runtime_config.py:1702` imports `DEFAULT_MAX_ITERATIONS` at
  module load, so an old runtime fails with an ImportError first): make it lazy or accept it (ROADMAP G S4).
- abstractcore → abstractvoice: **stays `>=0.20.0`** (Core goes first and alone); the gateway's voice floor stays too.
- Root `main` pins lag even the published registry (runtime 0.18.2 vs 0.18.4, assistant 0.18.1 vs 0.18.3, Code
  0.15.1 vs 0.15.6; `abstractframework/__init__.py`): every pin moves at the root cut anyway.

### Sequence (replaces "Sequence" above)

0. **Scope freeze** (ROADMAP H D2) and the Stop decision (D1: wait for the fence, time-boxed to one day, or ship with
   the known gaps in the notes).
1. **abstractcore 2.35.0 alone, first** (`8b970550` + the changelog-assemble commit; voice floor stays 0.20.0).
2. **Tier 0 in parallel, one visibility wait:** abstractskill 0.3.11 (re-read the `entity-self-knowledge` skill first:
   it never mentions the v25 `idle` state), abstractvoice 0.21.0 (`2b98d1e`), AbstractUIC (ui-kit 0.9.27,
   panel-chat 0.9.11), abstracttui 0.8.0 with graph/mermaid 0.7.0, abstractavatar 0.2.0 (the operator's local
   `cargo publish` first), Flow 0.14.2.
3. **AbstractMemory 0.5.0 after the fence** (it must contain `4074406`).
4. **AbstractRuntime 0.19.0** (core `>=2.35.0`, memory `>=0.5.0`, both HARD).
5. **abstractagent 0.6.1** (runtime `>=0.19.0`).
6. **abstractgateway 0.21.0** + gateway-console 0.18.1, after the gateway fence half lands: runtime, memory, core,
   avatar (HARD), agent and skill (recommended) floors, `ABSTRACTRUNTIME_FLOOR` and the pin tests in one drafted
   commit.
7. **Apps after the gateway is visible:** Entity 0.12.0 (drop the `file:` tarball and `bundleDependencies`), Code web
   0.15.21 or 0.16.0 (D4), Code crate 0.15.0 (TEMP patch removed, abstracttui 0.8.0), Assistant web 0.2.0 (into the
   root npm inventory, D4), Observer 0.13.0; each relocked from the registry.
8. **Candidate:** the exact matrix redeployed locally, website preview, change report, the operator's user test and
   GO; then **root 0.14.0** (`NPM_LIBRARY_RELEASE_VERSIONS`: ui-kit 0.9.27, panel-chat 0.9.11).

### Records this wave closes (backlog state after the 2026-11-10 pass)

| Item | State | Where |
|---|---|---|
| [1180](../completed/1180_an_activated_skill_is_always_reachable_and_the_core_and_gateway_skills_ship_by_default.md) skills reachable | completed (built, unreleased) | runtime `b22c901` `08ebf18`, gateway `134b90a4`, skill `bf6b982` |
| [1145](../completed/1145_entity_activity_is_durable_in_the_runtime.md) steps 1–2 | completed; steps 3–4 → [1188](1188_the_entity_probes_its_own_runtime_and_personal_ticks_are_real_runtime_runs.md) (next release) | runtime `d217d93`, gateway `d1d9656f` |
| [1146](../completed/1146_understanding_pass_summaries_always_computed.md) authored titles and summaries | completed; the drain, ripple, extraction, private entries stay in 1171–1173 / 1186 | memory `c4ffc45`…`f310865` `8235daf`, runtime `4eefddb`…`432f178` `baa401f` `b6d50d3`, gateway `a749e4e5` `58b51667` `5c2f5db7` |
| [1162](../completed/1162_mcp_initialize_sends_null_capabilities_strict_servers_refuse.md) MCP `{}` handshake | completed | core `44897db3` |
| [1178](../completed/1178_stopping_personal_time_leaves_the_entity_awake_and_visitable.md) personal off ends awake | completed (decision never recorded on the item; superseded by the phase rulings) | runtime `3cafac9` |
| [1168](1168_an_unreachable_model_endpoint_parks_the_step_and_the_run_continues_when_it_is_back.md) endpoint park | planned (decision wait = next release); the park ships now | core `44897db3`…`b8bcda1d`, runtime `15e4a01` `da03304` `ed7d605` |
| [1184](../completed/1184_a_visit_never_fails_on_a_busy_entity.md) a visit never fails | completed, operator review pending (tested live 2026-11-09 evening) | runtime `4978eda`, gateway `81a92233`, entity `e07f930` |
| gateway 1166 session kinds | built; its file lives in `abstractgateway/docs/backlog/planned/` (not touched by this root pass) | gateway `514d6175` `e089fc05` `2a68b105`; client halves = [1170](1170_session_kinds_client_halves.md) (planned) |
| Code 1163 reconnect | built; its file lives in `abstractcode/docs/backlog/planned/` (not touched by this root pass); one residual (400 px status bar) | kit `d67570f` `c197daf` `ca5720d` (0.10.16) `2a230fe` `2e6738e` (0.10.17), Code `8aca634` `94b5ae1` (0.15.18) `3ffa584` `2a5c432` (0.15.19) |

Next wave (filed 2026-11-10, not in this cut): 1188, the inline-mentions composer, the whole-life access-count
gradient, the bundle builders' baked iteration limit with the START_SUBWORKFLOW ceiling, 1187, 1170, 1168's decision
wait, voice 0069.

## Publish log 2026-11-10

The record of what reached a registry. Each row was checked on its registry (PyPI JSON, the npm
registry, the crates.io API) and with `gh run view` at about 03:45 Paris; each tag points at the same
commit locally and on `origin`. Times are Paris (UTC+1). The sections above stay as they were.

### Published

| Package | Version | Tag (commit) | Release run | On its registry |
|---|---|---|---|---|
| abstractskill (PyPI) | 0.3.11 | `v0.3.11` (`628f329c`) | [42736585852](https://github.com/lpalbou/AbstractSkill/actions/runs/42736585852), green | 02:34 |
| @abstractframework/flow (npm) | 0.14.2 | `v0.14.2` (`94e112c2`) | [42736595131](https://github.com/lpalbou/AbstractFlow/actions/runs/42736595131), green | 02:37 |
| abstracttui, abstracttui-graph, abstracttui-mermaid (crates.io) | 0.8.0, 0.7.0, 0.7.0 | `v0.8.0` (`bd3a3973`) | [42736086771](https://github.com/lpalbou/AbstractTUI/actions/runs/42736086771), green | 02:32–02:33 |
| @abstractframework/panel-chat, @abstractframework/ui-kit (npm, AbstractUIC) | 0.9.11, 0.9.27 | `v0.10.19` (`39c1189c`) | [42738434319](https://github.com/lpalbou/AbstractUIC/actions/runs/42738434319), green | 02:54, 03:01 |

**Incident: AbstractTUI `main` is red.** The CI run of the `v0.8.0` commit on `main`
([42736083911](https://github.com/lpalbou/AbstractTUI/actions/runs/42736083911)) failed in one job,
`test (windows, lib only)`: three snapshot tests (`app::anchored::tests::mention::chat_panel_sends_text_and_mentions_in_order`,
`widgets::chat::author_tests::a_row_without_author_renders_exactly_as_before`,
`widgets::chat::author_tests::an_entity_row_shows_its_coloured_mark_name_and_kind`; panic at
`src\testing\snapshot.rs:65`). The other seven jobs and the release run are green and the crates
are published. A red `main` is an incident (ADR 0050): fixed or reverted in AbstractTUI, not in
this root pass.

### Pending, in the order of "Sequence" above

| Step | Package | Version in its manifest | On its registry now | Note |
|---|---|---|---|---|
| 1 | abstractcore | 2.35.0 | 2.34.0 | `main` is `7d48ce5d`, 6 commits past the cached `origin/main` (the refresh's candidate was `8b970550`) |
| 2 | abstractvoice | 0.21.0 | 0.20.1 | `main` is `38750f4`, pushed: the candidate moved from `2b98d1e` (12 commits since, among them the opt-in ONNX Runtime CUDA step and the standalone one-line installers `def3204`, `38750f4`) |
| 2 | abstractavatar crate, then Python | 0.2.0, 0.2.0 | 0.1.1, 0.1.1 | the operator's local `cargo publish` first |
| 3 | AbstractMemory | 0.5.0 | 0.4.0 | after the Stop fence; must contain `4074406` |
| 4 | AbstractRuntime | 0.19.0 | 0.18.4 | core `>=2.35.0` and memory `>=0.5.0`, both HARD |
| 5 | abstractagent | 0.6.1 | 0.6.0 | runtime `>=0.19.0` |
| 6 | abstractgateway, abstractgateway-console | 0.21.0, 0.18.1 | 0.20.2, 0.18.0 | after the gateway half of the fence |
| 7 | @abstractframework/entity | 0.12.0 | 0.11.2 | after the gateway is visible |
| 7 | @abstractframework/code (web), abstractcode (crate) | 0.15.21 (or 0.16.0, D4), 0.15.0 | 0.15.6, 0.14.0 | crate: TEMP patch removed, `abstracttui = "0.8.0"` (now on crates.io) |
| 7 | @abstractframework/assistant (web) | 0.2.0 | 0.1.3 | not in the root inventory (D4) |
| 7 | @abstractframework/observer | 0.13.0 | 0.12.4 | |
| 8 | abstractframework (root) | 0.14.0 | 0.13.0 | after the candidate and the operator's GO; the pin matrix with each pin's status: [docs/releases/0.14.0-pins-draft.md](../../releases/0.14.0-pins-draft.md) |

Heads are the local checkouts' `main` (not fetched); "cached `origin/main`" is the last fetched
tracking ref.

### Publish log refresh 2026-11-10 ~11:00 (credits at 10 %; handoff; supersedes "Pending" above where it differs)

Published since the table above, all registry-visible (`pypi_visibility_gate.py`): abstractcore 2.35.0 (`v2.35.0`),
abstractvoice 0.21.0 (`v0.21.0`), abstractvision 0.3.35 (`v0.3.35`, run 42752091749), AbstractMemory 0.5.0
(`v0.5.0`), AbstractRuntime 0.19.0 (dispatch from `8c8a731`, run 42755657157), abstractagent 0.6.1 (run 42756305396),
abstractavatar 0.2.0 crate + Python (the operator's local `cargo publish --locked` from `a795a46`, tag `v0.2.0`, run
42786136902). Voice and vision proven on Linux GPU (OVH) and CPU (athena): `untracked/release-2026-11-07/audit-fable/VOICE-LINUX-PROOF.md`,
`VISION-LINUX-PROOF.md`.

| Step | Package | State at the handoff | Next action |
|---|---|---|---|
| 6 | abstractgateway 0.21.0 + console 0.18.1 | mentions routing COMMITTED `649776c5` (8 routing tests red on 98bcda38; 534/535 affected passed, the one failure a Stop timing race that passes alone); tree clean; floor runtime `>=0.19.0`; first gate RED for the network (30 jobs died at setup-python, PyPI unreachable; `gate-gateway-649776c5.log`), rerun launched 12:20 (`gate-gateway-649776c5-rerun.log`) | rerun green → push main → tag v0.21.0 → release run → visibility (gateway 0.21.0, console crate 0.18.1) → "gateway 0.21.0 visible" to the Entity session; red on code → fix forward, never push red |
| 6b | AbstractRuntime 0.19.1 (self-knowledge brief, 1197) | `0a8fc67` + `340b61b` + `9656cee` (the 249-character topics description fix, a BLOCKER for any cut from 0a8fc67) on main, unpushed; optional for this wave | cut only if time allows; otherwise the gateway ships on 0.19.0 and the brief rides 0.21.1 |
| 7 | Entity 0.12.0, Code web 0.16.0 (D4: 0.16.0) + crate 0.15.0, Assistant web 0.2.0 (in the inventory, D4: yes), Observer 0.13.0 | ALL client halves committed: Entity 8b86d00/820d0fe/1ba47f7/d7a063f (:3004), Assistant web 3e37883/78a5eb6, Code web 4beb02f + TUI a602c4c (:3003, binary installed; tag `web-v0.16.0` on a602c4c, changelog heading "[web 0.16.0]", crate stays 0.15.0) | tag on "gateway 0.21.0 visible" |
| 8 | candidate | not started | exact-matrix install Mac + Linux CPU host (Core session), website preview (`abstractframework-website`), pins draft, change report `docs/releases/0.14.0-changes.md` refresh |
| 9 | abstractframework 0.14.0 | pins draft `docs/releases/0.14.0-pins-draft.md`; root main ~66 commits ahead, unpushed | the operator's explicit GO only |

Known limits shipped in 0.21.0 (recorded in [1187](1187_a_mention_becomes_a_job_by_the_entitys_own_judgment.md)):
a not-addressed turn's `input_data` 404 (clients read the turn row); steer/guidance messages bypass the mentions rule.
After the release, in the Entity session's packages: AbstractMemory 0.5.1 (bookkeeping writes), the console crates'
modal fix at their next abstracttui relock, the abstractentity items from the operator's 12 UI findings of 2026-11-10: abstractentity backlog 0001-0012 (68ec3af):
0001 topics panel top-right, 0002 hover-highlight community + visibility, 0003 animated zoom, 0004 legend <= 2 lines +
interactive, 0005 members by type + type stats + last formed, 0006 UI polish, 0010 live activity panel (= root 1196),
0011 brief (= root 1197), 0012 slow Settings (= root 1195); 0007 green contrast, 0008 hovered-neighbourhood contrast and
0009 ledger key lines are DONE (d7a063f, :3004 rebuilt). Assistant web 78a5eb6 reads the not-addressed turn's row on reload.

Site note for the cut (operator on the abstractcore.ai preview, 2026-11-10 ~11:00): AbstractCore is presented as an
abstraction over AI capabilities (write once; generate with multimodal input and output; closed and open models alike;
build on capabilities independently of providers or models changing their contracts), never "for Python" or a provider
list. core.html's hero carries the rejected sentence; align it at the site cut. abstractcore.ai is PUBLISHED (AbstractCore
gh-pages 0a1407d, 2026-11-10 ~12:00) and links to abstractframework.ai/core.html, /install.html and the /core/ installer
files: those links are 404 until the site cut ships the back-links, the hero and the /core/ files from tag v2.35.0 — the
site cut is therefore a visible gap, not only a candidate step. CORRECTION 2026-11-10 18:10 (Core session, link check
of the live page): /core.html and /install.html answer 200 today; only the /core/ installer files were missing. Fixed
live on abstractcore.ai (gh-pages bdf0ecb): the five install lines now point at the raw files of tag v2.35.0 (both 200,
the sh line run with --print); swap back to abstractframework.ai/core/ at the site cut (three HTML files).

Candidate check, athena.ovh (Core session, 2026-11-10 ~14:45): with the host's own Python 3.14 the published set does not
install (abstractcore 2.35.0 pins `lxml<6`, lxml 5.x has no cp314 wheels, pip builds from source and fails). Not a 0.14.0
defect: the root docs state Python 3.10–3.13 (README, docs/install.md platform table, getting-started) and the installers
provision uv's Python 3.12. Core follow-up (next core release): lift the lxml ceiling to `<7` and test 3.14. On uv's Python 3.12
(scratch venv, CPU torch from the PyTorch index, one pip resolve): INSTALL OK, `pip check` clean, every package imports:
core 2.35.0, voice 0.21.0, vision 0.3.35, music 0.1.17, skill 0.3.11, semantics 0.0.5, 3d 0.3.2, camera 0.2.1, memory
0.5.0, note 0.3.1, runtime 0.19.0, lxml 5.4.0, torch 2.15.0+cpu; 1.8 GB. The run resolved abstractagent 0.6.0, not the
0.6.1 pin (the draft the Core session read predates the agent row): the final matrix install must pin 0.6.1. Gateway and
assistant not in that set (0.21.0 pending). abstractagent, abstractsemantics and AbstractMemory expose no `__version__`
(cosmetic; next wave). Python 3.14/lxml filed as abstractcore backlog 0886 (proposed). The `[gpu]` profile install of the
exact matrix runs on the operator's Linux GPU host (resumed on request, ~40 min) by the Core session's recipe once the
gateway and apps are published.

Gate finding 2026-11-10 (gateway shard 3, all Pythons): test_entity_idle_sleep's real repair sweeper left a dead worker
registered in the process-wide registry, so later /api/health answered degraded and two singleton-lock tests went red;
fixed in gateway 56451ab5 (teardown unregister + a conftest guard that fails the leaving test by name). Not a code defect.

## Receipts

- Release mechanics: the `abstract-release` and `release` skills; previous record [1132](../completed/1132_final_stable_release.md).
- Track: [understanding-pass](understanding-pass/README.md).
- Refresh 2026-11-10: `untracked/release-2026-11-07/audit-fable/PACKAGES.md` (sections a, c, e), `RESUME.md`, `ROADMAP-2026-11-09-2010.md`.
- Publish log 2026-11-10: the registries, `gh run view` of each release run, `git ls-remote --tags origin`; root 0.14.0 pins draft: [docs/releases/0.14.0-pins-draft.md](../../releases/0.14.0-pins-draft.md).
