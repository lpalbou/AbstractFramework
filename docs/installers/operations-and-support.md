# Operations and Support

Where a bootstrap install keeps its files, how to check it, and how to fix common problems. The
install itself is described in [user-journeys.md](user-journeys.md).

## Locations

| What | macOS | Linux | Windows |
|---|---|---|---|
| uv | `~/.local/bin/uv` | `~/.local/bin/uv` | `%USERPROFILE%\.local\bin\uv.exe` |
| Gateway commands (uv tool shims) | `~/.local/bin` | `~/.local/bin` | `%USERPROFILE%\.local\bin` |
| Gateway environment | `~/.local/share/uv/tools/abstractgateway` | same | `%APPDATA%\uv\data\tools\abstractgateway` |
| Gateway data | `~/Library/Application Support/AbstractGateway` | `${XDG_DATA_HOME:-~/.local/share}/abstractgateway` | `%LOCALAPPDATA%\AbstractGateway` |
| Admin token (0600) | `<data>/auth/bootstrap-admin-token` | same | same |
| Logs | `<data>/logs/gateway.log`, `<data>/logs/install-*.log` | same | `<data>\logs\gateway.err.log`, `install-*.log` |
| Bootstrap state (port, mode, profile) | `<data>/bootstrap.env` | same | same |
| AbstractCore config | `~/.abstractcore/config/abstractcore.json` | same | `%USERPROFILE%\.abstractcore\config\abstractcore.json` |

`--data-dir` (or `AF_DATA_DIR`) moves the gateway data directory.

## Health checks

```bash
curl http://127.0.0.1:8080/api/health          # the gateway answers
uvx abstractframework doctor                    # host, tools, gateway, engines
abstractgateway-config status --json            # data dir, auth, defaults
```

`abstractframework doctor` only reads: it sends `GET /api/health` to `ABSTRACTGATEWAY_URL`
(default `http://127.0.0.1:8080`), `GET /api/version` to Ollama and `GET /v1/models` to LM Studio.
Add `--json` for tooling and `--no-network` to skip the HTTP probes.

## Troubleshooting

- **`abstractgateway: command not found`**: open a new terminal (the PATH change applies to new
  shells) or call `~/.local/bin/abstractgateway` directly.
- **Port 8080 in use**: the script picks the next free port and records it in `bootstrap.env`;
  pass `--port` to choose one. The summary prints the URL.
- **Gateway exited during start**: the script prints the last log lines; the full log is
  `<data>/logs/gateway.log`.
- **No gateway after reboot**: the gateway starts at login only when a service or Startup entry was
  registered (see the `Mode:` line of the summary). Re-run the script, or start it by hand.
- **Browser apps cannot connect**: check `ABSTRACTGATEWAY_URL` and that the gateway is healthy.
- **Local engine not reachable**: start Ollama or the LM Studio server; the console's Engines tab
  and `abstractframework doctor` show what is reachable.
- **Linux ARM64 build error for psutil**: install a C compiler (`sudo apt-get install -y gcc`) and
  re-run.

## Uninstall

`sh install.sh --uninstall [--purge]` or `install.ps1 -Uninstall [-Purge]`. Data is kept unless
you purge it.
