# 1021 — Plane isolation that cannot be switched off: other planes, auth and audit are always denied; nothing host-wide is shared by accident

> Package: abstractgateway, abstractruntime
> Type: task
> Created: 2026-10-15
> Priority: high
> Labels: governance, security, workspace, tools, adversarial-review-required
> Track: governance (README rows 13, 14, 16, 17, 18, 29)

## Summary

Isolation between users' runtimes rests on one admin switch and a posture: with
`workspace_builtin_deny` off the built-in refusals list is empty, and under "Allow everything" any
path with no row gets the default mode, so a run can read and write `users/*` (every plane),
`entities/*`, `auth/users.json` and the audit log (row 13, P0 conditional; the live posture is
"Allow everything rw" on a folder that contains the data dir). Beyond folders, several host-wide
surfaces ignore the plane: the runtime prompt-cache key (client-settable, session-id based; two
planes can share or poison a provider cache entry, row 14), a shared KG store path with
`scope=all`/`all_owners` (row 16), MCP servers registered by the admin and called with the admin's
credentials from every plane, stdio servers outside the sandbox (row 17), the model told the host's
OS account when a run has no requester (row 18), and process-wide switches (`--unsandboxed-commands`,
one gateway-wide tool default, no per-account ceiling; row 29).

## Why

Operator, 2026-10-15: "runtime should be owned and should be the isolation layer of what a user do";
"a user is a user. it has nothing to do with the OS since the gateway & runtime are virtualizing
both digital and human users. gateway could run as root and have 100 of digital and human users."

## Scope

### In scope
- Row 13 (GW): other planes, the gateway home's `auth/` and the audit log are a DENY that no switch
  and no posture can lift; `workspace_builtin_deny` lifts only credential folders. A test turns the
  switch off and sets "Allow everything" and still gets a refusal on `users/<other>/…`.
- Row 14 (RT + GW): the derived prompt-cache key includes tenant and runtime; the gateway strips
  client `_runtime.prompt_cache.key` and `.namespace`.
- Row 16 (GW): refuse a shared `ABSTRACTGATEWAY_MEMORY_STORE_PATH` in multi-user mode, or prefix
  owner ids with tenant+runtime; `all_owners` admin-only and read-only.
- Row 17 (GW): MCP credentials per account (or a per-server list of accounts it is offered to);
  stdio servers run inside the command sandbox.
- Row 18 (RT): drop the `USER`/`LOGNAME` fallback in `_detect_runtime_user` (ties to 1024).
- Row 29 (GW): refuse `--unsandboxed-commands` in multi-user mode; introduce the per-account tool
  ceiling and default that 1023 consumes.

### Out of scope
- The admin's own plane and the gateway home split (1019); per-run subsets (1023).

## Acceptance criteria
- [ ] Alice's run, with every switch at its most permissive, cannot list, read or write Bob's plane, `auth/`, or the audit log (file tools AND sandboxed commands); the test deletes the deny and goes red.
- [ ] Two runs in two planes with the same client-minted session id and the same workflow never share a prompt-cache entry.
- [ ] An MCP server registered by the admin is not callable from a plane it is not offered to; stdio servers show the sandbox label on their ledger records.
- [ ] Adversarial review with a mutation pass on the deny list.

## Receipts
- Audit table: `README.md` rows 13, 14, 16, 17, 18, 29 (2026-10-15); live `GET /workspace/policy` (posture "Allow everything rw" on `/Users/albou/tmp/abstractframework`).
