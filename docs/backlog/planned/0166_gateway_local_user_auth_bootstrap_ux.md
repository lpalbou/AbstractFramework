# Planned: Gateway local user-auth bootstrap UX

## Metadata
- Created: 2026-05-31
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0001
- ADR impact: None

## Context
Docker Gateway already bootstraps `default/admin` in user-auth mode and writes `auth/bootstrap-admin-token`. Native `abstractgateway serve` did not do the same, so users installing `abstractframework[apple]` had no obvious browser-login token.

## Current code reality
- `abstractgateway-config bootstrap-admin` creates `default/admin`.
- `abstractgateway serve` accepts user auth without a legacy shared token, but previously required users to know the separate bootstrap command.
- `ABSTRACTGATEWAY_AUTH_TOKEN` is a legacy shared bearer token and maps to `local-admin`, so Flow correctly rejects it for browser sign-in.

## Problem
The local pip path made users confuse the legacy Gateway bearer token with the Gateway user token used by `/console` and AbstractFlow.

## What we want to do
When Gateway user auth is enabled, `abstractgateway serve` should ensure `default/admin` exists, persist the bootstrap token file, and print the exact browser sign-in values.

## Why
The first run must be self-explanatory for both technical users and installer/GUI flows.

## Requirements
- Do not re-enable legacy bearer tokens as browser login tokens.
- Keep public-bind startup safe: avoid casually dumping raw tokens for public hosts unless explicitly requested.
- Keep Docker behavior aligned with native pip installs.
- Document the distinction between legacy bearer tokens and user-session tokens.

## Suggested implementation
Factor the bootstrap-admin logic into a reusable helper, call it from `abstractgateway serve` when user auth is enabled, and update user docs to make user auth the default UI path.

## Scope
AbstractGateway CLI/config CLI/tests/docs; root install docs that mention Gateway startup.

## Non-goals
- Do not remove legacy bearer-token support for server-to-server compatibility in this item.
- Do not implement a full first-run provider wizard here.

## Dependencies and related tasks
- Related: 0149, 0153, 0154.

## Expected outcomes
- `ABSTRACTGATEWAY_USER_AUTH=1 abstractgateway serve --host 127.0.0.1 --port 8080` prints `Gateway admin user: default/admin` and a usable `agw_...` token.
- Flow and Gateway Console both accept `admin` plus that token.
- Docs no longer tell browser users to use `ABSTRACTGATEWAY_AUTH_TOKEN`.

## Validation
- Unit test for `abstractgateway serve` bootstrapping user auth with no legacy token.
- Existing `abstractgateway-config bootstrap-admin` tests still pass.
- Manual startup output reviewed for local and public host cases.

## Progress checklist
- [x] Factor bootstrap helper out of config CLI.
- [x] Call helper during `abstractgateway serve` when user auth is enabled.
- [x] Add CLI regression test.
- [x] Update coredocs and LLM indexes.

## Guidance for the implementing agent
Keep the security model crisp: `ABSTRACTGATEWAY_AUTH_TOKEN` is a Gateway-level bearer token, not a browser user token.
