# 0906 — AbstractFlow: interface pins on start/end nodes, no silent edge loss, deep-research wiring

> Package: abstractflow (web editor, examples/flows, bin/cli.js proxy)
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: flow, interfaces, editor, mission-wave-2026-09-25, unreleased

## Summary

Completed record for mission F of the 2026-09-25/26 wave (committed locally on `main`, not
released: the release is staged and waits for the operator's go). Choosing an interface for a flow
now adds the pins that interface declares to On Flow Start / On Flow End; opening and saving a flow
no longer deletes connections the editor cannot draw; the bundled deep-research flow reads the
`prompt` that AbstractCode sends and reports `success`.

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`, track F): "AbstractFlow: interface →
start/end node pins". While doing it, the corpus test found that a load→save cycle in the editor
silently lost 336 connections in 24 shipped flows (coding-agent, deep-research, entity-*…).

## What landed (abstractflow `main`, from clean `4dbb2b3`)

- **Interface → pins** (`e22bb71`): typed contract in `src/utils/flowFamilies.ts`
  (`applyInterfacePins`, `interfaceBoundaryPins`, `missingInterfacePins`); `setFlowInterfaces` is one
  undo step; the Toolbar no longer reloads the open flow on interface/name/description change;
  preflight warns on a missing required pin. `09e9abb` added `abstractassistant.agent.v1` and
  `abstractcode.goal.v1` and pins on newly added start/end nodes. `82b1482`: pins added on open show
  the flow as UNSAVED with a notice. `b897240`: preflight for unconnected required end pins and type
  mismatches. `d9229d0`: a metadata PUT applies only to the still-open document. `fbef0e2`: corpus
  preflight over 59 interface-declaring flows → zero type-mismatch warnings.
- **Bundled flows** (`e78bc9c`, `fd1fcc2`): deep-research, entity-chat, entity-goodbye and
  multiagent-coding gained their boundary pins; deep-research's `resolve_request` takes
  `request | prompt` and `report_success` feeds the end `success` (generator and JSON in sync).
- **Edges are never dropped silently** (`82539eb`, `5f19d38`, `0df9c65`): edges whose pin ids are
  undeclared (code-node dict keys, subflow `child_output`) or whose type the editor refuses are kept
  and saved back, never duplicated; "dropped" now means the node is gone; import shows the same
  notices; an amber "N hidden" badge per node lists the hidden connections. Corpus: 226 flow loads /
  8,052 edges, 0 dropped (was 336 lost in 24 flows).
- **About** (`0d3e72f`, `487cbdb`, `e4ed91c`) and **proxy forwarding** (`eb53099`): recorded in
  [0908](0908_framework_identity_about_screens_and_proxy_forwarded_address.md).
- Docs: `62d1856`, `a3ae24a`, coredoc pass `120336c` (3 Mermaid diagrams, troubleshooting,
  llms byte-reproducible).

## Completion report

- Tests: suite 666 → 717/717 over the wave (+21 interface pins, +10 new interfaces, 5 edge-preservation
  tests, corpus preflight); tsc/eslint/build clean; deliberate breaks red at each step (7, 2, 4).
- Reviews: REVIEW/06 ACCEPT-WITH-FIXES (D1 deep-research wiring before any bundle rebuild, D3–D5) →
  REVIEW/10 (d) ACCEPT; REVIEW/14 ACCEPT-WITH-FIXES (F1 nine type-refused edges still deleted by a
  save, F2 import without notice, F3 dedup untested) → closed by `5f19d38` / `0df9c65`, REVIEW/17 (f)
  ACCEPT.
- Not done, tracked: wiring the remaining unconnected pins of entity-chat/entity-goodbye/
  multiagent-coding and rebuilding the gateway's own `deep-research@0.1.7` bundle and its contract
  test → [0890](../planned/0890_wire_bundled_flow_interface_pins_and_rebuild_gateway_bundles.md)
  (release step; `KNOWN_GAPS` in `bundledFlows.test.ts` still non-empty on 2026-09-26). Drawing
  runtime-resolved handles → [0891](../proposed/0891_flow_runtime_resolved_handles_as_pins.md)
  (abstractflow proposed 0157). Flow vite dev proxy lacks forwarding headers; moving Flow onto
  app-server → [0894](../proposed/0894_migrate_flow_and_code_web_proxies_onto_app_server.md).
- No `required` flag on interface pins (orchestrator decision).
- ADR state: none.

## Receipts

- `untracked/missions-2026-09-25/F/REPORT.md`, `B/REPORT.md` (P-flow), `CD/REPORT.md` (abstractflow row)
- `untracked/missions-2026-09-25/REVIEW/06-flow.md`, `10-recheck-clients-flow.md`, `14-flow-edges.md`, `17-streaming-clients-flow.md`
