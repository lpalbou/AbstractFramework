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

## Recommended lifecycle controls

- Publish/install new versions instead of editing deployed bundles in place.
- Deprecate workflows instead of deleting:
  - hides from discovery
  - blocks new starts
  - keeps old versions available for replay/audit of historical runs

## See also

- [Scenario: Publish, install, and deprecate workflows](../scenarios/workflow-bundle-lifecycle.md)

