# Process Manager Env Vars (Write-only) - Operator Guide

This guide explains how to configure a small allowlist of environment variables on the gateway host via AbstractObserver,
without exposing the values back to browsers/clients.

## What this is (and why)

- Goal: configure framework integrations (for example email) from the UI.
- Security model:
  - allowlist-only keys (no arbitrary env var editing)
  - write-only values (the gateway API never returns env var values)
  - values are persisted on the gateway host with restrictive file permissions

## Requirements

- Gateway process manager enabled: `ABSTRACTGATEWAY_ENABLE_PROCESS_MANAGER=1`
- AbstractObserver connected to that gateway

## Where values are stored (host-side)

- `<ABSTRACTGATEWAY_DATA_DIR>/process_manager/env_overrides.json`

## How values are applied

- When you set/unset an allowlisted env var in the UI:
  - the gateway persists it to `env_overrides.json`
  - the gateway applies it to its own `os.environ` (so integrations reading env vars can see it)
- When the process manager launches managed processes, it merges:
  1. gateway `os.environ`
  2. allowlisted overrides
  3. per-process env (static)

If a service reads env vars only at startup, restart that service after changing env vars.

## Allowlisted keys

The allowlist is gateway-defined. Email-related keys are commonly allowlisted for inbox and SMTP defaults.

## See also

- AbstractGateway docs: https://github.com/lpalbou/abstractgateway

