# Accumulated-evidence investigation and adversarial council

Verified 2026-10-31. This record supports proposed 1088–1091; it does not approve implementation.
Raw tool outputs, provider payloads and credentials are deliberately not copied into this evidence
directory. [Measured fields](run-observation-measurements.json) were independently derived from
the existing local ledger after an authenticated Gateway lookup matched all seven tool signatures.

## Exact example and size

- Session: `acode-dc162823ab03`.
- ReAct child run: `b59a77eb-37e7-4e6d-9e31-6cd1337867ef`.
- Parent: `4a4daaa7-5959-4315-af9d-5aecd7c1ea82`.
- Run time: 2026-10-30 18:53:00–18:53:57 UTC (19:53 Europe/Paris).
- Screenshot time: 2026-10-31 12:03 Europe/Paris; it depicts the previous day's run.
- State: cancelled during model call five, after seven successful tool executions.
- Provider/model: remote `endpoint:airelay` / `gpt-5.6-terra`. No local KV result inferred.
- Local source: `runtime/ledger_b59a77eb-37e7-4e6d-9e31-6cd1337867ef.jsonl`.

| Tool/scope | Recorded observation characters | Interpretation limit |
|---|---:|---|
| Command: cwd and git status | 349 | Empty short-status output at that historical instant |
| Folder inventory | 23,006 | Depth 2, 220-directory traversal limit; 40/149 notable files shown |
| Image filename listing | 2,928 | First 30 entries; scanned composition counts 530, not an exhaustive total |
| Search in abstractcode-tui | 41,768 | 30/121 matching files shown; 91 more |
| Search in abstracttui | 56,501 | Stopped at 30 matching files; total unknown |
| Web-search leads | 2,589 | Five leads, degraded fused wording; source verification needed |
| Command printing approval-test prose | 479 | Successful printf only; approval-gate behavior unproven |
| Total | **127,620** | Unicode characters including tool labels, not tokenizer counts |

The fourth completed model request contained six tool messages totalling 127,141 characters.
The fifth recorded request contains seven totalling 127,620; cancellation means provider processing
of that last request cannot be established from this ledger. The run has no approval-wait records.
The final command's printed claim about approval gating is not evidence that the gate was tested.

Usable deterministic presentations include "No changes listed in the workspace check at 19:53"
and "30 of 121 matching files shown". Neither broad code matches nor web snippets establish a
rendering capability. This run supports expandable sources and scoped operational observations;
it cannot establish universal extraction quality or local cache performance.

## Truncation and registry check

Both command outputs have `stdout_truncated=false` and `stderr_truncated=false`. Core's command
tool emits truncation prose and flags when its 20k/5k previews cut content; previous discussion
should not be read as alleging those command previews are silent. Full streams can be artifact
backed, but the model's `output.rendered` path does not automatically include every structured
field/reference. Proposed 1091 checks that distinction end to end and coordinates existing 0961.

The ADR skill is already bundled under `abstractskill/src/abstractskill/registry/skills/adr`,
with an adopted host validation in `registry/validations.yaml`. Existing bundled-content and
registry-inventory tests passed (2 tests); no duplicate registry entry was added.

## Council execution and iteration

Three independent workers, each read-only, completed an initial investigation and a second
adversarial round. Their source observations were shared for rebuttal before synthesis.

| Perspective | Initial position/challenge | Final result |
|---|---|---|
| Minimalist / runtime trace | Find the actual run; test whether existing observations suffice | Recommend presentation; semantic/graph stages with reservations |
| Platform / Note–Memory boundary | Investigate reuse of Note extraction and a shared graph; challenge raw-output UX | Recommend with reservations; avoid Note application dependency and separate graph |
| UX / local extraction economics | Challenge factual overclaiming, output-format cost and mandatory extraction | Recommend with reservations; bounded cards first, opt-in semantic deltas and projection |

Changes driven by the adversarial round:

- Observation-only dumping rejected for the default avatar surface after measuring 127k chars;
  retained as the expandable source. Typed deterministic captions can be useful without inference.
