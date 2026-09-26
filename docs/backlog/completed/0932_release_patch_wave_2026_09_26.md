# 0932 — Release trace: patch wave 2026-09-26/27 (root 0.4.1)

- **Status:** completed
- **Created:** 2026-09-27
- **Completed:** 2026-09-27 ~00:55 CEST
- **Area:** release (AbstractRuntime, abstractcore, abstractagent, abstractgateway, abstractassistant, abstractframework)

## Summary
Fix-forward wave after 0921 (root 0.4.0), released with the operator's go of 2026-09-26 evening after the Automations backlog items were
written in every package (0928). Log: untracked/release-2026-09-26/PATCH-RELEASE-LOG.md; staging ledger PATCH-STAGING.md; reviews 29–34.

| Package | Version | Tag → commit | Registry / evidence |
|---|---|---|---|
| AbstractRuntime | 0.5.1 | `v0.5.1` → `8090efd` (release commit 2100d1f + backlog docs) | PyPI 22:44 CEST 26th (dispatch run 36270437112); GH release |
| abstractcore | 2.16.1 | `v2.16.1` → `e333219` | PyPI 23:00 CEST (run 36270788165); GHCR `abstractcore-server:2.16.1` + `latest`; GH release |
| abstractagent | 0.3.15 | `v0.3.15` → `6595453` | PyPI 22:44 CEST (dispatch 36270438876); GH release |
| abstractgateway | 0.5.1 | `v0.5.1` → `00d6c66` | PyPI 23:58 CEST (run 36273545437, 3 attempts: flaky test 0933 + PyPI index lag); GHCR `abstractgateway:0.5.1`/`latest` (ef4b98a0…) and `0.5.1-gpu`/`gpu-latest` (5bb200e7…); console crate stays 0.9.0 |
| abstractassistant | 0.6.1 | `v0.6.1` → `641b653` | PyPI 00:20 CEST 27th (dispatch 36275829674); Settings window clamped inside the screen; default edge gap 12 px |
| abstractframework | 0.4.1 | `v0.4.1` → `7decd36` | PyPI 00:43 CEST (run 36277138121); dry-run matrix 24/24; real scratch install ok (`abstractgateway --version` 0.5.1, `pip check` clean); GH release Latest with `AbstractFramework-Installer.pkg` 23428 B sha256 49dd6a6d…03f7 (unsigned, 0868) |

Root 0.4.1 pins gateway 0.5.1, assistant 0.6.1, core 2.16.1, runtime 0.5.1, agent 0.3.15, skill 0.3.0.

## What shipped (user-facing)
0923 (a wait is resumed at most once — an Agent/subflow node's child no longer runs twice; typed `StaleResumeError`); 0922 (MLX prompts
follow the model's chat template; renderer named in metadata); 0918 (agent re-prompts once on announced/unrunnable calls; `no_tool_call`
stop; crash fix for 0.3.13/0.3.14); gateway floors + quiet lost-race log; assistant settings placement + 12 px gap.

## Observations
- PyPI's index lags 1–2 minutes after an upload: first `pip download` and the gateway's image build (attempt 2) failed on it; rerun.
- The gateway test `test_live_deltas_hub.py::test_api_role_subscription_tails_the_runner_file` failed 2 of 8 jobs → real split-mode bug (0933).
- abstractcore's working tree carried uncommitted voice-clone edits from another seat (`server/audio_endpoints.py` + test) — not in 2.16.1, left untouched.
- The runtime's release workflow creates the tag with its own token, so no tag-triggered second run occurs (unlike this morning).

## Related
0921 (previous wave), 0922, 0923, 0918 (completed by this wave), 0925/0926/0927 (open), 0933 (new), 0928 (next wave: Automations v1).
