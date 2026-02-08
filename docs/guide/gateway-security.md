# Gateway Exposure Security (Checklist)

Treat `abstractgateway serve` as a control-plane service: it can access runs/ledgers/attachments, and (optionally) execute
maintenance actions depending on your deployment.

## Recommended defaults (local dev)

- Bind to loopback: `--host 127.0.0.1`
- Use a strong token:

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
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

## Verify quickly

- `/api/health` returns `200`
- `/api/gateway/*` endpoints return `401` without `Authorization: Bearer ...`

## See also

AbstractGateway has a deeper security guide (env vars, limits, lockouts, audit log):
- https://github.com/lpalbou/abstractgateway/blob/main/docs/security.md

