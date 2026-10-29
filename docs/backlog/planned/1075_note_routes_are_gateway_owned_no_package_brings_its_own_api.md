# 1075 — All note routes live in the gateway, nicely organised, accessible to any app dealing with notes

**The goal (operator, 2026-10-29):** every note operation is a gateway route under `/api/gateway/note/...`, organised
there with the rest of the gateway's API, callable by any app that deals with notes — the watch, the phone, the desktop
Assistant, the web apps, an automation — with the gateway's sign-in, authorization, audit and limits. No package brings
its own API or server.

> Status: planned (operator confirmed the direction, 2026-10-29) · Priority: P1 · Owner: gateway + AbstractNote
> Related: AbstractGateway ADR 0001 (AbstractCore access goes through AbstractRuntime facades), AbstractRuntime ADR 0008
> (runtime integration facades are the complete host surface), AbstractNote ADR 0001 (the one explicit seam),
> gateway backlog 0972 (CI installs the seam packages), gateway security incident 2026-10-29 (14 note write routes
> had no authorization decision), AbstractNote backlog 0040 (shared-plane gate for two routes).

## The situation today (read from the code, 2026-10-29)

- AbstractNote does **not** run a server of its own. It is a Python package with a CLI (`abstractnote`), a
  notebook store (`abstractnote.store.notebook.Notebook`), workflows, and one FastAPI router
  (`abstractnote/gateway/router.py`).
- That router is mounted **inside the gateway process** by `abstractgateway/abstractnote_seam.py` under
  `/api/gateway/note/...` (`app.include_router(_note_router, prefix="/api/gateway")`). The same seam also binds the
  note tools to each plane's notebook, adds them to the plane's auto-approve set, and loads AbstractNote's workflows
  as a framework bundle. Without the package installed, nothing of this exists and the gateway behaves as before.
- It is the **only** package mounted this way. Every other router in `app.py` is the gateway's own
  (`routes/*.py`); memory, voice, vision and the rest are gateway routes that call AbstractCore through the runtime
  facades. The seam module says so itself: "AbstractGateway has no plugin loader; this module is the one explicit seam".
- Clients reach note through the **same gateway base URL and the same sign-in**: the note web app
  (`@abstractframework/note`, served by the gateway's app proxy) calls `/api/gateway/note/...` with the browser's
  gateway session; the router resolves the caller's principal and plane with the gateway's own helpers. The watch and
  the iPhone do not call note routes today (no `/api/gateway/note` path in `phone/` or `watch/`); an agent or an
  automation reaches notes through the note **tools**, not the HTTP routes.
- What went wrong with the seam: the router's 14 write routes lived outside the gateway's route authorization table
  until 2026-10-29 (gateway PR #55 recorded the decision; #58 made CI install the package so the contract walks the
  routes). The authorization rules, the audit line, the body caps and the rate limits are the gateway's; a router that
  arrives from another package is only covered when someone remembers to install that package in CI.

## The rule (operator)

Note functionality is a set of **gateway-owned HTTP routes** that every app calls the same way, and **no package
brings its own API or server**. A capability package exposes a Python API; the gateway owns the HTTP surface, the
authorization decision for every route, the audit line and the limits.

## What the gateway and AbstractNote look like afterwards

- `abstractgateway/routes/note.py` (gateway-owned) serves `/api/gateway/note/...`. Compatibility note, not the goal:
  keeping today's paths means the note web app and any client keep working unchanged during the move. Each route carries an explicit authorization decision in
  `security/authorization.py` (admin row or user-level row with its reason), like every other gateway route; the
  two plane-wide routes (`PUT /settings`, `POST /processor/ensure`) get their shared-plane rule here (AbstractNote
  backlog 0040 moves into the gateway).
- AbstractNote keeps `Notebook` and the store as its **Python API**, plus its workflows and tool definitions. The
  gateway reaches it the way it reaches AbstractCore: through a runtime facade (`abstractruntime.integrations.
  abstractnote`, per runtime ADR 0008: the facade is the complete host surface), never by importing the package's
  router. `abstractnote/gateway/router.py` is deleted once the gateway route file ships.
- The seam module shrinks to **registration**: "is the package installed; here are its tool bindings, its
  auto-approve names and its workflow bundle". It mounts no HTTP router. `tests/test_gateway_seams_mounted.py`
  changes meaning: it asserts the gateway's own note routes exist and that the facade answers.

## What breaks if this is done naively

- A client pinned to a route shape that changes. Keeping the same paths and payloads avoids this; the contract test
  pins every route's decision.
- Version skew: today the note routes' behaviour follows the installed `abstractnote` version; afterwards it follows
  the gateway's version, with the facade's floor on `abstractnote` (a too-old package answers "update abstractnote"
  in words, as the runtime floor does for AbstractRuntime).
- AbstractNote's own tests of its router (they move to the gateway, or become facade tests).
- The unreleased `abstractnote` 0.3.0 and any PR touching `gateway/router.py` (one: AbstractNote #7 / backlog 0040).

## Migration steps

1. Runtime: add the `abstractnote` integration facade (open/bind a plane's notebook, the operations the router calls
   today: list/search/get, archive, redate, refile, retract, close, confirm, unmerge, normalize, ack, retry, priority,
   recompute, settings, processor). AbstractRuntime release.
2. Gateway: `routes/note.py` over the facade, same paths; authorization rows for all 14 writes (12 user-level, 2
   admin-or-plane-owner); audit, body caps and rate limits as for other routes; `tests/test_gateway_note_routes.py`
   with the mutation checks; the contract test's note rows become policy rows.
3. Gateway: the seam becomes registration only; remove the router mount; keep tools, auto-approve names, bundles.
4. AbstractNote: delete `gateway/router.py` and its tests; document the Python API and the facade; release.
5. Clients: nothing to change if the paths hold; the watch and the iPhone can adopt note later through the same
   routes.
6. Root: install profiles unchanged (abstractnote stays an optional package); `docs/architecture.md` states the rule.

## Cost

- Runtime facade: M (one module, ~15 operations, tests).
- Gateway routes + authorization + tests: M (the router exists; it is moved and audited, not designed).
- Seam reduction + AbstractNote cleanup: S.
- Releases: AbstractRuntime, AbstractGateway, AbstractNote, in that order (the gateway floor on both).
- Total: two to three worker-days, one release wave.

## Done when

Every `/api/gateway/note/...` route is served by `abstractgateway/routes/note.py`, has a row in the authorization
table, and the note web app, an automation using note tools, and a CLI call all behave as before on 8443/8080 at a
stated sha; `abstractnote` ships no router; the seam mounts nothing.
