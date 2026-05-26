# Agent Skills (SKILL.md) — Proposal

This guide captures a **planned** integration of the Agent Skills (`SKILL.md`) format into AbstractFramework.
Nothing in this document implies the feature is already shipped; it records a design direction so the knowledge
is not lost.

## What are “Agent Skills”?

In the Agent Skills ecosystem, a **skill** is a shareable folder with a required `SKILL.md` (YAML frontmatter +
instructions) plus optional `scripts/`, `references/`, and `assets/`. Skills are designed for **progressive disclosure**:
systems load only `name`/`description` for discovery and fetch the full content only when a skill is activated.

Spec constraints worth carrying into AbstractFramework:
- `name` is constrained (lowercase alphanumeric + hyphens, 1–64 chars) and must match the skill’s leaf directory name.
- `allowed-tools` is **experimental** and is a space-delimited list of “pre-approved” tools in the originating ecosystem.

## Skills vs flows (what each is “for”)

- **Flows** (`.flow` bundles / VisualFlow) are **executable programs** in AbstractFramework:
  durable execution, explicit waits, tool boundaries, replayable ledger history.
- **Skills** (`SKILL.md`) are **portable procedure packs**:
  prompt/instructions + optional scripts/resources, designed to be shared across agents/ecosystems.

### Are flows “more advanced” than skills?

They’re “more advanced” in different dimensions:

- **Execution**: flows are more advanced (they *run* as durable state machines).
- **Portability**: skills are more advanced (they’re a widely adopted, tool-agnostic packaging standard).

### Can every skill be modeled as a flow?

**Conceptually yes**: a skill is “a procedure + resources”, and a flow can orchestrate any procedure.
In practice, the limit is **tooling/environment assumptions**, not the flow model:
a skill may assume Playwright is installed, or a specific “container” tool surface exists.

Also, not every skill is *worth* turning into a dedicated flow:
“guidelines/checklists/style” skills often work best as **prompt modules** attached to a generic agent flow.

## Proposed interaction model (v0)

The key design choice is: **flows run; skills are activated/loaded** (and skill scripts only run as explicit tools).

### 1) Run-attached skills (primary)

- Clients/hosts attach an `available_skills` metadata set to a run (name/description only).
- Users explicitly activate a skill (e.g. `/skill <name>`), which loads full `SKILL.md` and any resources.
- Activation is logged durably (ledger record). For replay/resume safety, activation should snapshot skill content
  (or at least record a content hash) so a long-running run doesn’t silently pick up a modified skill file.

### 2) Bundle-declared skill dependencies (secondary)

Flows may declare skill dependencies without changing the `.flow` format by using `manifest.metadata`, for example:

- `skills.required`: skills that must be present on the host/gateway
- `skills.defaults`: skills to auto-activate at run start

This lets organizations ship a workflow that says “this workflow expects these skills”, while keeping skills
as separately managed artifacts.

### 3) Bundle-embedded skills (optional; later)

WorkflowBundles support `assets/*`. If we want hermetic distribution (“workflow + skills in one file”),
we can embed skills under bundle assets (e.g. `assets/skills/<id>/...`) and expose them via the gateway.

## Implementation notes (what fits best with existing runtime/flow mechanics)

The lowest-friction implementation in AbstractFramework is to add skills as **runtime-owned tools** in the
AbstractRuntime ↔ AbstractCore integration (the same pattern already used for `open_attachment`):

- `list_skills()` for metadata-only discovery (progressive disclosure).
- `open_skill(...)` to load full `SKILL.md` (and optionally specific resources), snapshotting large payloads as artifacts
  and recording a content hash.
- optional `activate_skill(...)` to update durable run state (`_runtime.skills.active`) and apply `allowed-tools` as a
  restriction (intersection with the run’s tool allowlist).

Because these are tools, **flows can compose over skills immediately** using existing Tool/CallTool nodes, and agent
loops can activate skills without introducing new effect types.

Note: bundle-declared dependencies via `manifest.metadata.skills.*` are supported as a pattern, but VisualFlow JSON
currently has no `metadata` field; making this authorable requires a UI/CLI surface (or a schema extension).

## Safety and tool gating

- Skills may include scripts. **Scripts must never run implicitly** “because a skill exists”.
- Skills may declare `allowed-tools` (ecosystem field; experimental). In AbstractFramework the safe behavior is:
  - treat it as a **restriction** when it can be mapped to AbstractFramework tool names (intersection with the run’s tool allowlist),
  - if it cannot be mapped (unknown grammar/tool ids), emit `#FALLBACK` and **do not relax** the run’s tool policy,
  - deny and log out-of-policy tool calls with actionable `#FALLBACK` warnings,
  - keep run state JSON-safe (store bodies/resources as artifacts when large).

## Where this fits (packages)

- `abstractagent`: prompt injection of metadata; “activate skill” as an explicit step; optional schema-only built-in
  (e.g. `open_skill`) so the runtime/host performs the read.
- `abstractruntime`: runtime-owned “skill read/activate” handler that is durable + ledger-recorded + artifact-backed,
  plus enforcement hooks for `allowed-tools`.
- `abstractgateway`: optional “skills registry” (list/fetch/install/deprecate), parallel to `.flow` bundle distribution.
- `abstractcore`: stays lean; any provider-specific “container skills” integration remains optional and gated.

## References and next steps

- Backlog item: `docs/backlog/planned/074_agent_skills_integration.md`
- Implementation plan (phased): `docs/backlog/planned/074_agent_skills_integration_plan.md`
- Research notes (spec + ecosystem scan): `docs/skills/`
