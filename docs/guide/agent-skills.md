# Agent Skills (SKILL.md)

A **skill** is a shareable folder with a required `SKILL.md` (YAML frontmatter plus instructions)
and optional `scripts/`, `references/` and `assets/`, following the
[Agent Skills](https://agentskills.io/) format. Skills are built for **progressive disclosure**: an
agent first sees only each skill's `name` and `description`, and reads the full instructions when a
task calls for them.

In AbstractFramework, skills are served by the gateway and used by agent runs. This guide explains
how they fit with workflows and where to find each piece. The user-facing steps (which shelf is
used, how to attach skills to a run) are in [Agent sessions: skills](../agent-sessions.md#skills).

## Skills and flows

- **Flows** (`.flow` bundles / VisualFlow) are executable programs: durable execution, explicit
  waits, tool boundaries, replayable ledger history.
- **Skills** are portable procedure packs: instructions plus optional resources, shareable across
  agents and ecosystems.

Flows run; skills are read. A skill never executes by being present: its instructions reach an
agent as text, and anything it asks the agent to do still goes through the run's tools and
approvals.

Not every procedure deserves a dedicated flow. Guidelines, checklists and style rules usually work
best as skills attached to a general agent workflow; multi-step procedures with waits and
approvals are better authored as flows.

## Where skills come from

- **AbstractSkill** (`pip install abstractskill`) is the shared library: it parses and validates
  `SKILL.md`, discovers skills on disk, computes stable content hashes, formats the compact skill
  index an agent sees, and applies the trust gate. Its wheel also carries a **curated shelf** of
  reviewed skills with their trust records.
- **AbstractGateway** installs AbstractSkill with itself and serves a shelf: by default its own copy
  of the curated shelf in `<data dir>/skills/registry`, refreshed at each start without overwriting
  files you edited; or the folder its `skills.shelf` setting names.

## Trust

Trust records bind to content hashes, not to paths:

- **validated** skills (their content matches a trust record) can be attached to runs;
- **unverified** skills (unknown, or edited since they were validated) are held;
- skills under a **do-not-use advisory** never reach a run.

A skill's own tool declarations can only narrow what the run's tool policy allows, never widen it.

## Using skills in a run

A client attaches skills by name (`input_data.skills` on `POST /api/gateway/runs/start`; the
skills settings in AbstractCode). The gateway passes the names through the trust gate, gives the
run a stable index of the active skills and a `read_skill` tool to open one, and records every
decision on the run, including skills it held or refused. Sub-agents started by the run inherit the
same skills.

## Reference

- [AbstractSkill](https://github.com/lpalbou/AbstractSkill): library API, the curated shelf, the
  trust model and the seeding rules.
- [AbstractGateway configuration: skills shelf](https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md#skills-shelf)
  and [API: run-level skills selection](https://github.com/lpalbou/AbstractGateway/blob/main/docs/api.md#run-level-skills-selection).
- [Workflow bundles](workflow-bundles.md): how flows are packaged and distributed.
