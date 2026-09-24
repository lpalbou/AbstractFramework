# 0864 — Gateway engines, apps, tray and network settings (abstractgateway 0.4.1 / 0.4.2)

> Package: abstractgateway (with abstractgateway-console crate 0.8.0, @abstractframework/continuum 0.3.0, @abstractframework/entity 0.2.0, @abstractframework/ui-kit 0.1.11)
> Type: feature
> Created: 2026-09-25
> Completed: 2026-09-24
> Priority: high
> Labels: gateway, engines, apps, tray, network, settings, release-trace

## Summary

Completed record for unplanned major work (written for traceability on 2026-09-25). The gateway
became the place a non-technical user manages the whole local stack without a terminal: engines,
browser and terminal apps, the tray, the network exposure mode, and stored settings that replace
environment variables.

## What landed (abstractgateway 0.4.1, tag `v0.4.1` = `1075cde`; 0.4.2, tag `v0.4.2` = `4b08b95`)

- **Engines without a terminal** (mission M): llama.cpp from the prebuilt Metal wheel, MLX wheel,
  Ollama official signed zip (sha256 + team id + `spctl`), LM Studio dmg; admin only via the OS
  dialog; `/api/gateway/engines/*`, `abstractgateway engines …`.
- **Apps managed by the gateway** (O, Y, HH, JJ, II, LL): Node installed from the PyPI wheel, apps
  from npm (sha512), run as managed processes, opened signed in through a single-use handover;
  Code's terminal app installed from checksummed release binaries and opened signed in; apps
  started outside the gateway detected by loopback probe; ports = stack map (Observer 3001,
  Continuum 3002, Code 3003, Entity 3004, Flow 3005); Entity "Create your first entity";
  Continuum works on a fresh install (gateway-owned backlog folder); Assistant as a desktop app
  card.
- **Downloads** (N, KK): bytes/percent/speed/ETA/per-file rows, `stalled`, cancel records who,
  downloads that stop on their own end `failed` with a reason (0.4.2).
- **Network exposure** (R, T, Z, BB): `localhost` / `lan` / `internet` setting in the console,
  terminal console, tray and CLI; `lan`/`internet` require user auth; login services run plain
  `serve`; allowed origins, trust proxy and apps knobs are stored settings (WUI, TUI, CLI);
  `PROTECT_READ=0` refused for `lan`/`internet`; token-only mode no longer lets a non-admin
  session act on the operator's settings.
- **Tray control centre** (Q, V): start at login on every OS, apps, model load/eject, signed-in
  Open Console, Network + copy address; Restart scrubs in-process offline flags.

## Completion report

- Validation (orchestrator runs, `untracked/missions-2026-09-22/SUMMARY.md`): full gateway suite
  2235 passed / 7 skipped / 0 failed with the real HOME untouched (fourth wave), 2272/0 after LL;
  per-mission tests + mutants (M 81 tests + 8/8, O 42 + 19/19, Z 238 + 16/16, BB 45 + 10/10,
  HH 303 + 12/12, KK 198+32+127 + 10/10); Rust console-tui 135 headless + 6 unit tests.
- Release evidence (`untracked/release-2026-09-24/STATUS.md`): PyPI 0.4.1 and 0.4.2 (0.4.2 requires
  abstractcore>=2.15.1, AbstractRuntime>=0.4.34), GHCR `abstractgateway:0.4.2` / `:latest` /
  `:0.4.2-gpu`, crate `abstractgateway-console` 0.8.0, npm continuum 0.3.0 and entity 0.2.0 (CI
  with provenance), ui-kit 0.1.11. Tag `v0.4.0` (`285665a`) exists with no artifacts: its Linux CI
  failed and the fix shipped as 0.4.1.
- Residual risks and follow-ups:
  - crates.io trusted publishing still missing; 0.8.0 was token-published → 0857.
  - Console toggle for `allow_engine_install` still missing → 0858 (refreshed).
  - Assistant opens without a sign-in handover → 0875. Gateway console TUI has no release
    binaries → 0876.
  - Internal HTML comments reach the browser → 0885; `mkdocs.yml` publishes `docs/backlog/**` →
    0884.
  - LM Studio automated install vendor terms, Linux/Windows tray + service validated by doubles only
    (0856 for Windows).
  - RBAC rulings → 0870 (0862).
- ADR state: no new ADR written. The "no environment-variable instructions in user-facing text;
  every setting has three doors (web console, terminal console, CLI)" rule was applied across the
  wave and is recorded in the operator's feedback memory; if it is to bind future packages it
  should become an ADR (not done in this pass — flagged in the overview).

## Receipts

- Mission reports: `untracked/missionM/`, `missionN/`, `missionO/`, `missionQ/`, `missionR/`,
  `missionT/`, `missionV/`, `missionY/`, `missionZ/`, `missionBB/`, `missionHH/`, `missionII/`,
  `missionJJ/`, `missionKK/`, `missionLL/` (local).
- Release ledgers: `untracked/release-2026-09-24/abstractgateway-ledger.md`,
  `abstractgateway-0.4.2-ledger.md`, `abstractcontinuum-ledger.md`, `abstractentity-ledger.md`,
  `abstractuic-ledger.md`.
