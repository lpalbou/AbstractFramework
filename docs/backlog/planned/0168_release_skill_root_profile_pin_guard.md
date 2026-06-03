# Planned: Abstract release root profile pin guard

## Metadata
- Created: 2026-05-31
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: None

## Context
After a partial Gateway release, root `abstractframework` still pinned `abstractgateway==0.2.23` while PyPI had `abstractgateway==0.2.25`. Docs also retained legacy browser-token examples.

## Current code reality
- The `abstract-release` skill already says root releases happen last and pins must agree before root publish.
- It does not explicitly force partial release handoff when a lower package is published but root is not released in the same wave.
- Root install manifest and `abstractframework.RELEASE_VERSIONS` depend on root pins.

## Problem
Partial package releases can leave the public meta-package and install docs behind even when individual package releases succeed.

## What we want to do
Update the release orchestration skill so every partial release records root/meta-package pin state and either updates/releases the root profile or leaves an explicit backlog/docs follow-up.

## Why
Users install `abstractframework[...]`, not just individual packages. A successful lower package release is incomplete if the profile still points users at stale code.

## Requirements
- Add a hard gate for partial release follow-through.
- Require root profile dry-run or install-manifest verification after lower package visibility.
- Require docs/LLM index drift audit for browser auth and install commands when Gateway/Flow auth changes.

## Suggested implementation
Patch the `abstract-release` skill instructions and validate the skill with `quick_validate.py`.

## Scope
Local Codex skill instructions, not framework package code.

## Non-goals
- Do not change the release scripts unless the instruction patch proves insufficient.

## Expected outcomes
- Future release waves surface root pin drift before reporting that users can install the latest framework.
- Partial release reports must say exactly which root/profile/docs work remains.

## Validation
- Skill validation passes.
- The new instruction is concise and trigger-relevant.

## Progress checklist
- [x] Patch `abstract-release` skill.
- [x] Validate skill metadata.
- [x] Update this backlog item with the result.

## Guidance for the implementing agent
Keep the skill concise. Add only the release guard that would have prevented this drift.
