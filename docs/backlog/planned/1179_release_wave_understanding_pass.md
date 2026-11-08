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

## Receipts

- Release mechanics: the `abstract-release` and `release` skills; previous record [1132](../completed/1132_final_stable_release.md).
- Track: [understanding-pass](understanding-pass/README.md).
