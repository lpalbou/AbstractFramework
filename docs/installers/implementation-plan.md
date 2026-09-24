# Implementation Plan

The install experience follows [ADR-0038](../adr/0038-script-bootstrap-and-gateway-console-install.md):
a one-line bootstrap per OS plus the gateway console. This page tracks what is delivered and what
comes next.

## Delivered

- `scripts/install.sh` (macOS, Linux; POSIX `sh`, tested with dash, bash and zsh) and
  `scripts/install.ps1` (Windows PowerShell 5.1 and PowerShell 7): preflight, profile selection,
  uv + Python 3.12, `uv tool install` of the pinned gateway, optional Node/cargo tools/Ollama/LM
  Studio, service or background start, health wait, console sign-in, dry run, idempotent re-runs,
  uninstall.
- Install manifest schema v2: a `bootstrap` section (gateway pin, Python, extras per profile,
  script URLs, flags) and a console-first `post_install`.
- `abstractframework doctor`: Python range, macOS/Apple Silicon for `apple`, GPU tools, uv, Node
  18+ (system or `nodejs-wheel`), disk, and read-only probes of the gateway, Ollama and LM Studio.
- CI job `bootstrap-smoke` on Ubuntu, macOS and Windows.

## Gateway features the scripts use

The pinned gateway (0.4.0) provides all of them. The scripts still detect each one, so an older
gateway selected with `--pin` falls back as the last column says.

| Feature | Command | Without it (older `--pin`) |
|---|---|---|
| Per-user service (LaunchAgent, `systemd --user`, Windows logon) | `abstractgateway service install --host 127.0.0.1 --port N`, `service uninstall` | Background start; Windows adds a Startup-folder shortcut |
| One-time console sign-in link | `abstractgateway-config claim-url --base-url URL` | The admin token file path is shown |
| First-run wizard in `/console` | opened by the claim link | Console sign-in form |
| Per-OS default data directory and loopback user auth | `abstractgateway serve` | The scripts set `ABSTRACTGATEWAY_DATA_DIR` and `ABSTRACTGATEWAY_USER_AUTH=1` |

## Next

- Validate `install.ps1` on physical Windows 10 22H2 and Windows 11 machines (x64 and ARM64),
  including the Startup shortcut, hidden-window start and winget installs.
- Host the scripts at a short URL (`abstractframework.ai/install.sh`, `…/install.ps1`).
- Validate `abstractgateway service install` end to end on each OS in CI (the smoke job runs with
  `--no-service`).
- Signed AbstractAssistant `.app`.

## Not planned in this model

A separate GUI installer manager, signed per-app installers for every component, enterprise
MSI/pkg packages and offline bundles. They would need a new ADR.
