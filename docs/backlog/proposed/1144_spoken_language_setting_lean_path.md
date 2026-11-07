# 1144 — Spoken language: one account setting, detected by default (lean re-implementation)

> Package: AbstractGateway (account setting + rule), AbstractUIC (shared language picker), AbstractAssistant web, AbstractCode web
> Type: feature, small; deferred
> Created: 2026-11-07 (ordered 2026-10-10 as round 18; lower halves merged 2026-11-07; upper halves PROPOSED, not planned)
> Priority: low (operator 2026-11-08: "if true, deprioritize it")
> Labels: voice, stt, settings

## Operator rulings

- 2026-10-10: add a **Spoken language** setting (Auto, or one of the supported languages) used by every transcription.
- 2026-11-07: "the language must be detected by default, unless changed by the user." No app sends a fixed language
  unless the user chose one.

## What is already on main (local, unpushed, 2026-11-07)

AbstractVoice e8e1572: `language=None` is auto on every STT engine (the manager no longer seeds mlx-whisper / remote STT
with the TTS voice's language, which had silently turned "auto" into English on Apple Macs); one supported-language list
(`abstractvoice.stt.languages`, 16 languages); `transcribe_detailed` reports the language told and the language
detected. AbstractCore 148726ec: `/v1/audio/transcriptions` answers `language` (null = detected) and `detected_language`.
AbstractRuntime a643b3c: the facts ride the child result's metadata.

## Why not merge the October branch

The round-18 branch exists in abstractgateway (3 conflicts), abstractuic (9: hold-to-talk landed since), abstractassistant
(10) and abstractcode (30: the composer was rebuilt); merging it was estimated at 12–15 h, almost all conflict work and
per-package gates. The feature itself is small.

## Lean path (4–6 h including gates)

1. Gateway: an account setting `spoken_language` (Auto | code from the voice list, validated against it), one rule for
   both transcription routes: the call's explicit hint > the account setting > auto; the answer and the run record carry
   `language` and `detected_language`.
2. AbstractUIC: one shared `SpokenLanguageSelect` (reads the list from the gateway, "Auto (detected)" first), used by the
   Assistant and Code settings; no per-app list.
3. Apps send no language unless the user picked one; Observer/Continuum verified to send none.
4. Tests: a French clip with Auto transcribes as French on an English-voiced account; a fixed language wins over detection.

## Related

Root 1001 decision 1 (the 10-10 order, recorded there 2026-11-07); branch `round18/2026-10-10` in the 4 upper repos (kept
until this item lands or is rejected).
