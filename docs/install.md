# Install AbstractFramework

## Quick start

One line installs the gateway, registers it to start at login, starts it on `127.0.0.1:8080`, and
opens its web console in your browser, already signed in. No admin rights and no system Python are
needed.

macOS and Linux:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
```

Windows 10 22H2+ / 11 (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
```

The console's first-run guide then walks you through a local engine (Ollama, LM Studio, MLX,
llama.cpp, with a one-click install that shows its exact command first) or a cloud API key, a
default model picked from the models that fit your machine, and the apps. The **Models** and
**Engines** tabs stay available afterwards.

### What the script does

1. Checks the machine (OS, CPU, macOS 14+ for Apple Silicon, NVIDIA/ROCm, free disk, a free port)
   and picks a profile: `apple` on Apple Silicon, `gpu` when `nvidia-smi` or `rocminfo` works,
   `light` otherwise.
2. Installs [uv](https://docs.astral.sh/uv/) when it is missing, then Python 3.12 through uv.
3. Installs the gateway as an isolated uv tool, pinned to this release:
   `uv tool install --python 3.12 "abstractgateway[<profile>,tray]==0.3.0"`, from prebuilt wheels
   only (see [No compiler needed](#no-compiler-needed)).
4. Optionally installs Node.js for the browser apps, terminal tools, Ollama or LM Studio (flags
   below).
5. Registers the gateway to start at login with `abstractgateway service install` (a LaunchAgent on
   macOS, a `systemd --user` unit on Linux, a Startup shortcut on Windows) and starts it. With
   `--no-service`, or on a Linux host without a user systemd session, it starts the gateway in the
   background instead.
6. Waits for `/api/health`, then opens `http://127.0.0.1:8080/console` through a one-time sign-in
   link (`abstractgateway-config claim-url`, valid 10 minutes, this machine only). If no link can be
   created, it shows where the admin token is.

Every command is printed as it runs, and the summary lists them all. Re-running the script
upgrades or repairs the install in place.

### No compiler needed

By default the script never compiles anything, so you do not need Xcode Command Line Tools, gcc
or the MSVC Build Tools. It passes uv a small overrides file (`uv-overrides.txt` in the gateway
data directory; `--print` shows it) that swaps `webrtcvad` for `webrtcvad-wheels`, keeps `vllm`
to Linux, and leaves out the three compiled extras below, and it refuses to build those packages
from source, so a gap fails with a clear error instead of starting a compiler. If macOS asks you
to install the command line developer tools (an `xcode-select` prompt) during an install, you are
running an older copy of the script: cancel the prompt, fetch the script again with the one-liner
above and re-run it.

### Compiled extras

Three optional engines publish no wheel on PyPI and are skipped by default: llama.cpp GGUF models
in-process (`llama-cpp-python`), stable-diffusion.cpp image generation
(`stable-diffusion-cpp-python`) and voice echo cancellation (`aec-audio-processing`). `--full`
(Windows: `-Full`) keeps them and builds them from source, which takes several minutes and needs a
C/C++ compiler (macOS: `xcode-select --install`; Debian/Ubuntu: `sudo apt-get install -y
build-essential`; Windows: Visual Studio Build Tools with "Desktop development with C++"). Without
a compiler, `--full` stops before installing anything. You do not need them for MLX on Apple
Silicon, for Ollama, LM Studio or other endpoint engines, or for cloud providers.

### Options

| macOS/Linux | Windows | What it does |
|---|---|---|
| `--profile auto\|light\|apple\|gpu` | `-Profile` | Override the profile choice |
| `--port N` | `-Port N` | Gateway port (default 8080; the next free port when 8080 is busy) |
| `--with-apps` | `-WithApps` | Make sure Node.js 18+ exists for the browser apps (`uv tool install nodejs-wheel`, no admin) |
| `--with-ollama` | `-WithOllama` | Run Ollama's official installer (Linux uses sudo; the script tells you first) |
| `--with-lmstudio` | `-WithLmStudio` | Install LM Studio (headless daemon on macOS/Linux, winget on Windows) |
| `--with-console` | `-WithConsole` | Install the `abstractgateway-console` crate with cargo (terminal console; needs Rust) |
| `--with-code-cli` | `-WithCodeCli` | Install the `abstractcode` crate with cargo (terminal client; needs Rust) |
| `--with-core-cli` | `-WithCoreCli` | Also put the `abstractcore` command on PATH |
| `--full` | `-Full` | Also build the [compiled extras](#compiled-extras) from source (needs a C compiler) |
| `--no-service` | `-NoService` | Do not register a login service |
| `--no-open` | `-NoOpen` | Do not open the browser |
| `--pin X` / `--from PATH` | `-Pin` / `-From` | Install another gateway version or a local checkout |
| `--data-dir DIR` | `-DataDir` | Gateway data directory |
| `--print` | `-Print` (or `-WhatIf`) | Show the plan and every command; change nothing |
| `--uninstall [--purge]` | `-Uninstall [-Purge]` | Remove the service and uv tools (purge also deletes the data) |

Pass options through the one-liner like this:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh -s -- --with-apps --with-ollama
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1))) -WithApps -WithOllama
```

### The same install by hand

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh             # Windows: irm https://astral.sh/uv/install.ps1 | iex
uv python install 3.12
uv tool install --python 3.12 "abstractgateway[tray]==0.3.0"    # [apple,tray] or [gpu,tray] for local engines
                       # (add --with and --overrides as shown by `install.sh --print` to avoid compiling)
uv tool update-shell                                          # puts ~/.local/bin on PATH; open a new terminal
abstractgateway service install --host 127.0.0.1 --port 8080   # or: abstractgateway serve
abstractgateway-config claim-url --base-url http://127.0.0.1:8080  # prints a one-time console link
```

### Run at login

`abstractgateway service install` registers the login service (LaunchAgent on macOS,
`systemd --user` on Linux, a Startup shortcut on Windows, experimental) and starts the gateway:

```bash
abstractgateway service install --host 127.0.0.1 --port 8080
abstractgateway service status
abstractgateway service uninstall
```

The bootstrap scripts use it by default. Gateways older than 0.3.0 (installed with `--pin`) have no
`service` command: `install.sh` then starts the gateway in the background and `install.ps1` adds a
Startup-folder shortcut. To write a login entry yourself on Linux, a user unit is enough:

```ini
# ~/.config/systemd/user/abstractgateway.service
[Service]
Environment=ABSTRACTGATEWAY_USER_AUTH=1
Environment=ABSTRACTGATEWAY_DATA_DIR=%h/.local/share/abstractgateway
ExecStart=%h/.local/bin/abstractgateway serve --host 127.0.0.1 --port 8080
Restart=on-failure

[Install]
WantedBy=default.target
```

Then `systemctl --user daemon-reload && systemctl --user enable --now abstractgateway`. On macOS
use a LaunchAgent in `~/Library/LaunchAgents/` with the same absolute command and environment
(launchd does not read your shell profile, so use absolute paths).

### Upgrade and uninstall

- Upgrade: re-run the one-liner (or `uv tool upgrade abstractgateway`).
- Uninstall: `curl -LsSf .../install.sh | sh -s -- --uninstall` (Windows: the script block with
  `-Uninstall`), or by hand: `abstractgateway service uninstall` (when registered), then
  `uv tool uninstall abstractgateway`. Your data stays in the data directory until you delete it
  (`--purge`). See [Operations and support](installers/operations-and-support.md) for locations.

### Check the install

```bash
uvx abstractframework doctor
```

It checks Python, uv, Node, disk, the gateway (`ABSTRACTGATEWAY_URL`, default
`http://127.0.0.1:8080`), and whether Ollama and LM Studio are reachable. It only reads.

## Install the Python framework (developers)

Use the profiles below when you want every framework library in one Python environment, for
example to build on AbstractCore or AbstractRuntime directly. Choose the profile by deciding where
inference should run. The framework APIs stay the same across profiles; the profiles mainly change
whether local inference engines are installed.

### Quick chooser

| Profile | Command | Use when | Local inference stacks |
|---|---|---|---|
| Light | `pip install abstractframework` | You use cloud APIs or endpoint servers such as LM Studio, Ollama, vLLM, llama.cpp, OpenRouter, or OpenAI-compatible services. | No |
| Apple | `pip install "abstractframework[apple]"` | You are on Apple Silicon and want local MLX/Metal-capable engines as well as endpoint providers. | Yes, Apple-focused |
| GPU | `pip install "abstractframework[gpu]"` | You have a supported discrete GPU and want local GPU-capable engines as well as endpoint providers. | Yes, GPU-focused |

#### Requirements per profile

| Profile | Platforms | Python | Notes |
|---|---|---|---|
| Light | macOS, Linux, Windows | 3.10–3.13 | No local inference engines. |
| Apple | macOS 14 or later on Apple Silicon | 3.10–3.13 | MLX wheels need macOS 14+. F5-TTS voice cloning needs Python 3.11+; the rest of the profile works on 3.10. |
| GPU | Linux (and Windows where the engines publish wheels) with NVIDIA CUDA or AMD ROCm drivers | 3.10–3.13 | F5-TTS voice cloning needs Python 3.11+; the rest of the profile works on 3.10. |

A plain `pip install` of the `apple` or `gpu` profile builds the
[compiled extras](#compiled-extras) (`llama-cpp-python`, `stable-diffusion-cpp-python`,
`aec-audio-processing`) from source, so it needs a C/C++ compiler. The one-line install above
does not.

`abstractframework` 0.2.0 pins `abstractgateway==0.3.0`, `abstractassistant==0.5.0`,
`abstractcore==2.14.0`, `AbstractRuntime==0.4.33`, `abstractagent==0.3.13`,
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

After install, run `abstractframework doctor`, start the gateway and configure providers in its
console (see [Start the gateway](#start-the-gateway-and-apps)).

## Apple profile

```bash
pip install "abstractframework[apple]"
```

Choose Apple when:

- you are on Apple Silicon;
- you want local Apple/MLX-capable inferencers in addition to endpoint providers;
- you accept larger downloads and platform-specific native dependencies.

Then run `abstractframework doctor`.

## GPU profile

```bash
pip install "abstractframework[gpu]"
```

Choose GPU when:

- you have a supported GPU stack and drivers;
- you want local GPU-capable inferencers in addition to endpoint providers;
- you accept larger downloads and platform-specific native dependencies.

Then run `abstractframework doctor`.

## Apps and tools outside pip

The browser apps and the Rust terminal tools are not Python packages, so no profile installs them.
Run or install them next to the Python stack:

| Tool | Command | Version released with 0.2.0 |
|---|---|---|
| Gateway web console | built into `abstractgateway`: open the link `abstractgateway serve` prints (`http://127.0.0.1:8080/console#claim=…`) | 0.3.0 |
| Core web console | built into `abstractcore`: open the link `abstractcore serve` prints (`http://127.0.0.1:8000/console#claim=…`) | 2.14.0 |
| Core terminal console | `cargo install abstractcore-console` (Rust 1.87+), then `abstractcore-console` (uses the `abstractcore` command) | 0.2.0 |
| Gateway terminal console | `cargo install abstractgateway-console` (Rust 1.87+), then `abstractgateway-console --url http://127.0.0.1:8080` | 0.7.0 |
| Flow Editor | `npx @abstractframework/flow` | 0.3.20 |
| Code Web UI | `npx @abstractframework/code` | 0.4.2 |
| Observer | `npx @abstractframework/observer` | 0.1.12 |
| Continuum console | `npx @abstractframework/continuum` | 0.2.0 |
| Entity manager | `npx @abstractframework/entity` | 0.1.0 |
| AbstractCode terminal client | `cargo install abstractcode`, or a prebuilt binary from the [AbstractCode GitHub release](https://github.com/lpalbou/AbstractCode/releases) | 0.5.1 |

The browser apps need Node.js 18 or later and a running gateway. Optional Python add-ons outside the
profiles install on their own: `pip install abstract3d`, `pip install abstractcamera`,
`pip install abstractskill`.

## Start the gateway and apps

Start the gateway, open its console, then any browser app against it:

```bash
abstractgateway serve            # binds 127.0.0.1:8080 and prints a one-time console link
npx @abstractframework/flow
```

Configure providers, API keys, engines and default models in the console. For library-only use
of AbstractCore, `abstractcore serve` opens the same Models and Engines screens in its own console,
and `abstractcore --config` remains available in the terminal. When you work from source, the workspace helper
scripts build and start the same services (see [Workspace scripts](workspace-scripts.md)).

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
  ghcr.io/lpalbou/abstractgateway:0.3.0
```

This is the Light container: full framework capabilities through remote/endpoint inference, without
local MLX/CUDA stacks. On first start it creates `default/admin` and writes the login token to
`runtime/auth/bootstrap-admin-token`. Use `ghcr.io/lpalbou/abstractgateway:gpu-latest` only on an
NVIDIA host when you explicitly want the local GPU profile (pinned tags are `<version>-gpu`, published on a best-effort basis; this image is
experimental). The AbstractCore OpenAI-compatible server is also published as
`ghcr.io/lpalbou/abstractcore-server:2.14.0`.

## How installs are designed

The one-line scripts and the gateway console are the install experience on every OS; there is no
separate GUI installer. Design, security model and per-OS behavior are in
[docs/installers](installers/README.md).

## Generated install manifest

The installer-facing contract is generated from the root release profile:

```bash
abstractframework manifest
abstractframework manifest --check docs/installers/install-manifest.json
```

The bootstrap scripts read `bootstrap.gateway_version` from it; other installers should consume
this manifest instead of maintaining independent package pins. Field reference:
[release-and-manifest.md](installers/release-and-manifest.md).
