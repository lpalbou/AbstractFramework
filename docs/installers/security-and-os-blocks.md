# OS Security and Installation Blocks

The bootstrap is a script, not a downloaded application, so the OS gates that block unsigned
installers do not apply to it. This page explains what each OS checks, what the scripts do about
it, and where code signing is still required.

## macOS (Gatekeeper)

- Gatekeeper checks **quarantined applications** (downloaded by a browser) for a Developer ID
  signature and notarization. Files fetched by `curl` carry no `com.apple.quarantine` attribute,
  so `curl … | sh` and the binaries it installs (uv, the uv-managed Python, wheels) run without a
  Gatekeeper prompt.
- The optional vendor installers (Ollama, LM Studio) are signed and notarized by their vendors.
- The gateway binds `127.0.0.1`, so the macOS Application Firewall does not ask to accept incoming
  connections.

## Windows (SmartScreen and execution policy)

- SmartScreen and Mark-of-the-Web apply to downloaded files. `irm … | iex` downloads the script
  into memory and writes no file, so SmartScreen does not prompt. The script launches `.exe`
  shims created by uv, not downloaded installers.
- **Execution policy** is the only script gate. Pasted commands always run; `.ps1` files do not
  under `Restricted` (the Windows client default) or `AllSigned`. The one-liner uses
  `powershell -ExecutionPolicy ByPass -c "…"`, which applies to that process only and is not
  persisted. Vendor one-liners run in a child `powershell -ExecutionPolicy ByPass` process.
- **Group Policy** (`MachinePolicy`/`UserPolicy`) overrides `-ExecutionPolicy ByPass`. The script
  detects an `AllSigned` or `Restricted` policy set this way and explains it: the pasted one-liner
  still works, a saved `install.ps1` does not, and managed machines may need an administrator.
- The autostart fallback is a Startup-folder shortcut that runs `powershell.exe -Command` (not a
  `.ps1` file), so the execution policy does not block it. No UAC prompt is needed: uv, Python,
  Node (`nodejs-wheel`), Ollama (`--scope user`) and LM Studio (`--scope user`) all install per
  user. `winget install OpenJS.NodeJS.LTS` is deliberately not used because it installs
  machine-wide and triggers UAC.

## Linux

- Nothing in the default path needs root. Everything installs under `~/.local` and
  `${XDG_DATA_HOME:-~/.local/share}`.
- `--with-ollama` runs Ollama's official installer, which **uses sudo**: it installs into
  `/usr/local`, creates an `ollama` user and a system `ollama.service`. The script prints this
  before running it. LM Studio's headless installer may ask for sudo to install `libatomic1`.
- On ARM64 without a C compiler, the gateway install fails while building `psutil`; install `gcc`
  from your distribution first.

## Sudo and UAC prompts at a glance

| Step | macOS | Linux | Windows |
|---|---|---|---|
| uv, Python, gateway, nodejs-wheel | none | none | none |
| Service / autostart | none (LaunchAgent) | none (`systemd --user`); `loginctl enable-linger` for always-on may need polkit | none (Startup folder) |
| `--with-ollama` | may ask for your password (`/usr/local/bin/ollama` link) | sudo | none (user scope) |
| `--with-lmstudio` | none | may ask sudo for `libatomic1` | none (user scope) |

## Network exposure

- The gateway binds `127.0.0.1` in every bootstrap path.
- One-time sign-in links (`abstractgateway-config claim-url`) are single use, expire after 10
  minutes and are accepted only from a loopback client.
- The admin token file is written with mode `0600`; the scripts print its path, not its content.
- Remote access: use an SSH tunnel (`ssh -L 8080:127.0.0.1:8080 <host>`) or the container
  deployment with explicit auth.

## Integrity

- Every download uses HTTPS from the vendor's official host (astral.sh, pypi.org, ollama.com,
  lmstudio.ai, raw.githubusercontent.com). uv verifies package hashes from the index.
- Review before running: fetch the script, read it, then run it, or use `--print` to see every
  command without changing anything.

## Where code signing still applies

Native double-click artifacts need signatures: the AbstractAssistant `.app` (Developer ID +
notarization + stapling) and any future Windows `.exe`/`.msi` launcher (Authenticode). The
bootstrap and everything it installs need no signature of ours.

## GPU drivers

The scripts never install drivers. They offer the `gpu` profile only when `nvidia-smi` or
`rocminfo` works; otherwise local engines fall back to CPU with a warning.
