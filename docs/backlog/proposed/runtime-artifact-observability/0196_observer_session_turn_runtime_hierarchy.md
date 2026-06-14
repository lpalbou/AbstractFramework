# Proposed: Observer session-turn-runtime hierarchy

## Metadata
- Created: 2026-06-06
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0036 for artifact descriptors; no direct governing ADR identified for session hierarchy
- ADR impact: May need a new ADR if a canonical cross-package session/turn/run hierarchy is established.

## Context
Runtime Activity now surfaces queues, runs, actions, and selected-run context. User testing still showed a missing concept: sessions are not explicit enough, turns are not unfolded, and runs appear as isolated operational rows even when they belong to the same conversation or multi-turn workflow.

## Current code reality
- `abstractobserver/src/ui/app.tsx` shows Runtime Activity queues and a run table with run/session metadata, selected-run details, actions, artifacts, ledgers, and logs.
- The artifact explorer can group by `turn`, `run`, `workflow`, and `source`, but Runtime Activity does not present a durable Session -> Turn -> Run hierarchy.
- Selected-run context can show a session id and loaded artifacts, but it does not unfold all turns in that session or explain which runs/subruns each turn produced.
- Gateway and Runtime expose run ledgers and artifact descriptors with `session_id`, `turn_id`, `run_id`, `workflow_id`, and `node_id` when available, but the UI does not yet treat them as a navigable tree.

## Problem or opportunity
Users need to answer questions such as "what session is this?", "which turn created this run?", "which subruns and artifacts came from that turn?", and "what files/logs were created by this conversation?" A flat run queue is useful for operations but weak for understanding ongoing conversations and their outputs.

## Proposed direction
Investigate a Runtime Activity navigation model with explicit hierarchy:
- Session list or rail with title, participants/origin, status rollup, active waits, last event, total runs, total turns, artifacts, provider calls, and token/cost summary when available.
- Expandable turns inside a session, each with user/assistant/request summary, started/finished times, runs/subruns, artifacts, provider traces, and waits.
- Runs and subruns nested under turns, preserving workflow/node status and operational actions.
- Artifact/log links scoped to session, turn, run, node, and provider call.
- Search/filter that can target sessions, turns, runs, statuses, artifact types, code artifacts, provider/model, time, and location.
- Fallback labels when older records lack canonical turn/session metadata.

## Why it might matter
Observer should let users supervise work at the level they think in: sessions and turns for conversations, runs and nodes for workflow execution, and artifacts/logs for evidence. Without that hierarchy, operational rows become hard to navigate at 100s or 1000s of runs.

## Promotion criteria
- Gateway/Runtime can provide exact session and turn indexes, or a bounded query strategy that does not require loading all runs.
- UX review validates a tree/table design that remains usable for many sessions and many runs.
- Technical review confirms how sessions, turns, subruns, artifacts, provider traces, and logs are linked without Observer-only inference.
- Acceptance criteria define what must be exact, what may be best-effort, and what legacy records look like.

## Validation ideas
- Use a dialogue session with several turns, a workflow session with subruns, and a media-generation session with artifacts.
- Verify expanding a session shows turns, and expanding a turn shows runs/subruns and generated artifacts.
- Verify counts remain exact or explicitly labeled bounded.
- Verify keyboard navigation and dense layout usability at large scale.

## Non-goals
- Do not implement the session tree in this proposal.
- Do not remove the run queue; operational supervision still needs a fast run-first view.
- Do not infer session turns solely from text snippets when canonical metadata is absent.

## Guidance for future agents
Start from Gateway/Runtime contract evidence, not UI wishful thinking. If exact session/turn indexes are missing, write the backend backlog first and keep Observer labels honest until the data is canonical.
