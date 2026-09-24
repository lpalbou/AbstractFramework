# 0867 — Release waves of 2026-09-24 (root 0.3.0, patch 0.3.1) and the 2026-09-25 docs pass

> Package: abstractframework (release sequence); abstractcore, AbstractRuntime, abstractgateway, abstractgateway-console, @abstractframework/ui-kit, @abstractframework/continuum, @abstractframework/entity
> Type: task
> Created: 2026-09-25
> Completed: 2026-09-25
> Priority: high
> Labels: release, release-trace, docs

## Summary

Release trace required by the `abstract-release` process after a wave; nobody wrote it on
2026-09-24, so it is written on 2026-09-25. Two waves shipped the work recorded in 0863–0866, then a
`coredoc` pass refreshed the docs of every released repo.

## Wave A — root 0.3.0 (2026-09-24)

Order: abstractcore 2.15.0 + ui-kit 0.1.11 → abstractgateway 0.4.1 + crate 0.8.0, then continuum
0.3.0 + entity 0.2.0 → abstractframework 0.3.0.

| package | version | tag → commit | published |
|---|---|---|---|
| abstractcore | 2.15.0 | `v2.15.0` → `12528d3` | PyPI, GHCR `abstractcore-server:2.15.0`, GH release |
| @abstractframework/ui-kit | 0.1.11 | `v0.1.11` → `ccd9184` | npm latest |
| abstractgateway | 0.4.1 | `v0.4.1` → `1075cde` | PyPI, GHCR `:0.4.1` / `:0.4.1-gpu`, GH release |
| abstractgateway-console (crate) | 0.8.0 | — | crates.io, local cargo token |
| @abstractframework/continuum | 0.3.0 | `v0.3.0` → `8e89b8c` | npm, CI with provenance |
| @abstractframework/entity | 0.2.0 | `v0.2.0` → `d8ea226` | npm, CI with provenance |
| abstractframework | 0.3.0 | `v0.3.0` → `0565c43` | PyPI, GH release with the `.pkg` |

`v0.4.0` of abstractgateway (`285665a`) is a tag with no artifacts: its Linux CI failed
(`ps -ww`, a guard-blocked LM Studio probe, Mac-only test assumptions) and the fix shipped as 0.4.1.

## Wave B — patch 0.3.1 (2026-09-24 evening)

Order: abstractcore 2.15.1 → AbstractRuntime 0.4.34 → abstractgateway 0.4.2 → abstractframework
0.3.1.

| package | version | tag → commit | published |
|---|---|---|---|
| abstractcore | 2.15.1 | `v2.15.1` → `e91fe9b` | PyPI, GHCR `abstractcore-server:2.15.1`, GH release |
| AbstractRuntime | 0.4.34 | `v0.4.34` → `a2e0e94` | PyPI via `workflow_dispatch` from `main` (requires abstractcore>=2.15.1) |
| abstractgateway | 0.4.2 | `v0.4.2` → `4b08b95` | PyPI (floors core>=2.15.1, runtime>=0.4.34), GHCR `:0.4.2` / `:latest` / `:0.4.2-gpu`, GH release; crate unchanged |
| abstractframework | 0.3.1 | `v0.3.1` → `cb29dda` | PyPI (pins core==2.15.1, gateway==0.4.2, runtime==0.4.34), GH release with the rebuilt `.pkg` |

Unchanged in both waves: abstractagent 0.3.13, abstractassistant 0.5.0, voice/vision/memory/
semantics/music, flow 0.3.20, code 0.4.2 (+ crate 0.5.1), observer 0.1.12, app-server/panel-chat/
monitors, abstractcore-console crate 0.2.0.

## Docs pass (2026-09-25)

`coredoc` commits pushed to `main`, docs only: abstractruntime `696f386`, abstractcore `194c312`,
abstractgateway `3312bfe`, root `cfb4926`, abstractcontinuum `7bc4616`, abstractentity `f3b5a11`,
abstractuic `9a307b3` (`untracked/coredoc-2026-09-25/STATUS.md`).

## Completion report

- Verification (re-checked 2026-09-25 ~01:20 CEST by this trace): PyPI latest abstractcore 2.15.1,
  AbstractRuntime 0.4.34, abstractgateway 0.4.2, abstractframework 0.3.1; npm latest ui-kit 0.1.11,
  continuum 0.3.0, entity 0.2.0; crates.io `abstractgateway-console` max 0.8.0 (published by user
  `lpalbou`, no trusted-publishing data); GitHub releases core v2.15.1 (Latest), gateway v0.4.2
  (Latest), root v0.3.1 with `AbstractFramework-Installer.pkg`. Orchestrator verification:
  `untracked/release-2026-09-24/STATUS.md` (20:47 and 00:50 CEST sections), 24/24 root dry-run
  matrix, real scratch install from PyPI.
- Incidents during the waves: gateway 0.4.0 CI failure (fixed forward as 0.4.1); root 0.3.0 `.pkg`
  asset first built with the unpublished gateway pin 0.4.0, rebuilt from the tag and replaced;
  continuum/entity first CI publish failed until the owner added the npm trusted publishers.
- Follow-ups created from the waves and the docs pass: 0868–0888 (see overview). Existing items
  refreshed: 0849, 0850, 0856, 0857, 0858, 0859, 0860, 0861, 0862. 0233 closed.
- Owner actions still open (no item needed beyond the ones named): sign + notarize the `.pkg`
  (0868); crates.io trusted publishing (0857); rotate the agora keys (0851); file the mlx-lm
  patch-release request; restart the local :8080 stack on the released code.
- Release-process note: AbstractRuntime publishes to PyPI only from `workflow_dispatch` on `main`
  (the tag-triggered run's PyPI step refuses by environment rule); the wave order core → runtime →
  gateway → root contradicts ADR-0034's hand-written list, which still puts core and runtime in one
  tier → 0860.
- ADR state: ADR-0034 governs the sequence (drift tracked by 0860); no new ADR.

## Receipts

- `untracked/release-2026-09-24/STATUS.md` and the per-package ledgers in that folder.
- `untracked/coredoc-2026-09-25/STATUS.md`.
