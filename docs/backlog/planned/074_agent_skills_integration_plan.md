# Agent Skills integration plan (phased) — AbstractFramework

Supplement to: `docs/backlog/planned/074_agent_skills_integration.md`

## Scope and goal

Integrate the **Agent Skills** (SKILL.md) format into AbstractFramework so that:

- skills are **discoverable** (local + gateway-first),
- skills are **loaded progressively** (metadata first; full content on activation),
- skill usage is **durable + observable** (ledger-recorded, replay-first),
- skill scripts are **safe by default** (explicit approvals, sandboxed execution, no silent fallbacks),
- the integration stays **modular** (does not bloat `abstractcore` or break layering).

This plan focuses on the core packages and contracts:
`abstractcore`, `abstractruntime`, `abstractagent`, `abstractgateway`, plus optional `abstractmemory`/`abstractsemantics`.

## What we learned (clarifications from the spec/ecosystem)

- The Agent Skills spec requires `SKILL.md` with YAML frontmatter including at least `name` + `description`.
- The spec constrains `name` (1–64 chars, lowercase alnum + hyphens) and requires it to match the skill’s directory name.
- The spec also defines optional fields (notably `license`, `compatibility`, `metadata`) and an **experimental** `allowed-tools` field.
- Skills support two primary integration shapes:
  - **Filesystem-based** (local): the agent reads skill folders from disk.
  - **Tool-based** (remote): the agent requests skill content via a tool/API.
- The ecosystem often packages skills as a zipped **`.skill` file** (convention used by Anthropic tooling), even though the base spec is folder-oriented.
- Claude Code adds extra features (slash commands, hooks, subagents) that are useful but **not** required to get value in AbstractFramework.

## Non-negotiable constraints (AbstractFramework architecture)

These come from the implemented contracts in `abstractruntime` + `abstractgateway`:

- **Durable state is JSON-safe** (`RunState.vars`); large content must be artifact-backed.
- **Replay-first**: the ledger is source-of-truth; streaming is an optimization.
- **Tool boundary**: tool schemas may cross boundaries; tool callables do not. Side effects must remain host-executed.
- **No silent fallbacks**: degraded paths must emit actionable `#FALLBACK` warnings; any truncation must be labeled `#TRUNCATION`.

## Skills vs flows (comparison + recommendation)

**Which is “more advanced”?**
- **Flows are more advanced as an execution model** inside AbstractFramework: they are durable, replayable programs (a persisted state machine) with explicit waits, tool boundaries, and ledger visibility.
- **Skills are more advanced as a portability/distribution format** across agent ecosystems: they are a lightweight, tool-agnostic packaging of procedures, prompts, scripts, and references.

**Can every skill be modeled as a flow?**
- **Conceptually: yes.** A skill is “a procedure + resources”; a flow is “a durable procedure.” If the host has the needed tools, a flow can orchestrate the same steps (including loops, approvals, and evidence capture).
- **Practically: the limiting factor is tool availability and environment assumptions**, not the flow model. Many ecosystem skills implicitly assume a specific toolset (Claude container tools, Playwright installed, doc tooling present, etc.). AbstractFramework can model the workflow, but it must also supply or map the required tools.
- **Some skills are not worth turning into flows**: “guidelines/checklists/style” skills are better as *optional prompt modules* that a generic agent flow can load, rather than as their own executable workflows.

### Recommended interaction model (v0)

Treat skills as **data modules** that can be attached to runs and optionally referenced by workflows.
In AbstractFramework terms: **flows run; skills are activated/loaded** (and skill scripts only execute as explicit tools).

1) **Run-attached skills (primary)**
   - A client/host (AbstractCode / AbstractAssistant / thin client via gateway) attaches `available_skills` metadata to the run and activates skills explicitly.
   - The agent workflow remains a normal `abstractcode.agent.v1` flow (or AbstractAgent pattern) that knows how to load/activate skills via a runtime-owned handler.

2) **Bundle-declared skill dependencies (secondary)**
   - A `.flow` bundle may declare skill dependencies in `manifest.metadata` (no format change required).
   - Example shape:
     - `skills.required`: list of `{id, version?}` that must be present
     - `skills.defaults`: list of `{id, version?}` to auto-activate at run start
   - This keeps workflows small and allows organizations to standardize “this workflow expects these skills”.

3) **Bundle-embedded skills (optional; later)**
   - WorkflowBundles already support `assets/*` in the format, but the current packer does not populate `manifest.assets`.
   - If we want hermetic distribution (“workflow + its skills in one file”), we can extend pack/unpack tooling to include `skills/<id>/SKILL.md` and resources as bundle assets, and expose them through the gateway like other bundle bytes.

