# 1180 — An activated skill is always reachable by the agents; the abstractcore and abstractgateway skills are registered on every fresh install

> Package: AbstractRuntime (the `read_file` interception in `integrations/abstractcore/effect_handlers.py`; the skills prompt text), AbstractSkill (bundled registry gains `abstractcore`; 0.3.11), AbstractGateway (no code: the shelf seed already registers bundled skills at start)
> Type: defect + default
> Status: completed
> Created: 2026-11-08
> Completed: 2026-11-10
> Priority: P1
> Labels: skills, tools, fresh-install

## What the operator saw

Code web, a skill activated for the session: the agent's `read_file` on `…/skills/abstractcore/SKILL.md` answered
`Error: File '…' is ignored by .abstractignore policy`. Core's file tool applies the workspace `.abstractignore` (which
on this machine prunes `untracked/` and the gateway data folder `runtime/`, where the skills shelf lives) and the
workspace scope; a skill offered to the model was therefore unreadable. The agent had also found a stale copy of the
skill under a scratch worktree because the prompt names skills without their path.

## Rulings

- "If a skill is activated for a session, it should always be reachable by the agents."
- "By default, the skills for abstractcore and abstractgateway should always be registered in the gateway on fresh install."

## The cleanest way (chosen)

1. **Reachability by design, in the runtime, not in a client and not by weakening the ignore policy.** The runtime
   already intercepts `read_file` before core's tool to serve session attachments. The same interception serves any
   file under one of the run's SKILL ROOTS (the folders of the skills the run was given, derived from the run's
   `skills` field exactly as the gateway derives `ABSTRACTCODE_SKILLS_ROOTS`): the runtime reads it whole and returns
   it in core's line-numbered format, so neither `.abstractignore` nor the workspace scope can refuse an activated
   skill; paths outside the roots behave as before; a symlink escaping a root is refused.
2. **The prompt names the path.** Beside the `<available_skills>` block the model is told "to use a skill, read
   `<root>/<name>/SKILL.md`", so it never searches the workspace for a copy.
3. **Fresh install.** AbstractSkill's bundled registry already carries `abstractframework-gateway` as a first-party
   curated skill; `abstractcore` joins it the same way (verbatim copy of `abstractcore/skills/abstractcore/`, catalog
   and validation records, 0.3.11). The gateway seeds bundled skills into `<data dir>/skills/registry` at every start
   and adds what is missing, so existing installs gain it at the next start and fresh installs have both from the
   first minute. An imported copy named `abstractcore` stays beside the curated one (imported never shadows curated).

## Not chosen

- Exempting skill folders inside `.abstractignore` (the shelf path differs per install; the policy is a walk filter, not
  the right place for a per-session grant).
- Serving skills only through a new tool (changes the model's habit; the path read is what every host does).

## Acceptance

- [ ] With a `.abstractignore` that refuses the shelf path, `read_file` on an activated skill's SKILL.md returns the whole file.
- [ ] The prompt carries the path for every offered skill.
- [ ] A fresh data dir lists `abstractcore` and `abstractframework-gateway` on the Skills page after the first start.

## Built 2026-11-08 16:40 (awaiting the next restart)

- abstractruntime b22c901: `integrations/abstractcore/skill_roots.py` + the read_file interception serve any file under
  the run's skill folders whole (core's line-numbered shape, ranges honoured, symlink escapes refused); roots derived from
  the run record only (`vars.skills` mapping or names + `_runtime.skills_resolution`, or the `<path>` of
  `_runtime.skills_block`). 7 tests red-without.
- abstractskill bf6b982 = 0.3.11: `registry/skills/abstractcore/` (verbatim from abstractcore main cac85276, first-party
  validation record), registry 2026.11.10 with 17 skills; `format_available_skills_xml` renders `<path>` per skill and
  the hint "read the SKILL.md at its <path> with read_file; do not search the workspace for another copy".
- No gateway change: the shelf seed adds `abstractcore` at the next start; abstractskill is an editable install on this
  machine, so the restart carries 0.3.11. Follow-up (one line, next release): `resolve_run_skills` records
  `resolution["shelf"]` so the runtime has a second root source when a prompt carries no `<path>`. Only `read_file` is
  intercepted (not list/search), by design.

## Completion report (2026-11-10)

Moved from `planned/1180_an_activated_skill_is_always_reachable_and_the_core_and_gateway_skills_ship_by_default.md`
to `completed/` by the backlog hygiene pass of 2026-11-10. Built and committed on every repo's `main`; not released.
It ships with the next wave ([1179](../planned/1179_release_wave_understanding_pass.md)): abstractskill 0.3.11 before
the gateway cut, AbstractRuntime 0.19.0, AbstractGateway 0.21.0. Original status line: "planned — THIS release
(operator 2026-11-08 16:01: "a new bug to fix within this release")".

