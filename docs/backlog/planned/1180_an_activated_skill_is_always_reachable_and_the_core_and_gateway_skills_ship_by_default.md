# 1180 — An activated skill is always reachable by the agents; the abstractcore and abstractgateway skills are registered on every fresh install

> Package: AbstractRuntime (the `read_file` interception in `integrations/abstractcore/effect_handlers.py`; the skills prompt text), AbstractSkill (bundled registry gains `abstractcore`; 0.3.11), AbstractGateway (no code: the shelf seed already registers bundled skills at start)
> Type: defect + default
> Status: planned — THIS release (operator 2026-11-08 16:01: "a new bug to fix within this release")
> Created: 2026-11-08
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
