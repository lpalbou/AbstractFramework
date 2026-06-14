# ADR-0037: Hosted File Source Contract And WorkspacePath Authority

## Status
Accepted (2026-06-11)

## Dates
- Proposed: 2026-06-11
- Accepted: 2026-06-11

## Context

Hosted AbstractFlow and other Gateway-first clients already expose three
practical ways to work with files:

- reuse an existing artifact;
- upload a browser-local file;
- import a server workspace path.

At the same time, the platform already has two durable truths:

- ADR-0036 makes Runtime the owner of canonical artifact meaning and
  provenance;
- Gateway already owns workspace policy, per-run workspace creation, and
  operator-approved mounts for server-side file access.

The missing contract is the boundary between user-facing source terms and the
engineering values that actually enter a hosted run. Without that contract,
product copy, authoring guidance, and future node work will keep conflating:

- durable artifacts with path capabilities;
- browser-local uploads with server-side workspace paths;
- workspace-scoped server access with a broader generic "server filesystem"
  idea.

This ADR is intentionally narrow. It does not design the full file/folder node
set, archive lifecycle, or local-folder snapshot format. It establishes the
hosted source contract and the authority model that later work must follow.

## Decision

### 1) Hosted users choose between three source classes

The user-facing source contract is:

| User-facing term | Meaning | What enters the flow | Durable / reusable | Access authority |
|---|---|---|---|---|
| `Artifact` | A saved runtime-owned file payload from previous workflow activity. | `ArtifactRef` | Yes | Artifact/runtime permissions |
| `Local File` | A file chosen from the client device. In hosted mode it is a source of bytes, not a live runtime path. | Uploaded bytes normalized into `ArtifactRef` before durable execution | Yes, after upload | User selects the file; then artifact/runtime permissions apply |
| `Server File` | A file already available inside Gateway-approved workspace scope or an approved mount on the server. It is not arbitrary server filesystem access. | A Gateway-owned workspace-scoped server-path value for path-based nodes, or `ArtifactRef` when imported | Path value: no. Imported artifact: yes | Gateway workspace policy. In hosted user-auth mode today, broader server workspace access remains admin/operator controlled until stronger per-principal grants land. |

Product copy may use `Server File` / `Server Folder` because users are choosing
an origin. Engineering docs and internal contracts should stay anchored on
`Workspace File` / `Workspace Folder` and `WorkspacePath`.

### 2) The hosted engineering target model is `ArtifactRef + WorkspacePath`

Hosted runs use two core file-like engineering values:

- `ArtifactRef`: the durable runtime-owned payload handle already governed by
  ADR-0036;
- `WorkspacePath`: the accepted contract name for a Gateway-owned path
  capability for a server file or folder under active workspace policy.

We do not introduce a separate durable `ServerFile` or `ServerPath` primitive
at this stage.

Current implementation note: this ADR accepts `WorkspacePath` as the contract
name and authority model to converge on. It does not claim that Flow, Gateway,
and Runtime already ship one shared typed `WorkspacePath` representation today.
Current file nodes still consume raw string paths under workspace policy, and
shared canonicalization is follow-up implementation work.

### 3) `WorkspacePath` is a scoped capability, not a portable absolute path

`WorkspacePath` has these rules:

- it identifies a server path only within Gateway-issued workspace policy;
- its portable identity is a workspace-relative path or a Gateway-issued
  mount-qualified path such as `mount_name + relative_path`;
- it must never treat a raw absolute OS path as the portable cross-surface
  identity;
- it is not an artifact and is not durable/reusable in the same sense as an
  `ArtifactRef`;
- file-versus-folder expectation is declared by the consuming node, tool, or
  pin, not by a separate core value primitive.

A stronger stable mount-id registry may be added later, but it is not a
precondition for this terminology contract.

### 4) Gateway owns the canonicalization authority boundary

Gateway owns:

