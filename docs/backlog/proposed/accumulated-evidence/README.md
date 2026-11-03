# Avatar conversation: subtitles, questions and participation

Status: mixed completed/planned/proposed. **The operator authorized development of 1088/1089/1092–1095
on 2026-11-01 after checkpoint `30bcc40`.** Live participation 1092 and questions 1093 are completed; 1088/1089/1094/1095 remain planned for their residual validation. 1090 structured knowledge
and 1091 broad audit remain separately proposed. No package publication or deployment is implied.

## Experience and first delivery

A full-screen avatar is the assistant's point of contact. Two or three readable subtitle lines
communicate useful discoveries, choices/reasons, uncertainty and questions. Messages roll forward
without racing someone who is reading/replying; scrolling reveals earlier conversation and the
final answer. The person can speak or write while work continues and see a correction affect the
assistant's next actions. Technical execution remains available separately.

The earlier “readable tool cards first, semantic findings optional later” plan is superseded as
the product milestone. Deterministic summaries can help with detail, but the first useful delivery
includes actual communication and participation: 1088 + 1089 + 1092. The original IDs/filenames
and investigation are retained. No graph, Note processing run, new scheduler or framework rewrite
is a prerequisite. First prove one reversible task on one existing web host/local model; Watch
adopts the same behavior afterward.

## Roadmap and estimates

All estimates are person-days for one developer after authorization, including focused validation.
They are planning ranges, not calendar commitments; publishing/store approval is excluded.
Dependency order is explicit so the early experience can ship without every later capability.

| Task | Description | Dependencies | Expected benefit | Status | ETA / remaining work |
|---|---|---|---|---|---|
| [1088 avatar/subtitles](../../planned/accumulated-evidence/1088_readable_accumulated_observations_for_avatar_surfaces.md) | Optional dominant avatar, 2–3 subtitle lines, public history/final; original view preserved | Shared UIC; existing hosts | Understand progress in ordinary language | Source implemented; web browser checks pass | Available in checkout; manual accessibility/usability remains |
| [1089 authored brèves](../../planned/accumulated-evidence/1089_optional_findings_deltas_and_local_kv_evaluation.md) | Actor communicates through its ordinary continuation with durable provenance | Agent + Runtime/Gateway | Meaningful discoveries/choices without a per-tool extraction call | Implemented; real local GGUF correction pilot passed | Available; quantitative KV/token/memory comparison remains a separate 1–2 day validation estimate |
| [1092 live participation](../../completed/accumulated-evidence/1092_reply_to_breves_during_active_work.md) | Typed/voice guidance, fixed public referent, durable original words and chronological history | 1088/1089; owned control routes | Correct the actual work while it unfolds | Completed; source and integration tested | Available from source after stack reload; no publication performed |
| [1093 questions](../../completed/accumulated-evidence/1093_question_state_and_durable_clarification_deadlines.md) | Essential waits; 120–300s clarification with declared fallback and durable identity | Existing Runtime waits/runner; ADR0045 | Ask without silently guessing or treating silence as consent | Completed; deadline/restart/race/late-reply tests pass | Available from source; physical-device behavior checked under 1095 |
| [1094 cues](../../planned/accumulated-evidence/1094_customizable_approval_question_and_completion_cues.md) | Independent foreground visual/audio/haptic preferences by category | Stable identities and existing notification policy | Notice questions, permission requests and completion comfortably | Implemented; web/simulator coverage | Physical sound/haptic/background checks need a device session |
| [1095 Watch adoption](../../planned/accumulated-evidence/1095_watch_conversation_adoption_and_user_validation.md) | Native optional face, live replies, questions, safe durable history | Shared public semantics; existing Watch transport | Same conversation on the wrist | Source/simulator implementation; hardware/usability open | One device session plus one user session; no calendar date promised |
| [1096 shared composer default](../../completed/accumulated-evidence/1096_shared_rounded_composer_default_across_hosts.md) | Rounded multiline composer is the one panel-chat default; hosts drop hand-written textareas (Code, Assistant, Entity, Flow, Note, Continuum, Observer, Gateway console) | panel-chat 0.7.0 / ui-kit 0.9.11 | One composer contract: keyboard, IME, attach, stop, a11y live once | Completed 2026-11-01 (five repos committed) | Publish panel-chat/ui-kit, then relock and commit Flow/Note/Continuum/Observer |
| [1097 rolling subtitles and evidence bubbles](1097_rolling_subtitles_shared_rendering_and_evidence_bubbles.md) | Captions rendered by the shared message renderer, realtime rolling list (no cycling), findings as bubbles beside the avatar | 1096; 1089 typed updates | The Avatar view the operator asked for on 2026-11-01 | Proposed; operator decision gate | Re-estimate after decisions |
| [1090 optional structured knowledge](1090_session_evidence_collections_and_optional_knowledge_projection.md) | Selected triples and optional Note/session collection adapter | Pilot value; Memory/vocabulary review | Reusable/queryable accumulated knowledge | Deferred proposal; separate confirmation | Original estimate 3–5 days; re-estimate before authorization |

