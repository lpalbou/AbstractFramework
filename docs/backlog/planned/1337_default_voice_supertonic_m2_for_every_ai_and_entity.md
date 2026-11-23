# 1337 — Default voice: Supertonic M2 for every AI and entity (OpenAI voice when no local voice)

> Package: framework (abstractcore recommendation data, abstractgateway entity birth + config upgrade)
> Type: improvement
> Created: 2026-11-22
> Priority: high
> Labels: voice, defaults, first-run, entities, install

## Summary

On a fresh install every AI (assistant, code, observer, any bare TTS request) and every entity should speak
with Supertonic voice `M2`. Today the voice ENGINE default is Supertonic but no voice is named, so bare
requests speak the engine fallback `M1`, and a new entity is born with **no voice at all** (speaking refuses
with 409 "has no voice yet") until someone picks one by hand. Where no local voice engine is installed, the
default should be an OpenAI voice instead.

## Why

Operator, 2026-11-22 (Windows validation machine): "It seems the default setup might not have set the
supertonic model M2 by default for AI and entities? set it as default unless you find a reason not to. [...]
in a light install, it would have to use by default the openai voice i think."

Found while investigating: entity `gandalf` speaks M2 only because `person:admin` chose it manually
(identity rev 2, 2026-11-22T00:51Z); at birth (rev 1, 2026-11-18) its voice was `null`.

## Current code reality (audited 2026-11-22, three independent read-only passes)

- **Recommended route names no voice.** `abstractcore/abstractcore/config/capability_defaults.py:395-399`:
  `"output.voice": RecommendedModel(route=CapabilityRouteDefault(provider="supertonic", model="supertonic-3"), ...)`
  — no `options={"voice": ...}`. `M2` appears only as an example (`capability_defaults.py:1151`).
- **Bare requests fall to the engine default `M1`.** The gateway fills the `output.voice` route only into a
  completely bare request (`abstractgateway/routes/gateway.py:2402-2460`, `13372-13384`); Supertonic's adapter
  defaults to `M1` and silently coerces unknown voices to `M1` (`abstractvoice/adapters/tts_supertonic.py:47,79-80,239`).
- **Entities are born voiceless.** `gateway_default_voice()` (`abstractgateway/entity_identity.py:253-269`)
  returns the route only if it names provider, model AND `options.voice`; otherwise the birth identity
  (`routes/entities.py:178-216`, `abstractruntime/identity/digital_identity.py:587-640`) records `voice: null`
  and speaking raises 409 (`routes/entities.py:6405-6408`). The voice is frozen in `identity.json` at birth; the
  boot pass never rewrites a record (`entity_identity.py:455-474`).
- **Seed and installs.** The AbstractCore seed runs only when `abstractcore.json` does not exist
  (`config/manager.py:972-985`) and drops routes whose engine is missing (`capability_defaults.py:836-843`,
  `route_engines.py:287-314`). The one-line installers put `abstractvoice[supertonic,stt]` on EVERY profile,
  light included (`scripts/install.ps1:155-158`, commit 9cc0b0b; Windows ARM64: Supertonic only). So "no local
  voice" only happens on a plain `pip install` light, a failed voice install, or a manual setup. There is no
  OpenAI voice row in the seed today; with no route at all abstractvoice's plugin falls to `openai`/`alloy`
  (`integrations/abstractcore_plugin.py:1668`, `adapters/tts_openai_compatible.py:61,74`), which errors without a key.
- **Platforms.** Supertonic is abstractvoice's own ONNX Runtime implementation (`supertonic/runtime.py`), weights
  `Supertone/supertonic-3` (~401 MB, pinned revision, cached in `~/.cache/abstractvoice/supertonic-3`), CPU
  everywhere, CUDA when present, CoreML on macOS; no OS guard. Voices are exactly `M1`–`M5`, `F1`–`F5`.
