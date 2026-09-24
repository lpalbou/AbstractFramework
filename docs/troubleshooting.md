# Troubleshooting

Symptoms you may meet when installing or running AbstractFramework, how to confirm the cause, and
how to fix it. Installation steps are in [Install](install.md); concepts and limits are in the
[FAQ](faq.md); package-specific problems are covered in each component's own documentation.

## First checks

Start with the read-only health report:

```bash
uvx abstractframework doctor        # or `abstractframework doctor` inside a framework venv
curl -sS http://127.0.0.1:8080/api/health
```

`doctor` checks Python, the pinned package versions, uv, Node.js, free disk, the gateway
(`ABSTRACTGATEWAY_URL`, default `http://127.0.0.1:8080`) and whether Ollama and LM Studio answer.
It changes nothing. See [API](api.md#abstractframework-doctor) for its options.

Logs:

| What | macOS | Linux | Windows |
|---|---|---|---|
| Install log | `~/Library/Application Support/AbstractGateway/logs/install-*.log` | `~/.local/share/abstractgateway/logs/install-*.log` | `%LOCALAPPDATA%\AbstractGateway\logs\install-*.log` |
| Gateway started at login | `~/Library/Logs/AbstractGateway/gateway.out.log`, `gateway.err.log` | `journalctl --user -u abstractgateway` and `<data>/logs/` | `<data>\logs\gateway.err.log` |
| Gateway started in the background | `<data>/logs/gateway.log` | `<data>/logs/gateway.log` | `<data>\logs\gateway.err.log` |

`<data>` is the gateway data directory; all locations are listed in
[Operations and support](installers/operations-and-support.md#locations).

## Installing

### macOS will not open `AbstractFramework-Installer.pkg`

- **Cause**: the package is not signed with an Apple Developer ID, so Gatekeeper blocks the first
  double-click of a downloaded copy.
- **Fix**: close the warning, open **System Settings > Privacy & Security**, click **Open Anyway**
  next to the installer's name, and confirm. The **Open Anyway** button appears after you have
  tried to open the file once.
- **Alternative**: paste the one-line install in Terminal; it is not subject to this step.
- **Verify**: the macOS Installer opens and then a Terminal window shows the install steps.

### The installer stopped with a message

Every stop names its cause and the next step. The full list of messages and what to do is the
table in [If something goes wrong](install.md#if-something-goes-wrong). After fixing the cause,
run the installer again: it continues where it stopped.

### macOS asks to install the command line developer tools

- **Cause**: something tried to compile a package. The installer itself uses prebuilt wheels only.
- **Fix**: cancel the prompt, fetch the script again with the one-liner in
  [Install](install.md#or-paste-one-line-in-terminal), and re-run it.
- You need a compiler only for `--full` ([Compiled extras](install.md#compiled-extras)) or for a
  plain `pip install` of the `apple` / `gpu` profiles.

### `abstractgateway: command not found`

- **Cause**: the commands live in `~/.local/bin` (`%USERPROFILE%\.local\bin` on Windows), which is
  added to your PATH for **new** terminals.
- **Fix**: open a new terminal, or call `~/.local/bin/abstractgateway` directly.
- **Verify**: `abstractgateway --version`.

### Windows says scripts are disabled on this system

- **Cause**: an execution policy set by Group Policy (`Get-ExecutionPolicy -List` shows
  `MachinePolicy` or `UserPolicy`) blocks saved `.ps1` files.
- **Fix**: paste the one-liner from [Install](install.md#windows), which runs a command rather than
  a script file, or ask your administrator.

## Starting and signing in

### The browser page asks for a token, or the sign-in link expired

- **Cause**: the one-time link (`/console#claim=…`) is single use, valid for 10 minutes and works
  only on the gateway's computer.
- **Fix**: `abstractgateway claim --open` opens a fresh link (or `abstractgateway-config claim-url`
  prints one). Re-running the installer also opens one.
- **Alternative**: sign in with the `admin` token stored in `<data>/auth/bootstrap-admin-token`.

### The gateway does not answer

- **Check**: `curl -sS http://127.0.0.1:8080/api/health` and, for a login item,
  `abstractgateway service status`.
- **Cause**: the first start loads the local engines and can take a few minutes; a gateway that
  exits during start writes the reason to its log (see [First checks](#first-checks)).
- **Fix**: wait for the first start to finish, restart the computer (the login item starts the
  gateway), or run the installer again, which repairs an interrupted install.
- **Verify**: `/api/health` answers and `http://127.0.0.1:8080/console` opens.

### The gateway is on another port

- **Cause**: port 8080 was taken (for example by `llama-server` or `mlx_lm.server`), so the
  installer used the next free port and remembered it.
- **Fix**: use the URL the install summary prints, or choose a port with `--port N` (Windows:
  `-Port N`) and re-run. `abstractgateway network status` shows the running address.

### No gateway after a restart

- **Cause**: the gateway starts at login only when a login item was registered (answering "no" to
  the start-at-login question, or `--no-service`, skips it).
- **Fix**: `abstractgateway service install --port 8080`, or re-run the installer and answer yes.

## Connecting clients

### Another device cannot reach the gateway

- **Cause**: the gateway listens on this computer only until you change its Network setting.
- **Fix**: `abstractgateway network set lan`, then apply it (`abstractgateway network restart`,
  the console, or the menu-bar icon). `abstractgateway network addresses` lists the URLs to use.
  See [Network setting](install.md#network-setting-who-can-reach-the-gateway).

### A browser app (Observer, Flow, Code Web) cannot connect

- **Check**: the gateway URL in the app, then `curl http://127.0.0.1:8080/api/health`.
- **Fix**: sign in with a Gateway user and that user's token (the `admin` token file on a fresh
  install), not the legacy `ABSTRACTGATEWAY_AUTH_TOKEN`. For apps served from another origin,
  include that origin in `ABSTRACTGATEWAY_ALLOWED_ORIGINS` (local development:
  `http://localhost:*,http://127.0.0.1:*`) or `abstractgateway network set --allowed-origins …`.
- See [Configuration](configuration.md#client-configuration-observer--flow-editor--code-web-ui).

## Models and providers

### Provider calls fail

- **Check**: `abstractcore --status` for the persisted configuration, and whether a local server
  (Ollama, LM Studio) is running. The console's **Engines** tab and `abstractframework doctor` show
  which engines answer.
- **Fix**: set the provider's environment variables or configure it in a console
  ([Configuration](configuration.md)); start the local server.

### Voice models are not found

- **Cause**: voice models download on demand and are not part of the install.
- **Fix**: prefetch them once, then they work offline:

  ```bash
  abstractvoice-prefetch --stt small --piper en
  ```

## Reporting a problem

When a step keeps failing, open an issue at
[github.com/lpalbou/AbstractFramework/issues](https://github.com/lpalbou/AbstractFramework/issues)
with the output of `abstractframework doctor --json` and the install log named in the error
message. Report security problems privately as described in [SECURITY.md](../SECURITY.md).
