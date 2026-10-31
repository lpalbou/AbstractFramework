# Avatar conversation: subtitles, questions and participation

Status: proposed. **Every item requires explicit operator confirmation before implementation.**
`decision-gate` labels prevent these proposals becoming accidental execution commitments.
Planning, code investigation and the Koine document intake were authorized; product work is not.

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

All estimates are person-days for one developer after confirmation, including focused validation.
They are planning ranges, not calendar commitments; publishing/store approval is excluded.
Dependency order is explicit so the early experience can ship without every later capability.

| Task | Description | Dependencies | Expected benefit | Status | Effort |
|---|---|---|---|---|---|
| [1088 avatar/subtitles](1088_readable_accumulated_observations_for_avatar_surfaces.md) | Dominant avatar, 2–3 subtitle lines, scrollable conversation/final, separate technical mode | Existing avatar/host; 1089 for meaningful messages | Calm, readable primary view | Proposed; confirmation required | 1–2 days |
| [1089 authored brèves](1089_optional_findings_deltas_and_local_kv_evaluation.md) | Public discoveries/choices/reasons through ordinary continuations; one local pilot | Existing actor; pair with 1088 | Understand what is unfolding and why, with low inference overhead | Proposed; confirmation required | 2–4 days |
| [1092 live participation](1092_reply_to_breves_during_active_work.md) | Speak/type while working; contextual replies and actual change of course | 1088/1089; existing guidance | First complete collaborative loop | Proposed; confirmation required | 2–3 days |
| [1093 questions](1093_question_state_and_durable_clarification_deadlines.md) | Explicit asking/waiting state; essential indefinite waits, timed clarification and declared fallback | Existing waits/runner, 1092; proposed ADR 0045 review | Ask for missing details without either blocking forever or guessing silently | Proposed; confirmation required | 4–6 days |
| [1094 cues](1094_customizable_approval_question_and_completion_cues.md) | Separate visual/audio/haptic preferences for approval, question and completion | Stable identities, 1093, current notification policy | Notice what needs attention in a personally comfortable way | Proposed; confirmation required | 1–2 days |
| [1095 Watch adoption](1095_watch_conversation_adoption_and_user_validation.md) | Native subtitle/reply/question/cue integration and real-device/user checks | Working first-host experience, 1093/1094 | Same conversation on the wrist | Proposed; confirmation required | 3–5 days |
| [1090 optional structured knowledge](1090_session_evidence_collections_and_optional_knowledge_projection.md) | Selected triples, session collection/view and optional Note adapter | Proven value from 1089; Memory facade/vocabulary review | Reusable/queryable accumulated knowledge | Deferred proposal; separate confirmation | 3–5 days, re-estimate after pilot |

First end-to-end checkpoint (1088/1089/1092): **5–9 person-days**. Questions and cues add **5–8**;
Watch adds **3–5**. Local-backend coverage beyond the first pilot is a later validation increment,
not a requirement to claim untested MLX/HF/GGUF parity. Re-estimate after the first checkpoint.

[1091 warning/full-output audit](1091_tool_observation_preview_warning_and_retrieval_audit.md)
remains separately confirmation-gated and coordinates existing 0961. Preserve warnings/evidence
while building this view; a broad audit is not required to create the first prototype.

## Question behavior to confirm

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
  records the question/deadline contract, pending confirmation.
- Planned 1083 now explicitly includes question/awaiting-answer purpose. Completed 1082 provides
  source-aware interaction; proposed 1086 covers custom preview geometry.
- Memory ADR 0003 and Runtime ADR 0011 own any later graph/provenance integration.
- [Semantics 0004 Koine review](../../../../abstractsemantics/docs/backlog/proposed/0004_review_koine_general_vocabulary_and_modeling_contract.md)
  stays separate and does not block the conversation experience.
- Do not encode a permanent new wire format, pose enum or vocabulary without its contract review.
- Hub is unavailable (`[Errno 61] Connection refused`); no thread/mirror receipt was fabricated.
