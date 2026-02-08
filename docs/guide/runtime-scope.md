# Runtime Scope (run / session / global / all)

This guide defines the meaning of **scope** across AbstractRuntime's memory effects and host UX.

## Why scope exists

The runtime stores durable "memory" under a runtime-owned namespace in run state. A scope decides **which durable owner**
receives reads/writes, and therefore which runs share memory.

## Scopes

### `run`

- The current `run_id`.
- Best for per-run working memory (notes/tags/compaction spans that should not leak outside this run).

### `session`

- Shared across runs that share the same `session_id`.
- Use when you want continuity across multiple runs launched by the same client "session".

Important: `session` is a host contract. If a host does not provide a stable `session_id`, session scope may degrade to
"per-run" behavior.

### `global`

- A single global owner shared across the whole runtime instance.
- Use for durable cross-session memory (preferences, stable facts).

### `all`

`all` is a query fan-out scope used by some operations to search across:
- `run`
- `session`
- `global`

This is why `global != all`:
- `global` means "only the global owner"
- `all` means "run + session + global"

## Practical examples

- "Remember this for the rest of this run": `scope=run`
- "Remember this for this user session": `scope=session`
- "Remember this forever": `scope=global`
- "Search everything I know": `scope=all`

## What survives a backend restart?

Scope controls *which durable owner* receives reads/writes, but persistence depends on the host stores:

- With file-backed stores (run store + ledger store + artifact store), `run`/`session`/`global` scoped memory persists.
- With in-memory stores, scope still works, but everything is lost on restart.

## Gateway API note (important)

If you start runs via the gateway and you want `scope=session` behavior across multiple runs, you must send a stable
`session_id` when starting those runs.

