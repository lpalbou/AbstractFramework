# 1183-office3d: [FEATURE] Explore specialty rooms for different kinds of work

> Package: office3d
> Type: feature
> Status: proposed
> Created: 2026-11-09
> Priority: P3
> Labels: office3d, rooms, workflows, research

## Summary

Explore rooms specialized for development, mathematics, analysis, reports and articles. Their value must come from useful team capabilities and work surfaces, not only different decorations. This is a future direction, not a commitment to build all five or to change the existing software team now.

## Current code reality

`office3d/engine.py` defines fixed software-team roles and project workspace tools, including file access, code execution, browser testing and previews. `office3d/static/app.js` displays one shared Three.js room and its board. Per-project themes are underway; physical project rooms are planned in [1182](../planned/1182_office3d_project_rooms_and_camera_transitions.md). Neither implies domain-specific workflows or domain expertise.

## Opportunity and proposed direction

Investigate what a person doing each kind of work needs: development may need code and preview; mathematics, equations and reproducible calculations; analysts, data and evidence; reports and articles, sources, drafts and review. Compare real user tasks and existing capabilities before choosing a small pilot. Define how a room's available roles, tools, artifacts, review and outputs differ, how sources and provenance are retained, and how a project selects or changes a specialty without confusing its history. Keep collaboration and runtime contracts independent of visual room presentation; never imply expertise or verification that has not occurred.

## Scope and non-goals

Scope is research and an evidence-backed pilot proposal, including accessibility, project isolation, tool permissions, review and user expectations. A theme selector alone is not a specialty workflow. This item does not authorize autonomous runtime starts, new domain claims, the implementation of every specialty, or cross-project data sharing.

## Promotion criteria

1182's room and project-lifecycle design is understood; at least one concrete user workflow and measurable improvement are identified; the pilot's capabilities, safeguards, evaluation and ownership are feasible. Review whether a durable ADR is needed before implementation; no governing office3d ADR identified.

## Acceptance criteria

- [ ] Compare the five requested specialties against real tasks and existing capabilities; select or reject a pilot with reasons.
- [ ] Define the pilot's roles, tools, artifacts, provenance, review, isolation, accessible interaction and success measures.
- [ ] Preserve the findings and any ADR decision so a later implementation can be scoped independently.

## Testing

- Run `npm run test:browser` for any prototype that changes the UI, and exercise an end-to-end representative task with evidence of its actual outputs and review.
- Check project isolation and tool permissions with `python -m unittest discover -s tests` when applicable; record limitations and qualitative user feedback.

## Receipts

- Planning based on `office3d/engine.py` and `static/app.js` inspected 2026-11-09; themes are a separate ongoing change.