The original estimates were 5–9 person-days for the first conversation loop, 5–8 for questions/cues,
and 3–5 for Watch adoption. Source delivery and automated validation are recorded separately from
physical hardware, human usability, package publication and performance measurement. See the
[implementation/test record](../../evidence/1088/implementation.md) and
[real-model public evidence](../../evidence/1088/local-model.json). No MLX/HF/GGUF-wide cache claim
is inferred from one GGUF model or stable request-prefix tests.

[1091 warning/full-output audit](1091_tool_observation_preview_warning_and_retrieval_audit.md)
remains separately confirmation-gated and coordinates existing 0961. Preserve warnings/evidence
while building this view; a broad audit is not required to create the first prototype.

## Authorized question behavior

| Situation | What happens |
|---|---|
| Approval required | Existing permission wait; silence cannot approve |
| Essential question | Ask and wait for the answer; no automatic deadline |
| Ordinary clarification | Configurable 2–5 minute wait only with a safe fallback stated beforehand |
| No reply before deadline | Explain the fallback, continue accordingly and keep the question/history |
| Late answer | Retain it as a contextual correction; never answer a newer question accidentally |

Example: “Inside or outside? If you cannot answer in three minutes, I will compare both.” The
question is distinct from a tool approval. The pending question remains reachable even if its
alert is muted; asking/awaiting an answer does not mean the microphone is recording. Background
completion alerts still follow existing explicit notification policy, not a new after-run hook.

## Current evidence and sources

Exact screenshot: session `acode-dc162823ab03`, child run
`b59a77eb-37e7-4e6d-9e31-6cd1337867ef`, parent `4a4daaa7-5959-4315-af9d-5aecd7c1ea82`.
Seven persisted rendered observations total 127,620 characters. The remote run was cancelled
on 2026-10-30 during its fifth inference; it proves no local KV result. See the
[investigation and three-reviewer councils](../../evidence/1088/README.md).

Watch source currently lists technical activity and lacks ordinary in-flight tap-to-reply;
web guidance supports a bounded first pilot. ASK_USER is currently indefinite; deadline-bearing
EVENT waits/runner/indexes are reusable, but ordinary questions and expiry arbitration need work.
No current deployment or live user usability has been validated by this planning pass.

## Decisions, existing work and limits

- Root ADRs 0007/0009/0026/0027/0041/0043 apply. Proposed 0044 preserves renderer/host ownership;
  [proposed 0045](../../../adr/0045-conversational-questions-and-clarification-deadlines.md)
  records the approved question/deadline contract.
- Planned 1083 now explicitly includes question/awaiting-answer purpose. Completed 1082 provides
  source-aware interaction; proposed 1086 covers custom preview geometry.
- Memory ADR 0003 and Runtime ADR 0011 own any later graph/provenance integration.
- [Semantics 0004 Koine review](../../../../abstractsemantics/docs/backlog/proposed/0004_review_koine_general_vocabulary_and_modeling_contract.md)
  stays separate and does not block the conversation experience.
- Do not encode a permanent new wire format, pose enum or vocabulary without its contract review.
- Hub is unavailable (`[Errno 61] Connection refused`); no thread/mirror receipt was fabricated.

## Implementation

[Shared mission, contracts and test scenarios](../../evidence/1088/implementation.md) preserves the
goal across context changes. The first delivery must support both agents and entities without
replacing existing chat/technical interfaces. Independent adversarial review is required.
