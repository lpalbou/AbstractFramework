# Install AbstractFramework

Choose the install path by deciding where inference should run. The framework APIs stay the same
across profiles; the profiles mainly change whether local inference engines are installed.

## Quick chooser

| Profile | Command | Use when | Local inference stacks |
|---|---|---|---|
| Light | `pip install abstractframework` | You use cloud APIs or endpoint servers such as LM Studio, Ollama, vLLM, llama.cpp, OpenRouter, or OpenAI-compatible services. | No |
| Apple | `pip install "abstractframework[apple]"` | You are on Apple Silicon and want local MLX/Metal-capable engines as well as endpoint providers. | Yes, Apple-focused |
| GPU | `pip install "abstractframework[gpu]"` | You have a supported discrete GPU and want local GPU-capable engines as well as endpoint providers. | Yes, GPU-focused |

Light is not a reduced-functionality framework. It is the remote-first profile: multimodal input,
multimodal output, embeddings, tools, durable runs, workflows, and Gateway/Flow still work when
they are backed by remote or local endpoint providers.

## Recommended technical install

Use a clean virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install abstractframework
abstractframework doctor
```

Use `uv` if you prefer faster environment management:

```bash
uv venv
source .venv/bin/activate
uv pip install abstractframework
abstractframework doctor
```

`pipx` is useful for isolated command-line apps, but a normal venv is usually clearer for the full
framework because Gateway, Flow, Core, and local plugins share one environment.

## Light profile

```bash
pip install abstractframework
```

Choose Light when:

- you use OpenAI, Anthropic, OpenRouter, Portkey, or other hosted providers;
- you use local model servers through HTTP, such as LM Studio, Ollama, vLLM, llama.cpp, or LocalAI;
- you want the smallest and least surprising install;
- you do not want pip to install MLX, CUDA, Diffusers, or local model-runtime stacks.

After install:

```bash
abstractframework doctor
abstractcore --config
```

## Apple profile

```bash
pip install "abstractframework[apple]"
```

Choose Apple when:

- you are on Apple Silicon;
- you want local Apple/MLX-capable inferencers in addition to endpoint providers;
- you accept larger downloads and platform-specific native dependencies.

Run:

```bash
abstractframework doctor
abstractcore --config
```

## GPU profile

```bash
pip install "abstractframework[gpu]"
```

Choose GPU when:

- you have a supported GPU stack and drivers;
- you want local GPU-capable inferencers in addition to endpoint providers;
- you accept larger downloads and platform-specific native dependencies.

Run:

```bash
abstractframework doctor
abstractcore --config
```

## Start Gateway and Flow

For a local development setup, start Gateway and Flow from their package commands or from the
workspace helper scripts when working from source. The first health check should always be:

```bash
abstractframework doctor
```

Then configure providers:

```bash
abstractcore --config
```

Gateway-hosted browser apps use Gateway user tokens and browser sessions. Do not use the bootstrap
server token as a browser login token.

## Non-technical installs

Native GUI installers are moving to the standalone
[`AbstractInstallers`](https://github.com/lpalbou/AbstractInstallers) repository. Until signed
installer artifacts are published, the supported production path is the Python install profile
described above.

## Generated install manifest

The installer-facing contract is generated from the root release profile:

```bash
abstractframework manifest
abstractframework manifest --check docs/installers/install-manifest.json
```

Installers should consume this manifest instead of maintaining independent package pins.
