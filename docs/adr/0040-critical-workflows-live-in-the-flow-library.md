# ADR-0040: Critical Workflows Live in the Flow Library and Are Published by the Operator

## Status
Accepted (2026-10-25)

## Dates
- Proposed: 2026-10-25
- Accepted: 2026-10-25

## Context

On 2026-10-25 two automations judged the operator's mail with a workflow that existed only as a
hand-packaged `.flow` bundle (`live-mailbox-judge@1.0.1`, written by an agent straight into
`abstractgateway/flows/bundles/`). AbstractFlow's library lists saved flows and the bundles that
carry a visual flow it can open; this bundle had never been a library flow, so the operator could
not see what ran on their mail, could not read its prompt, could not change it. The operator's
ruling: "all critical workflows should be loadable in abstractflow, so we can see them and adjust
them", and the bundles the framework ships are published by the operator, personally, from Flow.

Today every bundle in the repository carries a visual flow except three shipped chat agents built
on a native loop (`react-agent`, `codeact-agent`, `memact-agent`, `metadata.native_loop_factory`,
see `abstractgateway/docs/api.md`); those cannot be opened in Flow.

## Decision

1. **A workflow that runs for a person is a visual flow in the Flow library.** Anything an
   automation, a trigger, an app or a shipped feature runs (a judge, a digest, an orchestrator, an
   entity brain, a coding loop) exists as a flow Flow can open: its nodes, wires, prompts and
   models visible and editable. A compiled or native workflow with no visual flow is the
   exception, declared in `abstractgateway/docs/shipped-workflows.md` with the reason, never the
   default.
2. **The operator publishes.** A bundle that the framework ships, or that an automation on the
   operator's gateway runs, is published from Flow by the operator. Agents and scripts may build a
   flow in the library and test it; they do not package bundles by hand and do not point
   automations at bundles the operator has not published. An agent that needs a workflow for a
   test publishes it under a test name on a hermetic gateway, never on the operator's.
3. **Packaging follows publishing.** A bundle enters the wheel (`pyproject.toml` package data)
   only after the operator has published that version from Flow; the packaged file is the
   published file, byte for byte.
4. **The library is the register.** Flow's library shows every flow the person can run or that
   runs for them, with what starts it; a workflow that runs on a gateway and is not in the library
   is a bug, reported as such.

## Consequences

### Positive
- The person can read, test ("Run as if triggered") and change everything that acts on their mail,
  feeds, calendar or files; no hidden prompts.
- One register (the library) and one publish path (Flow → bundle), so bundles never drift from a
  graph nobody can open.

### Negative
- Agents lose a shortcut: a quick hand-written bundle for a live test must now go through the
  library and the operator's publish.
- Native-loop agents need either a visual wrapper or an explicit, documented exception.

### Neutral
- Draft and test bundles under `flows/bundles/` in a source checkout stay (gitignored); only what
  ships or runs for a person is governed.

## Enforcement
- Code review: a change that adds a bundle to `pyproject.toml` package data or points an
  automation at a bundle cites the library flow it was published from.
- Gateway test (planned, backlog 1051): every wheel-shipped bundle's entrypoints carry a visual
  flow, except the ids listed in `shipped-workflows.md` under "Exceptions".
- Completion reports for work that runs a workflow for the operator name the library flow and who
  published the bundle.
- Flow's library is the surface where the rule is visible: a running automation whose bundle is
  not in the library is reported as a defect (Observer and the console show the bundle ref).

## Validation
- `abstractgateway` test from backlog 1051 (shipped bundles ⊆ visual flows ∪ exceptions).
- Manual: open the Flow library, filter Triggered, every automation on the gateway has its flow
  there (checked 2026-10-25 for "Judge what arrived").

## Backlog links
- Originating: 1050 (events and attention follow-ups), the 2026-10-25 live mail test.
- Adoption: 1051 (shipped bundles loadable in Flow; the three native agents as exceptions or
  wrapped).

## Related
- ADR-0012 (portable WorkflowArtifact deprecated in favour of VisualFlow bundles), ADR-0001.
- `abstractflow/docs/web-editor.md` (Flow Library, Kinds of flows), `abstractgateway/docs/shipped-workflows.md`.
