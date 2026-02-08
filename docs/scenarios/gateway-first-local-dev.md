# Scenario: Gateway-first Local Development

Goal: run the full "thin clients + gateway control plane" stack locally:

- AbstractGateway (HTTP/SSE control plane)
- AbstractObserver (run observability)
- AbstractFlow Editor (author `.flow` workflows)
- Code Web UI (browser coding assistant)

This is the recommended topology because execution is unified and clients can attach/detach freely.

## Step 0: Install the pinned stack (recommended)

```bash
pip install "abstractframework==0.1.1"
```

If you want a minimal install instead, you need at least:
- `abstractgateway[http]`
- `abstractruntime[abstractcore]`
- (optional) `abstractagent`, `abstractflow[editor]` depending on your bundles

## Step 1: Prepare directories

Pick two folders:

- `FLOWS_DIR`: where your `.flow` bundles live
- `DATA_DIR`: where gateway stores run state/ledger/artifacts

Example:

```bash
mkdir -p ./runtime/gateway ./runtime/flows
```

## Step 2: Configure the gateway

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/runtime/flows"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
```

Optional defaults (if your flows use LLM nodes):

```bash
export ABSTRACTGATEWAY_PROVIDER="ollama"
export ABSTRACTGATEWAY_MODEL="qwen3:4b-instruct"
```

## Step 3: Start the gateway

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

Smoke check:

```bash
curl -sS http://127.0.0.1:8080/api/health
```

## Step 4: Start the thin clients

In separate terminals:

```bash
npx @abstractframework/observer
npx @abstractframework/flow
npx @abstractframework/code
```

Default ports:
- Observer: http://localhost:3001
- Code Web: http://localhost:3002
- Flow Editor: http://localhost:3003

## Step 5: Connect UIs to the gateway

In each UI:
- Set Gateway URL: `http://127.0.0.1:8080`
- Paste the auth token
- Connect

## Step 6: Author and run a specialized agent

1. In Flow Editor, create a workflow implementing `abstractcode.agent.v1`.
2. Export as a `.flow` bundle.
3. Put the `.flow` file into `FLOWS_DIR` (or configure the editor to publish to the gateway).
4. In Observer or Code Web, pick the workflow and start a run.
5. Watch the ledger stream in Observer.

See [Specialized agent as a portable `.flow`](specialized-agent-flow.md).

## Troubleshooting

- CORS errors in browser: widen `ABSTRACTGATEWAY_ALLOWED_ORIGINS` for your UI origin.
- "Unauthorized": ensure the UI auth token matches `ABSTRACTGATEWAY_AUTH_TOKEN`.
- Bundles not showing up: verify `ABSTRACTGATEWAY_FLOWS_DIR` contains `.flow` files, then reload bundles from the UI (or
  restart the gateway).

