# Proposed: User profile metadata for selective model grounding

## Metadata
- Created: 2026-05-30
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: May revise existing ADR

## Context
Gateway user auth now resolves a principal with `tenant_id`, `user_id`, roles,
scopes, token fingerprint, and `runtime_id`. The user record owns the
principal-to-runtime routing decision, but it does not yet store human profile
metadata that can help ground model behavior at query time.

The requested direction is to associate users with metadata such as first name,
last name, birth date, and country. Country may be inferred during interactions,
but inferred metadata must have provenance and review semantics. This metadata
should help ground AI responses when relevant, but it must not be injected into
every query by default.

## Current code reality
- `abstractgateway/src/abstractgateway/security/principal.py` defines
  `GatewayPrincipal` with identity/routing fields only.
- `abstractgateway/src/abstractgateway/users.py` stores Gateway users in a
  file-backed registry with token hashes, roles, scopes, enabled state, and
  `runtime_id`; it has no profile or inferred-facts fields.
- `abstractgateway/src/abstractgateway/routes/gateway.py` exposes `/me` and
  admin user CRUD, but no user profile CRUD or consent/audit controls.
- Runtime/Gateway LLM execution paths resolve provider/model/default context,
  memory, artifacts, and prompt-cache state, but there is no central
  user-profile context injection policy.
- AbstractMemory can store durable facts, but using it for profile grounding
  would need ownership, provenance, edit/delete, and query-time selection rules.

## Problem or opportunity
User metadata can improve personalization and reduce ambiguity. For example,
knowing the user's preferred name, age band, or country can help with tone,
legal/regulatory caveats, date formatting, and localization.

The same metadata is sensitive. Birth date, country, and inferred attributes can
create privacy, consent, correctness, and bias risks if injected silently into
every prompt or stored without user-visible provenance.

## What we might do
Introduce a user-profile layer attached to Gateway users and selectively
available to model execution:

- explicit profile fields: first name, last name, birth date, country;
- inferred fields: country or other location hints inferred from queries, with
  source, confidence, timestamp, and review status;
- user-visible profile read/update/delete routes;
- admin-visible profile controls with audit;
- query-time profile selection policy that injects only relevant, allowed
  profile facts into model context;
- clear separation between identity/routing metadata and model-grounding
  metadata.

## Why
This enables more grounded assistants without turning every query into a hidden
profile dump. It also creates a durable place to discuss and enforce privacy
rules before these facts affect model behavior.

## Requirements to decide before implementation
- Which fields are explicit user inputs versus inferred facts.
- Whether birth date is stored as full date, year, age band, or optional claim.
- How country inference is triggered, confirmed, corrected, expired, and
  deleted.
- Whether profile facts live in the Gateway user registry, a separate profile
  store, AbstractMemory, or Runtime context.
- Which query categories should receive profile context.
- How users inspect the exact profile facts that were injected into a run.
- How profile context is represented in ledgers/audit without leaking sensitive
  data to unrelated readers.
- How profile data follows or does not follow a user across runtimes, tenants,
  and shared/team memory.

## Scope
- AbstractGateway user profile storage and profile API design.
- AbstractRuntime/Gateway query-time context assembly policy.
- AbstractMemory integration only if it provides the right ownership and
  provenance semantics.
- Thin app UI for users to inspect, edit, and delete their profile metadata.
- Documentation for privacy, consent, and selective context injection.

## Non-goals
- Do not inject profile metadata into every prompt by default.
- Do not infer sensitive attributes silently without provenance.
- Do not use profile metadata for authorization or runtime routing.
- Do not make cross-user/team profile sharing implicit.
- Do not store raw personal metadata in logs, audit entries, or public ledgers.

## Expected outcomes
- A user can have a small, inspectable profile that improves relevant AI
  responses.
- The runtime can decide, per query, whether a profile fact is useful and
  allowed.
- Users and admins can understand and control profile facts, including inferred
  country.
- Profile metadata remains separate from Gateway auth/routing identity.

## Validation ideas
- Unit tests for explicit profile CRUD, inferred fact provenance, and deletion.
- Policy tests showing profile facts are injected for relevant queries and not
  injected for unrelated queries.
- Ledger/audit tests proving sensitive fields are redacted or represented by
  references.
- UI tests proving users can inspect and correct inferred country.
- Security tests proving one user cannot read or mutate another user's profile.

## Discussion prompts
- Should the profile context be opt-in globally, opt-in per fact, or opt-in per
  query category?
- Should country be inferred only after repeated evidence or only after user
  confirmation?
- Should birth date be stored at all, or should age band be preferred?
- Should injected profile facts be visible in run details for transparency?
