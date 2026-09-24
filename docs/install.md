# Install AbstractFramework

Most people want AbstractFramework running on their own computer with nothing to set up by hand.
That is what the installer does: one download or one line, no admin password, and at the end
AbstractFramework opens in your web browser, already signed in. Developers who want the Python
libraries in their own environment go to [Install the Python framework](#install-the-python-framework-developers).

## Install on a Mac

You need a Mac with macOS 13 or later (Apple Silicon gets the fast local engines; they need
macOS 14), an internet connection, and about 5 GB of free disk space before models.

1. **Download** [AbstractFramework-Installer.pkg](https://github.com/lpalbou/AbstractFramework/releases/latest/download/AbstractFramework-Installer.pkg).
   The release process attaches it to each GitHub release (built by
   `scripts/lib/build_macos_installer.sh`); if the link does not work yet, use
   [the one line below](#or-paste-one-line-in-terminal) instead.
2. **Double-click it.** The macOS Installer opens. Click **Continue**, then **Install**. It installs
   for you only, so it does not ask for your password.
3. **A Terminal window opens** and shows each step as it happens. It asks one question:

   ```
   ? Start AbstractFramework automatically when you log in? (a per-user login item, no admin; the uninstaller removes it) [Y/n]
   ```

   Press **Return** for yes (recommended: it is then always there when you need it), or type `n`.
4. **Wait** 2 to 15 minutes, depending on your connection. The last lines say
   `AbstractFramework is ready.` and your browser opens AbstractFramework.
5. **In the browser**, the first-run guide helps you pick an engine (it detects what this Mac can
   run and installs it with one click) and a model that fits your Mac. You can close the Terminal
   window.

Afterwards, AbstractFramework is at `http://127.0.0.1:8080/console` (bookmark it), and its icon in
the menu bar opens it and shows its status.

What it puts on your Mac, all inside your home folder: uv and a private Python 3.12 in
`~/.local`, the AbstractFramework gateway (about 2.4 GB on Apple Silicon, with the MLX engines),
uv's download cache (about 2.4 GB, reused by upgrades), your data in
`~/Library/Application Support/AbstractGateway`, and, if you said yes, a login item
(`~/Library/LaunchAgents/ai.abstractframework.gateway.plist`). Models you download later come on
top.

**If macOS says the installer "cannot be opened because Apple cannot check it for malicious
software"**, you have an unsigned build: open **System Settings > Privacy & Security**, scroll
down, click **Open Anyway** next to the installer's name, and confirm. Signed releases do not show
this message.

The same installer also exists as a zip (`AbstractFramework-Installer-macOS.zip` on the release
page) with two double-clickable files: **Install AbstractFramework.command** and **Uninstall
AbstractFramework.command**. They do exactly what the package does.

### Or: paste one line in Terminal

On macOS and Linux, open Terminal, paste this line and press Return:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh -s -- --interactive
```

`--interactive` makes it ask the start-at-login question; without it the answer is yes. Everything
else is the same as the Mac package above. On Linux the login item is a `systemd --user` service and
the data lives in `~/.local/share/abstractgateway`.

### Windows

Windows 10 22H2+ / 11: open PowerShell, paste this line and press Enter:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
```

It installs under your user account (no administrator rights), starts AbstractFramework at sign-in
and opens it in your browser. The Windows script does not ask the start-at-login question yet; use
`-NoService` to skip it.

## If something goes wrong

The installer stops at the first problem, says what happened in plain words, and says what to do.
It never leaves a half-finished install behind that a second run cannot fix: after fixing the
cause, run it again (double-click the installer again, or paste the line again) and it continues
where it stopped.

| What you see | What to do |
|---|---|
| `no internet connection: the installer could not reach pypi.org` | Connect to the internet, then run the installer again. Nothing was changed. |
| `cannot reach pypi.org through the proxy set in your environment (…)` | Your computer is set up to use a proxy that does not answer. Fix the proxy (or remove the `HTTPS_PROXY` setting), then run it again. |
| `… failed because the internet connection dropped` | Reconnect and run it again; it continues where it stopped. |
| `this Terminal runs in Intel (Rosetta) mode on an Apple Silicon Mac` | Quit Terminal. In Finder open **Applications > Utilities**, select **Terminal**, choose **File > Get Info**, untick **Open using Rosetta**, then run the installer again. (Double-clicking the installer restarts itself in the right mode on its own.) |
| `the folder … belongs to 'root', so the installer … cannot write there` | An earlier command was run with `sudo`. Run the `sudo chown -R …` line the message shows (it asks for your password once), then run the installer again. |
| `macOS … is older than the versions AbstractFramework is tested on` | A warning, not a stop. If the install then fails, update macOS in **System Settings > General > Software Update**. |
| `the Apple Silicon engines (MLX) need macOS 14 or later` | You get the light version (remote and endpoint engines). Update macOS and run the installer again to add the local engines. |
| `the installed gateway does not start … reinstalling it` | Nothing to do: an earlier install was interrupted and the installer repairs it. |
| `the gateway did not answer … within 180 s` | Restart the computer (the login item starts it) or run the installer again, then open `http://127.0.0.1:8080/console`. |
| The browser page asks for a token | The one-time sign-in link lasts 10 minutes. Run the installer again: it opens a fresh link. |
| Anything else | Run the installer again. If it stops at the same step, report it with the log file named at the end of the message (`~/Library/Application Support/AbstractGateway/logs/install-….log`). |

## Remove AbstractFramework

Double-click **Uninstall AbstractFramework.command** (from the zip, or in
`~/Library/Application Support/AbstractFramework/Installer` after a package install), or paste:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/uninstall.sh | sh
```

It asks before removing anything, then asks two more questions, both defaulting to no:

- **Also delete your AbstractFramework data** (settings, users, chats, run history)? This cannot be
  undone.
- **Also remove uv, its Python and its download cache** (about 2.5 GB)? Asked only when the
  installer is what added uv; answer no if you use uv for anything else.

It always removes the login item, stops AbstractFramework and removes the gateway. It keeps Ollama
and LM Studio (they have their own uninstallers) and the one PATH line uv added to your shell
profile. Without questions: `sh uninstall.sh --yes` (keeps data), add `--purge` to delete the data
and `--remove-uv` to remove uv. Windows: `install.ps1 -Uninstall [-Purge]`.

## Advanced: what the installer does

The Mac package, the `.command` files and the one line all run the same script,
[`scripts/install.sh`](../scripts/install.sh) (Windows: `scripts/install.ps1`):

1. Checks the machine (OS, CPU, macOS 14+ for Apple Silicon, Rosetta, NVIDIA/ROCm, the folders it
   writes, internet access to PyPI, free disk, a free port) and picks a profile: `apple` on Apple
   Silicon, `gpu` when `nvidia-smi` or `rocminfo` works, `light` otherwise.
2. Asks whether to start at login (only with `--interactive`; the default is yes, and a previous
   "no" is remembered).
3. Installs [uv](https://docs.astral.sh/uv/) when it is missing, then Python 3.12 through uv.
4. Installs the gateway as an isolated uv tool, pinned to this release:
   `uv tool install --python 3.12 "abstractgateway[<profile>,tray]==0.4.1"`, from prebuilt wheels
   only (see [No compiler needed](#no-compiler-needed)), and checks that the command starts
   (reinstalling it in place when it does not).
5. Optionally installs Node.js for the browser apps, terminal tools, Ollama or LM Studio (flags
   below).
6. Registers the gateway to start at login with `abstractgateway service install` (a LaunchAgent on
   macOS, a `systemd --user` unit on Linux, a Startup shortcut on Windows) and starts it. With
   `--no-service` (or "no" to the question), or on a Linux host without a user systemd session, it
   starts the gateway in the background instead and removes a login item an earlier run
   registered.
7. Waits up to 180 seconds for `/api/health`, then opens `http://127.0.0.1:8080/console` through a
   one-time sign-in link (`abstractgateway-config claim-url`, valid 10 minutes, this machine only).
   If no link can be created, it shows where the admin token is.

Every command is printed as it runs, and the summary lists them all. Re-running the script
upgrades or repairs the install in place. The macOS package is built by
`scripts/lib/build_macos_installer.sh`, which signs and notarizes it when given a Developer ID
(see the header of that script).

### No compiler needed

By default the script never compiles anything, so you do not need Xcode Command Line Tools, gcc
or the MSVC Build Tools. It passes uv a small overrides file (`uv-overrides.txt` in the gateway
data directory; `--print` shows it) that swaps `webrtcvad` for `webrtcvad-wheels`, keeps `vllm`
to Linux, and leaves out the two compiled extras below, and it refuses to build those packages
from source, so a gap fails with a clear error instead of starting a compiler. If macOS asks you
to install the command line developer tools (an `xcode-select` prompt) during an install, you are
running an older copy of the script: cancel the prompt, fetch the script again with the one-liner
above and re-run it.

### llama.cpp GGUF models

Every profile, light included, gets in-process llama.cpp GGUF support (`llama-cpp-python`). PyPI
has only its source, so the script takes upstream's prebuilt wheel from
[abetlen's wheel index](https://abetlen.github.io/llama-cpp-python/whl/) (`--find-links` on the
package page, pinned in `uv-constraints.txt` next to the overrides file):

| Machine | Wheel |
|---|---|
| Apple Silicon Mac | `llama-cpp-python==0.3.28`, Metal (GPU offload) |
| Linux x86_64 / aarch64 (glibc) | `llama-cpp-python==0.3.35`, CPU |
| Windows x64 | `llama-cpp-python==0.3.35`, CPU |
| Intel Mac, musl Linux, Windows on ARM | no prebuilt wheel: skipped |

Where no wheel exists, or when the wheel install fails, the script installs everything else and
says `GGUF (llama.cpp) skipped: no prebuilt wheel for this machine`; `--full` then builds it from
source. The summary's `GGUF:` line says which wheel was installed. The Metal pin stays at 0.3.28
because the 0.3.32-0.3.35 Metal wheels fail zip integrity checks and uv refuses them.

### Compiled extras

Two optional engines publish no wheel on PyPI and are skipped by default: stable-diffusion.cpp
image generation (`stable-diffusion-cpp-python`) and voice echo cancellation
(`aec-audio-processing`). `--full` (Windows: `-Full`) keeps them and builds them, and llama.cpp,
from source, which takes several minutes and needs a C/C++ compiler (macOS:
`xcode-select --install`; Debian/Ubuntu: `sudo apt-get install -y build-essential`; Windows:
Visual Studio Build Tools with "Desktop development with C++"). Without a compiler, `--full` stops
before installing anything. You do not need them for MLX on Apple Silicon, for llama.cpp GGUF
models (above), for Ollama, LM Studio or other endpoint engines, or for cloud providers.

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
| `--full` | `-Full` | Also build the [compiled extras](#compiled-extras) and llama.cpp from source (needs a C compiler) |
| `--no-service` | `-NoService` | Do not register a login service |
| `--no-open` | `-NoOpen` | Do not open the browser |
| `--pin X` / `--from PATH` | `-Pin` / `-From` | Install another gateway version or a local checkout |
| `--data-dir DIR` | `-DataDir` | Gateway data directory |
| `--interactive` | (not yet) | Ask whether to start at login (and, with `--uninstall`, whether to delete data and uv); the double-click installers pass it |
| `--print` | `-Print` (or `-WhatIf`) | Show the plan and every command; change nothing |
| `--uninstall [--purge] [--remove-uv]` | `-Uninstall [-Purge]` | Remove the service and uv tools (purge also deletes the data; `--remove-uv` also removes uv, its Python and cache when the installer added uv) |

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
uv tool install --python 3.12 "abstractgateway[tray]==0.4.1"    # [apple,tray] or [gpu,tray] for local engines
                       # (add --with and --overrides as shown by `install.sh --print` to avoid compiling)
uv tool update-shell                                          # puts ~/.local/bin on PATH; open a new terminal
abstractgateway service install --port 8080                   # or: abstractgateway serve
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

`abstractframework` 0.3.0 pins `abstractgateway==0.4.1`, `abstractassistant==0.5.0`,
`abstractcore==2.15.0`, `AbstractRuntime==0.4.33`, `abstractagent==0.3.13`,
`AbstractMemory==0.3.0`, `abstractsemantics==0.0.5`, `abstractvoice==0.11.4`,
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

| Tool | Command | Version released with 0.3.0 |
|---|---|---|
| Gateway web console | built into `abstractgateway`: open the link `abstractgateway serve` prints (`http://127.0.0.1:8080/console#claim=…`) | 0.4.1 |
| Core web console | built into `abstractcore`: open the link `abstractcore serve` prints (`http://127.0.0.1:8000/console#claim=…`) | 2.15.0 |
| Core terminal console | `cargo install abstractcore-console` (Rust 1.87+), then `abstractcore-console` (uses the `abstractcore` command) | 0.2.0 |
| Gateway terminal console | `cargo install abstractgateway-console` (Rust 1.87+), then `abstractgateway-console --url http://127.0.0.1:8080` | 0.8.0 |
| Flow Editor | `npx @abstractframework/flow` | 0.3.20 |
| Code Web UI | `npx @abstractframework/code` | 0.4.2 |
| Observer | `npx @abstractframework/observer` | 0.1.12 |
| Continuum console | `npx @abstractframework/continuum` | 0.3.0 |
| Entity manager | `npx @abstractframework/entity` | 0.2.0 |
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
  ghcr.io/lpalbou/abstractgateway:0.4.1
```

This is the Light container: full framework capabilities through remote/endpoint inference, without
local MLX/CUDA stacks. On first start it creates `default/admin` and writes the login token to
`runtime/auth/bootstrap-admin-token`. Use `ghcr.io/lpalbou/abstractgateway:gpu-latest` only on an
NVIDIA host when you explicitly want the local GPU profile (pinned tags are `<version>-gpu`, published on a best-effort basis; this image is
experimental). The AbstractCore OpenAI-compatible server is also published as
`ghcr.io/lpalbou/abstractcore-server:2.15.0`.

## How installs are designed

The scripts and the gateway console are the install experience on every OS. On macOS the
double-click artefacts (a payload-free `.pkg` and two `.command` files) only launch the same
script in Terminal; they add no install logic of their own. Design, security model and per-OS
behavior are in [docs/installers](installers/README.md).

## Generated install manifest

The installer-facing contract is generated from the root release profile:

```bash
abstractframework manifest
abstractframework manifest --check docs/installers/install-manifest.json
```

The bootstrap scripts read `bootstrap.gateway_version` from it; other installers should consume
this manifest instead of maintaining independent package pins. Field reference:
[release-and-manifest.md](installers/release-and-manifest.md).
