# ADR-0025: KG Entity Normalization (Stable CURIEs) and De-duplication Strategy

## Status
Proposed

## Date
2026-01-20

## Context

AbstractFramework’s long-term semantic memory is an append-only temporal KG (AbstractMemory) populated by:

- workflow extraction (AbstractFlow `ltm-ai-kg-extract-triples` → `memory_kg_assert`)
- provenance-preserving ingestion of runtime artifacts/spans (`ltm-ai-kg-ingest-span`, `ltm-ai-kg-ingest-turn`)

This system’s usefulness depends on **stable entity identifiers**:

- If the same real-world entity is minted with multiple IDs across turns/runs (e.g. `ex:person-noonien-soong` vs `ex:person-doctor-noonien-soong`), recall quality degrades and the graph becomes expensive to consolidate.
- Today, entity ID consistency is mostly a **prompt-level convention** (“use `ex:{kind}-{kebab-case}` and reuse IDs”), with limited deterministic enforcement.
- The store canonicalizes terms (`trim + lower`) for matching, but canonicalization does **not** solve entity identity drift (synonyms/variants still produce different canonical strings).

We need an explicit, testable contract for how CURIEs are minted, normalized, and later de-duplicated so that:

1) extraction can be stable enough for online recall (near-real-time composition into Active Memory/MemAct), and  
2) offline consolidation can safely reconcile remaining duplicates without destructive rewrites.

## Decision

### 1) Define a strict instance-ID contract for the `ex:` namespace

All instance entities minted by extraction workflows MUST use:

- **CURIE form**: `ex:{kind}-{slug}`
- **kind**: a controlled, low-cardinality prefix aligned to the ontology class
- **slug**: a deterministic, human-auditable, lowercase kebab-case string

Rationale (why we choose mnemonic IDs *for now*):
- In an LLM-driven extraction pipeline, mnemonic IDs are substantially easier to produce, review, and debug.
- They make KG traces and MemAct/Active Memory text readable without a separate label lookup step.

SOTA note (trade-off):
- Many “public / FAIR” KG guidelines recommend **opaque accession identifiers** to prevent churn when names change and to avoid accidental semantics in identifiers.
- We may adopt a **hybrid** later (e.g. `ex:{kind}-{slug}~{opaque}`), but v0 prioritizes LLM usability and auditability.

Allowed kinds (v0):

| Ontology class | Kind | Examples |
|---|---:|---|
| `schema:Person` | `person` | `ex:person-noonien-soong` |
| `schema:Organization` | `org` | `ex:org-openai` |
| `skos:Concept` | `concept` | `ex:concept-emotion-chip` |
| `cito:Claim` | `claim` | `ex:claim-memory-system-quality` |
| `schema:Event` | `event` | `ex:event-kickoff-meeting` |
| `dcterms:Text` | `doc` | `ex:doc-a-christmas-carol` |
| fallback / unknown | `thing` | `ex:thing-temporal-anchoring` |

Non-`ex:` namespaces (`schema:`, `skos:`, `cito:`, `dcterms:`, `rdf:`) are treated as vocabulary terms and must remain CURIEs as well.

### 2) Normalize `ex:` instance IDs deterministically at the ingestion boundary

At the ingestion boundary (the extractor’s deterministic gate, and/or runtime-side `MEMORY_KG_ASSERT`), apply:

- lowercasing
- whitespace and underscore → `-`
- Unicode normalization (best-effort ASCII folding)
- punctuation stripping (keep `[a-z0-9-]` only)
- `-` collapse and trim

This produces a stable slug even if the extraction model emits small formatting variants.

### 3) Prefer “entity linking” by reuse, but treat “perfect de-dup” as a follow-up

Normalization does not solve name variation (“Doctor Noonien Soong” vs “Noonien Soong”). Therefore:

- Online ingestion SHOULD attempt to **reuse existing IDs** when an entity is already in the KG.
- When reuse is uncertain, ingestion MAY mint a new entity and attach soft links:
  - `skos:closeMatch` or `schema:sameAs` (only when confidence is high)
  - `skos:altLabel` for known synonyms/aliases

Full cross-document entity resolution is explicitly out of scope for v0. We will instead:

