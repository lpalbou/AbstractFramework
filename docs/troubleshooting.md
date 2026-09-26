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

## Agent sessions

### Runs are refused: the default agent workflow is unavailable

- **Cause**: the gateway's saved `agents.default_workflow.<interface>` names a workflow that is no
  longer on the gateway (removed or deprecated). The gateway refuses runs that ask for the default
  (HTTP 409, naming the setting and its value) instead of running another workflow.
- **Check**: `abstractgateway config get agents.default_workflow.abstractcode.agent.v1`, or the
  console's **Workflows** → *Default agent workflow*, which shows the reason.
- **Fix**: choose an available workflow there, or `abstractgateway config unset
  agents.default_workflow.<interface>` to return to the built-in default. In the client, you can
  also pick a named workflow for now (`/workflow`, the **Workflow** list).
- See [Agent sessions](agent-sessions.md#the-default-agent-workflow).

### Replies do not stream

- **Check**: the client's **Stream replies** choice (browser Settings, `/stream` in the terminal,
  Assistant Settings → Models) and the gateway's `abstractgateway config get
  agents.streaming_default`. A client on **Gateway default** follows the gateway, which is off
  until saved.
- **Cause**: when a call does not stream, the client shows why: structured output, a gateway that
  calls a remote AbstractCore server, a provider that cannot stream or cannot report usage while
  streaming, or a workflow step that turns streaming off. **On — not supported by this gateway**
  means the gateway does not advertise live replies.
- **Fix**: choose **On** in the client or save `agents.streaming_default on`; for the listed
  causes, the finished answer still arrives complete.
- See [Agent sessions](agent-sessions.md#live-replies-streaming).

### No skills are listed

- **Check**: the empty list shows the gateway's explanation and its shelf folder; the console's
  **Apps** → *Skills shelf* shows where the shelf comes from.
- **Cause**: a saved `skills.shelf` folder that does not exist or holds no `skills/` folder is
  reported as unavailable (the gateway does not fall back to another shelf).
- **Fix**: `abstractgateway config unset skills.shelf` to use the gateway's own copy of the curated
  shelf, or save a folder that holds `skills/<name>/SKILL.md`. **Refresh the curated shelf** in the
  console copies the shipped shelf again.

### "Open folder" is missing from the Files view

- **Cause**: the workspace is on the gateway's computer, and only an admin sitting at that
  computer can have it opened there. A browser on another machine, even through an app proxy on
  the gateway's computer, counts as remote.
- **Fix**: copy the path shown (it is on the gateway host), or open it on the gateway's computer.
- See [Architecture: app proxies](architecture.md#app-proxies-and-the-forwarded-address).

### The Assistant opened from the console is not signed in

- **Cause**: an Assistant that was already running cannot receive the one-time sign-in; the code
  also expires after two minutes.
- **Fix**: quit the Assistant, then click **Open** on its card in the gateway console again.
- See [Agent sessions](agent-sessions.md#opening-the-assistant-from-the-gateway).

### The gateway still holds memory after an eject

- **Check**: the console's **Resources** view. With no model listed, it says how much accelerator
  memory the gateway process still holds, how that was measured, and what holds it. Ejects that
  wait for an in-flight call, or that failed, are listed above the table with the reason.
- **Cause**: a call still running on the old model, a model locked by another client (an eject
  without force is refused), or memory no model library reports.
- **Fix**: wait for the in-flight call, eject the named holder (with force for a locked model:
  `abstractgateway models unload --provider <p> --model <m> --force` or the console's force
  confirmation),
  or restart the gateway.
- **Verify**: the meter returns to the baseline and the resident-models table is empty.

## Reporting a problem

When a step keeps failing, open an issue at
[github.com/lpalbou/AbstractFramework/issues](https://github.com/lpalbou/AbstractFramework/issues)
with the output of `abstractframework doctor --json` and the install log named in the error
message. Report security problems privately as described in [SECURITY.md](../SECURITY.md).
