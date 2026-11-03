# 1007 — Assistant (v1) interface: voice, per-model settings, sound and media outputs

> Package: abstractflow, abstractassistant, abstractgateway
> Type: task
> Created: 2026-10-11
> Priority: normal
> Labels: interfaces, assistant, voice, media

## Summary

The Assistant interface (`abstractassistant.agent.v1`, "Assistant (v1)") got its own contract on
2026-10-11: the agent trio required, plus OPTIONAL On Flow Start pins for the provider and model of each
modality the workflow generates (image, image edit, upscale, video, image to video, music), the sound
output spec and the image a request refers to. Four parts of the operator's ask are not covered yet:
voice in and out, settings some models need beyond provider/model, sound as provider/model pins, and the
generated media on On Flow End.

## Why

Operator, 2026-10-11: "we must have ALL the (provider/model) for ALL input & output modalities, but that
they should be optional (and by default, using the gateway default) [...] important note: some
(provider,model) requires more information (eg TTS language, voice, etc). but the goal is not to break
what currently works either [...] if we can't do everything here, then we need to create also a
$backlog item to continue to revise and optimise this."

## Current code reality (2026-10-11)

- Contract: `abstractflow/src/utils/flowFamilies.ts` `KNOWN_INTERFACES` (`optionalStartPins` is new;
  `interfaceBoundaryPins` flags them `optional`; preflight never asks for them).
- The Assistant orchestrator (`abstractassistant/abstractassistant/assistant_workflow.py`) declares the
  interface and has every optional pin with the same type; its chat branch runs `basic-agent` as a
  subflow.
- Voice is not in the workflow: speech-to-text and text-to-speech (language, voice, quality) run in the
  Assistant app through the gateway's voice routes (`abstractassistant/core/gateway_voice_manager.py`),
  with the app's own provider/model overrides (`input.voice`, `output.voice`).
- Sound: the override rides inside the `sound_output` spec object (an `llm_call` whose output spec selects
  the sound capability), not as `sound_provider` / `sound_model` pins.
- Media results: each media branch's On Flow End carries `artifact`, `artifact_id`, `content_type`,
  `outputs` and per-kind artifacts, but the interface requires only response/success/meta.

## Scope

### In scope

- Decide whether voice (STT/TTS) belongs to the assistant workflow contract; if so, optional pins for it
  (provider, model, and the settings TTS needs: language, voice) without breaking the app's current voice
  routes.
- A way for an interface to carry per-model settings beyond provider/model (one pattern, not per model).
- `sound_provider` / `sound_model` optional pins, if the runtime's sound node can take them as pins.
- Optional On Flow End pins for the generated media (the artifact), so a caller reads them by contract.

### Out of scope

- Renaming the interface id (1006).
- Changing the required pins.

## Acceptance criteria

- [ ] Every input and output modality the Assistant can use has an optional provider/model pin, or a
      recorded reason why not.
- [ ] The orchestrator still matches the interface (a test compares pin ids and types).
- [ ] Nothing that works today changes behavior when the optional pins are empty.

## Receipts

- (to fill)
