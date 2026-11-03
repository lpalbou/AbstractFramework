# 1072: The installer never leaves a gateway running outside systemd

**Status**: completed 2026-10-29 (scripts/install.sh; ships with the next root release).
**Found by**: the OVH release-test server (2026-10-28). At 17:37 an install started the gateway in the background
(`MODE=background`) while the systemd user unit of the same gateway, from the 14:04 install, stayed enabled. At
17:52 a new login started that unit; it could not bind port 8080 (held by the background gateway), shut down and
(gateway bug, fixed in AbstractGateway PR #23) exited 0, so `Restart=on-failure` never retried. The gateway that
answered from then on was supervised by nothing.

## Fix (scripts/install.sh)

- `start_background`: before starting a background gateway on Linux, a systemd user unit that starts THIS install's
  gateway (`unit_runs_this_gateway`) is turned off (`systemctl --user disable --now abstractgateway.service`); a unit
  of another gateway is left as it is.
- `--server`: when the gateway service cannot be registered, the installer stops with the cause instead of falling
  back to a background gateway (a server's gateway is supervised by systemd or not started).

## Evidence

`tests/test_install_sh_linux_server.py::test_a_background_start_turns_off_a_login_service_of_this_gateway_first`
(red without the guard), `::test_a_background_start_keeps_another_gateways_login_service`; the installer suites
(linux server, server, profiles): 60 passed. The `--server` refusal is not exercised by a `--print` test (the plan
never fails a step); it is one `die` on the existing failure path.
