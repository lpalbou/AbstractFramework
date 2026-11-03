# 1055 — Release wave 2026-10-27: voice library, personal voices, replayable ledger, memory graph, shared UI primitives

> Package: root (release sequence), abstractvoice, abstractruntime, abstractgateway, abstractuic, abstractassistant (desktop, iPhone, watch), abstractcode, abstractobserver, abstractentity, abstractnote, abstractmemory
> Type: release + architecture
> Created: 2026-10-27
> Priority: P0
> Labels: release, voice, replay, memory, ui-kit
> Status: Completed 2026-10-28 (root `abstractframework` 0.11.15)

## Summary

One wave, in dependency order, that (1) ships the voice library and personal voices per account through every
layer, (2) lands one replayable-ledger abstraction (runtime reducer, gateway projection) every thin client builds on,
(3) starts moving AbstractNote's graph logic into AbstractMemory as the one semantic temporal memory graph with
ledger provenance, and (4) consolidates the shared UI primitives in abstractuic. The gateway 0.16.0 release waits for
(2); the apps release after the gateway.

## Tracks and their backlog items

| Track | Items | Status (2026-10-27) |
| --- | --- | --- |
| Voice library and personal voices | abstractvoice 0063, 0065 (done, 0.19.0/0.19.1); abstractruntime 0851, 0852 (done, 0.13.0/0.13.1); abstractgateway 0942 (done, unreleased); abstractcore 0857 (planned) | released up to the runtime; gateway main carries it |
| Architecture rule: no direct lower-level imports | abstractruntime ADR 0008; abstractgateway ADR 0001 | accepted |
| Shared UI: voice picker, create a voice | abstractuic 0.6.4 / ui-kit 0.8.9 (released); AbstractCode, Observer, Entity merged on main (unreleased); Assistant desktop branch; iPhone/watch branch | in progress |
| Replayable ledger | root 0993 (master); abstractgateway 0082, 0075; abstractruntime 0854 + ADR 0010 (reducer, durable seq, conformance cases: released in AbstractRuntime 0.14.0); gateway `/view` routes in PR #8 | runtime done, gateway pending (blocks gateway 0.16.0) |
| Memory graph consolidation | abstractnote 0033-0036; abstractmemory ADR + items (being written) | audit and design in progress |
| Shared UI primitives consolidation | abstractuic items (being written): chat, attachments, questions and approvals, tool selection, provider/model/reasoning/MTP picker, voice controls, top-right widgets, drawers | audit in progress |

## Release order

abstractvoice 0.19.1 (done) → abstractruntime 0.13.1 (done) → abstractuic 0.6.4 (done) → abstractruntime 0.14.0
(replay view) → abstractgateway 0.16.0 → abstractassistant, abstractcode, abstractobserver, abstractentity,
abstractnote, abstractflow → abstractmemory and abstractnote (memory track) → root `abstractframework` pins.

## Acceptance criteria

- [x] Every track above has its backlog item in its package, linked here (per-package evidence lives in those items; not re-audited at the root).
- [x] Each release published from a merged, green `main` (per-package PRs; the adversarial reviews are recorded in each package, not re-audited at the root).
- [x] A final per-package table: what was released, new capabilities, remaining work and improvements (below).

## Evidence (2026-10-28)

Every version below was checked visible on its registry (`pypi_visibility_gate.py`, GHCR manifest) before the root
pinned it; root 0.11.15 pins them, and the pinned set was checked for mutual `requires_dist` consistency on PyPI.

| Package | Released | Registry | What it carries |
| --- | --- | --- | --- |
| abstractcore | 2.31.0 | PyPI; GHCR `abstractcore-server:2.31.0` | Clone language over HTTP; streamed tool calls keep the declared name; MLX prefix-cache snapshot placed before per-call system riders (tool-loop calls restore the prefix instead of re-prefilling) |
| abstractmemory | 0.4.0 | PyPI | `abstractmemory.graph` (one write path of a mind), revisions, provenance, history; **one-way**: vectors rewritten as float32 BLOBs, four graph tables added |
| abstractruntime | 0.15.0 (after 0.12.0–0.14.0) | PyPI | Session tool policy (0853, in 0.14.0); replay view reducer and durable `seq` (0854, ADR 0010); memory facade, `MEMORY_REVISE`, provenance stamping, ledger row index (`ledger_<run_id>.idx`) |
| abstractagent | 0.4.0 | PyPI | `schedule_run`; prompt-prefix stability across ReAct/CodeAct/MemAct; floors runtime 0.12.0, core 2.30.0 |
| abstractgateway | 0.17.0 (after 0.16.0); console crate 0.16.0 | PyPI; GHCR `abstractgateway:0.17.0`; crates.io | Voice library and personal voices per account (0942); replay view routes (0947); session tool policy routes (0946); memory graph routes (0948); `/kg/query` owner-scoped for non-admins |
| abstractvoice | 0.19.2 | PyPI | Voice library, languages and stores; clones stay listed; cloning checkpoints in the TTS model list |
| abstractassistant | 0.15.0 | PyPI | Chat-wide tool approval through the session tool policy; Create a voice; voices grouped by owner |
| abstractnote | 0.2.0 | PyPI (Python only) | Statements with sources (0037); requires runtime 0.15.0 and memory 0.4.0. **The `@abstractframework/note` 0.2.0 web publish failed: not on npm.** Not pinned by the root (optional gateway seam). |
| abstractskill | 0.3.3 | PyPI | Bundled `abstract-release` skill |
| abstractuic | ui-kit 0.9.2, panel-chat 0.5.0 | npm | Shared UI primitives; session-policy kit and panel-chat approvals through the route (AbstractUIC #9, #11). Not pinned by the root (the apps bundle them) |
| AbstractCode web | 0.12.0 | npm | Web app release of the wave |
| AbstractObserver | 0.9.0 | npm | Web app release of the wave |
| AbstractEntity | 0.8.0 | npm | Web app release of the wave |
| AbstractContinuum | 0.7.1 | npm | Web app release of the wave |
| root abstractframework | 0.11.15 | PyPI after its tag | Pins the matrix above; Flow stays at 0.10.1 and the `abstractcode` crate at 0.10.0 (their 0.11.0 is not published) |

Remaining: `@abstractframework/note` 0.2.0 on npm; Flow 0.11.0 and the `abstractcode` 0.11.0 crate unreleased;
1061's live three-client check and its iPhone/watch and AbstractCode follow-ups.
