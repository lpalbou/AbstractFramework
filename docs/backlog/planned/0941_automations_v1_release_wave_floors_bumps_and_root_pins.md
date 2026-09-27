# 0941 — Automations v1 release wave: floors (gateway → runtime with automations), minor bumps, root pins

- **Status:** planned (release checklist; starts only after the operator has validated Automations v1 and given an explicit per-release go)
- **Created:** 2026-09-27
- **Area:** abstractruntime, abstractgateway (+ console re-vendor), abstractuic (ui-kit, panel-chat), abstractflow, abstractobserver, abstractassistant, abstractframework (root pins, install manifest)
- **Parent:** [0928](../completed/0928_automations_v1_runtime_native_scheduled_and_triggered_tasks.md) (completed, UNRELEASED)
- **Process:** the `abstract-release` and `release` skills; coredoc per repo (operator rule); ADR-0034 order via `scripts/lib/packages.txt` + `scripts/deps.sh` (see 0860)

## Summary
Automations v1 exists only as local, unpushed commits in six repos (see 0928's commit table). Releasing it is one minor
wave. Each package's pins must resolve on packages already published, so the order below is fixed. No step starts
without the operator's explicit go for that release: earlier authorisations never carry over.

## Order and per-step checks
1. **AbstractRuntime** (minor, from 0.5.1).
   - Carries `79d9bf6` … `d02578a` and the controller bundle as package data. Check that the wheel contains the bundle:
     `test_controller_bundle_packaged.py`.
   - Release notes:
     - the custom-store requirements (create-if-absent, a run index for sessions; see
       [0938](0938_runtime_start_session_starts_on_duck_typed_stores_documented_and_refused.md));
     - the non-strict history read now raises on a failing index (review 44 F5);
     - J50-1 (command results recorded before `e690b55` have no digest; irrelevant because no released gateway has
       automations).
2. **abstractgateway** (minor, from 0.5.1) + the console crate if its tree changed.
   - **Raise both floors** to the runtime version from step 1: `pyproject.toml` `AbstractRuntime>=` and
     `live_deltas.ABSTRACTRUNTIME_FLOOR` (a test keeps them equal).
   - This is review 52 addendum **W1**: boot calls `warm_session_index()`, and every create sends
     `policy.tool_approval`. Both fail on 0.5.1, with an `AttributeError` at boot and a 422 on create.
   - The R52-1 / W2 fix set is committed (`4ece2f5`). Confirm that review 55 (the final delta) is GO and that the
     acceptance script passes (16/16 or more) on the released runtime.
   - The re-vendored kit theme/islands must match the kit version that step 3 publishes.
3. **@abstractframework/ui-kit + panel-chat** (minor).
   - The automations client, panel, dialog and fixtures.
   - The fixtures' `CHECKSUMS.sha256` equal the Assistant's vendored copy: root `scripts/check_identity_sync.py`
     (`cf71688`).
4. **@abstractframework/flow** (minor): `automation_defaults` + trigger-source discovery (`c5961d1` … `0d4bf76`).
5. **@abstractframework/observer** (minor).
   - Built through the source alias to `../abstractuic`, so it needs the kit checkout at the published tag.
   - Relock after the kit publishes (the 0899 pattern).
   - Re-run the vitest suite against the published kit fixtures (review 54 O-1 was exactly this drift).
6. **abstractassistant** (minor, from 0.7.0). Capability-gated at runtime (`contracts.common.automations.available`), so
   it adds no gateway pin. Its vendored fixtures must equal the kit's.
7. **abstractframework root** (minor, from 0.4.2).
   - Pin runtime, gateway and assistant (light / apple / gpu) to the new versions.
   - Regenerate the install manifest.
   - Update the root docs (`docs/automations.md` exists since `606afa6`).
   - Write the release trace record.

Unchanged in this wave: abstractcore, abstractagent (0034 is still planned) and abstractcode. Code shows automation
sessions through `root_only` turn roots; its kind filter is abstractcode 0001 / root 0930.

## Gates (each package)
- Full suite green on a clean checkout. CI green on `main`. The coredoc pass (`llms.txt` / `llms-full.txt` regenerated).
  A CHANGELOG `## Unreleased` → version section.
- A matrix install of the root profile in a scratch venv (`HOME`, `HF_HOME` and caches isolated).
- The two live example automations (`untracked/missions-2026-09-27/LIVE/`) keep ticking on the operator's `:8080`
  after the upgrade. They were created on the unreleased code. An upgrade that cannot read them is a release blocker.
  The runtime's history is byte-identical to 0.5.1 for ordinary sessions (job 51 (d)).

## Acceptance criteria
- [ ] Every package in the order above is published, tagged, and verified on its registry.
- [ ] The gateway's runtime floor names the release that contains `b000036` and `3cc9900` (W1, P2-2).
- [ ] Root pins resolve in a clean venv: `pip install abstractframework` + `abstractframework doctor`.
- [ ] A release trace record in `completed/` with tags → commits and follow-ups.
