# Proposed: Code node managed Python packages with simple authoring UX

## Metadata
- Created: 2026-06-04
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0015 execution targets and remote tool workers, ADR-0029 permissive dependency and licensing policy, ADR-0033 install profiles and server boundaries
- ADR impact: Needs new ADR or threat-model update before promotion if arbitrary package installation becomes available on shared/hosted Gateway deployments. This proposal does not authorize package installation in the current in-process `full_access` executor.

## Context
Flow Code nodes are useful for small Python transformations, but users naturally expect to write code like:

```python
import pandas as pd

def transform(_input):
    return pd.DataFrame(_input["rows"]).to_dict("records")
```

Today that is intentionally limited. The default `sandbox` mode rejects imports, and `full_access` imports only work when the host already has the package installed and `ABSTRACTRUNTIME_CODE_FULL_ACCESS=1` is enabled. That keeps the current implementation conservative, but the user experience is poor for common data, parsing, document, API, and scientific-library workflows.

The earlier proposed Flow item `abstractflow/docs/backlog/proposed/0077_custom_code_languages_and_dependencies.md` correctly identifies dependency declarations, bundle packaging, validation, deterministic install behavior, and isolation as the hard engineering problems. This proposal revises the product direction toward a simpler authoring process for Python packages first, instead of exposing a broad multi-language/dependency system to users up front.

## Current code reality
- `abstractflow/src/types/nodes.ts` defines the `code` node with `input`, `permissions`, `output`, `success`, and `execution`; default permissions are `sandbox`.
- `abstractflow/src/components/CodeEditorModal.tsx` lets users edit the body of `transform(_input)` and test by posting generated code to Gateway `/visualflows/code/simulate`.
- `abstractflow/src/utils/gatewayClient.ts` reads Gateway `code_execution_policy_v1` and disables unavailable Code permission modes.
- `abstractgateway/src/abstractgateway/routes/gateway.py::simulate_visualflow_code` executes Code-node tests through AbstractRuntime without starting a full run.
- `abstractruntime/src/abstractruntime/visualflow_compiler/visual/code_executor.py` rejects imports in `sandbox`, has optional RestrictedPython support, and runs `full_access` in-process with normal Python builtins.
- `abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py` regenerates Code-node code from `codeBody`, resolves the `permissions` pin, and creates a handler per permission mode.
- `abstractruntime/src/abstractruntime/workflow_bundle/models.py` supports free-form bundle `metadata`, but there is no structured dependency manifest for Code nodes.
- ADR-0015 already points toward ExecutionTargets and remote workers for sandboxed or placed execution. ADR-0029 requires explicit dependency justification and licensing clarity. ADR-0033 keeps package install profiles and server boundaries explicit.

## Problem or opportunity
The correct implementation cannot be a visible pile of venvs, requirements files, lockfiles, index URLs, workers, caches, and security jargon in the Code-node modal. A naive user should be able to:

1. Write Python imports.
2. See which packages are missing.
3. Add the package with a clear prompt.
4. Test the code.
5. Run the flow.

At the same time, the platform must avoid silently mutating the shared Gateway/Runtime Python environment, avoid implicit host imports, and preserve reproducibility and auditability.

## Proposed direction
Provide a simple "managed packages" UX for Python Code nodes while keeping package execution explicitly Gateway/Runtime managed.

The user-facing process should be:

1. User writes imports in the Code editor.
2. Flow performs best-effort import/package detection and shows small package chips such as `pandas`, `requests`, or `beautifulsoup4`.
3. If a package is not available, the editor shows `Add package` or `Prepare environment`, not venv/lock terminology.
4. Gateway advertises whether managed packages are available for this user and deployment.
5. When approved, Gateway asks Runtime to create or reuse a managed execution zone behind the scenes.
6. Runtime records the package set, environment hash, install logs, and policy decisions for that zone.
7. Code tests and real runs use the same prepared zone.
8. If the deployment is shared or hosted, package preparation requires operator/admin approval or an allowlisted package policy.

Flow remains the authoring surface. It can help users add a package declaration while the flow is still a draft, but the executable unit belongs to Runtime. When the flow is published or otherwise saved as a versioned executable unit, the dependency set should be frozen into an immutable Runtime execution zone. A later package change is a new authoring revision that creates a new zone or zone version; it must not mutate the zone used by already-published or otherwise versioned executable flow versions.

The durable model should still be explicit:

