# Components and Packaging Matrix

How each component reaches a user's machine under the [script bootstrap](strategy.md).

## Installed by the bootstrap

| Component | Delivered as | Installed by | Notes |
|---|---|---|---|
| uv | Static binary | astral.sh `install.sh` / `install.ps1` | Skipped when already on the machine. Lives in `~/.local/bin` (`%USERPROFILE%\.local\bin`). |
| Python 3.12 | python-build-standalone | `uv python install 3.12` | Isolated from any system Python. |
| AbstractGateway (+ AbstractCore, AbstractRuntime, AbstractAgent, AbstractMemory as dependencies) | PyPI wheel, uv tool | `uv tool install --python 3.12 "abstractgateway[<profile>,tray]==<pin>"` | Exposes `abstractgateway` and `abstractgateway-config`; `--with-core-cli` also exposes `abstractcore`. |
| Gateway service | LaunchAgent / systemd user unit / Startup entry | `abstractgateway service install` | When the installed gateway provides it; otherwise a background start (Windows: Startup-folder shortcut). |
| Node.js (optional) | `nodejs-wheel` uv tool | `--with-apps` | Only when no Node 18+ is present; no admin, same bin directory. |

## Run on demand

| Component | Command | Notes |
|---|---|---|
| Gateway web console | `http://127.0.0.1:8080/console` | Built into the gateway; the guided setup UI. |
| Flow editor, Code web, Observer, Continuum, Entity | `npx -y @abstractframework/<app>` | Need Node 18+ and a running gateway. |

## Optional tools (flags)

| Component | Flag | Installed with |
|---|---|---|
| Gateway terminal console | `--with-console` | `cargo install --locked abstractgateway-console` (needs Rust; the script prints the command when cargo is missing) |
| AbstractCode terminal client | `--with-code-cli` | `cargo install --locked abstractcode` |

## Third-party engines

| Engine | Flag | macOS / Linux | Windows | Detection (skip when found) |
|---|---|---|---|---|
| Ollama | `--with-ollama` | `curl -fsSL https://ollama.com/install.sh \| sh` (Linux: sudo, system service) | `winget install Ollama.Ollama --scope user`, else `irm https://ollama.com/install.ps1 \| iex` | `ollama` on PATH or `GET :11434/api/version` |
| LM Studio | `--with-lmstudio` | `curl -fsSL https://lmstudio.ai/install.sh \| bash` (headless daemon; Apple Silicon only on macOS) | `winget install ElementLabs.LMStudio --scope user`, else `irm https://lmstudio.ai/install.ps1 \| iex` | `lms`, `~/.lmstudio/bin/lms`, the app bundle, or `GET :1234/v1/models` |

The console's Engines tab offers the same installs later, with the command shown before it runs.

## Native apps (outside the bootstrap)

| Component | Delivery | Notes |
|---|---|---|
| AbstractAssistant | `pip install "abstractassistant[apple]"`; macOS `.app` build | The `.app` is the component that needs Developer ID signing and notarization. |
| Docker image | `ghcr.io/lpalbou/abstractgateway:<version>` | Server deployments; see [Install](../install.md#container-deployment). |

## Availability rules

- The `apple` profile is refused on anything but Apple Silicon with macOS 14+.
- The `gpu` profile warns (and continues) when no `nvidia-smi`/`rocminfo` works; engines then run
  on CPU.
- Engines that do not support the host (LM Studio on Intel Macs) are skipped with a message.
