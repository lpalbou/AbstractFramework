# 0220 — Persistent Shell: Agent-Callable Tool Exposure (opt-in)

**Status**: Implemented + tested; live-verified (in-process ReAct, OVH gpt-oss-120b, n=1 per
arm, no retained artifact — surface qualifier per the evidence protocol; the A/B narrative
lives in the checklist below)
**Date**: 2026-07-08
**Priority**: High (unlocks 0215's ergonomics win; deliberate security posture)
**Components**: abstractruntime (effect_handlers runtime-owned tools, workspace policy), abstractagent (tool advertising), abstractgateway (capability/allowlist surface)

## Summary
Expose the shipped persistent PTY shell engine (`abstractcore.tools.shell_session`, backlog 0215) as
agent-callable tools — deliberately, opt-in, and honestly labeled. The engine is done and verified;
this item is ONLY the tool surface and its safety posture. Maintainer decision 2026-07-08: expose it,
but NOT in the default toolset until the OS sandbox (gateway backlog 0062) exists.

## ADR status
- Governing ADRs: ADR-0006 (durable execution — sessions are explicitly NON-durable, documented),
  ADR-0014 (runtime-owned timeouts), ADR-0026 (offload/preview marking, reuse 0215 offload).
- ADR impact: none new; the 0062 ADR (isolation tiers) must cover this tool when written.

## Context / current code reality
- Engine shipped + adversarially hardened: `ShellSession`/`ShellSessionRegistry` (PTY transport,
  persistent cwd/env, `write_stdin`, exit codes, O(n) sentinel scan, deterministic post-timeout
  resync, killpg teardown). 14 tests. No tool calls it yet.
- Adversarially-reviewed design (recorded in 0215): runtime-owned tools (like `open_attachment`),
  registry keyed by run id; approval via `_DEFAULT_REQUIRE_APPROVAL`; initial cwd pinned through
  `rewrite_tool_arguments` workspace policy; teardown at the runtime terminal seam
  `_append_terminal_status_event` (covers completed/failed/cancelled — the gateway `_tick_run` seam
  misses explicit cancel); non-durable across process restarts → re-open on replay with a documented
  state-loss note in the observation.
- Security reality (why opt-in): once approved, a persistent shell escapes per-call cwd confinement
  — same weakness one-shot `execute_command` already has, but persistent. Runtime tool-gating is a
  logical boundary; only the 0062 OS sandbox is a physical one.

## What we want to do
1. **Tools**: `shell_exec(command, session_id?, timeout?)` + `shell_write_stdin(session_id, input)`
   (+ close semantics — either explicit `shell_close` or close-on-run-end only; decide at
   implementation with a documented rationale).
2. **Opt-in exposure**: NOT in `get_default_toolsets()`. Enabled per run/workflow via explicit
   allowlist (and/or a gateway capability default an admin turns on). A workflow that needs a venv
   or dev server asks for it; the default agent posture is unchanged.
3. **Approval-gated**: in `_DEFAULT_REQUIRE_APPROVAL` next to `execute_command`; per-run
   `tool_policy` can widen/narrow as usual.
4. **Honest schema**: the tool description states plainly: "persistent session; non-durable across
   host restarts (state re-opens empty on replay with a notice); once approved, commands are not
   confined to the workspace cwd" — no isolation claims the OS does not enforce.
5. **Lifecycle**: sessions keyed by run id; torn down at `_append_terminal_status_event`; replay
   after process death re-opens a fresh session and the observation says so (never silently
   pretends continuity).
6. **Output offload**: session output flows through the 0215 generalized offload (inline budget,
   50 MB retention cap, explicit >cap push-back notice).
7. **0062 composition**: when the OS sandbox lands, the persistent shell inherits the same
   confinement as `execute_command` (default-sandboxed, explicit admin opt-out). Until then the
   approval prompt wording must state "runs unsandboxed".

## Non-goals
- Not an OS sandbox (0062).
- Not changing one-shot `execute_command`.
- Not durable shell state (explicitly out; documented).
- Not full TTY UIs — dev workflows (venv, REPL, servers, watchers).

## Dependencies and related tasks
- 0215 (engine + offload; design record). Gateway 0062 (sandbox posture; capability truthfulness).
- Gateway tool-inventory surfaces should label it with its approval default and non-default status.

## Validation
- Unit: cwd/env persist across two `shell_exec` calls in one run; approval wait fires before first
  execution; session torn down on run completion AND on cancel; replay after simulated process
  death re-opens with the state-loss notice; tool absent from default toolsets; schema text carries
  the non-durability + confinement warnings.
- Live (endpoint `http://127.0.0.1:8317/v1`): venv-create → pip install → run-inside-venv succeeds
  in one session where one-shot `execute_command` demonstrably cannot.

## Progress checklist
- [x] Tools wired (`abstractcore/tools/shell_tools.py`: `shell_exec`/`shell_write_stdin`/
      `shell_close`; engine gained `read_output` quiet-gap drain, `close_namespace`,
      `namespaced_session_id`, atexit reaping). DESIGN DELTA from the 0215 record, for cause:
      tools execute as HOST tools (MappingToolExecutor callables) with the registry namespace
      force-stamped by the TOOL_CALLS handler — runtime-owned execution (open_attachment-style)
      would BYPASS `ApprovalToolExecutor` (runtime-owned segments execute pre-approval) and the
      approved-resume path (`execute_approved` runs outside the handler, no run context). The
      host-tool shape gets approval + resume through the existing tested machinery; the stamped
      namespace rides the stored wait, so resume executes with the right scope.
- [x] Opt-in exposure: `ABSTRACT_ENABLE_SHELL_TOOLS=1` gates a `shell` toolset in
      `get_default_toolsets()` (comms-pattern); absent otherwise (test-pinned).
- [x] Approval gating (`_DEFAULT_REQUIRE_APPROVAL`) + honest schema ("NOT a sandbox", "NOT
      durable", both test-pinned); per-call timeout capped at 600s (models emit ms-as-seconds).
- [x] Teardown: generic `Runtime.add_terminal_hook` at `_append_terminal_status_event` (fires on
      completed/failed/cancelled incl. explicit cancel) + `register_shell_session_teardown` in all
      abstractruntime factories AND the gateway tools-only bundle-host path. Non-durability notice:
      every fresh open announces "new shell session ... no state carries over" (truthful for both
      first-open and post-restart replay; no durable bookkeeping needed).
- [x] cwd pinning: `shell_exec.working_directory` rides `rewrite_tool_arguments`
      (default-to-workspace-root, like `execute_command`).
- [x] Tests: 12 in `abstractruntime/tests/test_shell_tool_exposure.py` (persistence, namespace
      hijack overwritten, cross-run isolation, approval wait + stamped resume, teardown on
      complete AND cancel, defaults-absence, env opt-in, schema wording, stdin interactive
      round-trip) + 2 engine tests (read_output, close_namespace).
- [x] LIVE evidence (OVH `gpt-oss-120b`, 2026-07-08): venv → pip install → python-inside-venv
      across SEPARATE shell_exec calls: PASS (28 tool calls, 246s, cowsay verified inside the
      venv). A/B against one-shot `execute_command` on the same state-dependent task: the
      persistent arm installed into the venv correctly (9 LLM calls, 30.6k in / 2.8k out tokens,
      122s); the one-shot arm CLAIMED success but silently installed into the WRONG environment
      (the host process's venv — cleaned up) because activation cannot persist. The failure mode
      is worse than an error: it is a false success with environment pollution.
- [x] Found + fixed during live testing: OVH AI Endpoints 400-rejects the best-effort
      `prompt_cache_key` field; the OpenAI-compatible provider now drops-and-retries once and
      stops sending it per instance (4 tests). Without this, default-on prompt caching (0212)
      broke every generation against OVH.

## Follow-ups
- Gateway tool-inventory labeling (approval default + non-default status) is inherited from the
  generic tool-spec path; a dedicated capability banner for "persistent shell enabled" could be
  added when 0062 lands and the posture flips to default-sandboxed.
- When gateway 0062 ships, the persistent shell inherits the same OS confinement as
  `execute_command`; approval prompt wording should then change from "runs unsandboxed" to
  "runs sandboxed; admin opt-out available".

## Guidance for the implementing agent
Implemented. The posture is the point: opt-in, approval-gated, honestly labeled, composing with
0062 when it lands. Any deviation from "not in defaults" needs a maintainer ruling.
