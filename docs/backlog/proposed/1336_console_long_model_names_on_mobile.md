# 1336 — Keep long model names and repository actions readable on phones

> Package: AbstractGateway Console
> Type: bug
> Status: Proposed
> Created: 2026-11-14
> Priority: P2
> Labels: console, models, responsive, release-qa

## Summary and reason

At 400 px, a long Hugging Face model name/provider badge and repository-details action
can be clipped by the model card. The document itself has no horizontal overflow,
so a page-width assertion alone misses this loss of content.

## Current code reality

Observed in the pristine published Gateway 0.21.1 Console with Core 2.35.2, normal
account login and supported HF_ENDPOINT pointing to owned synthetic metadata.
The model card stays within the viewport while its header/action text exceeds its
inner edge. Desktop remains readable. The request-budget/cache/cooldown behavior
passes independently. Evidence: framework release-recovery review-console-registry-proof.md
and site-0.14.1/console-registry-root.txt, including both 400 px state captures.

## Scope and expected outcome

Keep the full model identity and selected-repository action accessible on narrow
screens through wrapping or an explicit accessible truncation/copy affordance.
Review model_catalog card/header/action CSS in console_catalog.py. Preserve the
manual-search/details split and the shared quota cooldown. This is a follow-up
proposal, not implementation included in the 0.14.1 recovery candidate.

No inference, model downloads, service changes, provider routing or card redesign
is needed to reproduce it. The metadata and repository names are synthetic.

## Dependencies and validation

Use a released or candidate Console and controlled metadata, without real HF calls.
Check long real-shaped IDs and short names at 400 px and desktop; inspect children
and screenshots, not only document.scrollWidth. Verify keyboard access and readable
identity/action labels. Existing bounded search, explicit details and cached-row
cooldown contracts must continue to pass.
