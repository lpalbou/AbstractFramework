# Gateway Exposure Security (Checklist)

Treat `abstractgateway serve` as a control-plane service: it can access runs/ledgers/attachments, and (optionally) execute
maintenance actions depending on your deployment.

## Recommended defaults (local dev)

- Bind to loopback: `--host 127.0.0.1`
- Enable Gateway user auth for browser apps and per-user runtime routing:

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
```

- Use the generated `default/admin` browser-login token from
  `$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token` for first setup, then
  rotate it or create named users in `/console`.
- Use a strong `ABSTRACTGATEWAY_AUTH_TOKEN` only for legacy server/operator
  bearer-token deployments; it is not a browser sign-in token.

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
```

- Allow only localhost origins for browser UIs:

```bash
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

## If exposing beyond localhost (LAN, tunnels, internet)

1. Run behind TLS (reverse proxy or a trusted tunnel).
2. Use a strong token and rotate it periodically.
3. Restrict `ABSTRACTGATEWAY_ALLOWED_ORIGINS` to exact UI origins (avoid broad wildcards).
4. Protect reads as well as writes (ledgers contain prompts and tool outputs).

## Hosted file-source terms

When hosted browser clients talk about files, use this vocabulary:

- `Artifact`: a saved Runtime-owned file payload.
- `Local File`: a file chosen from the client device. In hosted/browser mode it
  is uploaded and becomes an Artifact before durable execution.
- `Server File`: a user-facing label for a file inside Gateway-approved
  workspace scope on the server. It does **not** mean arbitrary server
  filesystem access.

Canonical server paths use:

- `rel/path` for the main workspace root
- `mount_alias/rel/path` for approved mounts

If two allowed mounts share the same basename, Gateway now assigns
deterministic digest-suffixed mount aliases so the public path string is stable
across Gateway discovery, import/export, and Runtime execution.

Current UI surfaces may still say `Workspace` in some places. The engineering
term remains `Workspace File` / `Workspace Folder`.

## User isolation

When Gateway user auth is enabled, each user token resolves to a Gateway
principal and runtime mapping. Hosted browser apps such as AbstractFlow,
AbstractCode Web, and AbstractObserver exchange the signed-in user's token for
a Gateway browser session, store only an app-scoped opaque session id in an
HTTP-only browser cookie, and forward that session to Gateway server-side. The
raw user token is not stored in browser settings, and Gateway login response
bodies do not expose the session id or CSRF token. Mutating proxied Gateway
requests also carry a CSRF token. A server/admin token does not sign in
browsers. Gateway browser session cookies use an HTTP-only cookie for the
session id, a separate CSRF cookie, `SameSite=Lax`, path `/`, no `Secure` flag
on plain HTTP, and `Secure` when served over HTTPS. Sessions expire, logout
revokes the session record, and disabling/deleting/rotating the backing Gateway
user invalidates existing sessions.

For independent users, prefer `1 user = 1 runtime` through Gateway's
per-principal router. Gateway rejects duplicate runtime ids within the same
tenant when creating or updating users, so an admin cannot accidentally map two
tenant users to the same runtime. When a user is deleted, Gateway removes that
user's credential but reserves the retained runtime id for that deleted
principal; assigning the retained runtime to a different user is rejected unless
an admin explicitly transfers or purges the retained runtime reservation. Purge
requires exact runtime-id confirmation and deletes the retained runtime directory
before releasing the runtime id. Transfer assigns the retained runtime to an
existing same-tenant user and reserves that user's previous runtime id. Keep
shared/cross-user memory or collaboration explicit, permissioned, and auditable.

Hosted browser apps use the server-configured Gateway URL on non-local hosts.
AbstractFlow, AbstractCode Web, and AbstractObserver reject browser-supplied
Gateway URL changes when the UI is served from a non-loopback hostname. Enable
the app-specific override only behind your own access control:
`ABSTRACTFLOW_ALLOW_REMOTE_BROWSER_GATEWAY_CONFIG=1`,
`ABSTRACTCODE_ALLOW_REMOTE_BROWSER_GATEWAY_CONFIG=1`, or
`ABSTRACTOBSERVER_ALLOW_REMOTE_BROWSER_GATEWAY_CONFIG=1`. The host check uses
the request `Host` header by default. Trust proxy headers only when your reverse
proxy strips client-supplied forwarded headers, using the app-specific
`*_TRUST_PROXY_HEADERS=1` setting or `ABSTRACTGATEWAY_TRUST_PROXY_HEADERS=1`.

Shared workflows are handled through the Gateway workflow catalog rather than
by sharing a user's private runtime bundle directory. Catalog versions are
immutable by `bundle_id@version`; admins can move a default pointer, set ACLs,
deprecate or block a version, or tombstone it without deleting the stored
bundle bytes. Catalog workflows run in the requesting user's runtime by
default, so the shared workflow definition does not imply shared run state.
Run-start policy checks the signed-in user's tenant, roles, and catalog ACL
before execution. Private `/api/gateway/bundles` routes remain per-runtime
authoring surfaces.

Catalog bundles are loaded under internal host ids, but those internal ids are
not a public authorization surface. Direct private-bundle inspection routes
reject catalog-internal ids; use the ACL-aware `/api/gateway/workflow-catalog`
routes to list or inspect shared workflows. Gateway also strips client-supplied
`_runtime.workflow_policy` values and replaces catalog starts with a signed
Gateway-issued policy snapshot before Runtime sees the run.

Gateway serves a built-in admin/account console at `/console`. The console uses
the same browser-session contract: users sign in with a Gateway user id and
token, then the browser keeps only the opaque session cookie. Because the
console is served by Gateway itself, it does not ask for a Gateway URL; the
current origin is the Gateway. Admin users can
manage Gateway users, rotate tokens, and handle retained runtime reservations
from this console. Signed-in users configure provider connections in the
Providers tab, then set capability defaults from those configured virtual
providers and discovered models. Admin/root defaults act as the Gateway
baseline; normal users inherit that baseline and can override it only for their
own runtime.

The console also supports Gateway-owned provider endpoint profiles. Profiles
can describe OpenAI-compatible or hosted provider endpoints with a display name,
description, provider family, base URL, API key, capabilities, and optional
model allowlist. Discovery exposes only non-secret metadata and a virtual
provider id such as `endpoint:office-vllm`; Gateway injects the raw key only into
the runtime call that resolves that profile. Normal users can create user-scoped
profiles. Gateway-scoped profiles require an admin principal.

The console Sandbox sends browser-local prompt-grounding metadata such as local
datetime, timezone, timezone offset, and locale with test chat requests. Runtime
may use those fields to ground the model response for the browser user, but the
fields are explicitly untrusted and are never used for authorization, runtime
routing, provider credential selection, or audit authority. Server-derived
grounding remains recorded as provenance. When both browser timezone and browser
locale are present, country grounding prefers the timezone mapping over the
locale region because browser language is not a reliable location signal.

Gateway keeps operator surfaces admin-only through a central route-family
policy. User management, audit/process/backlog/triage/report routes, email
bridge routes, host metrics, model residency list/load/unload, server workspace
file helpers, and server workspace artifact import/export require an admin
principal. Browser local files should use upload routes; server filesystem
read/import/export is not exposed to ordinary hosted users.

In hosted user-auth mode today, ordinary users can still upload `Local File`
sources and reuse Artifacts, but server workspace helper routes and server
workspace artifact import/export remain admin/operator controlled until a
stronger per-principal workspace grant model lands.

Discovery metadata is permission-aware for these high-trust surfaces. Ordinary
users see admin-only workspace artifact import/export and provider prompt-cache
control operations marked unavailable with `admin_required` metadata. Their
session prompt-cache names are still usable, but the private hash includes the
current principal scope so two users cannot collide by choosing the same
session id, provider, and model.

## Verify quickly

- `/api/health` returns `200`
- `/api/gateway/*` endpoints return `401` without `Authorization: Bearer ...`
- `/console` loads the Gateway Console, and admin-only actions return `403` for
  non-admin users

## See also

AbstractGateway has a deeper security guide (env vars, limits, lockouts, audit log):
- https://github.com/lpalbou/abstractgateway/blob/main/docs/security.md
