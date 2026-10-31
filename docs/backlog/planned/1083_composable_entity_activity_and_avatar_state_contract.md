# 1083 — Composable entity activity and avatar state contract

> Package: abstractavatar, abstractentity, abstractruntime, abstractgateway, abstractuic, abstracttui
> Type: contract design and future integration
> Created: 2026-10-31
> Status: Planned
> Priority: medium
> Labels: entities, activity, sleep, collaboration, compatibility

## Summary

Design an evolvable presentation contract for what an agent/entity is doing. Include sleep for
maintenance, collaboration, self-directed personal time, and finer thinking/speaking activities.
This task is recorded now; rendering and contextual interaction 1081/1082 take execution priority.

## Current code reality

AbstractAvatar v1 has seven flat poses: ready, thinking, working, listening, speaking, waiting,
error. JSON descriptors are strict schema version 1; native pose codes and persisted style IDs
must remain stable. Entity interfaces already use visit/work/personal/sleep: `personal` is the
canonical phase, spoken as own time; `own_time` and `tasked` remain compatibility spellings in
abstractentity/src/workspace_panel.tsx. Actual own-time grants and life orchestration live in
Runtime/Gateway, not the avatar. A future avatar state must project this source of truth.
Runtime `identity/tool_policy.py` owns those four canonical phases; Gateway `/life_state`
supplies phase/posture and Entity `entity_state.ts` consumes them. Sleep-stage progress
(`resolution`, `world_models`, `maintenance`, `mining`, `dream`) is another existing axis:
maintenance already occurs during real sleep orchestration in Runtime `identity/life.py`.

## Requirements and design direction

- Separate lifecycle/availability, canonical life phase, sleep stage, activity family/detail and
  expressive parameters. Keep maintenance as a sleep stage and personal as the own-time phase.
  Do not continually expand a Cartesian-product enum.
- Model working/collaborating and thinking/planning or designing as refinement relationships.
  Questioning/exclaiming are speaking intent refinements. Exact labels remain open for review.
- Explicitly represent asking a task-related question and awaiting its answer, including essential
  and timed clarification behavior from proposed 1093/ADR 0045. Distinguish question purpose from
  approval waits and microphone listening; preserve legacy waiting-pose mapping until a compatible
  schema is accepted. Do not add permanent v1 pose codes just to display a question label.
- Represent sleeping/maintenance distinctly from offline/error and distinguish granted personal
  time from an actual self-directed activity. Avoid inventing a second entity lifecycle.
- Parent activity remains a predictable rendering fallback for unknown future refinements;
  unsupported schema versions still fail explicitly. Keep stable typed names and bounded values.
- Host supplies authoritative activity/reason and source/revision; renderer never infers grants,
  starts maintenance, creates tasks, performs network calls or decides autonomy policy.
- Specify precedence for simultaneous activities, transitions, pause/reduced motion, stale data,
  unknown status and sleeping/wake behavior. Shared interpolation stays deterministic/testable.
- Bound clock phase and retain precision for long-lived entities; include multi-day operation,
  hidden/resume and large time-step tests rather than accumulating an unbounded f32 tick counter.
- Backward compatibility must include a projection to legacy seven poses and append-only ABI
  identities or an explicit new ABI. No silent reinterpretation of existing codes/JSON fields.

## Expected outcomes and validation

Accepted schema/ADR with examples for maintenance, collaboration, personal reflection, planning,
designing, questioning and exclamation. Host mappings from actual Runtime/Gateway/Entity records;
conformance tests for old consumers, unknown detail fallback, conflicting signals, sleep/wake,
stale updates and native/web/TUI agreement. Introduce implementation only after contract review.

## Scope, dependencies and ADR state

Root proposed ADR 0044 records the design boundary. Depends on entity lifecycle sources and
coordinates expression research 1084. Non-goals: rewriting entity orchestration, personality
diagnosis, paid content, arbitrary fields or scripts, changing v1 merely to reserve future names.

## Related content proposals (2026-10-31)

The [avatar-conversation track](../proposed/accumulated-evidence/README.md), proposals 1088–1095,
requires explicit user confirmation before implementation. Subtitles/public brèves are host-owned
conversation content; authored meanings come from Agent/Flow, with optional triples in Runtime/Memory.
Reuse this item's authoritative activity precedence and existing selection/source identities;
do not make the Avatar renderer interpret tools, store knowledge or choose semantic truth.
Those proposals neither change this item's lifecycle nor adopt proposed ADR 0044.
The revised experience uses full-screen avatar + 2–3 subtitle lines, scrollable history/final,
natural in-work replies, explicit question state and independently configurable approval/question/
completion cues. Public brèves are now part of the first useful delivery; triples remain later work.