- workspace roots and per-run workspace creation;
- operator-approved mounts / allowlisted roots;
- the authoritative public mount names/aliases exposed to clients today;
- the future canonical workspace-path serialization that follow-up
  implementation must align across Gateway and Runtime;
- hosted authorization over which principals and runs may use which workspace
  scope.

Follow-up implementation must make Runtime consume the same canonical
`WorkspacePath` values and workspace policy that Gateway issues. Runtime must
not invent alternate portable identities for the same server path.

### 5) Hosted authorization stays explicit and conservative

The hosted boundary is:

- browser-local files become artifacts before durable execution;
- server file access is limited to Gateway-approved workspace scope;
- current hosted behavior remains operator/admin controlled for broader
  workspace import/export and helper surfaces until stronger per-principal grant
  handling lands;
- client-supplied `workspace_root`, `workspace_access_mode`,
  `workspace_allowed_paths`, and `workspace_ignored_paths` are trusted/dev-mode
  exceptions, not authoritative hosted identity inputs.

### 6) This ADR does not imply shell sandboxing

Workspace scoping constrains path-oriented helpers. It does not make shell or
command-execution tools safe. `execute_command` and similar tools remain a
separate security boundary and must not be described as sandboxed merely
because workspace policy exists.

## Consequences

### Positive

- Product language can consistently teach `Artifact`, `Local File`, and
  `Server File` without inventing a broader server-filesystem abstraction.
- Future node and pin work has a narrow hosted engineering model:
  `ArtifactRef + WorkspacePath`.
- Artifact durability remains clearly separated from workspace-path capability.
- Operator docs can explain server access as workspace policy instead of
  implying generic server browsing.

### Negative

- Current Gateway/Runtime path identity still needs follow-up implementation for
  shared canonicalization and round-trip validation.
- `Server File` still needs strong helper text in user-facing surfaces so users
  understand it means an allowed workspace file, not arbitrary server access.
- The current hosted grant model remains conservative until later per-principal
  workspace grants are designed and implemented.

### Neutral

- This ADR does not decide the full file/folder node catalog.
- This ADR does not decide local-folder snapshot packaging.
- This ADR does not change artifact/session archive lifecycle behavior.

## Enforcement

- User-facing docs and UI may say `Server File`, but must qualify it as a file
  within Gateway-approved workspace scope when ambiguity matters.
- Engineering docs should use `WorkspacePath` and `Workspace File` /
  `Workspace Folder` for the server-side primitive.
- Hosted browser-local file flows must normalize to artifacts before durable
  execution.
- Runtime and Gateway implementations must not treat raw absolute server paths
  as the portable cross-surface identity for hosted workflows.
- Reviews for future file/folder features should reject any proposal that
  reintroduces a generic durable `ServerFile` primitive without a new ADR.

## Validation

This ADR is adopted when:

- root docs teach the accepted source contract and the `Artifact` /
  `WorkspacePath` boundary;
- backlog items for Flow terminology and coredoc alignment reference this ADR;
- follow-up implementation work explicitly tracks shared `WorkspacePath`
  canonicalization and round-trip validation.

Implementation evidence for canonical path round trips belongs to follow-up
backlog execution, not to this ADR-only adoption pass.

## Packages Affected

- AbstractFlow
- AbstractGateway
- AbstractRuntime
- AbstractObserver
- AbstractCode

## Related

- ADR-0023: File Attachment Path Resolution and Authorization (Absolute Paths + Mounts)
- ADR-0036: Runtime-Owned Artifact Descriptor Contract
- `abstractflow/docs/backlog/completed/0105_file_source_contract_and_workspacepath_foundation.md`
- `abstractflow/docs/backlog/planned/0104_abstractflow_node_and_authoring_terminology_alignment.md`
- `abstractflow/docs/backlog/completed/0103_coredoc_terminology_alignment_for_artifact_workspace_and_local_sources.md`
- `abstractflow/docs/backlog/planned/0106_workspacepath_canonicalization_mount_registry_and_roundtrip_validation.md`
