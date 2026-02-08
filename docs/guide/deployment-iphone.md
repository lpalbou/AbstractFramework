# iPhone Notes (Safari / PWA)

Code Web UI is designed to run on iPhone as a thin host UI that connects to a remote gateway deployment.

## Prereqs (recommended)

- Gateway reachable over HTTPS (reverse proxy + TLS).
- Web UI hosted over HTTPS.
- Gateway configured with:
  - `ABSTRACTGATEWAY_AUTH_TOKEN` (recommended)
  - `ABSTRACTGATEWAY_ALLOWED_ORIGINS` including your web UI origin (exact host recommended for prod)

## Steps

1. Open the web UI URL in Safari.
2. In Settings:
   - set Gateway URL (for example `https://gateway.example.com`)
   - set auth token if required
3. Optional: Safari -> Share -> Add to Home Screen.

## Constraints

- iOS suspends background tabs aggressively; durability depends on ledger replay, not "staying connected".
- File access is remote (via gateway); the phone does not run local tools in v1.