### What was built (commits checked against each repo's log on 2026-11-10)

| Repo | Commit | What |
|---|---|---|
| AbstractRuntime | `b22c901` (2026-11-08 16:21) | `read_file` inside one of the run's skill folders is answered by the runtime, whole, before core's tool: core's line-numbered shape, ranges honoured, realpath containment, a symlink out refused |
| AbstractSkill | `bf6b982` (2026-11-08 16:22), version 0.3.11 | the `abstractcore` skill bundled beside `abstractframework-gateway` (verbatim from AbstractCore `cac85276`, first-party record, registry 2026.11.10, 17 skills); the prompt names each skill's `<path>` and says to read that SKILL.md, never to search the workspace for a copy |
| AbstractRuntime | `08ebf18` (2026-11-09 13:29) | security, review 2026-11-09 finding 1 (BLOCKER, live since 2026-11-08 16:32: any client could read any file under a folder holding a SKILL.md by forging run variables): the interception serves a folder only under a skill root the HOST registered (`register_skill_roots` / `registered_skill_roots` / `clear_skill_roots`), for a name the run selected; nothing registered means nothing served (fail closed) |
| AbstractGateway | `134b90a4` (2026-11-09 13:38) | the gateway half of the same finding: it registers its own roots at service build (curated shelf, `<data>/skills/registry/skills`, `<data>/skills/imported`) and drops a client's `_runtime.skills_block`, `_runtime.skills_resolution` and skills roots at `/runs/start`, `/runs/schedule` and every host start |
| AbstractSkill | `9bb1f38` (2026-11-09 19:52) | test only: the shelf test pins spec v25's "never refused" wording (cross-repo drift found by the hermetic run) |

### Tests and validation

- `b22c901`: 7 tests, red without the change. `08ebf18`: 3 tests red on the previous implementation. `134b90a4`:
  5 tests red on the previous source; the reviewer's forged-variable probe through `/runs/start` now gets the normal
  policy answer and the secret is not served, while a legitimately activated skill still reads whole.
- AbstractSkill `tests/test_bundled.py:78` (both skills are bundled) and `:412` (seeding a shelf that already has the
  gateway skill adds `abstractcore` and overwrites nothing).
- The blocker was found by the adversarial review `untracked/release-2026-11-07/review-debt/REVIEW-1.md` and fixed the
  same day (running log `untracked/release-2026-11-07/RESUME.md`, 2026-11-09 14:00 and 15:20).
- Hermetic suites at every HEAD, 2026-11-09 19:10–19:46 (`untracked/release-2026-11-07/audit-fable/VERIFY.md`): skill
  225 passed / 1 failed (the wording drift, fixed by `9bb1f38`); none of the runtime or gateway failures is in this
  item's files.
- Live: restart #3 (2026-11-08 16:33) seeded `abstractcore` into the live shelf; the security fix has been live since
  the 2026-11-09 afternoon restarts (`ROADMAP-2026-11-09-2010.md` section D: "Closed, Live").

### Acceptance

- [x] With a `.abstractignore` that refuses the shelf path, `read_file` on an activated skill's SKILL.md returns the
      whole file (runtime tests; since `08ebf18` only under a host-registered root).
- [x] The prompt carries the path for every offered skill (AbstractSkill `bf6b982`).
- [x] A fresh data dir has `abstractcore` and `abstractframework-gateway`: by test (the seeding tests above) and by the
      live shelf after restart #3. No screen check on a truly fresh install is recorded.
- [ ] Released: abstractskill 0.3.11, AbstractRuntime 0.19.0, AbstractGateway 0.21.0 (root 1179).

### Residual follow-ups

- The bundled `entity-self-knowledge` skill never mentions the v25 `idle` state (0 hits in
  `abstractskill/src/abstractskill/registry/skills/entity-self-knowledge/SKILL.md`, checked 2026-11-10): re-read it
  before 0.3.11 is cut (about 30 min; `ROADMAP-2026-11-09-2010.md` section D). Recorded in 1179's refresh.
- The earlier follow-up "`resolve_run_skills` records `resolution["shelf"]` as a second root source" is probably
  stale: since `08ebf18` the roots are the ones the host registers, never the run record's. Check before building it.
- Only `read_file` is intercepted (not list or search), by design.
- ADR state: none written. The rule "an activated skill is always reachable by the agents" is an operator ruling
  recorded in this item; promote it to an ADR only if a second host implements skills.
