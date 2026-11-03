# 1032 — iPhone timed expandable activity and voice incident trace

> Package: abstractassistant
> Type: bug
> Created: 2026-10-18
> Status: Completed
> Completed: 2026-10-18
> Priority: P1
> Labels: iphone, observability, runtime, voice

## Summary

Replace generic nonexpandable model rows with meaningful step identity, public outcome,
route/model/usage and timing details. Make historical child/root events chronological and
approval history understandable. Trace the operator's completed-looking Hamlet voice
request that displayed internal router JSON instead of an audio attachment; preserve exact
run evidence and repair the proven boundary rather than guessing why generation stopped.

## Why

Operator screenshots IMG_1347/1348 show Model call/Agent cycle rows without time or detail;
tool output is the only expandable evidence. Screenshot 19.25.15 shows a mode=audio plan
as the assistant reply, not the requested generated spoken file.

## Current code reality

- `RunActivity` deliberately discards model result content, node identity and timing except
  one end/start timestamp. `ActivityEventRow` only expands nonempty detail, never shows
  time. `AnswerActivity.load` ingests all root records before child records; item order is
  traversal order, not chronological. Approval rows keep the title Approval needed after
  completion. Generic model titles hide router versus agent steps.
- Canonical orchestrator schema uses voice/music/sound, not audio, and routes unknown modes
  to an agent subflow. Runtime validates structured output and has a schema repair path.
  Exact remote selection/root+child ledgers are needed before deciding the voice fix.

## Scope

### In scope

- Expandable safe public step results/metadata and clear timestamp/duration/status/node/run
  detail, chronological replay and resolved approval wording. Preserve activity counts,
  ownership, failures, public/private boundaries and lean collapsed rows.
- Read-only saved phone/Gateway incident trace; a separately numbered workflow/runtime
  repair item if the root cause requires independent package work.
- Package/native/live checks, visual inspection, one existing adversarial reviewer,
  documentation, evidence and guarded normal iPhone installation.

### Out of scope

- Rendering private reasoning, system prompts, messages or credentials; new endpoints,
  inferring audio modality without evidence, remote package deployment or Watch edits.

## Acceptance criteria

- [x] Model/tool/wait rows expose useful public details and clear times/durations.
- [x] Events have deterministic chronological ordering across root/descendants and resolved
  approvals use past-tense status; newer/older events are easy to distinguish.
- [x] Exact voice incident selection/ledger/outcome is established and explained; a proven
  repair is implemented/tested or a concrete deployment boundary documented.
- [x] Regression tests and screenshots support the final behavior; normal app installed.

## Receipts

- Intake before production edits 2026-10-18, baseline iPhone 0.6.13 (21).
- One adversarial reviewer `tools_astra`: schema excludes audio but unknown switch is
  connected; exact run trace required rather than speculative switch changes.
- Related [1031](../completed/1031_iphone_condensed_file_and_web_activity.md),
  [1027](1027_restore_media_endpoint_resolution_and_verify_remote_iphone_images.md).
- ADR impact: None intended; authorized durable public ledger remains source of truth.

## Completion report

Completed 2026-10-18. `RunActivity` now preserves separate start/end timestamps,
chronological parent/child ordering, meaningful routing/media titles, safe public model
results, provider/model/usage/finish metadata, and subworkflow boundaries. Matching resumes
close approval/subworkflow rows; approval timing measures request to resume. Every row
expands; legacy fields stay unavailable. History is oldest first and uses local iPhone time.
Routing decisions use readable response/message/generation-prompt text rather than raw JSON.

Validation: **218 package tests** (142 AssistantKit + 76 GatewayClient); final two visual
native tests passed, with live tool/approval and compact-action regressions also passing.
The initial identifier and media-detail test failures were fixed and retained in evidence.
One adversarial reviewer inspected source and four final screenshots; final verdict Approved.
Physical Hamlet projection/voice and ordinary selection proof passed with 1033. Normal
signed **0.6.14 (22)**, without test plugins, installed/launched on the iPhone. Phone build
guard/isolated DerivedData respected Watch priority. Source/docs/bundle changes uncommitted.
README/architecture/validation and Assistant aggregate updated.

[Evidence, screenshots, review and commands](../evidence/1032/README.md).

### Insight and follow-up triage

ADR impact: None; existing authorized public ledger remains canonical. Public model output
is distinct from private reasoning; tool metadata is not an invitation to expose raw
prompts/provider payloads. Elapsed tool duration can include an approval delay; wait rows
measure that wait separately. Missing legacy fields and bounded history remain explicit.
A hosted SDK AVAudioSession main-thread warning remains in physical validation despite
moving test decode to a detached task; no functional/decoding failure observed and no
warning-fix claim made. No new urgent follow-up/priority change; general replay convergence
already lives in 0993, and unrelated remote deployment evidence remains in 1027.
