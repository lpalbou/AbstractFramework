# Install AbstractFramework

Choose the install path by deciding where inference should run. The framework APIs stay the same
across profiles; the profiles mainly change whether local inference engines are installed.

## Quick chooser

| Profile | Command | Use when | Local inference stacks |
|---|---|---|---|
| Light | `pip install abstractframework` | You use cloud APIs or endpoint servers such as LM Studio, Ollama, vLLM, llama.cpp, OpenRouter, or OpenAI-compatible services. | No |
| Apple | `pip install "abstractframework[apple]"` | You are on Apple Silicon and want local MLX/Metal-capable engines as well as endpoint providers. | Yes, Apple-focused |
| GPU | `pip install "abstractframework[gpu]"` | You have a supported discrete GPU and want local GPU-capable engines as well as endpoint providers. | Yes, GPU-focused |

### Requirements per profile

| Profile | Platforms | Python | Notes |
|---|---|---|---|
| Light | macOS, Linux, Windows | 3.10–3.13 | No local inference engines. |
| Apple | macOS 14 or later on Apple Silicon | 3.10–3.13 | MLX wheels need macOS 14+. F5-TTS voice cloning needs Python 3.11+; the rest of the profile works on 3.10. |
| GPU | Linux (and Windows where the engines publish wheels) with NVIDIA CUDA or AMD ROCm drivers | 3.10–3.13 | F5-TTS voice cloning needs Python 3.11+; the rest of the profile works on 3.10. |

`abstractframework` 0.1.12 pins `abstractgateway==0.2.30`, `abstractassistant==0.5.0`,
`abstractcore==2.13.42`, `AbstractRuntime==0.4.32`, `abstractagent==0.3.13`,
`AbstractMemory==0.3.0`, `abstractsemantics==0.0.5`, `abstractvoice==0.11.3`,
`abstractvision==0.3.29` and `abstractmusic==0.1.15`. The `apple` and `gpu` extras select
`abstractgateway[apple|gpu]` and `abstractassistant[apple|gpu]` at the same versions
(`abstractassistant[apple]` is installed on macOS only). `abstractframework doctor` reports any
installed package whose version differs from these pins.

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

## Apps and tools outside pip

The browser apps and the Rust terminal tools are not Python packages, so no profile installs them.
Run or install them next to the Python stack:

| Tool | Command | Version released with 0.1.12 |
|---|---|---|
| Gateway web console | built into `abstractgateway`: open `http://127.0.0.1:8080/console` after `abstractgateway serve` | 0.2.30 |
| Gateway terminal console | `cargo install abstractgateway-console` (Rust 1.87+), then `abstractgateway-console --url http://127.0.0.1:8080` | 0.6.0 |
| Flow Editor | `npx @abstractframework/flow` | 0.3.20 |
| Code Web UI | `npx @abstractframework/code` | 0.4.2 |
| Observer | `npx @abstractframework/observer` | 0.1.12 |
| Continuum console | `npx @abstractframework/continuum` | 0.2.0 |
| Entity manager | `npx @abstractframework/entity` | 0.1.0 |
| AbstractCode terminal client | `cargo install abstractcode`, or a prebuilt binary from the [AbstractCode GitHub release](https://github.com/lpalbou/AbstractCode/releases) | 0.5.1 |

The browser apps need Node.js 18 or later and a running gateway. Optional Python add-ons outside the
profiles install on their own: `pip install abstract3d`, `pip install abstractcamera`,
`pip install abstractskill`.

## Start Gateway and Flow

Start the gateway, then open a browser app against it:

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
npx @abstractframework/flow
```

When you work from source, the workspace helper scripts build and start the same services (see
[Workspace scripts](workspace-scripts.md)). The first health check should always be:

```bash
abstractframework doctor
```

Then configure providers:

```bash
abstractcore --config
```

Gateway-hosted browser apps use Gateway user tokens and browser sessions. Do not use the bootstrap
server token as a browser login token.

## Container deployment

For a server/VPS deployment, prefer the Gateway container rather than installing every app package
on the host:

```bash
docker run \
  -p 8080:8080 \
  -v "$PWD/runtime:/data" \
  -e ABSTRACTGATEWAY_DATA_DIR=/data \
  -e ABSTRACTGATEWAY_USER_AUTH=1 \
  ghcr.io/lpalbou/abstractgateway:0.2.30
```

This is the Light container: full framework capabilities through remote/endpoint inference, without
local MLX/CUDA stacks. On first start it creates `default/admin` and writes the login token to
`runtime/auth/bootstrap-admin-token`. Use `ghcr.io/lpalbou/abstractgateway:gpu-latest` only on an
NVIDIA host when you explicitly want the local GPU profile (pinned tag: `0.2.30-gpu`; this image is
experimental). The AbstractCore OpenAI-compatible server is also published as
`ghcr.io/lpalbou/abstractcore:2.13.42`.

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