```json
{
  "code_execution": {
    "language": "python",
    "mode": "managed_packages",
    "execution_zone": {
      "id": "codezone_...",
      "hash": "sha256:...",
      "state": "frozen"
    },
    "packages": [
      {"name": "pandas", "specifier": ">=2.2,<3"},
      {"name": "requests", "specifier": ">=2.32,<3"}
    ],
    "lock": {
      "hash": "sha256:...",
      "source": "gateway_prepared"
    }
  }
}
```

That shape is illustrative, not final. The key point is that users see package chips and preparation state, while bundles and ledgers carry reproducible Runtime execution-zone metadata.

## Why it might matter
- Makes Code nodes useful for realistic data and document workflows without forcing every integration into a custom tool package.
- Preserves Flow as a thin editor: Flow authors package intent, Gateway advertises policy, Runtime or an execution worker owns execution.
- Avoids the bad path where users enable `full_access` and mutate the Gateway/Runtime host environment by hand.
- Gives local personal deployments a convenient path while leaving shared deployments policy-gated.

## User experience target
The default UX should feel like a code editor with package assistance, not an environment manager.

- The Code node still opens to the editor, variables, test input, and result.
- A compact `Packages` strip appears only when imports are detected or when the user opens it.
- Each package chip has status: `available`, `missing`, `preparing`, `ready`, `blocked`, or `failed`.
- The primary action is `Prepare and test` when packages are missing.
- Errors should say what to do: "Package `pandas` is blocked by Gateway policy. Ask an admin to allow it or use a preinstalled tool."
- Advanced controls such as version specifier, lock hash, index source, and environment logs are available but not the first view.
- A first-run personal Gateway may offer a single setup prompt: "Enable managed Code packages for this local Gateway." Hosted/shared Gateway must not silently enable it.

## Detailed product proposal
The user should be able to author complex Code nodes through one continuous workflow:

1. Open a Code node.
2. Write normal Python, including imports.
3. See unresolved imports as package chips.
4. Accept suggested packages or edit the package list.
5. Click `Prepare and test`.
6. See preparation progress and test output in the same modal.
7. Publish/run the flow without learning environment internals.

The important design point is that "seamless" does not mean implicit mutable host installs. It means the UI hides environment machinery while still producing an explicit Runtime execution zone.

### Code editor affordances
- Import detection:
  - detect `import x`, `import x.y`, and `from x import y`;
  - ignore standard-library modules for the selected Runtime Python version;
  - map import names to package names using a Gateway/Runtime resolver table plus user confirmation for ambiguous cases, for example `bs4 -> beautifulsoup4`, `PIL -> Pillow`, `cv2 -> opencv-python`.
- Package strip:
  - show detected packages as compact chips below or beside the editor;
  - use chip states: `declared`, `missing`, `preparing`, `ready`, `blocked`, `failed`, `frozen`;
  - keep manual `Add package` for packages that are imported dynamically or are optional extras.
- Package editor:
  - default view shows package names and statuses only;
  - advanced view allows version specifiers, optional extras, policy/index source, and logs;
  - users should not need to edit requirements files, lockfiles, venv paths, or hashes directly.
- Test path:
  - `Test code` becomes `Prepare and test` when package declarations are unresolved or not prepared;
  - editor tests use the same Runtime zone backend used by real runs;
  - result diagnostics include the execution zone id/hash behind a details toggle.

### Draft authoring behavior
- While a flow is a draft, package declarations are editable.
- Draft package changes invalidate only the prepared test zone for that draft.
- Flow may auto-detect imports, but it should not persist package declarations until the user confirms them or runs `Prepare and test`.
- Draft saves preserve package intent and preparation status, but do not freeze the executable zone.

### Publish and durable run behavior
- Publish, or an explicit versioned executable save, freezes package declarations into a Runtime execution zone.
- If the draft has no compatible prepared zone, publish should either prepare and freeze the zone after user/admin approval or fail with a clear message that the Code node package environment must be prepared first.
- Published flow metadata binds managed Code nodes to immutable zone hashes.
- Runtime runs use the frozen zone for that published flow version.
- Re-running an old published flow version must use the same zone hash unless an operator explicitly deprecates or migrates it with an audit record.
- Editing packages after publish creates a new draft dependency set and later a new frozen zone. It must not mutate the old zone.

## Runtime execution-zone model
Runtime should expose execution zones as durable execution resources. A zone is not just a venv path; it is the recorded contract for how Code was prepared and how it will run.

Suggested zone record:

