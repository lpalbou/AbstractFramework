# User Journeys

These flows describe exactly what the bootstrap scripts do. Commands are in
[Install](../install.md); the model is in [strategy.md](strategy.md).

## First install on macOS

With the Mac installer, the user downloads `AbstractFramework-Installer.pkg`, allows it once in
**System Settings > Privacy & Security** (**Open Anyway**: the package is not signed with an Apple
Developer ID), and clicks through the macOS Installer. Its postinstall copies the two `.command`
files to `~/Library/Application Support/AbstractFramework/Installer` and opens
`install.sh --interactive` in Terminal, which asks one question (start at login, default yes) and
then runs the steps below. The one-line path:

1. Paste in Terminal:
   `curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh`
2. **Preflight** (read-only): macOS version and CPU (`sw_vers`, `uname -m`), profile choice
   (`apple` on Apple Silicon with macOS 14+, else `light`), free disk under your home, port 8080
   (the next free port is used and remembered when 8080 is taken).
3. **uv**: installed into `~/.local/bin` by the official astral.sh script when missing
   (`UV_NO_MODIFY_PATH=1`), then `uv tool update-shell` adds `~/.local/bin` to your shell profile
   once.
4. **Python**: `uv python install 3.12`.
5. **Gateway**: `uv tool install --python 3.12 "abstractgateway[apple,tray]==<pin>"`. The
   commands `abstractgateway` and `abstractgateway-config` land in `~/.local/bin`.
6. **Optional** (flags): Node for the apps (`--with-apps` installs the `nodejs-wheel` uv tool when
   no Node 18+ exists), Ollama (`--with-ollama`: the official installer, which may ask for your
   password to link `/usr/local/bin/ollama`), LM Studio (`--with-lmstudio`: the headless `llmster`
   daemon), terminal tools (`--with-console`, `--with-code-cli` through cargo).
7. **Service**: `abstractgateway service install --port 8080` registers a per-user LaunchAgent
   and starts it, so the gateway also starts at login. The LaunchAgent runs plain
   `abstractgateway serve`, so the gateway's Network setting (default `localhost`) decides where it
   listens. With `--no-service` (or "no" to the question), the script stores the setting and starts
   the gateway in the background instead.
8. **Health**: waits up to 180 seconds for `GET /api/health` (the first start loads the local
   engines), with a progress line every 15 seconds.
9. **Sign-in**: `abstractgateway-config claim-url` mints a one-time link valid for 10 minutes on
   this machine; if no link can be created, the script prints the path of the admin token file
   (`~/Library/Application Support/AbstractGateway/auth/bootstrap-admin-token`).
10. **Browser**: opens the claim link (`http://127.0.0.1:8080/console#claim=…`). The first-run guide
    walks through engines (detected on this Mac, with one-click installs), a default model that fits
    the machine, and the apps; the **Models** and **Engines** tabs stay available afterwards.

## First install on Linux

Same one-liner and steps, with these differences:

- Profile: `gpu` when `nvidia-smi` or `rocminfo` works, else `light`. The tray extra is added only
  when a display (`DISPLAY`/`WAYLAND_DISPLAY`) exists.
- Data: `${XDG_DATA_HOME:-~/.local/share}/abstractgateway`.
- Service: a `systemd --user` unit when a user session bus exists
  (`systemctl --user show-environment`). Containers and minimal SSH hosts have none; the script
  then starts the gateway in the background and says so. For always-on servers use the container
  deployment in [Install](../install.md#container-deployment).
- Browser: `xdg-open` when a display exists; otherwise the script prints the URL and an SSH tunnel
  hint (`ssh -L 8080:127.0.0.1:8080 <host>`).
- `--with-ollama` runs Ollama's Linux installer, which uses sudo, installs into `/usr/local` and
  creates a system service. The script announces this before running it.
- Linux ARM64: gateways before 0.3.0 (selected with `--pin`) pull an AbstractCore that caps
  `psutil` below 6, which has no aarch64 wheel, so a C compiler is needed
  (`sudo apt-get install -y gcc`). The preflight warns when none is found.

## First install on Windows

1. In PowerShell:
   `powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"`
2. **Preflight**: Windows build (22H2/19045 or later), architecture, execution policy set by Group
   Policy (reported and explained), long-path support, free disk, port.
3. **uv**: the official `install.ps1` from astral.sh into `%USERPROFILE%\.local\bin`.
4. **Python and gateway**: `uv python install 3.12`, then
   `uv tool install --python 3.12 "abstractgateway[tray]==<pin>"` (`[gpu,tray]` when `nvidia-smi`
   works).
5. **Optional**: `-WithApps` (nodejs-wheel, no UAC), `-WithOllama` (`winget install Ollama.Ollama
   --scope user`, or Ollama's `install.ps1`), `-WithLmStudio` (`winget install
   ElementLabs.LMStudio --scope user`, or LM Studio's headless `install.ps1`).
6. **Autostart**: `abstractgateway service install` (a Startup-folder entry, experimental on
   Windows). With `-NoService` the gateway starts once in a hidden window instead.
7. **Start, health, sign-in, browser**: hidden-window start, `/api/health`, claim link or the token
   file under `%LOCALAPPDATA%\AbstractGateway\auth\`, then the console opens.

To pass options through the one-liner, use a script block:
`& ([scriptblock]::Create((irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1))) -WithApps`.

## Apps

Browser apps (Flow, Code, Observer, Continuum, Entity) run on demand with
`npx -y @abstractframework/<app>`; nothing is installed globally. They talk to the gateway at
`ABSTRACTGATEWAY_URL` (default `http://127.0.0.1:8080`). `--with-apps` only makes sure Node 18+
exists.

## Upgrade and repair

Re-run the same one-liner. The script keeps the previous port and profile, installs the pin from
the current manifest (a no-op when it is already installed), restarts the gateway only when the
package changed, and re-checks health. `uv tool upgrade abstractgateway` and the tray's "Check for
updates" are equivalent for uv-tool installs.

## Uninstall

`sh install.sh --uninstall` (or `install.ps1 -Uninstall`) removes the service or Startup shortcut,
stops the gateway, and uninstalls the `abstractgateway` uv tool (and `nodejs-wheel` when the script
installed it). The data directory is kept unless you add `--purge` (`-Purge`). uv, Ollama and LM
Studio stay installed; remove them with their own uninstallers.

## Dry run

`--print` (`-Print`, or `-WhatIf`) runs the read-only preflight and prints every command the
install would run, then stops.
