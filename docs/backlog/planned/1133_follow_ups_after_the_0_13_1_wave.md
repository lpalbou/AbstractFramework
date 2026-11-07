# 1133 — Follow-ups after the 0.13.1 wave (2026-11-07)

> Package: AbstractGateway, AbstractVoice, AbstractUIC, AbstractAssistant, AbstractNote, AbstractCode, AbstractFramework
> Type: task
> Created: 2026-11-07
> Priority: medium
> Labels: release, follow-up

## Summary

Residual findings from the adversarial reviews of the 2026-11-07 wave (runtime 0.18.2, voice 0.20.1,
AbstractUIC 0.10.2, gateway 0.20.2, apps, assistant 0.18.1) that were not release blockers, plus the
release-mechanics problems that bit. Each line is small; split into package items when picked up.

## Items

- **Gateway** — the model worker drops only `''` from `sys.path`; an empty `PYTHONPATH` entry (`:/x`) puts the
  data directory back. Compare entries with `realpath(cwd)` (`model_host.py` ~1016). Stale
  `-m abstractgateway.model_host_child` mentions: `model_host.py:4`, `model_host_child.py:1`, ADR 0002:32, a test
  docstring. `scope` is a free string with a hand-written 422; the 0.20.2 CHANGELOG lists it under Fixed.
- **Gateway** — the console-islands drift test silently skips the bundle comparison when the kit bundle is not built.
- **Gateway release.yml** — "Publish GHCR Gateway images" installs `abstractgateway==X` seconds after the PyPI
  upload; v0.20.2 failed on index lag (run 42339708494, green on re-run). Wait for visibility before the build.
- **Voice** — the first meter frame after a listening pause shows half the old level (normalizer not reset,
  `recognition.py` ~290-307, 664-667); smoothing assumes 30 ms chunks.
- **AbstractUIC** — after a network gap a click on another message may be queued silently (review U4); no test for the
  avatar conversation's live-line read-aloud button (U7); three kit voice messages point at "Settings → Voice", a page
  Note does not have.
- **Assistant desktop** — dictation and the Microphone pause are reachable only by right-click (no keyboard route).
- **Assistant web on npm** — `@abstractframework/assistant` has no trusted publisher on npmjs.com: CI publish of 0.1.2
  fails with E404 PUT (run for tag `web-v0.1.2`). The owner configures trusted publishing (repo
  lpalbou/AbstractAssistant, workflow `release-web.yml`, environment `npm`) and re-runs, or publishes 0.1.2 by hand.
  `web-v0.1.1` is tagged and never published (tarball path bug, fixed in 0.1.2).
- **Entity 0.11.1** — the Avatar view still draws a border on a finished answer, although its changelog says the
  border was removed (site review 2026-11-07); find the Entity-side style.
- **Assistant docs** — `docs/voice.md:4-6` at v0.18.1 says dictation needs the `voice` extra; the base install already
  captures the microphone.
- **Flow, Continuum, Assistant web** — still bundle ui-kit before 0.9.15 (no audible-only speaking state); pick it up at
  their next release.
- **Note** — `web/scripts/check_dictation.mjs` runs in no CI; user docs do not explain dictation.
- **Local gate (`scripts/ci_local.py`)** — on this Mac: AbstractNote's wheel check uses a fixed `/tmp/wheel-check`
  shared across runs and `pip` resolving to the uv shim; AbstractAssistant's path tests fail because the job TMPDIR
  under `~/Library/Caches` is outside the app's safe-to-read roots; two jobs of one repository share one Rust target
  folder concurrently (gateway console-tui doctest lost an rlib); one gateway gate run kept 53 GB.
- **Code web** — the Playwright e2e against the disposable test gateway has about 12 environment failures (sign-in
  timeouts) on this Mac, same on main.
- **Root `.venv`** — AbstractAvatar's editable native library was overwritten in place on 2026-11-06 22:44 (exit 137 on
  render); re-signed onto a new inode on 2026-11-07. Whatever rebuilds it must write a new file.

## Evidence

Reviews and logs: `untracked/release-2026-11-07/` (review-step1.md, review-gateway-note.md, review-apps.md,
review-assistant.md, gate-*.log, FOLLOWUPS.md).
