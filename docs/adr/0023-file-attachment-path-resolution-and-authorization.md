# ADR-0023: File Attachment Path Resolution and Authorization (Absolute Paths + Mounts)

## Status
Proposed (Draft)

## Dates
- Proposed: 2026-01-19
- Accepted: TBD

## Context

AbstractCode TUI supports attaching local files to a prompt via `@file` mentions (e.g. `@docs/readme.md`).

We must balance:

- **UX**: users frequently paste absolute paths (e.g. `@/Users/.../Desktop/toto.png`) and expect them to work.
- **Safety**: attachments should not allow arbitrary host filesystem access; they must be constrained to explicit roots.
- **Stability**: multiple syntaxes for the same file should resolve to a stable key for caching/dedup.

Historically, AbstractCode normalized `@file` tokens early using a *relative-only* normalizer that intentionally rejected absolute paths. This prevented `@/abs/path` from ever being resolved, even when the directory had been explicitly authorized via `/whitelist`.

In addition, attachments interact with **active context construction** and token usage. There is ongoing work on a more explicit “context placeholder” strategy to avoid any accidental duplication of file contents in the LLM prompt; this ADR does not decide that design.

## Decision

### 1) Explicit roots: workspace root + mounts

Attachments are only allowed if they resolve under one of the approved roots:

- **workspace root** (the default root for relative `@file` mentions)
- **mount roots** added via `/whitelist` (referenced as `@MountName/...`)

### 2) Support absolute paths, but only when authorized

`@/absolute/path` is allowed *only if* that absolute path resolves under:

- the workspace root, or
- any whitelisted mount root

If an absolute path is accepted, it is normalized to a stable **virtual path**:

- workspace-root file → `relative/path/to/file`
- mount file → `MountName/path/to/file`

This makes `@Desktop/toto.png` and `@/Users/.../Desktop/toto.png` canonicalize to the same key.

### 3) Blacklist and ignore rules still apply

- Any path matching a `/blacklist` entry is rejected, even if it is under an approved root (**blacklist wins**).
- Ignore rules (e.g. `.gitignore`) apply during attachment resolution.

### 4) Scope of this ADR

This ADR covers **path resolution and authorization** only.

It does not accept or reject any specific strategy for:

- how attachment contents are represented in the LLM prompt (inline vs placeholders),
- how token accounting is computed for attachments,
- or how attachments are summarized/compacted.

Those are expected to be clarified by a follow-up ADR once the “context/placeholders” design is finalized.

## Future Work (not decided here)

This ADR assumes the file being attached is on the **same machine as the client** (e.g. AbstractCode TUI running on a developer laptop).

For thin/remote clients (web/mobile/remote CLI), we also need:

- **Client-local attachments**: attach files from the *device running the client* by uploading bytes to the gateway (artifact-backed), not by referencing server filesystem paths.
- **Dual-policy / targets**: separate `target=server` (gateway host filesystem; operator-controlled policy) vs `target=client` (client device filesystem; user-controlled policy).
  - This prevents remote users from expanding server file access at runtime while still enabling convenient local-device attachments.

Hosted Flow/Gateway source terminology and workspace authority for these thin
clients are now governed by ADR-0037. This ADR remains focused on attachment
path resolution and authorization behavior rather than the broader hosted source
contract.

Tracked in:
- `docs/backlog/planned/511-framework-attachment-targets-and-dual-workspace-policy-server-client.md`
- `docs/backlog/completed/468-framework-gateway-attachments-upload-endpoint-v0.md`
- `docs/adr/0037-hosted-file-source-contract-and-workspacepath-authority.md`

## Consequences

### Positive

- Users can attach files via either relative or absolute paths (when authorized).
- Safety properties remain intact (approved roots + blacklist).
- Stable “virtual paths” enable caching and dedup across different input syntaxes.

### Negative

- Users may still be surprised when an absolute path fails because the directory is not mounted/under workspace root.
- Adds some complexity in the `@file` token normalization path (resolution happens before final normalization).

### Neutral

- No architectural decision is made here about placeholder-based context injection; this ADR remains compatible with either approach.

## Packages Affected

- AbstractCode (TUI file mention parsing, ingest, policy enforcement)

## Related

- `docs/guides/file-attachment-scope-policy.md`
- `docs/backlog/completed/463-abstractcode-tui-file-mentions-and-attachments.md`
- `docs/backlog/completed/473-framework-session-attachment-registry-and-open-tool-v0.md`
- `docs/backlog/completed/248-framework-env-context-and-absolute-paths-in-file-tools.md`
- `docs/backlog/completed/476-framework-workspace-mounts-and-allowlist-v0.md`
- `docs/backlog/completed/511-framework-attachment-targets-and-dual-workspace-policy-server-client.md`
- `docs/backlog/completed/468-framework-gateway-attachments-upload-endpoint-v0.md`
