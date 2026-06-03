# Scenario: Gateway-first Local Development

Goal: run the full "thin clients + gateway control plane" stack locally:

- AbstractGateway (HTTP/SSE control plane)
- AbstractObserver (run observability)
- AbstractFlow Editor (author `.flow` workflows)
- Code Web UI (browser coding assistant)

This is the recommended topology because execution is unified and clients can attach/detach freely.

## Step 0: Install the pinned stack (recommended)

```bash
pip install abstractframework
```

From a source checkout, `./scripts/gateway-flow-local.sh` starts Gateway and
Flow together and prints the default `admin` browser-login token. For a
published-package smoke run, `./scripts/gateway-flow.sh` creates an isolated
published-package venv, enables Gateway user auth, prepares the same `admin`
user, and prints the Gateway URL, user, and token to enter in Flow.

If you want a minimal install instead, you need at least:
- `abstractgateway`
- `npx @abstractframework/flow` for the editor UI

## Step 1: Prepare directories

Pick the Gateway data folder. Packaged Gateway installs already include the
shipped `basic-agent` bundle. In a source checkout, point the gateway at the
repo's bundled workflows.

- `DATA_DIR`: where gateway stores run state/ledger/artifacts
- `FLOWS_DIR`: optional custom `.flow` bundle directory; in this repo use
  `./abstractgateway/flows/bundles`

Example:

```bash
mkdir -p ./runtime/gateway
```

## Step 2: Configure the gateway

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

# Source checkout only. Packaged installs can omit this and use the shipped bundle path.
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/abstractgateway/flows/bundles"
```

When the gateway starts, it creates `default/admin` if needed and writes the
browser-login token to `$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token`.

Optional route defaults (if your flows use LLM nodes):

```bash
abstractgateway-config set-default input.text \
  --provider ollama \
  --model qwen3:4b-instruct
```

You can also set the text default through Core:

```bash
abstractcore --set-global-default ollama/qwen3:4b-instruct
```

Capability routes are the durable default surface for local setups.

## Step 3: Start the gateway

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

Smoke check:

```bash
curl -sS http://127.0.0.1:8080/api/health
```

Read the local admin user token for browser UIs:

```bash
cat "$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token"
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
- Set User: `admin`
- Paste the generated Gateway user token
- Sign in

## Step 6: Author and run a specialized agent

1. In Flow Editor, create a workflow implementing `abstractcode.agent.v1`.
2. Export as a `.flow` bundle.
3. Put the `.flow` file into `FLOWS_DIR` (or configure the editor to publish to the gateway).
4. In Observer or Code Web, pick the workflow and start a run.
5. Watch the ledger stream in Observer.

See [Specialized agent as a portable `.flow`](specialized-agent-flow.md).

## Troubleshooting

- CORS errors in browser: widen `ABSTRACTGATEWAY_ALLOWED_ORIGINS` for your UI origin.
- "Unauthorized": ensure the browser UI is signed in with a Gateway user token, not the admin token.
- Bundles not showing up: verify `ABSTRACTGATEWAY_FLOWS_DIR` contains the shipped `basic-agent` bundle and any custom `.flow`
  files, then reload bundles from the UI (or restart the gateway).
