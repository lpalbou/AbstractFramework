# 1084 — Entity expression and personality-grounded visual behavior

> Package: abstractavatar, abstractentity, abstractruntime
> Type: research and contract proposal
> Created: 2026-10-31
> Status: Proposed
> Priority: medium
> Labels: expression, personality, provenance, visual-behavior

## Summary and rationale

Explore actionable visual expression for confidence, uncertainty/confusion, deliberateness,
tempo, positive/negative tone and perceived tension. Keep stable personality traits separate
from momentary expression and from authoritative operational/security status. The operator
mentioned Big Five/BFI and HEXACO as possible grounding; names and final axes remain undecided.

## Current code reality

Avatar inputs are pose/time/level/eight audio bands/gaze, with no expressive or personality input.
Entity activity and personal-time lifecycle already exist independently. A flat list of every
activity × expression combination would be unmaintainable. Root ADR 0044 proposes separate
channels and 1083 owns lifecycle/activity compatibility.

Existing expression work must be reused/audited first: UIC `cognition_bloom_core.ts` defines
nine registers, spring morphing and derived valence/arousal; `cognition_conduct_core.ts` derives
effort/conduct from observed facts and abstains on absent evidence. Entity `cognition_adapter.ts`
and its pinned-embedder scorer already carry register scores, evidence/provenance and
session-relative novelty, explicitly reading textual expression rather than inner state.
Define an adapter from those established bounded signals instead of introducing another scorer
or calling embeddings/models from the avatar's frame loop. Stable personality remains separate.

## Proposed exploration

- Identify a small bounded momentary expression vector and map each axis to observable changes:
  movement regularity, gaze, amplitude, openness, transition speed, hue/light or spatial cohesion.
- Stable traits may bias defaults, never override activity truth, accessibility or user choices.
  Distinguish configured style/persona, host measurement and entity self-report, with provenance.
- Preserve existing abstention and absent-versus-zero semantics. Confidence in an expression
  reading is not task correctness, tool safety, or an entity's internal confidence.
- Treat Big Five and HEXACO as human trait frameworks to investigate, not validated measurements
  of an AI's internal feelings. Do not label aesthetics as proof of competence, safety or trust.
- Actual approval, tool risk, compromised/offline status and permission indicators remain
  authoritative UI signals. A calm/confident-looking avatar never certifies a secure operation.
- Review questionnaire/content licensing before copying items, scoring instruments or commercial
  distribution. Research concepts and original bounded rendering parameters do not require
  shipping a questionnaire. Avoid automatic human assessment or psychometric claims.

## Sources and promotion criteria

[Berkeley BFI-2](https://www.ocf.berkeley.edu/~johnlab/bfi) describes the Big Five Inventory;
its commercial-use permission requirements need review before instrument reuse.
[HEXACO authors](https://hexaco.org/scaledescriptions) describe the six trait dimensions.
Confirm intended uses and permissions, define a small interpretable model with examples, and
review user comprehension before promotion. No trait inference/model calls occur in rendering.

## Expected outcomes, validation and non-goals

A proposed schema and visual mapping with repeatable examples, neutral defaults and explicit
data provenance. Compare recognizability across focus designs, themes, motion preferences and
platform capabilities. Test all normalization/clamping and absence/staleness behavior. Exclude
medical/diagnostic claims, moral classifications of entities, hidden affect inference, payment
policy and orchestration changes. ADR impact: root 0044 pending review; no implementation yet.
