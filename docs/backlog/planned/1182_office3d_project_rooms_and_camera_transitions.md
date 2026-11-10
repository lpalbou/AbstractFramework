# 1182-office3d: [FEATURE] Give each project a physical room and transition between rooms

> Package: office3d
> Type: feature
> Status: planned
> Created: 2026-11-09
> Priority: P2
> Labels: office3d, projects, rooms, visualization

## Summary

Give each project its own spatially distinct room and let the user travel between project rooms with a camera transition. Project work continues to belong to the project, independently of which room is visible. The current three room themes are a separate, ongoing visual change; a theme alone does not create multiple rooms.

## Current code reality

`office3d/static/app.js` constructs one Three.js scene, camera and room, renders a single `state`, and uses camera goals for board and follow views. Project-scoped API calls capture the project ID and reject stale views. `office3d/engine.py` `Office` stores one active `project`, tasks, DMs and events; `open_project` swaps that state and currently blocks switching while agents are active. `server.py` scopes project requests against that active project. Recheck these paths and ongoing theme, shared dossier and kickoff work before design; they are changing concurrently.

## Why

Projects should feel like places in the same office while remaining separate workspaces. Navigation must never cause one project's messages, files, actions or work to appear in another, or cause work to start merely because the camera moved.

## Scope

### In scope

- Design a project-to-room identity and navigation model, including a clear selected-project indicator and a camera transition between rooms. Address reduced motion, interrupted transitions, reload, missing/deleted projects, and a usable non-spatial project selector.
- Separate collaboration/project lifecycle from rendering. Decide and document how multiple project contexts and active runs are isolated, persisted and synchronized; re-examine the current single-active-project guard rather than bypassing it. Establish any needed architectural decision in an ADR before closure.
- Preserve project-scoped commands, modal ownership, polling and async responses during rapid navigation. A visit or camera movement alone must not launch, resume or duplicate runtime work; explicit project creation/kickoff semantics remain separate.
- Make room geometry and resources scale reasonably with project count, and reuse the existing theme choices without coupling room identity to a theme.

### Out of scope

Specialty workflows are a later proposal ([1183](../proposed/1183_office3d_specialty_rooms_and_workflows.md)); implementing themes, a dossier or kickoff already underway is not part of this item. Do not assume all project runtimes can safely run concurrently until the isolation design proves it.

## Acceptance criteria

- [ ] Two projects have distinct room identities; navigating between them produces a comprehensible transition, with reduced-motion and interruption handling.
- [ ] Returning to either project restores its own data and visual context; concurrent or delayed responses, actions and modals cannot cross project boundaries.
- [ ] Navigating or reloading does not start or duplicate a run; existing explicit kickoff behavior remains correct.
- [ ] Active-run switching behavior is safe and clearly communicated; the implementation and any ADR describe its isolation and lifecycle constraints.
- [ ] Browser and engine coverage exercises navigation, isolation, interrupted transitions and active-run behavior, including accessible navigation and reduced motion.

## Testing

- Run `npm run test:browser` and relevant existing project isolation and lifecycle tests, extending them with the scenarios above.
- Run `python -m unittest discover -s tests` where the local dependencies support it; document any environment limitations and manually verify the transition in a browser.

## Dependencies and ADR status

Reassess the in-flight themes, shared dossier and kickoff changes first. No governing office3d ADR identified; the collaboration/runtime boundary may need a new ADR, to be decided before implementation closure.

## Receipts

- Planning based on `office3d/static/app.js`, `engine.py`, and `server.py` inspected 2026-11-09.

## Deployment state 2026-11-10 (handed to the framework seat; operator: later; NOT part of release 0.14.0)

Operator ruling 2026-11-10 ~13:00: office3d is an ongoing, still experimental project and an app; it is not part of the
0.14.0 release and does not gate it.

The athena.ovh install of the dev framework + office3d stopped mid-way; full state and the operator's decisions in
`office3d/untracked/handoff-2026-11-10.md` (untracked, on purpose: hosts, ports, auth files). Resume from there: deploy both via
the gateway and its managed apps, office over HTTPS + basic auth, keep `~/.local/share/abstractgateway` and the GitLab-nginx
vhosts. Same host as the 0.14.0 candidate's Linux CPU clean-install check (1179).
