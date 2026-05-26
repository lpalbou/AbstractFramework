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
- `scene3d`

Examples:

- `input.text`: model used to understand text input.
- `input.image`: VLM or captioning route for images.
- `output.text`: model used for text generation.
- `output.image`: image generation backend.
- `output.voice`: TTS route.
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
abstractcore --set-global-default lmstudio:qwen/qwen3.6-35b-a3b
```

This writes explicit `input.text` and `output.text` route defaults while older config fields still
exist for compatibility with lower-level code.

Set one route directly:

```bash
abstractcore --set-capability-default output.voice \
  --capability-provider supertonic \
  --capability-model supertonic-3 \
  --capability-base-url http://127.0.0.1:5000/v1 \
  --capability-option voice=M1
```

Configure text embeddings:

```bash
abstractcore --set-capability-default embedding.text \
  --capability-provider lmstudio \
  --capability-model text-embedding-nomic-embed-text-v1.5 \
  --capability-base-url http://127.0.0.1:1234/v1
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

abstractgateway-config set-default output.text \
  --provider lmstudio \
  --model qwen/qwen3.6-35b-a3b \
  --base-url http://127.0.0.1:1234/v1

abstractgateway-config set-default embedding.text \
  --provider lmstudio \
  --model text-embedding-nomic-embed-text-v1.5 \
  --base-url http://127.0.0.1:1234/v1
```

Gateway still has deployment settings such as host, port, auth, store backend, and the Core server
URL/token it uses to reach the execution host. Those are Gateway internals, not framework model
defaults.

## AbstractFlow UI

The AbstractFlow model residency modal separates:

- **Loaded models**: provider-reported runtime residency.
- **Defaults**: execution-host route defaults for input/output/embedding/rerank.

Changing a default route does not load a model. Loading/unloading is an operator action against the
provider/runtime residency surface.

## Related

- ADR: `docs/adr/0035-capability-routing-defaults.md`
- Gateway configuration: `abstractgateway/docs/configuration.md`
- Core configuration: `abstractcore/docs/centralized-config.md`