- **Overrides that legitimately win** (no change): per-app `route_overrides["output.voice"]` and
  `ABSTRACTASSISTANT_*TTS_VOICE` (abstractassistant `controller.py:2690-2712`), browser-stored voice prefs
  (assistant web, abstractcode, observer via ui-kit `use_voice_preferences.ts`), session identities,
  per-user default overlays (`core_config.py:1724-1744`), entity voices with `source: chosen`.
- Related: [1069](../proposed/1069_first_run_default_models_per_modality.md) ("voice out: Supertonic by
  default", no voice named); gateway PR #48 (refuses a default voice whose model is not downloaded).

## Scope

### In scope

1. **One source of truth:** add `options={"voice": "M2"}` to the recommended `output.voice` row in
   `capability_defaults.py`. This alone feeds the first-install seed, the wizard's "Use recommended defaults",
   bare TTS requests, and new entities (born with `M2`, `source: default`).
2. **No local voice engine:** a per-host alternative recommendation (the existing `AcceleratorPick`/per-host
   mechanism, not a new one): when the Supertonic engine is missing AND an OpenAI key is configured, recommend
   `openai / gpt-4o-mini-tts / <voice>`; without a key, leave the route unset and say why (as today). In practice
   the wizard applies it (its Cloud providers step precedes Default models; the seed runs before any key exists).
3. **Existing installs:** a config upgrade step in the style of the existing ones (`capability_defaults.py:293-301`):
   if the stored `output.voice` route is exactly `supertonic/supertonic-3` with no `options.voice`, set
   `options.voice = "M2"`. Never touch a route that names a voice or another engine.
4. **Existing entities:** fill only identities whose `voice` is `null` with the gateway default, recorded as
   `source: default` (decision below). Never touch `source: chosen`.
5. Docs: gateway first-run/voice docs and the root install docs state the default voice and the no-local-voice case.

### Out of scope

- Changing abstractvoice's library fallbacks (`M1` for Supertonic, `alloy` for OpenAI): they stay neutral engine defaults.
- Overriding any voice a person chose (app prefs, browser prefs, env vars, `source: chosen` identities).
- Re-resolving entity voices at speak time (the voice stays part of the frozen identity).
- The other first-run inconsistencies found in the same audit (light seeds an LM Studio text route without
  LM Studio; NVIDIA image route only via the wizard; `install.ps1` lacks the "download the default voice" hint;
  README says "Light (default)" but the one-liner auto-detects) — separate items.

### Decisions needed (operator)

- Which OpenAI voice for the no-local-voice case (`alloy` is the engine fallback today)?
- Backfill existing `voice: null` entities (scope 4), or keep the "has no voice yet" prompt for them?

## Acceptance criteria

- [ ] A fresh install (new `abstractcore.json`) on Windows, Linux and macOS seeds `output.voice` = supertonic / supertonic-3 / `M2`; `GET /api/gateway/voice/defaults` reports voice `M2`.
- [ ] A bare TTS request (assistant with no override) speaks `M2`.
- [ ] An entity created through the console/entity app is born with voice `supertonic/supertonic-3/M2`, `source: default`, and speaks without a 409.
- [ ] An install without the Supertonic engine but with an OpenAI key gets the OpenAI voice route from "Use recommended defaults"; without a key the route stays unset with a stated reason.
- [ ] Upgrading an existing install whose stored route is supertonic with no voice gains `M2`; a stored route naming any voice is unchanged (test).
- [ ] An entity with `source: chosen` is never modified (test).

## Testing

- `cd abstractcore && python -m pytest tests -k "capability_defaults or recommended" -q`
- `cd abstractgateway && python -m pytest tests -k "entity_identity or default_voice or voice_defaults" -q`

## Receipts

- Investigation 2026-11-22 (session on the Windows validation machine): live `GET /api/gateway/voice/defaults` → `tts: supertonic / supertonic-3, voice: null`, seed `recommended-v2`; gandalf `identity.json` voice M2 `source: chosen`, `state_history.jsonl` rev 1 `voice: null`.
