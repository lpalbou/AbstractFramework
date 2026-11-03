# Optional public conversation view

Status: Accepted — operator authorization 2026-11-01.

## Context

A tool trace explains execution to a developer, but people also need to understand useful
progress and participate while work unfolds. An avatar with short public messages provides
that conversation without replacing the existing chat, evidence, permissions or technical view.
A communicated choice such as “I am keeping the quiet café” must remain correctable through
“Please keep the accessible one too,” with the later work showing whether the correction mattered.

## Decision

Offer a second, optional view over the same run and session. Preserve the ordinary default and
its draft, attachments, history, tool policy and stop controls. Show an avatar driven by actual
activity, two or three readable subtitle lines, full public history and the final delivery.
Reading, selecting or composing pins the referent; returning to latest is explicit.

AbstractAgent owns actor-authored public updates in its ordinary continuation. The opt-in is
fixed at turn start. A bounded explicit public content envelope produces a completed Runtime
`public_update` event with stable run/cycle identity and validated observed source references.
Never derive this lane from private reasoning, tool-output summaries or fabricated progress.
Malformed or oversized messages are rejected with an explicit technical code, never clipped.
Keep the system instruction stable and preserve the existing append-only model transcript.
No extra inference call is required for publishing a brève; added output tokens still cost time.
Backend KV reuse remains a measured provider property, not a consequence of this protocol.

Runtime owns durable records; Gateway owns authenticated control and safe projection. Accepted
human guidance has a distinct host-provenanced `user_guidance` receipt preserving the original
words separately from a quoted public referent. Acceptance is neither delivery nor adoption.
Ordinary operational steers cannot masquerade as human speech. Preserve source words through
receipt failure and repair before acknowledgment. Entity visits use their owned visit routes
and fresh attribution/recall boundary; generic visit steering stays refused. Ordinary summoned
Flows retain their established authenticated command path.

Questions and approvals use existing authoritative interactions. Follow ADR0045 for durable
question identity, essential waits and declared clarification deadlines. Silence, cue dismissal,
view changes and ordinary messages never grant permission. Visual/audio/haptic cues are
independently configurable by category, silent on initial history and reconnect, and foreground
only unless an explicit authorized notification node requests background delivery (ADR0041).
Required-attention cues remain eligible during reading; narration does not interrupt reading,
recording or composing. Microphone, playback and task stop have separate effects.

Clients render validated public projections, preserve final files and results, and retain the
technical view for source inspection. Do not add a mandatory graph, AbstractNote ingestion,
new scheduler, new avatar ABI or universal framework refactor to obtain this experience.
Controlled triples remain a separate proposal.

## Consequences

Public communication adds small decoding and ledger/UI work and depends on model compliance.
Some continuations have nothing useful to publish. A source reference establishes lineage,
not truth. Legacy runs cannot acquire missing brèves retrospectively merely by changing views.
Provider performance and physical-device usability require their own evidence.

## Enforcement

Opt-in parser tests protect legacy prompt/tool bytes and explicit content ownership. Runtime and
Gateway tests enforce host receipt provenance, participant authority, privacy and replay. Shared
UI tests cover public-only messages, stable selection, spoken-message identity, attention,
finite-stream completion and default-view compatibility. Hosts must use the canonical producer
artifact or released package; no hand-edited compatibility bundles.

## Validation

Require a real correction loop in addition to fixtures: an actor publishes a choice, receives
original human words, changes a subsequent action and explains its final choice. Exercise built
web hosts, exact pending-question routing, refusal/draft preservation, source history, voice
pause/resume, silent replay and default-mode regressions. Record simulator checks separately
from physical voice, haptics, background and human usability. Do not claim KV hit rate from an
unchanged request prefix alone.

## Related

- [Implementation and validation record](../backlog/evidence/1088/implementation.md), originating
  items [1088/1089/1092–1095](../backlog/planned/accumulated-evidence/README.md).
- [Question policy](0045-conversational-questions-and-clarification-deadlines.md).
- [No hidden post-flow effects](0041-no-hidden-effects-after-a-flow.md).
- [Readable labels](0043-readable-labels-never-computer-ids.md).
- ADR0044 remains a separate broader presentation proposal.
