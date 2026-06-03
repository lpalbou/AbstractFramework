# Capability Routing Defaults

Capability routing defaults define which provider/model/backend the framework should use when a
request does not provide an explicit route.

They are configuration, not residency. A route can be configured even when the provider does not
currently have that model loaded. Loaded-model state is reported separately by provider residency
endpoints and the AbstractFlow "Loaded models" view.

## Route Keys

Routes use:

```text
<kind>.<modality>
```

Route kinds:

- `input`: understanding or enrichment of request content.
- `output`: generation targets.
- `embedding`: vectorization for retrieval and indexes.
- `rerank`: ranking routes for a future reranker manager.

Core modalities:

- `text`
- `image`
- `video`
- `voice`
- `sound`
- `music`
- `scene3d`

Examples:

- `input.text`: canonical LLM route for text understanding and text generation.
- `input.image`: VLM or captioning fallback route for images when `input.text`
  is not vision-capable.
- `input.video`: native video or video-frame understanding fallback. When
  `input.text` is known to handle visual frames, this route may be reported as
  covered by `input.text`; unlike `input.image`, it remains overrideable.
- `input.voice`: speech-to-text fallback route for audio attachments.
- `input.sound`: non-speech audio understanding route. It is not used as a
  speech-to-text fallback.
- `output.text`: read-only derived view of `input.text`.
- `output.image`: image generation backend.
- `output.voice`: TTS route.
- `output.sound`: sound effects / text-to-audio route.
- `output.music`: music generation route.
- `embedding.text`: text embedding model for semantic retrieval.
- `rerank.text`: reserved route for text reranking.

## Route Payload

Each route stores a small JSON-safe target:

```json
{
  "provider": "lmstudio",
  "model": "qwen/qwen3.6-35b-a3b",
  "base_url": "http://127.0.0.1:1234/v1",
  "options": {
    "voice": "M1"
  }
}
```

`provider`, `model`, and `base_url` are shared fields. `options` is provider/plugin-specific and can
carry values such as a voice, language, quality preset, or backend profile.

Secrets do not belong in route defaults. API keys remain provider credentials managed by
AbstractCore, Gateway deployment secrets, or the capability plugin.

## Configuration Ownership

AbstractCore owns the schema and persistence. Routes live in:

```text
~/.abstractcore/config/abstractcore.json
```

Gateway is the control plane:

- co-located Gateway reads/writes the local AbstractCore config;
- split Gateway proxies to the configured AbstractCore server;
- Gateway does not create a separate provider/model defaults file.

In split deployments, `base_url` is interpreted from the execution host that actually calls the
provider. A URL that works from the Core/Runtime host may not work from the browser or Gateway host.

## Configure From Core

Set the framework text default:

```bash
abstractcore config set-default input.text \
  --provider lmstudio \
  --model qwen/qwen3.6-35b-a3b
```

`output.text` is accepted as a compatibility alias, but Core persists it as
`input.text`. Use `abstractcore --set-global-default ...` only when you want the
older global-default helper, which now writes that same canonical route.

Configure `input.image` only as a fallback for text models that cannot accept
images. When AbstractCore's model-capability registry knows the `input.text`
model supports image input, Gateway and Core report `input.image` as covered by
`input.text` instead of as an independently editable route.

Configure `input.voice` when speech attachments should be transcribed before a
text model receives the request:

```bash
abstractcore config set-default input.voice \
  --provider faster-whisper \
  --model large-v3
```

Core does not silently use installed STT packages as a hidden fallback. If the
current text model cannot accept audio natively, `audio_policy=auto` needs this
`input.voice` route. `audio_policy=speech_to_text` remains available for
explicit per-call routing, but normal framework defaults should use the route.

Configure `input.sound` only for non-speech audio understanding such as sound
events, audio scenes, and SFX. This is not the same as STT: Whisper-style
transcription models belong under `input.voice`, while audio-language models
such as `qwen3-omni-30b-a3b-instruct`,
`qwen3-omni-30b-a3b-captioner`, `qwen2.5-omni-7b`, or
`qwen2-audio-7b-instruct` are better candidates when a provider can serve them.
`qwen/qwen3.6-35b-a3b` remains a text/image/video default candidate, not an
audio-understanding model.

Configure `input.video` when a text route should use a separate video/VLM
fallback instead of native video support or the `input.text` model's frame
support:

```bash
abstractcore config set-provider office-vlm \
  --family openai-compatible \
  --base-url https://vlm.example.com/v1 \
  --api-key $OFFICE_VLM_API_KEY \
  --description "Office vision endpoint"

abstractcore config set-default input.video \
  --provider endpoint:office-vlm \
  --model qwen2.5-vl-72b
```

If no native video route and no `input.video` default are available, Core
reports a configuration error instead of silently choosing an unrelated
vision/video backend.

Set one route directly:

```bash
abstractcore config set-default output.voice \
  --provider supertonic \
  --model supertonic-3 \
  --base-url http://127.0.0.1:5000/v1 \
  --option voice=M1
```

Configure text embeddings:

```bash
abstractcore config set-default embedding.text \
  --provider lmstudio \
  --model text-embedding-nomic-embed-text-v1.5 \
  --base-url http://127.0.0.1:1234/v1
```

or through the embedding convenience commands:

```bash
abstractcore --set-embeddings-provider lmstudio
abstractcore --set-embeddings-model lmstudio:text-embedding-nomic-embed-text-v1.5
abstractcore --set-embeddings-base-url http://127.0.0.1:1234/v1
```

## Configure Through Gateway

Use Gateway when it is the operator/control-plane entry point:

```bash
abstractgateway-config defaults

abstractgateway-config set-default input.text \
  --provider lmstudio \
  --model qwen/qwen3.6-35b-a3b \
  --base-url http://127.0.0.1:1234/v1

abstractgateway-config set-default embedding.text \
  --provider lmstudio \
  --model text-embedding-nomic-embed-text-v1.5 \
  --base-url http://127.0.0.1:1234/v1
```

With Gateway user auth enabled, the default command edits the Gateway baseline
Core config at `$ABSTRACTGATEWAY_DATA_DIR/config/abstractcore.json`. Target one
runtime explicitly with:

```bash
abstractgateway-config set-default input.text \
  --scope user \
  --tenant default \
  --user alice \
  --provider endpoint:alice-openai \
  --model gpt-4.1
```

Gateway still has deployment settings such as host, port, auth, store backend, and the Core server
URL/token it uses to reach the execution host. Those are Gateway internals, not framework model
defaults.

## AbstractFlow UI

AbstractFlow authoring surfaces treat blank provider/model pins as
`Auto (Gateway default)`. This is the preferred portable setting for LLM Call,
Agent, and generative media nodes because the saved workflow does not bake in a
deployment-specific provider/model.

Provider dropdowns include `Auto (Gateway default)` as the first option so a
user can switch back after pinning a provider.

The AbstractFlow Model Residency modal is loaded-state only:

- **Loaded models**: provider-reported runtime residency.

Changing a default route does not load a model. Loading/unloading is an operator action against the
provider/runtime residency surface. Configure capability defaults in Gateway
Console or with the Core/Gateway config CLIs.

## Related

- ADR: `docs/adr/0035-capability-routing-defaults.md`
- Gateway configuration: `abstractgateway/docs/configuration.md`
- Core configuration: `abstractcore/docs/centralized-config.md`
