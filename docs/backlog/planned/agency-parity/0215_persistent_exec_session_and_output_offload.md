# 0215 — Persistent Exec Session + Command Output Offload

**Status**: Planned
**Date**: 2026-07-07
**Priority**: High (real-dev ergonomics; ledger/prompt bloat)
**Components**: abstractcore (common_tools execute_command + new exec-session module), abstractruntime (effect_handlers offload symmetry)

## Summary
Add a persistent, PTY-backed shell session alongside the current one-shot `execute_command`, and
artifact-offload large command output symmetrically with `read_file`. Today every command is a fresh
`subprocess.run(shell=True)`, so `cd`/venv/REPL/dev-server state cannot persist, and large logs sit
inline in the durable ledger.

## ADR status
- Governing ADRs: ADR-0006 (durable tool execution), ADR-0014 (runtime timeouts), ADR-0026 (offload = preview + full-content path, not truncation).
- ADR impact: May need a short ADR/section on persistent-exec session lifecycle + capability reporting.

## Context / current code reality
Verified 2026-07-07:
- `abstractcore/.../common_tools.py:execute_command` (~`:7684`) is one-shot:
  `subprocess.run(command, shell=True, cwd=…, timeout=…, capture_output=True)` (`:7829-7837`).
  Default timeout 300s (`:7687`). No PTY, no `write_stdin`, no background/detached processes, no
  streaming. `working_directory` is per-call only.
- Output is preview-bounded for the model (stdout 20000 chars, stderr 5000, `:7861-7870`) but the
  **full** stdout/stderr are kept in structured result fields and land in the ledger — no artifact
  offload.
- Contrast `read_file`: >256 KB is offloaded to a session artifact with an `open_attachment` stub
  (`effect_handlers.py:3175-3285`). `execute_command` output has no equivalent.
- Timeout helper `_call_with_timeout` runs work in a daemon thread that cannot kill the callable
  (`tool_executor.py:43-77`); `subprocess` timeout does kill the child.

## Problem
1. No persistent shell: `cd`, `source venv/bin/activate`, interactive prompts, REPLs, and long-lived
   dev servers/watchers are impossible or must re-establish state every call. This is the biggest
   ergonomics gap versus Codex `unified_exec` (`exec_command` + `write_stdin`, background handles).
2. Large command output (builds, test logs) bloats the prompt preview's parent ledger record.

## What we want to do
Provide a session-scoped exec capability with a persistent working directory/environment, the
ability to send stdin, start background processes and read incremental output, and a clean lifecycle
— offered as an additional tool surface, not a replacement for the safe one-shot tool. Offload large
command output to an artifact with an `open_attachment`-style handle.

## Requirements
1. **Persistent session**: a durable session handle with persistent cwd + env; `exec_command`
   (start / run) and `write_stdin` (send input) semantics; ability to launch a background process
   and read incremental output; explicit close/teardown; per-session and per-call timeouts honored
   by the runtime (ADR-0014).
2. **Safety parity**: persistent exec is at least as guarded as one-shot `execute_command`
   (approval policy, workspace path policy, the existing command-security checks). Report the
   capability honestly (do not advertise isolation that is not enforced; see backlog 0062).
3. **Output offload**: when command stdout/stderr exceeds a threshold (reuse
   `ABSTRACTRUNTIME_MAX_INLINE_BYTES`/256 KB), store full output as an artifact and return a
   preview + `open_attachment` handle, mirroring `read_file`. Keep the preview marked (ADR-0026).
4. **Backward compatibility**: existing one-shot `execute_command` behavior unchanged; the
   persistent surface is additive and allowlist-gated.

## Non-goals
- Not an OS sandbox (that is backlog 0062, separate).
- Not removing or changing the one-shot `execute_command` default behavior.
- Not required to support full interactive TTY UIs — target dev workflows (venv, REPL, servers,
  test watchers).

