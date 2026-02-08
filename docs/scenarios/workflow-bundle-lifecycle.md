# Scenario: Publish, Install, and Deprecate Workflows (`.flow` bundles)

Goal: author a workflow once, distribute it as a portable `.flow` bundle, and manage its lifecycle on a gateway so it is
discoverable across clients.

## What you're managing

AbstractFramework distributes workflows as WorkflowBundles (`.flow` files):
- a zip bundle containing `manifest.json` + `flows/*.json` (and optional assets)
- entrypoints can advertise interface contracts (for example `abstractcode.agent.v1`) for discovery across clients

## Step 1: Author the workflow (Flow Editor)

Run the editor UI:

```bash
npx @abstractframework/flow
```

Open http://localhost:3003 and create/update your workflow.

## Step 2: Export/publish a `.flow` bundle

In the editor, export a `.flow` file (the bundle includes the root flow plus referenced subflows).

## Step 3: Put the bundle where the gateway loads bundles

On the gateway host, configure:

```bash
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/workflows"   # directory containing *.flow
export ABSTRACTGATEWAY_DATA_DIR="/path/to/gateway-data" # durable stores (run, ledger, artifacts)
```

Copy your bundle into `ABSTRACTGATEWAY_FLOWS_DIR`, for example:

- `my-bundle@0.1.0.flow`

Start/restart the gateway (bundle mode is the default):

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

## Step 4: Discover and run from clients

Once loaded, the bundle entrypoints show up in:
- Observer workflow picker
- Code Web UI workflow picker
- Gateway discovery endpoints (for custom clients)

If you built a chat-like agent flow, declare `interfaces: ["abstractcode.agent.v1"]` so clients can run it as an agent.

## Step 5: Deprecate instead of deleting (recommended)

Deprecation hides workflows from discovery and blocks new starts, while keeping installed bundles for:
- reproducibility of past runs
- auditability and traceability

Look for gateway lifecycle controls in your UI client (Observer / Flow Editor), or use the gateway API if needed.

