# Process manager environment overrides (write-only) - Operator guide

In this release the allowlist of this mechanism is empty, so nothing can be set here; it is
described for completeness. The gateway's process manager can store write-only environment
overrides for allowlisted keys of the processes it launches, from AbstractObserver, without ever
returning the values to browsers or clients.

## Security model

- Allowlist-only keys: no arbitrary environment editing (`PATH`, `LD_PRELOAD`, `PYTHONPATH`,
  `NODE_OPTIONS` and the like are never accepted).
- Write-only values: the gateway API never returns them.
- Values are stored on the gateway host with restrictive file permissions, in
  `<data dir>/process_manager/env_overrides.json`.

## Requirements

- The gateway process manager enabled (`ABSTRACTGATEWAY_ENABLE_PROCESS_MANAGER=1`).
- AbstractObserver connected to that gateway.

## Allowlisted keys

The gateway ships with an **empty** allowlist: framework settings are configured in the consoles,
not through environment variables. Email in particular is a per-user setting (the account page on the console's **Accounts** page;
see [Email integration](email-integration.md)). Email values saved here by an earlier gateway are
imported once into the administrator's own mailbox settings and then ignored.

## How overrides apply

When the process manager launches a managed process, it merges the gateway's own environment, the
allowlisted overrides, then the process's own static environment. A service that reads its
environment only at startup needs a restart after a change.

## See also

- [AbstractGateway: Maintenance](https://github.com/lpalbou/AbstractGateway/blob/main/docs/maintenance.md)
