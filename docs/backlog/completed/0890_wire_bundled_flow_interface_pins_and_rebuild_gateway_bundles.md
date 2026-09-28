# 0890 — Wire the unconnected interface pins of the bundled flows, then rebuild the gateway's shipped bundles

> Package: abstractflow (examples/flows, scripts/build_*); abstractgateway (flows/bundles, pyproject.toml, tests); abstractframework release wave
> Type: task
> Created: 2026-09-26
> Priority: low
> Labels: flow, gateway, interfaces, release-step
> Status: completed 2026-09-28 — ships in abstractflow 0.4.0 (main `d59b6b0` contains `3ad9dbc`, `561f4bd`; publishing in the wave-2 release) and root abstractframework 0.6.0
> Moved: `planned/0890_…` → `completed/0890_…` on 2026-09-28

## Summary

Mission F (2026-09-25/26) made AbstractFlow add the pins an interface declares to On Flow Start /
On Flow End. Four bundled flows gained the missing boundary pins; deep-research was then wired
(`prompt` feeds the request, `success` is set). Three flows still carry pins that nothing feeds or
reads: entity-chat (`success`, `meta`), entity-goodbye (`prompt`, `provider`, `model`, `success`,
`meta`) and multiagent-coding (`provider`, `model`, `passed` on both end nodes). A host that reads
these outputs gets `null`. Separately, the gateway serves its OWN copy of deep-research
(`deep-research@0.1.7.flow`), which predates the wiring, and its contract test pins the old start
outputs. Both halves must land in the release wave, in this order: wire, then rebuild and
republish.

## Why

- REVIEW/06 D4: unwired `success`/`meta` produce `success: null`; `maintenance/notifier.py` in the
  gateway requires `is True`, and any future boolean reader sees null.
- REVIEW/06 "Bundled flows and the release": do NOT rebuild the gateway bundles only to add unwired
  pins; rebuild after the pins are wired. F report: "NOT wiring the unconnected pins of the four
  bundled flows (backlog follow-up)" and "the gateway's shipped bundles must be rebuilt at release
  time".

## Current code reality (2026-09-26; abstractflow `0df9c65`, abstractgateway `1172686` + uncommitted S-gw edits)

- `abstractflow/src/utils/bundledFlows.test.ts` l.284–286: `KNOWN_GAPS = {'entity-chat:success',
  'entity-goodbye:prompt', 'entity-goodbye:success'}` — the test tolerates exactly these gaps for
  `abstractcode.agent.v1` flows.
- A read of `abstractflow/examples/flows/*.json` on 2026-09-26 (edges into/out of the boundary nodes,
  pin defaults excluded) finds unwired: entity-chat end `success`, `meta`; entity-goodbye start
  `provider`, `model`, end `success`, `meta`; multiagent-coding (`abstractcode.coding.v1`) start
  `provider`, `model`, end nodes `end_pre` and `end` `passed`. deep-research: none (fixed by `fd1fcc2`).
- abstractgateway ships only `flows/bundles/deep-research@0.1.7.flow` of these (pyproject.toml l.103
  wheel force-include, l.131 sdist). `tests/test_deep_research_bundle_contract.py` l.245–247 asserts
  the start outputs `{"exec-out","request","viewpoint","effort","provider","model"}` (no `prompt`).
- `entity-life@*.flow` and `multiagent-coding@*.flow` under `abstractgateway/flows/bundles/` are
  untracked local bundles, not shipped by the wheel; they are rebuilt only if the release decides to
  ship them.

## Scope

### In scope

- Wire the listed pins from values the flows already compute (entity-chat/goodbye: the reply's
  verdict → `success`, run metadata → `meta`; entity-goodbye `prompt`/`provider`/`model` into the
  nodes that use them; multiagent-coding: the verification verdict → `passed`). Edit the generator
  scripts, regenerate the JSON, and empty `KNOWN_GAPS`.
- Rebuild `deep-research` as a new bundle version in abstractgateway, update pyproject force-include
  and `tests/test_deep_research_bundle_contract.py` to the wired outputs (`prompt`, `success`).
- One line in the release staging checklist: "rebuild gateway bundles only after 0890's wiring".

### Out of scope

- Drawing runtime-resolved handles (0891 / abstractflow 0157).
- A `required` flag on interface pins.

## Dependencies

- abstractflow commits `e78bc9c`, `fd1fcc2`, `b897240`, `fbef0e2` (pins, deep-research wiring,
  preflight, corpus test).
- Release order: abstractflow examples → gateway bundle rebuild → gateway release (ADR-0034, 0860).

## Expected outcomes

- No bundled agent/coding flow ends a run with `success`, `meta` or `passed` = null.
- A fresh gateway install serves a deep-research bundle that reads `prompt` from AbstractCode.

## Acceptance criteria

- [ ] `KNOWN_GAPS` is empty and the bundled-flow test is green.
- [ ] Preflight on the four flows reports no "required end pin not connected" warning.
- [ ] The gateway wheel ships the rebuilt deep-research version; the contract test asserts `prompt`
      and `success`.
- [ ] A hermetic run of deep-research started from AbstractCode with only `prompt` produces a
      non-empty report and `success: true`.

## Validation

- `npm --prefix abstractflow test -- --exclude 'untracked/**'`
- `python -P -m pytest abstractgateway/tests/test_deep_research_bundle_contract.py` (scratch HOME)
- Deliberate break: re-add one gap to the flow JSON; the bundled-flow test must go red.

## Evidence

