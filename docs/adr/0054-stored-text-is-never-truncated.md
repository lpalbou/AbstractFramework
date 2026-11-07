# ADR 0054: Stored Text Is Never Truncated — Store the Verbatim, Let the Consumer Decide

Status: Accepted (2026-11-08; operator ruling of 2026-11-08 ~05:00, after two runtime findings the same night).
Applies to every package that stores a summary, a title, a digest, a gist, a card lead or any other text derived
from a model or a person: AbstractRuntime, AbstractMemory, AbstractGateway, AbstractNote, the apps.

## Context

Two stored texts were found cut by the runtime on 2026-11-08: the mechanical title builder
(`abstractruntime identity/digest.py` ~171) cuts a Markdown line at the 14th word, leaving `###` and `**` mid-title in
30 of nerin's 292 records; and a diary entry's digest is stored as `first_line[:120]` when no gist was elected
(`integrations/abstractmemory/identity_support.py:180`), so the record holds 120 characters and "…", the gateway serves
that, and no app can show more. A comment called the second cut "a ruled act-only ledger contract". The operator:
"the truncation is a violation of ADR. It is true that for rendering purposes we may sometimes allow truncation, but
here those are summaries: never truncate summaries or titles, especially not in what is stored. You must store the
verbatim and let the consumer apps decide what they show or not. The only cases where we may (TBD) accept truncation
would be for major API speed-ups."

## Decision

1. **What is stored is whole.** A summary, title, digest, gist, card lead, narration or verbatim is stored exactly as
   produced: no character cap, no word cap, no "…". A builder that needs a short form derives it from the whole text at
   read time, never by cutting the stored text.
2. **Rendering may shorten, storage may not.** An app or console may fold, collapse or elide for its screen (ADR 0053
   rule 2: an explicit "…" control reveals the rest); the record it reads stays whole.
3. **A short form is derived, never cut mid-structure.** When a short form is needed (a one-line title from a
   paragraph), it is derived from the text rendered to plain text (a parser, never a regex on prose) or from the first
   sentence before any heading marker; it never ends inside a Markdown marker, a word or a sentence.
4. **The only exception is explicit and recorded.** A field may carry a bound only when a measured API speed-up
   requires it; the bound is a documented field property (`max_chars`, with the reason and the measurement), the whole
   text is still stored elsewhere and reachable by reference, and the operator has ruled on it (TBD: none today).
5. **Existing cut records are repaired**, not left as history: the understanding pass (root 1146) rewrites them from
   their verbatims; a record whose verbatim is gone is marked `truncated_at_source` so nobody mistakes it for whole.

## Consequences

- AbstractRuntime: the title builder and the diary digest fallback change at the source (root 1146, "related runtime
  fixes"); tests assert a 300-char first line stores a 300-char digest and that a title never contains a stray marker.
- AbstractMemory: `digest`, `title`, `narration` columns carry no length limit; the display block exposes the whole
  text; any shortening lives in read helpers.
- AbstractGateway: serves what is stored; never shortens on the way out.
- Reviews of any package check for `[:N]`, `max_length`, `truncate(` on stored text paths; each found instance is a
  defect unless it carries the rule-4 record.
- Related: ADR 0053 rule 2 (rendering), ADR 0003 (AbstractMemory redigestion, amended by root 1146's in-place rewrite).