```json
{
  "zone_id": "codezone_...",
  "zone_hash": "sha256:...",
  "language": "python",
  "python_version": "3.11",
  "platform": "macos-arm64",
  "state": "frozen",
  "backend": "local_venv_subprocess",
  "packages": [
    {"name": "pandas", "specifier": ">=2.2,<3", "resolved_version": "2.2.3"},
    {"name": "requests", "specifier": ">=2.32,<3", "resolved_version": "2.32.4"}
  ],
  "lock": {
    "resolver": "uv",
    "hashes_required": true,
    "lock_hash": "sha256:..."
  },
  "policy": {
    "network": "install_only",
    "indexes": ["pypi"],
    "approval": "local_user",
    "max_disk_mb": 2048
  },
  "created_at": "2026-06-04T00:00:00Z",
  "created_by": "tenant/user",
  "source": {
    "bundle_id": "example",
    "bundle_version": "1.2.0",
    "flow_id": "main",
    "node_id": "code_1"
  }
}
```

Zone states:

- `draft`: dependency declarations exist but are not installed/resolved.
- `preparing`: Runtime is resolving/installing packages.
- `prepared`: packages are resolved and testable, but the authoring flow is still mutable.
- `frozen`: bound to a versioned executable flow; immutable.
- `failed`: preparation failed; logs are retained.
- `superseded`: replaced by a newer zone for newer flow versions.
- `retired`: no longer runnable except through explicit operator recovery policy.

Immutability rules:

- `frozen` zone package declarations, resolved versions, and lock hash are immutable.
- A new package, version change, Python version change, backend change, or platform change creates a new zone hash.
- Cleanup can remove unused physical files, but it must not rewrite ledger history or published-flow metadata.
- If physical zone material is missing, Runtime should fail with a recoverable "zone material unavailable" error or rebuild only when the lock and policy allow exact reproduction, recording the rebuild.

## Durable runtime integration
Managed Code execution must become a durable Runtime activity, not an editor-only convenience.

- Zone preparation is durable:
  - preparation jobs have ids, status, logs, and retry/failure semantics;
  - publish can wait for or require a prepared zone;
  - failed preparation is visible to Flow and operators.
- Zone binding is durable:
  - published flow versions record the zone hash;
  - run ledgers record the zone id/hash/backend for each managed Code execution;
  - replay/debug can explain which package set was used.
- Code execution is durable:
  - long-running or worker-backed Code can be represented as a job/wait when needed;
  - repeated resume/retry must be idempotent where possible;
  - failures return the standard Code-node `success=false`, `output=null`, `execution`, and error diagnostics.
- Zone cleanup is policy-controlled:
  - draft/prepared zones can expire;
  - frozen zones are retained while published flow versions or ledgers depend on them;
  - operators can retire/rebuild zones with explicit audit.

## Failure and recovery UX
Common failures should have user-facing recovery paths:

- Missing package: "Add package `x` and prepare."
- Ambiguous import: "Import `PIL` usually comes from `Pillow`; confirm package."
- Policy blocked: "Package `x` is blocked by Gateway policy. Ask an admin or use a different package."
- Install failed: show concise error plus expandable logs.
- Zone changed after publish: "This published flow uses frozen zone `abc`; edit creates a new draft zone."
- Zone material missing: "Runtime cannot find execution zone material for this published flow. Rebuild from lock or contact operator."

## Promotion criteria
Promote this to `planned/` when the team is ready to implement Python package support and these decisions are accepted:

- Managed package execution has an owner: Runtime local backend, isolated worker, or ExecutionTarget.
- Runtime has an immutable execution-zone concept for published/versioned executable flows, with clear draft-vs-frozen lifecycle semantics.
- The security boundary is explicit for local personal Gateway vs shared/hosted Gateway.
- The UI can query a Gateway contract that reports managed package availability, policy, preparation endpoint, and current package status.
- There is a bundle metadata shape for Code-node dependencies that avoids implicit host imports.
- There is a validation plan for package install, test execution, real run execution, failure messages, and ledger provenance.

## Validation ideas
- Flow unit tests:
  - detected imports produce package chips without changing code;
  - package chips persist into Code node data or bundle metadata only after user confirmation;
  - unavailable Gateway policy disables `Prepare and test` with an actionable reason;
  - simple code with no imports keeps the current minimal editor.
- Gateway tests:
  - `code_execution_policy_v2` advertises managed package support and policy;
  - package prepare requests require the right role/policy;
  - blocked packages fail with stable, user-readable errors;
  - install logs and environment hashes are redacted and recorded.