### Implementation reality check (what fits best with existing code)

AbstractRuntime’s AbstractCore integration already supports **runtime-owned tools** via the `TOOL_CALLS` effect handler
(example: `open_attachment`). This is the best “lowest-friction” way to integrate skills without introducing new effect
types or special-casing flows:

- Add runtime-owned tool specs (no host callable) like:
  - `list_skills()` → returns metadata-only list (progressive disclosure)
  - `open_skill(skill_id, version?, resource_path?)` → returns full `SKILL.md` (and optionally a specific resource),
    snapshotting content into `ArtifactStore` (recording a content hash) and returning artifact refs for replay safety
  - optional `activate_skill(skill_id, ...)` → updates `_runtime.skills.active` and applies `allowed-tools` as a
    restriction (intersection with the run’s allowed tool policy)
- Execute these inside the existing `TOOL_CALLS` handler (same pattern as `open_attachment`), so:
  - activation/read events are ledger-recorded like any other effect
  - runs remain JSON-safe (bodies/resources artifact-backed when large)
  - flows can compose over skills naturally using existing Tool/CallTool nodes (no new VisualFlow node type required)

**Important edge case (passthrough/untrusted tool execution):**
runtime-owned tools cannot be interleaved with delegated tool execution. The existing `open_attachment` logic already
detects delegating executors and falls back to a durable WAIT that the host must resume; the skills tools should follow
the same contract.

## Proposed component map (where code should live)

### A) New small library: `abstractskills` (recommended)

Create a tiny, dependency-light package (like `abstractsemantics`) to avoid sprinkling parsers across clients:

- **Parsing**
  - Parse `SKILL.md` frontmatter + body.
  - Provide a stable `SkillProperties` model (name/description/license/compatibility/metadata/allowed_tools).
- **Validation**
  - Validate required files and basic folder layout.
  - Provide deterministic “available skills” prompt text (prefer spec-style `<available_skills>...</available_skills>`).
- **Packaging**
  - `pack_skill_dir(...) -> .skill` zip (convention)
  - `unpack_skill_zip(...) -> dir`
- **Loaders**
  - `FilesystemSkillLoader` (project + user scopes; precedence rules)
  - `RemoteSkillLoader` (fetch by id/version from a gateway API)

Why a separate package:
- Keeps `abstractcore`/`abstractruntime` lean.
- Lets UIs/hosts (AbstractCode, AbstractAssistant, web) share identical semantics.

### B) `abstractagent` (agent patterns)

Add a **skill-aware prompt builder** while keeping “logic stays runtime-agnostic”:

- Extend adapters to optionally inject *only* a compact “available skills” metadata block into the system prompt.
- Support “activation” as an explicit step (user-invoked first; model-invoked later).
- If we add a model-invoked path, define a **schema-only built-in tool** (e.g., `open_skill`) so the runtime/host executes the read and logs it.

### C) `abstractruntime` (durable execution + ledger)

Add a runtime-owned integration point so skill loading/activation is durable and observable:

- Provide a runtime-owned tool/effect handler for reading skill content by `(skill_id, version, path?)` that:
  - stores full SKILL.md content as an artifact (or returns it if small),
  - appends a ledger record for “skill activated/read”,
  - enforces limits (max bytes, max refs) and emits `#FALLBACK`/`#TRUNCATION` as needed.
- Add a small policy hook that merges a skill’s `allowed-tools` into `_runtime.allowed_tools` (intersection, not union) when present.

### D) `abstractgateway` (distribution + multi-client)

Add a **skills registry** parallel to the existing WorkflowBundles (`.flow`) registry:

- Storage: `<data_dir>/skills/` (folders and/or `.skill` zips), with a small index file.
- API:
  - list skills (metadata-only)
  - fetch skill content/resources on demand
  - install/update/deprecate skills (admin endpoints; auth-protected)
- Thin-client support: include skills metadata in discovery endpoints so UIs can show “available skills” without fetching full bodies.

### E) Optional: `abstractmemory` + `abstractsemantics`

Later, add “skills search” and governance:

- Store skill metadata + embeddings in AbstractMemory for semantic lookup and recommendations.
- Use AbstractSemantics to standardize skill categories/tags if you want “approved skill taxonomy”.

## Phased delivery plan

### Phase 0 — ADR + minimal core utilities (1–2 weeks)

Deliverables:
- ADR: “Agent Skills integration in AbstractFramework”
  - define goals/non-goals, security posture, default discovery paths, and what “activation” means.
- New package `abstractskills` (or a minimal module under `abstractcore` if you want fewer repos)
  - parse SKILL.md, expose `SkillProperties`, validate folder, compile metadata prompt block.
