# 1073: The installer installs a second gateway on the same host as an instance

**Status**: completed 2026-10-29 (scripts/install.sh, scripts/uninstall.sh, docs/deploy-linux.md section 9;
ships with the next root release; needs the gateway's instances, AbstractGateway PR #37).
**Found by**: the OVH release-test server (2026-10-29). A second gateway on port 8443 was built by hand: a venv with
a `.pth` pointing into the 8080 gateway's site-packages, a transient `systemd-run` unit, a hand-made data dir, and
the 8080 gateway's apps listed by the 8443 console. The operator's ruling: a second gateway is a first-class,
scripted, self-contained instance.

## Fix

- `install.sh --instance NAME` (with `--port N`, required): it exports `ABSTRACTGATEWAY_INSTANCE`,
  `UV_TOOL_DIR=<data>/tool`, `UV_TOOL_BIN_DIR=<data>/bin` and `ABSTRACTCORE_CONFIG_DIR=<data>/core-config`. The data dir
  is the per-OS default plus `-NAME`. Its systemd unit is `abstractgateway-NAME.service` and its LaunchAgent label
  `ai.abstractframework.gateway.NAME`. It never runs `uv tool update-shell`, never writes the gateway pointer, and
  refuses a gateway too old to know instances (that one's `service install` would overwrite the default gateway's
  unit).
- `--tailscale-funnel` publishes on `--https=443` for the default gateway and `--https=8443` for an instance
  (`--funnel-https-port` 443|8443|10000). The Funnel check reads `<host>:<https port>`.
- The summary and the by-hand steps name the instance: its command `<data>/bin/abstractgateway --instance NAME`,
  its unit, and an `export` line before the by-hand steps.
- `install.sh --uninstall --instance NAME` (also `uninstall.sh --instance NAME`) removes that instance only. `--purge`
  deletes its data dir and nothing shared. `--remove-uv` is refused (uv is shared).

## Evidence

`tests/test_install_sh_server.py`, the five instance tests (unit, data dir, tool dir export, Funnel 8443, no PATH and
no pointer, `--port` required, the name checked, Funnel https ports, a scoped uninstall). Each test goes red when
its guard is mutated out (5 of 5 mutations checked).
