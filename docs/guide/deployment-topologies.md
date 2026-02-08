# Deployment Topologies (Supported Patterns)

AbstractFramework is easier to reason about if you think in roles, not packages:

- UI / host UX: renders progress, collects approvals (AbstractCode, browser UIs, custom apps)
- Orchestrator: durable state machine + stores (AbstractRuntime + stores)
- Agent logic: produces effects/steps (AbstractAgent patterns, flows)
- LLM gateway: provider abstraction + tool-call parsing (AbstractCore)
- Tool executors: side effects (local tools, MCP workers, sandboxes)

## Topology A: Single machine (local everything)

Best for local development and offline-first workflows.

- UI + runtime + tools run in one process (or one machine).
- You can still use file-backed stores for durability.

## Topology B: Local orchestration + remote inference

Best when you want local tool execution but a remote model (GPU box, cloud API, hosted vLLM).

- Runtime + tools stay local.
- AbstractCore routes LLM calls to a remote provider endpoint.

## Topology C: Remote tool execution (MCP-backed)

Best when tools must run near the target environment (servers, private networks, sandboxes).

- Runtime stays on the durable host.
- Tool calls are delegated to an MCP worker.

## Topology D: Thin client UI + remote durable host (Gateway-first)

Recommended for multi-device, multi-client use.

- The gateway host owns the durable runtime + stores and progresses runs.
- Thin clients render by replaying/streaming the ledger and act by submitting durable commands.
- Bundles (`.flow`) provide portable, discoverable specialized agents.

## Topology E: Multi-host orchestration (planned/advanced)

Only needed when you want to distribute durable orchestration itself across multiple hosts.
For v0, prefer picking a host per run (avoid mid-run migration).

## See also

- [Scenario: Gateway-first local development](../scenarios/gateway-first-local-dev.md)
- [Guide: Gateway exposure security](gateway-security.md)