- Platform's earlier sidecar-first experiment preference changed under the explicit local-KV
  constraint: next-normal-continuation extraction is the preferred semantic candidate, subject to
  task/tool validity and measured cache/latency gates.
- Mandatory per-tool model extraction, automatic KG promotion and a required full Note run rejected.
- Cancellation became an explicit coverage test: immediate observations survive, while an unfinished
  model continuation must not imply completed semantic interpretation.
- Process provenance and supporting evidence stay distinct. Successful printf cannot validate the
  printed assertion. Quote/source existence does not by itself establish entailment.
- Session collections remain an optional query/membership scope over Memory, with strict owner/mind
  boundaries. The Note private projection is existing convergence debt, not a new session store.

The remaining tension is useful semantic condensation versus extra decode/output-contract work.
No local performance experiment ran; MLX/HF/GGUF measurements require confirmation under 1089.

All three workers subsequently read the written artifacts and passed them. Platform's final
refinement was adopted: a Note adapter is conditional on confirmed scope, so generic session
collections do not wait for Note integration. New-item IDs/links/decision gates, recursive counts,
PDF byte identity and ADR-skill validation hash were checked; root `llms-full.txt` remains current.

## Direct agent-loop precedents

These are closer than corpus GraphRAG to the requested loop-level accumulation:

- Hugging Face smolagents periodically refreshes learned/missing/derivable facts from execution
  history in its [planning prompts](https://github.com/huggingface/smolagents/blob/main/src/smolagents/prompts/code_agent.yaml),
  with observations retained in [action memory](https://github.com/huggingface/smolagents/blob/main/src/smolagents/memory.py).
- LlamaIndex's [AgentWorkflow research example](https://developers.llamaindex.ai/python/examples/agent/agent_workflow_multi/)
  uses `record_notes` to accumulate research notes in shared state during agent execution.

These are direct precedents for accumulating knowledge during agent work, not verified equivalents
of claim-level supporting evidence plus local-KV-aware extraction and avatar presentation.

## Governing boundaries and authorization

Root ADRs 0007/0009/0026, proposed 0044; Memory accepted ADR 0003 and Runtime accepted ADR 0011.
Existing 1082/1083/1086 and 0961 are linked by the proposals without silently replacing their scopes.
All four new root items and Semantics 0004 are proposed, decision-gated and awaiting explicit user
confirmation before undertaking their work. No product code, running state or package release
changed. The Koine PDF copy/intake is completed; scientific review/adoption has not begun.

Agora identity/inbox calls returned `[Errno 61] Connection refused`; no alternate hub, listener,
claim, thread or mirror receipt was fabricated.

## Subsequent conversational-design iteration and roadmap revision

The operator clarified that the desired experience is an incarnated avatar with brief ordinary
communication and natural intervention, not Elicit-style research output or a renamed tool log.
A further two-round three-worker council covered conversational minimalism, truthful control,
and accessibility. All favored replyable brèves over a passive feed or continuous spoken narration.
They required natural replies without compulsory selection, stable reference when a prior message
is selected, quiet/repeat controls, and a real change of work after the actor considers a correction.
Saved Watch artifacts/current source were inspected, not a live prototype. Current thinking-time
Watch input and decoded technical activity need adaptation; web guidance is a useful first pilot.

The subsequent operator request specifies full-screen avatar + two/three subtitle lines, scrolling
to history/final, explicit ask-question state and separate configurable approval/question/finished
visual/audio cues. Critical questions wait; lesser clarifications can use a declared two-to-five-
minute window and fallback. The revised track makes 1088/1089/1092 the first useful delivery and
adds 1093/1094/1095. All remain confirmation-gated. Initial deterministic-only card milestones in
this historical council record are superseded by that later product clarification.

Current-code question audit (2026-10-31): ASK_USER is indefinite USER; WaitState already has
until/details; EVENT/UNTIL expiry, SQLite indexing and Gateway wake are reusable. Strict timed
ordinary questions require coordinated representation/index/handler work. Existing resume does
not enforce the deadline itself, so late-answer arbitration and repeated-question generation are
explicit acceptance criteria, not claimed present functionality. Proposed ADR 0045 records the
policy for review. No implementation, scheduler, live notification or graph was created.
