# Proposed: Observer wait handling via session replay and chat handoff

## Metadata
- Created: 2026-06-06
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: None identified after review
- ADR impact: May need a new ADR if Observer becomes an owner of durable chat replay, cross-device session handoff, or interactive wait resumption policy.

## Context
Observer currently exposes waiting runs through an operational modal that tries to explain why a run is blocked and offers submit/cancel actions. User testing showed this is not enough. For waits that originate from a dialogue or agent conversation, the user does not only need a form field; they need to reconnect to the conversation, replay the session context, and answer in the same mental model as AbstractCode Web or the Observe Chat tab.

## Current code reality
- `abstractobserver/src/ui/app.tsx` has an Observe Chat surface backed by `ChatThread`, local `chat_messages`, and save/export actions for a selected run.
- The wait modal renders inferred wait context, recent session turns, full run input JSON, recent workflow steps, and submit/cancel actions.
- `abstractobserver/src/lib/gateway_client.ts` exposes `get_run_history_bundle(...)`, and `abstractobserver/src/ui/app.tsx` calls it for selected runs with `include_subruns` and ledger tail options.
- Wait context is still modal-driven and action-driven, not a replayable chat surface.
- The current modal may infer a closest prior user request from run input when Runtime did not attach an explicit question. That inference is useful as a diagnostic but is not a reliable substitute for session replay.

## Problem or opportunity
Answering a wait without the surrounding conversation is risky and often confusing. The right product may be a chat/replay handoff: open the session, show the turns that led to the wait, show the pending request in context, and submit a response through the wait resume path only when the user clearly chooses to answer that pending wait.

## Proposed direction
Investigate a first-class "resume through replay" flow:
- Define whether Observer should answer waits at all, or whether it should deep-link to a reusable chat/session surface.
- Audit AbstractCode Web replay capabilities and identify the existing session replay contract, if any.
- Model a pending wait as part of a session timeline, not only as a run action.
- Reuse shared chat components where possible, including markdown/JSON rendering and saved transcript behavior.
- Keep cancel/stop available as an operational action, but separate it from chat response composition.
- Require the UI to show the exact wait target, session turns, run/turn/node provenance, and the consequences of submitting a response.

## Why it might matter
Observer is becoming the place users go when runtime work is stuck. If it cannot reconstruct the discussion that caused a wait, users may submit wrong answers, cancel useful runs, or distrust the monitor.

## Promotion criteria
- AbstractCode Web or another app has a documented replay/session contract that Observer can reuse, or Gateway/Runtime can expose one cleanly.
- UX review agrees on whether the wait action belongs inside Observer, Observe Chat, AbstractCode Web, or a shared chat shell.
- Runtime/Gateway can expose enough session-turn provenance to answer without guessing from raw run input.
- Security/redaction requirements are known for cross-device replay and wait resume.

## Validation ideas
- Reproduce a waiting dialogue run and verify the proposed surface shows the full preceding conversation, not only run input JSON.
- Verify submit resumes only the intended wait key and preserves ledger evidence.
- Verify cancel stops the whole workflow and is visually distinct from replying.
- Test on a run with subworkflows, a tool approval wait, and a plain user-response wait.

## Non-goals
- Do not implement the replay chat or change current wait submit semantics in this proposal.
- Do not make Observer the durable chat storage authority without an ADR-level ownership decision.
- Do not hide ledger/raw diagnostics; they remain necessary for expert debugging.

## Guidance for future agents
Start by comparing Observer Chat, AbstractCode Web replay, Gateway `history_bundle`, and Runtime session metadata. If replay already exists, prefer a shared contract and component over inventing an Observer-only chat path.
