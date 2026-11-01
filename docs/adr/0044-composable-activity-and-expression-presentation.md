# Composable activity and expression presentation

Status: Proposed

## Context

AbstractAvatar renders seven flat activity poses, while entity applications already distinguish
visit/work/personal/sleep and granted self-directed personal time. Collaboration, planning,
designing and speaking intent require finer detail without multiplying every possible pose.
Stable persona, momentary expression and operational truth are different inputs.
UIC/Entity already expose evidence-gated cognition registers, valence/arousal, spring morphing
and fact-based conduct. Future avatar expression should adapt those signals where suitable,
preserving abstention/provenance rather than creating a parallel model or a frame-loop scorer.

## Proposed decision

Keep the current v1 contract stable. Design a future version with separate bounded channels:

1. Host-owned lifecycle/availability, canonical entity phase and optional sleep stage/reason,
   projected from actual entity/runtime status. Maintenance is a sleep stage, not a new phase.
2. An activity family and optional refinement, with explicit parent fallback.
3. Optional momentary expression values, with defaults and source/provenance.
4. Optional stable persona/style influence, distinct from transient activity and expression.

Authoritative security/approval/connection indicators remain outside expressive appearance.
The host owns grants, work, collaboration and maintenance. AbstractAvatar owns deterministic
visual generation and shared interpolation; UIC/TUI own presentation, visibility and input.
Renderers perform no network, assessment, payment, orchestration or autonomous action.

Future refinements may include working/collaborating, thinking/planning, thinking/designing and
speaking/questioning. The conversational experience explicitly needs a semantic question purpose:
asking the person something and awaiting an answer must remain distinct from tool approval,
microphone listening and generic working. Host state/labels may project this to legacy waiting
without a new v1 pose code. Accepted ADR 0045 owns critical versus timed clarification behavior.
These examples do not reserve final persisted names. `personal` remains
the existing entity phase; “own time” is its human-facing wording, not a new autonomy grant.

## Compatibility and review gates

- Preserve legacy pose/style identities and strict descriptor validation.
- Version new fields explicitly; define a legacy projection and unknown-detail parent fallback.
- Document simultaneous activity precedence, transitions, staleness and sleep/wake semantics.
- Keep trait-framework research and instrument licensing separate from the rendering API.
- Adopt this ADR only after host mappings and conformance examples are reviewed; do not ship
  provisional lifecycle/trait fields as a permanent v1 extension.

## Implementation tracking

[1083](../backlog/planned/1083_composable_entity_activity_and_avatar_state_contract.md) owns the
contract design; [1084](../backlog/proposed/1084_entity_expression_and_personality_grounded_visual_behavior.md)
owns expression/personality research. Rendering and contextual interaction take priority under
[1081](../backlog/completed/1081_avatar_rendering_fidelity_and_platform_quality.md) and
[1082](../backlog/completed/1082_contextual_content_selection_and_agent_steering.md).
The confirmation-gated [conversation track](../backlog/proposed/accumulated-evidence/README.md)
adds avatar subtitles, live replies, explicit questions and configurable cues; none is implemented
or authorized by this proposed ADR.
