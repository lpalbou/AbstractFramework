# Claude Shareable Skills Overview (Agent Skills) — Feb 2026

## What “Skills” Means Here
This report covers **shareable Agent Skills**: portable, model-agnostic skill packs
defined by the **Agent Skills open standard** and used in Claude (Claude.ai, Claude Code,
and Claude API). These are *not* intrinsic model capabilities; they are **files and folders**
that specialize an agent’s behavior.

Primary definitions:
- Agent Skills are “folders of instructions, scripts, and resources” that agents can discover
  and use to perform tasks more accurately and efficiently.  
  Source: https://agentskills.io/what-are-skills.md
- Anthropic’s skills repository is an implementation of this standard for Claude.  
  Source: https://raw.githubusercontent.com/anthropics/skills/main/README.md

## Core Structure (How Skills Are Packaged)
An Agent Skill is a directory with a required `SKILL.md` and optional resources:
```
my-skill/
├── SKILL.md        # required: YAML frontmatter + instructions
├── scripts/        # optional: executable code
├── references/     # optional: on-demand docs
└── assets/         # optional: templates/resources
```
Sources:
- https://agentskills.io/what-are-skills.md
- https://agentskills.io/specification.md

### SKILL.md Format
`SKILL.md` includes:
- YAML frontmatter (required): `name`, `description`
- Markdown body: instructions and workflow details  
Source: https://agentskills.io/specification.md

## How Skills Work (High-Level)
Agent Skills use **progressive disclosure**:
1. **Discovery**: Only `name` and `description` are loaded at startup.
2. **Activation**: Full `SKILL.md` is loaded when relevant.
3. **Execution**: Optional scripts/resources are accessed as needed.  
Sources:
- https://agentskills.io/what-are-skills.md
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

This keeps context small while enabling rich, on-demand specialization.

## How Skills Are Used In Claude Code
Claude Code implements the Agent Skills standard and extends it with:
- **Slash commands**: `/skill-name` invokes a skill directly.
- **Invocation control**: `disable-model-invocation` and `user-invocable` frontmatter.
- **Allowed tools**: `allowed-tools` to restrict or pre-approve tool use.
- **Subagents**: `context: fork` to run a skill in a dedicated subagent.
- **Dynamic context injection**: `!` command execution inside skill content.  
Source: https://code.claude.com/docs/en/skills

### Skill Locations In Claude Code
Claude Code loads skills from specific directories:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`
- Enterprise-managed settings
- Plugins (skill packs in plugin directories)  
Source: https://code.claude.com/docs/en/skills

## How Skills Are Used In Claude API
The Claude API supports skills as **containers** combined with **code execution**:
- Skills are attached in the `container.skills` parameter.
- Types: `anthropic` (pre-built) or `custom` (uploaded).
- Versions can be pinned or set to `latest`.
- Requires beta headers and the code execution tool.  
Source: https://docs.claude.com/en/api/skills-guide

## How Skills Are Shared
Skills are shareable because they are just folders/files:
- **GitHub repos** and **plugin marketplaces** for discovery.
- **Version control** for team sharing (commit `.claude/skills/`).
- **Claude API Skills** allow uploading custom skills.  
Sources:
- https://raw.githubusercontent.com/anthropics/skills/main/README.md
- https://code.claude.com/docs/en/skills
- https://docs.claude.com/en/api/skills-guide

## Key Takeaways
- Skills are portable, model-agnostic, and *not tied to Claude only*.
- They enable **specialization** by bundling procedural knowledge and scripts.
- Claude Code and Claude API provide first‑party implementations and distribution paths.

