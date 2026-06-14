# Planned: Gateway recursion observability and runner coverage

## Metadata
- Created: 2026-06-05
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018 durable run gateway and remote host control plane, ADR-0032 package dependency boundaries and gateway-first apps
- ADR impact: May revise existing ADR if Gateway policy projection or catalog identity semantics change.

## Context
Gateway hosts durable runs, bundles, catalogs, ledger streams, and UI-facing run summaries. It should expose recursive-budget results and prove parents do not get stuck, but it should not become the layer that decides whether a recursive child may start.

## Current code reality
- `abstractgateway/src/abstractgateway/runner.py` ticks Runtime runs and repairs terminal subworkflow waits.
- Failed child subworkflows are currently summarized back to parents through runner logic, but recursive-limit failures need explicit regression coverage.
- Gateway bundle host code wraps start-subworkflow behavior for catalog/ACL policy. A recursion guard implemented outside Runtime could bypass or compete with this policy.
- Bundle publishing and host namespacing can qualify workflow ids, which matters for Runtime's canonical workflow identity.
- Flow run UI consumes Gateway history and ledger streams, so recursion-limit errors should be visible through existing run details rather than ad hoc UI-only logs.

## Problem
A runtime-denied recursive start could be hard to diagnose or could leave a parent in `WAITING/SUBWORKFLOW` if Gateway runner behavior is not tested. Bundle/catalog identity and ACL wrappers also need coverage so Runtime recursion checks do not accidentally misidentify workflows or bypass policy.

## What we want to do
Add Gateway-side policy projection, observability, and integration tests around Runtime recursive-budget enforcement. Keep Gateway as the control-plane and visibility layer, not the enforcement owner.

## Why
Users will experience recursive-limit failures through Gateway-hosted Flow runs. Operators need stable error details in ledgers/history. Platform maintainers need proof that Gateway restarts, bundle host wrappers, catalog ACLs, and parent wait repair all compose with Runtime enforcement.

## Requirements
- Do not enforce recursive subworkflow budgets in Gateway.
- Ensure Runtime's stable error code and details are preserved through ledger replay, SSE, history bundles, and run details.
- If Gateway exposes an effective recursion policy in APIs or run summaries, mark it as policy/projection and keep Runtime authoritative.
- Add tests proving denied recursive starts do not strand parents in `WAITING/SUBWORKFLOW`.
- Add tests for sync and async+wait child starts under Gateway runner.
- Add tests for bundle-qualified workflow identities and catalog namespacing.
- Add tests proving catalog/ACL wrappers still apply around allowed subworkflow starts.
- Ensure sanitized diagnostics do not leak cross-tenant private workflow ids or unauthorized bundle details.
- Document how Gateway admins can inspect or configure the default Runtime recursion cap if such config is exposed.

## Suggested implementation
1. Reuse Runtime's structured error details in Gateway history mapping and run detail views.
2. Add Gateway runner tests for recursive-limit failure in live tick and replay paths.
3. Add bundle host/catalog tests around canonical workflow id qualification.
4. Add a small API projection only if Flow needs it to display the effective default before a run starts.
5. Add docs or comments making Runtime the policy owner explicit.

## Scope
- AbstractGateway runner tests and any necessary history/summary mapping.
- Bundle/catalog host tests for namespaced workflow identity and ACL composition.
- Flow run-history compatibility only where Gateway event shape changes.
- Gateway docs for operator-facing policy projection if added.

## Non-goals
- Do not duplicate Runtime ancestry traversal in Gateway.
- Do not add Gateway-only recursion caps.
- Do not broaden this into generic resource quotas or fan-out limits.
- Do not expose sensitive workflow identities across tenant/catalog boundaries.

## Dependencies and related tasks
- `0182_runtime_recursive_subworkflow_budget.md`.
- `0186_recursion_contract_adr_docs_and_vocabulary.md`.
- Gateway control-plane ACL track items `0145` through `0153`.
- ADR-0018 and ADR-0032.

## Expected outcomes
- Gateway-hosted recursive-limit failures are visible, stable, and understandable.
- Parent runs never wait for a recursive child that was denied before creation.
- Bundle-qualified workflow ids work with Runtime recursion checks.
- Gateway catalog ACL wrappers continue to guard subworkflow starts.
- Flow's run modal can render recursive-limit failures from normal Gateway history.

## Validation
- Gateway integration test for direct recursive Subflow over the cap.
- Gateway integration test for mutual recursion over the cap.
- Gateway test for async+wait denial and parent terminal behavior.
- Gateway test for sync denial.
- Bundle/catalog test for namespaced workflow identity.
- ACL wrapper test proving unauthorized subworkflow start remains denied independently of recursion checks.
- History/SSE test proving error code and sanitized details are replayed.

## Progress checklist
- [ ] Confirm Runtime exposes stable recursive-limit error details.
- [ ] Add runner no-stuck-parent tests.
- [ ] Add bundle/canonical identity tests.
- [ ] Add catalog/ACL composition tests.
- [ ] Add history/SSE mapping coverage if needed.
- [ ] Document Gateway's non-owner role for enforcement.

## Guidance for the implementing agent
Treat Gateway as the place users and operators see the result, not the place that computes recursion. Verify behavior through durable history and restarted/replayed runs, because live-only tests miss the control-plane contract.
