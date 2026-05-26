# AbstractFramework Backlog Overview

This root backlog is the framework-level planning ledger for cross-package work. Some older items
use legacy naming and duplicate numeric prefixes; new items should use four-digit global IDs and
the lifecycle folders described by the backlog process.

## Current Counts

- Planned: many legacy items plus active cross-package work.
- Proposed: legacy proposed items exist.
- Completed: historical completion ledger exists under `completed/`.
- Deprecated: not yet normalized at the root level.
- Recurrent: not yet normalized at the root level.

## Active Planned Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| - | - | - | No active root planned item added by the latest capability-defaults pass. |

## Recent Completed Work

| ID | Item | Completed | Notes |
|----|------|-----------|-------|
| 0140 | [Abstract Release Skill](completed/0140_abstract_release_skill.md) | 2026-05-24 | Added a read-only framework release orchestration skill with package discovery, release-wave planning, dependency-floor review, root profile pin drift checks, PyPI visibility gates, and approval/traceability guidance. |
| 0139 | [Unified Framework Capability Defaults](completed/0139_unified_framework_capability_defaults.md) | 2026-05-24 | Core-owned routing defaults for input/output/embedding/rerank, Gateway control-plane access, atomic provider/model resolution, catalog-backed Flow defaults UI, and qwen3.6 text default. |

## Operating Notes

- Use `docs/adr/` for durable architecture policy.
- Use this backlog for execution traceability, validation evidence, and follow-up state.
- New backlog item filenames should use `NNNN_<slug>.md`; date-prefixed legacy files should not be copied for new work.