- keep the system auditable (provenance back to spans)
- add scheduled consolidation jobs later (see Follow-ups)

### 4) Default to append-only, but allow explicit admin maintenance edits

Normal ingestion and automated consolidation should treat the KG as **append-only** (safer, auditable, replayable).
However, the system should still support **explicit admin/maintenance mutations** with strong guardrails, because:

- operational reality includes “bad IDs” and “bad extractions” that you may want to clean up,
- some repairs are cheaper as an edit than as long-lived alias clutter.

Policy:
- **Default path**: add new assertions (and, when needed, link entities using `schema:sameAs` / `skos:*Match`).
- **Maintenance path (admin-only)**: allow controlled edit/delete/merge operations, with:
  - durable audit log (who/when/why),
  - optional “dry-run” preview,
  - re-embedding/re-indexing when the stored text/vector representation changes,
  - conservative scoping (operate within a scope/owner partition by default).

## Implementation (v0 → v1)

### v0 (now): document the contract + enforce formatting

- Update docs to make the contract explicit and user-facing.
- Ensure the extractor gate enforces CURIE formatting rules for `ex:` IDs (kebab-case, lowercase, no spaces).
- Keep the current store canonicalization (`trim+lower`) as a matching layer, but treat it as separate from ID normalization.

### v1 (next): add an explicit resolver step (“reuse IDs”)

Add a small, deterministic “entity resolver” step before extraction:

1) For each candidate entity label/type, query the KG (`memory_kg_query`) to find existing entities with:
   - matching kind, and
   - a label triple (`schema:name`, `skos:prefLabel`, `dcterms:title`) similar to the candidate label
2) Present top candidates to the extractor prompt as an allowlist (“reuse these IDs when appropriate”)

This shifts de-dup from “hope the model reuses IDs” to “model chooses from presented candidates”.

### v2 (later): scheduled consolidation / reconsolidation

Introduce scheduled jobs to:

- cluster likely-duplicate entities (labels + neighborhood similarity)
- emit non-destructive reconciliation edges (`schema:sameAs`, `skos:exactMatch/closeMatch`)
- optionally write “canonical-of” pointers used by query-time rewriting (without rewriting historical assertions)

## Consequences

### Positive
- Stable, predictable instance IDs improve recall, packetization, and MemAct/Active Memory reconstruction quality.
- Deterministic normalization makes the system more robust to minor model drift (spaces/underscores/casing).
- Makes later consolidation tractable, while keeping risky admin edits rare and auditable.

### Negative / Risks
- Over-aggressive slug normalization can cause collisions (`ex:person-john-smith` is ambiguous).
- Honorific/role words (“doctor”, “captain”) may be inconsistently included; resolver v1 is needed to reduce this drift.
- Admin maintenance edits are powerful and risky:
  - can break provenance expectations if not audited carefully,
  - can invalidate embeddings/vectors unless re-indexed,
  - can make debugging harder if used as a “silent cleanup” mechanism.

### Neutral / Notes
- `TripleAssertion` canonicalization (`trim+lower`) is a storage/query matching policy, not identity resolution.
- “Claim vs concept” duplication is intentional in the current semantic model:
  - claims capture verbatim statements with provenance
  - concepts capture reusable topics/entities referenced by many claims

## Follow-ups

- Add a resolver primitive (or flow composition) so extraction can reuse existing entity IDs deterministically.
- Add optional collision-avoidance suffixing (`-2`, `-3`) when minting would collide within an owner scope.
- Add a scheduled consolidation workflow for duplicate entities and alias edges.
- Add explicit admin KG maintenance tools (merge/rename/delete) with audit and re-indexing.

## Related

- `docs/memory-kg.md` (KG behavior, canonicalization, provenance)
- `docs/guides/memory-components.md` (how KG packets become Active Memory)
- `docs/adr/0009-connected-memory-recall-and-provenance.md` (spans as durable provenance units)
- `docs/backlog/completed/409-abstractflow-kg-extractor-grounding-normalization-and-dedup-v0.md`
- `abstractflow/web/flows/ltm-ai-kg-extract-triples.json` (extractor prompt + deterministic gate)