- `untracked/missions-2026-09-25/F/REPORT.md` (Open list; Review 06 fixes release note)
- `untracked/missions-2026-09-25/REVIEW/06-flow.md` (D1, D4, "Bundled flows and the release")
- `untracked/missions-2026-09-25/REVIEW/10-recheck-clients-flow.md` (d)

## ADR status

- Governing: ADR-0034 (release sequence). ADR impact: None.

## Receipts

- None yet.

## Status update 2026-09-26 (after the release wave)

Half done, stays planned. The gateway half shipped in abstractgateway 0.5.0 (`v0.5.0` → `3f08db2`):
the wheel carries `flows/bundles/deep-research@0.1.8.flow` (sha256 `fe34bb5b…4805`, no 0.1.7 bundle)
and the new contract test asserts the wired outputs. Still open: the three other flows (entity-chat,
entity-goodbye, multiagent-coding) keep their unwired pins and `KNOWN_GAPS` is not empty in
abstractflow 0.3.21; abstractflow's `scripts/pack_deep_research_bundle.py` /
`build_deep_research_workflows.py` still name 0.1.7, so re-running them would write a stale file.
Evidence: `STAGING-RESULT.md` deviation 8, `RELEASE-LOG.md` Phase C; record [0921](../completed/0921_release_wave_2026_09_26.md).


## Verification (2026-09-28, operator asked to confirm the issues are real)

Verdict: **no user-visible bug; cosmetic clean-up only.** Priority lowered from high to low.

- deep-research: **already fixed** — the gateway ships `deep-research@0.1.8.flow` (identical to the
  abstractflow example, no unwired boundary pins; `tests/test_deep_research_bundle_contract.py`
  asserts `prompt` and the wired `success` edge). Leftover: `abstractflow/scripts/pack_deep_research_bundle.py:27`
  and `build_deep_research_workflows.py:19,1959` still name 0.1.7 (re-running them would write a stale bundle).
- entity-chat (`success`, `meta` unwired) and entity-goodbye (`prompt`/`provider`/`model` in,
  `success`/`meta` out unwired): the end pins do return `null` (hermetic run), but **no host reads
  them** — the Entity app reads `answer`/`response` (`abstractentity/src/flow_lane.ts:110,125`), the TUI
  reads `answer`/`degraded`/`moment_error` (`abstractcode-tui/src/convo.rs:564`), generic hosts test
  `success is False` (null counts as success). entity-goodbye never calls an LLM, so its unwired
  `provider`/`model` inputs are correctly unused. The earlier cited evidence
  (`maintenance/notifier.py`) does not read flow outputs.
- multiagent-coding: `provider`/`model` (and `build_command`/`run_command`) ARE used — read through
  Get Var nodes (run vars), which an edge-only audit misses. Only `passed` is unwired; nobody reads it.
- The gateway 0.6.0 wheel ships none of these three flows (entity-life / multiagent-coding bundles
  are local, untracked). No gateway release needed.

Remaining scope (one abstractflow release, any wave): wire entity-chat `success`/`meta` and
entity-goodbye `success`/`meta` from values the flows already compute; feed multiagent-coding `passed`
from `all_passed` (default false on `end_pre`); a documented test exemption for flows that never call
an LLM instead of fake-wiring their `provider`/`model`; empty `KNOWN_GAPS` in `bundledFlows.test.ts`;
bump the stale 0.1.7 script constants to 0.1.8.

## Implementation (wave 2, 2026-09-28)

abstractflow branch `wave2/mount` (worktree `untracked/wave2/flow`), local commits, no version bump:

- `3ad9dbc` — flows: agent.v1 `success`/`meta` on entity-chat and entity-goodbye, coding.v1 `passed`
  on multiagent-coding.
  - entity-chat: a `chat_report` code node (`success` = the moment was not degraded; `meta` = the
    host's provider/model, tools-ran count, tool rounds, degraded).
  - entity-goodbye: `close_report` (`success` = the session-close child delivered its output;
    `meta` = turns folded + reason). Named code outputs (`completed`, `meta`), so a code node's own
    success (the executor's) is never taken as the verdict.
  - multiagent-coding: `end.passed` reads the `all_passed` chip; `end_pre` sets `passed=False`.
  - Bundle versions: entity-life 0.0.19, multiagent-coding 0.0.19.
  - `bundledFlows.test.ts`: `KNOWN_GAPS` removed; a documented no-LLM exemption for the prompt check
    (entity-goodbye), guarded so it fails if the flow or a subflow gains an `llm_call`/agent node;
    run preflight reports no "hosts will read null" on the four flows.
  - Smokes (real runtime, scripted LLM): goodbye/chat `success` + `meta`; multiagent `passed` on
    refusal, full and stall.
  - deep-research scripts: one `BUNDLE_VERSION` 0.1.8 in the generator (the pack script reads it);
    no 0.1.7 left.
- `561f4bd` — docs (entity-chat/goodbye `success` + `meta`, CHANGELOG [Unreleased], llms regenerated).

Acceptance against the remaining scope of the 2026-09-28 verification: `KNOWN_GAPS` empty and the
bundled-flow test green; preflight clean on the four flows; the stale 0.1.7 constants gone. The
gateway ships none of these three flows, so no gateway bundle rebuild is needed; deep-research
0.1.8 already shipped in abstractgateway 0.5.0.

Release: abstractflow's next version in the wave-2 release (the operator's go). Recorded by the root
worker from the lead's progress note (untracked/wave2/PLAN.md: "DONE flow mount: 638acdf, 3ad9dbc
(0890), 561f4bd/1470cf1 docs").