## Dependencies and related tasks
- ADR-0014 (runtime-owned timeouts), backlog 0062 (isolation tiers — coordinate capability claims).
- Shares `common_tools.py` with 0216 (edit_file); different functions, coordinate to avoid churn.

## Expected outcomes
- `cd`/venv/env set in one call is visible in the next call of the same session.
- A background dev server can be started and its incremental output read without blocking the loop.
- Large command output is artifact-offloaded; the ledger record stays small; full output is
  retrievable via handle.

## Validation
- Unit: two calls in one session where call 1 `cd`s / exports an env var and call 2 observes it;
  a background process whose output is read incrementally then terminated; an output >256 KB is
  offloaded and retrievable.
- Live (endpoint `http://127.0.0.1:8317/v1`): a task that creates a venv, installs, and runs a
  command needing that venv — succeeds with persistent exec, and demonstrably cannot with one-shot.

## Progress checklist
- [x] Persistent exec session ENGINE (PTY-backed: cwd/env persist, write_stdin, exit codes,
      background reap via killpg). Hardened + adversarially verified: bounded O(n) sentinel scan
      with capped memory on huge output, deterministic post-timeout resync (no stale bleed),
      fd-leak-free reopen. Handles the failure modes a pipe design couldn't (`cat`, `set -x`,
      binary output, no-echo). 14 tests.
- [x] Command-output artifact offload symmetric with read_file (large stdout → session artifact +
      open_attachment handle; byte-measured; dedup). 2 tests.
- [x] Offload generalized (2026-07-08, maintainer-directed): applies to `execute_command` stdout
      AND stderr regardless of exit code (a noisy failure offloads like a noisy success), and to
      any other host tool returning a large string output. Retention cap raised to 50 MB
      (`ABSTRACTRUNTIME_MAX_ATTACHMENT_BYTES`); output beyond the cap is NEVER silently kept
      inline or dropped — the result carries an explicit notice (size, cap, narrow-the-command
      guidance) so the agent/user decides. 6 tests; documented in abstractruntime
      `docs/artifacts.md` ("Tool-output offload").
- [x] Native-provider system-message delivery fixed (so tail-placed system hints / attachment index
      reach OpenAI/Anthropic) — pinned by 11 provider tests.
- [ ] Tool SURFACE exposure — split out to **0220** (maintainer ruling 2026-07-08: expose it,
      opt-in + approval-gated + honestly labeled, NOT in the default allowlist until the OS
      sandbox of gateway 0062 exists). The adversarially-verified design (runtime-owned, run-id
      keyed, `_DEFAULT_REQUIRE_APPROVAL`, cwd via `rewrite_tool_arguments`, teardown at
      `_append_terminal_status_event`, re-open-on-replay with state-loss note) is recorded in 0220.
- [ ] Live evidence (agent actually using a persistent session across calls).

## Known follow-ups (adversarial review)
- ~~Offload gates on `success is True` + stdout only~~ RESOLVED 2026-07-08: offload now applies to
  stdout+stderr on any exit code and to any tool's large string output; >cap output surfaces an
  explicit push-back notice instead of staying inline (see checklist).
- ~~OpenAI system passthrough is positional; … The shipped caller only tail-appends, so this
  cannot fire today.~~ **THIS CLAIM WAS WRONG — production incident 2026-07-09**: the risk model
  asked only about mid-tool-run placement on native OpenAI and never asked whether the
  openai_compatible family accepts a non-leading system message AT ALL. OVH/vLLM rejects the
  tail-append itself ("System message must be at the beginning.", HTTP 400) — the exact shape
  this sentence certified safe failed a production assistant's first message. Fixed at the
  transport (`_normalize_system_messages_for_strict_servers`, wire-path-pinned); recorded here
  as a standing lesson: "cannot fire" requires a probe against every provider family that can
  receive the shape, and template strictness is per-model-endpoint.

## Guidance for the implementing agent
Keep the one-shot tool intact; add the persistent surface additively. Never claim isolation that the
OS does not enforce. Coordinate `common_tools.py` edits with 0216.
