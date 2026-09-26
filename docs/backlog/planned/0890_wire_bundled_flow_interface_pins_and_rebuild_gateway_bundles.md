# 0890 — Wire the unconnected interface pins of the bundled flows, then rebuild the gateway's shipped bundles

> Package: abstractflow (examples/flows, scripts/build_*); abstractgateway (flows/bundles, pyproject.toml, tests); abstractframework release wave
> Type: task
> Created: 2026-09-26
> Priority: high
> Labels: flow, gateway, interfaces, release-step

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
