# WorkflowBundles (`.flow`) and Lifecycle

WorkflowBundles (`.flow`) are the portable distribution unit for VisualFlow workflows:

- a zip bundle containing `manifest.json` + `flows/*.json` (and optional assets)
- entrypoints can advertise interface contracts (for example `abstractcode.agent.v1`) for discovery across clients

## Where bundles live (gateway-first)

On a gateway host, configure a bundles directory:

```bash
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/workflows"   # contains *.flow
```

The gateway discovers and serves bundles to thin clients via discovery endpoints.

Hosted gateways now distinguish two bundle registries:

- **Private runtime bundles** live in the caller's routed runtime and are served
  through `/api/gateway/bundles`. AbstractFlow's normal save/publish/test loop
  continues to use this private surface.
- **Workflow catalog bundles** live in the Gateway control plane and are served
  through `/api/gateway/workflow-catalog`. Admins upload or promote immutable
  `.flow` versions, move explicit default pointers, set ACLs, and deprecate,
  block, or tombstone versions without deleting bundle bytes.

Catalog workflows run in the requesting user's runtime by default. Clients
start them with `registry_scope: "tenant_catalog"` plus `bundle_id`,
`bundle_version` when an exact version is required, and `flow_id`. If the
version is omitted, Gateway resolves the admin-managed default pointer rather
than guessing from semantic version order. Exact older versions keep working
until that specific version is deprecated, blocked, or tombstoned.

Catalog starts must be explicit. If `registry_scope` is omitted, Gateway treats
the request as a private-runtime bundle start and will not silently fall through
to the shared catalog. Catalog run policy is Gateway-issued and signed before it
is passed into Runtime state; clients cannot authorize catalog subworkflow
starts by sending their own `_runtime.workflow_policy`.

## Recommended lifecycle controls

- Publish/install new versions instead of editing deployed bundles in place.
- Deprecate workflows instead of deleting:
  - hides from discovery
  - blocks new starts
  - keeps old versions available for replay/audit of historical runs
- For shared/default workflows, use the workflow catalog. Do not overwrite
  catalog bundle bytes for an existing `bundle_id@version`; publish a new
  immutable version and move the default pointer.
- `framework_catalog` is reserved for a later cross-tenant catalog. The
  implemented shared catalog scope today is `tenant_catalog`.

## See also

- [Scenario: Publish, install, and deprecate workflows](../scenarios/workflow-bundle-lifecycle.md)
