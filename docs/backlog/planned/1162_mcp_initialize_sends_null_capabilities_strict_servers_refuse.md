# 1162 — The MCP client's `initialize` sends `null` capabilities; strict servers (Context7) refuse the handshake

> Package: AbstractCore (`abstractcore/mcp/client.py:57-70 initialize_params`, shared by the HTTP and stdio transports; the core agent's package, filed here for the owner). AbstractGateway's Skills & MCP page only shows the result.
> Type: defect
> Status: planned
> Created: 2026-11-08
> Priority: P1 (a normal user cannot add Context7, the one MCP server every coding assistant ships with)
> Labels: mcp, tools, interop

## What the operator saw (2026-11-08 11:29, gateway web console → Skills & MCP → Add server, URL `https://mcp.context7.com/mcp`)

> context7: The server answered but refused initialize: [ { "expected": "record", "code": "invalid_type", "path": [
> "params", "capabilities", "experimental" ], "message": "Invalid input: expected record, received null" }, … sampling,
> elicitation, roots, tasks … ]

RAGnarok (a lenient local server) accepts the same handshake, so the page looked healthy until a strict server came.

## Cause (read in the code)

```python
# abstractcore/mcp/client.py
def initialize_params(*, protocol_version, client_name, client_version):
    return {
        "protocolVersion": protocol_version,
        # Match the MCP reference client's envelope shape (server-side validators often
        # expect these keys to exist even when the values are null).
        "capabilities": {"experimental": None, "sampling": None, "elicitation": None, "roots": None, "tasks": None},
        "clientInfo": {...},
    }
```

The comment is wrong: the MCP schema declares every client capability as an optional OBJECT. The reference
TypeScript client sends `capabilities: {}` and adds a key only for a capability it implements. A zod-validated server
(Context7, most hosted servers) rejects `null` with exactly the message above; a key that is absent passes.

## Fix

- Send `"capabilities": {}` plus only the capabilities this client really implements (none today; `roots` only when
  the host registers roots).
- Same in the stdio transport (it shares `initialize_params`).
- Test: the initialize params contain no `None` value anywhere; a fake strict server that validates like zod accepts
  the handshake; the existing lenient-server tests still pass.
- Gateway follow-up after the core release: the Skills & MCP page's error is already the server's own words (good);
  the floor on AbstractCore rises at the next gateway cut so a fresh install gets the fix.

## Validation

- Add `https://mcp.context7.com/mcp` from the web console with no key: Test lists its tools (`resolve-library-id`,
  `get-library-docs`); Enable for agents works.

## Exchange with the core owner (2026-11-08 12:05)

Confirmed at core HEAD 492e210f (`mcp/client.py:58-72`). Agreed fix: `capabilities: {}`; a test in
`tests/test_mcp_handshake.py` walking `initialize_params` recursively (no `None` anywhere) and a fake server that
rejects `None` records the way zod does. The core owner ships it in one core patch with 1164 and the embeddings race
once the operator says go; the gateway raises its AbstractCore floor at its next cut.