- Runtime tests:
  - managed package Code runs out-of-process or through a worker, not inside the current in-process `full_access` handler;
  - tests and real runs use the same prepared backend;
  - published/versioned executable flow versions bind to an immutable execution-zone hash;
  - changing a package declaration creates a new zone or zone version instead of mutating the old one;
  - sandbox import rejection still works;
  - `full_access` remains local-trust only and does not masquerade as managed packages.
- End-to-end smoke:
  - create a Code node with `import requests` or `import pandas`;
  - add/prepare the package through Flow;
  - test in the editor;
  - publish/run the workflow;
  - inspect ledger/environment provenance.

## Non-goals
- Do not allow arbitrary `pip install` from inside user code.
- Do not install packages into the shared Gateway/Runtime process environment.
- Do not make current `full_access` the package-install solution.
- Do not expose venv, lockfile, worker, or index details as mandatory beginner UI.
- Do not build multi-language custom Code support in the first version.
- Do not guarantee that every PyPI package can run. Native extensions, platform wheels, GPU libraries, network access, and licenses remain policy-controlled.

## Suggested architecture
Use two layers: a simple UX contract and a stricter execution contract.

## Architecture confirmation
The confirmed direction is Runtime-owned immutable execution zones, not Flow-owned packages and not mutable Gateway package profiles.

Flow is first an authoring surface. It may help users detect imports, choose package declarations, and request preparation, but it must not become the execution environment owner. Gateway may approve and broker preparation according to deployment policy, but it should not mutate the executable package environment for an already versioned flow. Runtime owns Code execution and therefore owns the execution-zone lifecycle.

The critical lifecycle distinction is:

- draft Flow saves remain editable authoring state;
- publish, or an explicit versioned executable save, freezes the dependency set to an execution-zone hash;
- package changes after that point create a new draft/prepared/frozen zone or zone version;
- existing published/versioned executable flow versions continue to use their original frozen zone until retired or garbage-collected.

This preserves a simple user experience without sacrificing reproducible execution.

### UX contract
Flow asks Gateway for a Code execution contract, likely a successor to `code_execution_policy_v1`, with fields such as:

```json
{
  "contract": "code_execution_policy_v2",
  "modes": [
    {"id": "sandbox", "available": true},
    {"id": "managed_packages", "available": true, "requires_prepare": true},
    {"id": "full_access", "available": false}
  ],
  "packages": {
    "detect_endpoint": "/api/gateway/code/packages/detect",
    "prepare_endpoint": "/api/gateway/code/packages/prepare",
    "status_endpoint": "/api/gateway/code/packages/status/{job_id}",
    "zones_endpoint": "/api/gateway/code/execution-zones/{zone_id}",
    "approval": "local_user",
    "policy_summary": "Allowed packages from PyPI with admin denylist"
  }
}
```

Flow should degrade cleanly if Gateway only advertises `code_execution_policy_v1`.

Flow should send Gateway package intent, not install commands. A prepare request can look like:

```json
{
  "flow_id": "draft-flow",
  "node_id": "code_1",
  "language": "python",
  "python_version": "3.11",
  "code_hash": "sha256:...",
  "packages": [
    {"name": "pandas", "specifier": ">=2.2,<3"}
  ],
  "purpose": "editor_test"
}
```

Gateway validates authorization and policy, then asks Runtime to prepare a zone. Runtime returns a job or zone descriptor. Flow displays progress through Gateway.

Code simulation should reference the prepared zone:

```json
{
  "code": "def transform(_input): ...",
  "input": {"rows": []},
  "function_name": "transform",
  "permissions": "managed_packages",
  "execution_zone": {"zone_id": "codezone_...", "zone_hash": "sha256:..."}
}
```

Published WorkflowBundle metadata should include each managed Code node's frozen zone binding, package declarations, and lock/provenance. The exact storage location can be manifest metadata or a first-class manifest field, but it must be explicit and JSON-safe.

### Execution contract
Gateway/Runtime should treat managed packages as a different execution backend from `sandbox` and `full_access`.

Recommended order:

1. Local trusted v1: Runtime creates a hash-keyed execution zone, backed by a venv/cache or equivalent package environment, and executes Code out-of-process with server-side timeout and resource controls where available.
2. Safer v2: Gateway routes managed package Code to an ExecutionTarget/worker with stronger filesystem, CPU, memory, wall-clock, disk, and network limits.
3. Stable integrations: frequently used package workflows may graduate into tools or capability plugins instead of remaining ad hoc Code.

