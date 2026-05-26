# ADR-0034: Framework Release Sequence and Gates

## Status
Accepted (2026-05-09)

## Dates
- Proposed: 2026-05-09
- Accepted: 2026-05-09

## Context

AbstractFramework is released as multiple PyPI packages and GitHub projects, but the packages are
not independent at release time. Several CI jobs intentionally install packages from PyPI rather
than from neighboring local clones so that packaging mistakes and missing published dependency
versions are caught before users hit them.

This means a package can be correct locally and still fail CI if it is released before one of its
new dependency floors is visible on PyPI. The recent Runtime, Agent, and Gateway profile work made
this risk concrete:

- Runtime CI asked for `abstractsemantics>=0.0.3` before the newer Semantics package was visible.
- Agent CI asked for `abstractruntime>=0.4.8` before Runtime `0.4.8` was visible.
- Gateway should not be considered ready until Core, Runtime, Agent, Memory, Semantics, and
  capability packages are all published and their normal branch checks are green.

The project needs an explicit release order and release gate so agents do not race ahead to higher
packages just because local tests or one workflow passed.

## Decision

Release packages in topological order by published dependency floors, not by local workspace
availability.

### Standard Order

1. Release media/capability packages first when their versions are consumed by Core, Gateway, or
   app-facing install profiles:
   - `abstractvoice`
   - `abstractmusic`
   - `abstractvision`
   - future generated-media capability plugins
2. Release schema, vocabulary, and storage packages whose versions are consumed by Runtime,
   Gateway, or memory-aware app features:
   - `abstractsemantics`
   - `abstractmemory`
3. Release `abstractcore` after any capability plugin versions referenced by Core extras are
   already available on PyPI.
4. Release `abstractruntime` after `abstractsemantics`, `abstractmemory`, and any Core version
   referenced by Runtime extras are available on PyPI. Runtime owns the `MEMORY_KG_*` effect
   contract and therefore depends on the light AbstractMemory package, while hosts choose storage
   backend extras such as LanceDB.
5. Release `abstractagent` after the required `abstractcore` and `abstractruntime` versions are
   available on PyPI.
6. Release `abstractgateway` last among backend packages, after required Core, Runtime, Agent,
   Memory, Semantics, Vision, Voice, and Music versions are available on PyPI and their current
   branch checks are green. Gateway's base install is the remote-light server profile; its
   `apple` and `gpu` extras are full hardware deployment profiles.
7. Release the root `abstractframework` manifest, installers, or app-facing docs after Gateway
   install profiles and deployment images are verified.
8. Release thin-client apps after Gateway APIs, readiness contracts, artifact routes, and
   generated-media capabilities are stable enough for them to consume.

If a package does not depend on a changed lower package, it may be skipped. If a package raises a
dependency floor, the lower package must already be published and visible to `pip`.

### Release Gates

Before triggering a higher-layer release:

- Confirm each required lower package version is visible from PyPI using a clean index query.
- Confirm the lower package's normal `main` branch CI is green for the commit being released, not
  only that a manual release workflow succeeded.
- Confirm a clean virtual environment can install the target package using PyPI dependencies, not
  editable sibling clones.
- Confirm version, changelog, package metadata, and profile extras match the dependency floor being
  released.
- Confirm release workflows do not mask missing PyPI packages by relying on local monorepo paths.

If branch CI failed only because a lower package had not propagated to PyPI yet, rerun the failed
jobs after the lower package is visible. Do not proceed upward until the rerun is green.

### Docker Gate

Gateway Docker images are a deployment artifact, not a substitute for Python package readiness.
Build or publish Gateway images only after the Gateway Python release gate is satisfied. The
supported Docker strategies are:

- lightweight Gateway server image;
- explicit NVIDIA server image for GPU deployments.

Native Apple/MLX deployment remains a Python installation path on macOS, not a portable Docker
target.

## Consequences

### Positive

- Prevents higher packages from depending on unpublished or not-yet-propagated lower versions.
- Keeps CI meaningful by validating the same PyPI dependency closure users will install.
- Makes Gateway releases a true framework integration gate rather than a local green test.
- Gives agents a deterministic sequence to follow during multi-package release work.

### Negative

- Release work is slower because PyPI propagation and branch checks are explicit gates.
- A correct package may need a CI rerun after an upstream package becomes visible.
- Agents must distinguish "manual release workflow succeeded" from "current commit is releasable".

### Neutral

- This ADR does not change package ownership or layering. It only governs release order and
  readiness checks.
- Package-specific hotfixes can still be released independently when their dependency floors do
  not change.

## Packages Affected

- `abstractframework`
- `abstractsemantics`
- `abstractmemory`
- `abstractvision`
- `abstractvoice`
- `abstractmusic`
- `abstractcore`
- `abstractruntime`
- `abstractagent`
- `abstractgateway`
- app and installer repositories that consume Gateway/Core releases

## Related

- ADR-0001: `docs/adr/0001-layered-architecture.md`
- ADR-0032: `docs/adr/0032-package-dependency-boundaries-and-gateway-first-apps.md`
- ADR-0033: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- Runtime CI rerun root cause: missing `abstractsemantics>=0.0.3` on PyPI at first push check.
- Agent CI rerun root cause: missing `abstractruntime>=0.4.8` on PyPI at first push check.
