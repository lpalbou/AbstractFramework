# Proposed: Hosted proxy shared helper extraction

## Metadata
- Created: 2026-05-30
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0033
- ADR impact: None unless promoted to a package-boundary change.

## Context
Flow, Code Web, and Observer all implement hosted Gateway browser-session
proxying. Code Web and Observer currently duplicate similar Node server logic
for app cookies, Gateway session exchange, CSRF forwarding, logout, and Gateway
URL selection. A review found real drift: Flow blocked remote-host browser
Gateway URL changes while Code Web and Observer did not.

## Current code reality
- Flow's Python backend and static/Vite server implementations already reject
  browser Gateway URL changes from non-local hosts unless explicitly enabled.
- Code Web and Observer now have matching guards and focused tests, but their
  Node server implementations remain package-local.
- No shared JavaScript package currently owns hosted Gateway proxy semantics.

## Problem or opportunity
Duplicated hosted proxy logic can drift again as app behavior evolves. A shared
helper could reduce security drift, but extracting too early may create a
cross-package abstraction that fits only today's two Node servers and not Flow's
Python host or future apps.

## Alternatives
- Keep package-local code and require conformance tests in every hosted browser
  app. This is small and reversible, but duplicated code remains.
- Extract a tiny shared Node helper for Code Web and Observer only. This reduces
  drift for the duplicated Node servers, but adds a new dependency boundary and
  does not help Flow's Python host.
- Define a language-neutral conformance suite first, then extract helpers only
  when at least two apps need identical behavior beyond tests. This has slower
  reuse but better evidence for the abstraction.

## Recommendation
Use conformance tests immediately and defer helper extraction. Promote this
proposal if another hosted app is added or Code/Observer drift again despite
tests. At that point, extract the smallest shared Node helper that owns only
cookie/session/proxy policy, not app UI or provider/default UX.

## Promotion criteria
- Two or more Node hosted apps need the same code changes at the same time.
- A conformance test catches repeated drift that would be easier to prevent by
  centralizing the helper.
- The helper can stay independent of app layout, routing, and feature flags.

## Non-goals
- Do not force Flow's Python backend into a JavaScript helper.
- Do not create a shared UI component for login/defaults from this proposal.
- Do not move Gateway authorization decisions out of Gateway.

## Validation if promoted
- Shared helper unit tests for cookie flags, URL guards, session exchange,
  logout, CSRF injection, and header stripping.
- App-level tests proving Code Web and Observer still expose the expected API
  shape after adopting the helper.