Minimum local implementation:

- Create package environment outside the shared Gateway/Runtime process environment.
- Execute Code in a subprocess using the zone interpreter.
- Pass input/output through JSON-safe files or pipes.
- Enforce wall-clock timeout.
- Capture stdout/stderr with truncation labeled `#TRUNCATION`.
- Return execution metrics and zone provenance.
- Keep `sandbox` import rejection unchanged.
- Keep `full_access` local-trust only and separate from managed packages.

Preferred hosted/shared implementation:

- Route execution to an ExecutionTarget/worker.
- Apply filesystem, network, CPU, memory, disk, and wall-clock policy.
- Pass large files through artifact refs, not inline payloads.
- Treat execution as durable job work with idempotency and provenance, aligned with ADR-0015.

### Execution-zone lifecycle
Runtime should own execution-zone lifecycle because Runtime owns Code execution. Flow can display and request changes, and Gateway can approve and broker policy, but neither should mutate an executable zone after it has been frozen.

Suggested lifecycle:

1. `draft`: package declarations are editable while the Flow author is still changing the Code node.
2. `prepared`: Runtime has resolved and installed packages for testing, producing a deterministic zone hash.
3. `frozen`: publish or an explicit versioned executable save binds the flow version to the zone hash. Runs use that exact zone.
4. `superseded`: package changes create a new draft/prepared/frozen zone; old flow versions keep their old zone until retired or garbage-collected.

This keeps the UX simple while preserving execution reproducibility: users do not need to understand venvs or lockfiles, but the Runtime still has a stable immutable execution target.

## Decision boundaries
- Flow owns the beginner package UX, package chips, editor affordances, and preflight display.
- Gateway owns user/admin policy, preparation authorization, package status, logs, and deployment-facing controls.
- Runtime owns Code execution semantics, execution-zone lifecycle, and the backend contract used by real runs.
- ExecutionTarget or a worker owns stronger isolation when packages are not trusted local-only code.
- Core should not own Code-node package installation. Core remains the provider/model/tool/capability layer.

## Risks and review notes
- Installing packages is supply-chain code execution. This needs policy, logs, and audit.
- A Python venv isolates dependencies from other Python environments, but it is not a security sandbox.
- RestrictedPython is not a secured sandbox; import/package support must not be represented as safe simply because RestrictedPython exists.
- Extra package indexes can create dependency-confusion risk; any custom index support must be deliberate and visible to operators.
- Package resolution can be slow or fail due to platform wheels. The UX needs progress, cancellation, and useful diagnostics.
- Native packages can consume significant disk and memory. Gateway needs quotas and cleanup.
- Local personal Gateway may allow user-approved packages by default only after explicit first-run enablement.
- Shared/hosted Gateway should default to disabled or admin-approved package allowlists.
- Network access during execution should be separately controlled from network access during package installation.
- Secrets must not be injected into Code zones by default.
- Package preparation logs should redact tokens, URLs with credentials, and environment variables.

## Dependencies and related tasks
- `abstractflow/docs/backlog/proposed/0077_custom_code_languages_and_dependencies.md`
- `abstractflow/docs/backlog/completed/0079_code_node_editor_execution_policy.md`
- `abstractflow/docs/backlog/completed/0081_code_editor_test_result_stability.md`
- `docs/adr/0015-execution-targets-and-remote-tool-workers.md`
- `docs/adr/0029-permissive-dependency-and-licensing-policy.md`
- `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- Official references to re-check during promotion:
  - RestrictedPython security statement: https://restrictedpython.readthedocs.io/en/stable/
  - Python `venv`: https://docs.python.org/3/library/venv.html
  - pip install and secure installs: https://pip.pypa.io/en/stable/cli/pip_install/ and https://pip.pypa.io/en/stable/topics/secure-installs/
  - uv environment/package management: https://docs.astral.sh/uv/pip/environments/

## Guidance for future agents
Re-check current Code-node execution before implementing. Favor the smallest user-facing surface:

- write imports;
- confirm package chips;
- prepare/test;
- run.

Keep the implementation strict behind that surface. The simple UI should manipulate draft dependency declarations, not mutate a frozen Runtime execution zone. If the simple UX requires unsafe implicit installs or mutable saved-flow environments, reject that design and keep this item proposed until the execution boundary is ready.