- Unit tests for parsing/validation (no runtime/gateway changes yet).

Decisions to lock:
- Skill identity:
  - spec-level identity is the skill `name` (must match the leaf directory name)
  - AbstractFramework may optionally add an external namespace/source dimension (e.g., multiple skill roots or gateway registry) to avoid collisions
- Skills ↔ flows contract:
  - run-attached skills are the primary mechanism
  - `.flow` bundles may declare dependencies in `manifest.metadata`
  - bundle-embedded skills (assets) is optional and can be deferred
- Default skill search paths:
  - user: `~/.abstractframework/skills/`
  - project: `.abstractframework/skills/`
  - plus an explicit CLI override list

### Phase 1 — Local skills in host apps (metadata + user-invoked activation) (1–2 weeks)

Target: AbstractCode + AbstractAssistant (local-host mode).

Deliverables:
- “Skills discovery” in the host process:
  - scan default paths; load only properties (`name`/`description`/optional metadata).
  - show skills in `/help` or a dedicated command (`/skills`).
- User-invoked activation:
  - `/skill <name>` loads full SKILL.md and injects it (or a summarized form) into the next agent cycle.
  - activation is **explicit** (no model-invoked loading yet).

Guardrails:
- Hard cap on metadata per skill + total skills injected.
- No `scripts/` execution in this phase; if present, display “requires enablement” with `#FALLBACK`.

### Phase 2 — Durable activation + ledger logging + allowed-tools gating (2–3 weeks)

Target: AbstractRuntime + AbstractAgent integration.

Deliverables:
- Runtime-owned “skill activation/read” handler:
  - artifacts for skill bodies/resources
  - ledger record for activation and any resource reads
- Tool gating:
  - if a skill provides `allowed-tools`, enforce it at the runtime tool executor boundary
  - log any denied tool calls with `#FALLBACK` and actionable instruction

Why now:
- This is where skills become “first-class and auditable” rather than a prompt trick.

### Phase 3 — Gateway skills registry (distribution + thin-client UX) (3–5 weeks)

Target: AbstractGateway + web/thin clients.

Deliverables:
- Gateway skills registry:
  - scan `<flows_dir>/`-adjacent `skills/` OR a new `ABSTRACTGATEWAY_SKILLS_DIR`
  - install/update via `.skill` zip upload (admin-only)
  - deprecate/disable skills without deleting (keeps historical replay intact)
- APIs:
  - `GET /api/gateway/skills` (metadata)
  - `GET /api/gateway/skills/{id}` (skill body + index of resources)
  - `GET /api/gateway/skills/{id}/resources/{path}` (resource bytes)
- Thin clients:
  - show available skills list; allow activation by sending a durable command that updates run vars (or triggers a runtime effect).

### Phase 4 — Script execution (safe-by-default) (3–6 weeks)

Target: host tool execution + approvals + evidence.

Deliverables:
- Define a safe contract for skill scripts:
  - scripts run only via explicit tools (never “implicitly because a skill exists”)
  - require allowlisted tool names + explicit approvals (and/or a sandbox)
  - capture evidence/artifacts for outputs
- Provide a “skill tool adapter”:
  - map skill scripts to runtime tools (e.g., `skill.<skill_id>.<script_name>`) with stable schemas.

### Phase 5 — Advanced features + ecosystem compatibility (ongoing)

Optional enhancements once core value is proven:
- Claude Code extensions support (selectively):
  - `user-invocable`, `disable-model-invocation`, `argument-hint`
  - `context: fork` (maps well to runtime subworkflows)
  - hooks (pre/post) as explicit, durable nodes/effects
- Skill search:
  - index skill metadata in AbstractMemory; add a “recommend skills” tool.
- Provider-specific integration:
  - Optional AbstractCore integration for Anthropic “container skills” (behind an extra and explicit config).

## Open questions (resolve in Phase 0 ADR)

- Skill id/version semantics: do we require semantic versions, or use content hashes?
- Where does “active skills” live in the durable model: `context`, `scratchpad`, or `_runtime`?
- Do we ever want a first-class `manifest.skills` field (instead of `manifest.metadata.skills`) for bundle-declared dependencies?
- Authoring UX for bundle-declared dependencies:
  - VisualFlow JSON currently has no `metadata` field; the gateway publish path auto-generates manifest metadata.
  - If we want authors to declare skill dependencies via manifests, we must add an authoring surface (CLI metadata,
    Flow Editor fields, or extend VisualFlow schema to carry an optional metadata object).
- Multi-tenant gateway policy:
  - who can install skills, who can activate, and how to audit skill usage?
