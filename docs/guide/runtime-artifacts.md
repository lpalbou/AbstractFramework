# Runtime artifacts and retrieval

This guide explains how to investigate runtime resources without conflating
artifacts, ledgers, provider traces, and semantic memory.

## Responsibility map

| Layer | Responsibility |
|---|---|
| AbstractRuntime | Stores runs, ledgers, waits, artifacts, artifact descriptors, media facts, and access stats. Runtime is the source of truth for artifact identity and canonical descriptors. |
| AbstractGateway | Exposes Runtime resources over HTTP, applies auth/RBAC, projects `artifact_envelope_v1`, provides exact stats/facets/paging, and adds action links where available. |
| AbstractObserver | Visualizes Gateway data. Observe explains workflow narratives from ledger records; Runtime Activity supervises runs; Artifact Explorer inventories artifacts. |
| AbstractMemory / KG | Stores semantic memory and knowledge graph records. It is for concept/entity/relationship retrieval, not byte-level artifact inventory. |
| AbstractSemantics | Validates semantic predicates and schema-level meaning where KG/memory data is used. |

## Artifact vs local/server file sources

Use these terms consistently when a hosted client works with files:

- `Artifact`: the durable Runtime-owned file payload. This is what Artifact
  Explorer inventories.
- `Local File`: a client-device source. In hosted/browser mode it is uploaded
  and stored as an Artifact before durable execution.
- `Server File`: a user-facing label for a file inside Gateway-approved
  workspace scope. For artifact-style inputs it may be imported into a new
  Artifact; for path-based operations it remains a workspace-scoped server path
  whose availability depends on current Gateway policy and grants.

This guide is about Artifacts. A server workspace file that has not been
imported or produced as an Artifact will not appear in Artifact Explorer.

## Which surface to use

Use **Observe** when the question is about a workflow: what was requested, what
steps ran, what is waiting, what failed, what subworkflows exist, and what the
final outcome was. Observe replays the run ledger and can stream updates.

Use **Runtime Activity** when the question is operational: what is running,
waiting, failed, scheduled, stale, or needs a human action. Activity rows expose
open Observe, open ledger, open artifacts, open logs, copy ids, and cancel/stop
actions where Gateway authorizes them. Queue counts are for the loaded run page
unless Gateway exposes a broader run-stats endpoint.

Use **Artifact Explorer** when the question is about outputs: images, markdown,
HTML, JSON, voice, music, transcripts, documents, workflow snapshots, and other
files. Artifact Explorer uses Gateway artifact search with exact stats/facets
when available and pages the result set.

If the question is “what files are available in the server workspace for this
run?”, use workspace/file-helper surfaces instead. Artifact search only answers
questions about stored artifacts.

Use **Mindmap/KG** when the question is semantic: entities, relationships,
notes, memories, and graph-level knowledge. Do not use artifact metadata search
as a substitute for KG retrieval.

Use **Gateway audit/provider links** for host-level request traces. Audit tails
are global system activity unless an artifact envelope or ledger record links a
trace to a specific run/artifact.
Gateway artifact envelopes only expose safe relative Gateway/UI action links;
external provider URLs should be converted into Gateway-owned trace records or
redacted trace artifacts before users open them.

## Artifact search contract

Gateway artifact search is the canonical thin-client query path:

```bash
curl -sS -H "$AUTH" \
  "$BASE_URL/api/gateway/artifacts/search?scope=all&artifact_kind=music,voice&include_stats=true&limit=500"
```

Useful filters include `scope`, `session_id`, `run_id`, `artifact_kind`,
`semantic_kind`, `render_kind`, `modality`, `content_type`, `workflow_id`,
`node_id`, `created_after`, `created_before`, `query`, and `tags`.

Use `include_stats=true` when a UI needs exact totals, byte totals, or facet
counts. The stats are independent of the current page limit. Use `limit`,
`offset`, and cursors for bounded pages.

`artifact_kind` is UI-oriented. Canonical filters should prefer descriptor
fields:

- `semantic_kind=music` for generated music.
- `semantic_kind=voice` for TTS/voice artifacts.
- `render_kind=markdown` for Markdown rendering.
- `render_kind=html` for HTML source rendering and full-page preview.
- Generic `audio` should be treated as unclassified audio, not as voice or
  music unless the descriptor says so.

## Provenance and descriptors

Runtime-owned artifact descriptors are the reliable source for artifact meaning.
For descriptor-aware generated media, the envelope may include:

- producer package, capability route, provider, model, backend;
- prompt or TTS text, requested format, redacted parameters, output index;
- source artifacts used for edits, reference media, image-to-video, or other
  derivations;
- media facts such as dimensions, sample rate, channels, duration, and frame
  counts;
- links back to run, workflow, node, turn, ledger cursor, and provider trace
  availability.

Missing descriptor fields mean the producer did not record that fact or the
artifact is legacy. Consumers should show that absence plainly.

## Direct Runtime inspection

When investigating from the filesystem, start with the Gateway data directory
or runtime root configured by `ABSTRACTGATEWAY_DATA_DIR`. Artifact bytes,
metadata, and catalog state are Runtime-owned. Prefer Gateway APIs when the
server is running because Gateway applies authorization and records access
actions for previews/downloads.

For package-level details, see:

- `abstractruntime/docs/artifacts.md`
- `abstractruntime/docs/api.md#artifacts-store-by-reference`
- `abstractgateway/docs/api.md#artifacts-and-filesystem-handoff`
- `abstractobserver/docs/architecture.md#runtime-boundary`

## Privacy and safety

Artifact metadata can include prompts, source refs, provider/model ids, and
bounded generation parameters. Do not dump raw provider payloads, secrets, or
large artifact contents in summaries. Prefer ids, counts, descriptors, and
redacted snippets unless the user explicitly asks to inspect a non-image
artifact's content.
