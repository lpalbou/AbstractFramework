# ADR 0047: Voice transport is never an attachment

Status: Accepted — operator ruling 2026-11-02.

## Context

A person speaks a question to the watch or the phone; the app uploads the recording so the
gateway can transcribe it. An answer is read aloud; the gateway synthesizes the speech and keeps
the sound as an artifact so a reading can be replayed. Both recordings are stored in the same
artifact store as a person's real attachments (a PDF, a photo) and the media an answer generates
(an image, a song). On 2026-11-02 the iPhone app listed `tts-….wav` rows under every answer that
had been read aloud, and a `File-…` row for a spoken question, because it rebuilt the conversation
from the gateway's history bundle, whose per-turn artifact list carried them. Nothing in the
protocol said these sounds were different from a generated song.

They are different. The recording of a spoken question is how the question travelled; the
synthesized reading is how the answer travelled. Neither is content a person attached or asked for,
and showing them makes a conversation unreadable and leaks the mechanics of the app into it.

## Decision

The recording of a person's spoken input and the audio synthesized to read an answer aloud are
**voice transport**: never an attachment, never media of the conversation, in every app
(AbstractAssistant on watch, phone and web, AbstractCode, AbstractObserver, AbstractEntity, the
gateway console) and in every projection of a conversation the gateway serves.

1. **Producers tag it.** The gateway stamps every read-aloud artifact with
   `purpose: "voice_playback"` and `artifact_space: "voice"` (already the case,
   `abstractgateway/voice_artifacts.py`), and every upload into the reserved `voice/dictation/`
   namespace with `purpose: "voice_dictation"` and `artifact_space: "voice"`. The tags are the
   contract; a file name or a content type never is.
2. **Conversation projections hide it by default.** The session artifacts listing, the history
   bundle's session turns (`attachments` and `artifacts`), conversation search and any later
   "what this conversation contains" view exclude voice transport unless the caller asks for it
   explicitly (`include_voice=true`). The full run bundle used for replay and audit stays
   complete: hiding is a conversation rule, not a deletion.
3. **Clients hide it defensively.** A client that renders attachments or media from any
   artifact list applies the same tag rule (shared Swift: `SessionTurn.isVoiceTransport`), so an
   older gateway or a new projection never puts a recording on screen. Playback of a reading
   stays a voice control (the speaker button, replay), never an attachment row.
4. **Transcripts are text.** The transcription of a spoken question is the question; it is shown
   as the person's words, never as a "derived text" file.

## Consequences

Positive: conversations show what people attached and what the assistant made, and nothing else;
the rule is one predicate in each layer, decided by tags.
Negative: a person cannot open their own spoken recording from the conversation; a dedicated
voice history (if ever wanted) is a separate, explicit surface. Projections that compensated
by file name (`tts-` prefixes) must move to the tags.
Neutral: `include_voice=true` keeps the old listing for tools that need every artifact.

## Enforcement

- Code review: any new artifact list rendered as attachments or media must cite this ADR and
  filter with the shared predicate; a filter keyed on file names is rejected.
- The gateway's upload route is the only place that classifies dictation; clients only use the
  reserved namespace. A new voice lane (a voice note the person records on purpose, a generated
  song) must NOT reuse `purpose: voice_playback`/`voice_dictation`: it is content and is shown.
- Search `voice_playback`, `voice_dictation`, `isVoiceTransport`, `is_voice_transport` to find the
  enforcement points.

## Validation

- AbstractRuntime: history bundle session turns with a read-aloud artifact, a dictation
  attachment and an image carry only the image.
- AbstractGateway: an upload under `voice/dictation/` gets the dictation tags; the session
  artifacts listing hides both transport kinds by default and returns them with `include_voice`.
- Shared Swift package: `SessionTurnVoiceTransportTests` (bundle turn decoding; the predicate by
  tags, not names).
- Manual: open a conversation that was spoken and read aloud on the phone and the watch — no
  `.wav` row appears under the question or the answer.

## Backlog links

- Originating work: the 2026-11-01/02 watch and phone voice stall and history-bundle changes
  (`untracked/voice-stall/REPORT.md`, uncommitted at the time of writing).
- Adoption: gateway upload tagging, runtime bundle filter, shared Swift predicate (this change);
  web assistant, Code TUI and console audits are follow-ups.

## Related

- ADR 0046 (public conversation view) — the same conversation surfaces.
- `abstractgateway/src/abstractgateway/voice_artifacts.py`, `abstractruntime/history_bundle.py`
  (`_best_effort_session_turns`), `AbstractGatewayClient/Models.swift` (`SessionTurn`).
