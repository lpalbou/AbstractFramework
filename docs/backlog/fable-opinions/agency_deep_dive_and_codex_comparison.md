# AbstractFramework Agency — Deep Dive and Codex 0.89 Comparison

**Author:** Fable (analysis agent)
**Date:** 2026-07-07
**Type:** Opinion / assessment (no code was modified during this study)
**Scope:** the agentic execution path — the ReAct/CodeAct/MemAct loops, the tool system, memory & context handling, and end-to-end performance — compared to a Codex-CLI-class harness (baseline: OpenAI Codex CLI v0.89, Jan 2026).

---

## How this report was produced

Four independent, read-only adversarial audits were run in parallel, each with a narrow mandate, plus a first-hand verification pass by the author. The four audits:

- **ReAct/loop audit** — loop anatomy, stop conditions, planning, parallelism, steering, durability cost, prompt quality.
- **Memory/context audit** — in-loop context growth, session memory, the `abstractmemory` engine, MemAct, project memory, KV-cache friendliness.
- **Tool-system audit** — registry, execution path, approvals, shell/exec, file editing, sandboxing, MCP, output budgets.
- **Performance audit** — the hot path of one hosted iteration, streaming, ledger overhead, poll cadence, concurrency.

Every load-bearing claim below is anchored to code that was read directly, with `file:line` citations. Where a number is an inference from code structure rather than a profiler measurement, it is labelled as such. Where the framework's own `AGENTS.md` notes disagree with the current code, that is called out.

### The Codex 0.89 baseline (what we are comparing against)

Codex CLI 0.89 (released 2026-01-22) is the mature form of a harness whose agent-loop design OpenAI documented publicly ("Unrolling the Codex agent loop", Jan 2026). The properties that matter for this comparison:

- **Model-driven turn loop** over the Responses API; inference is streamed (SSE) and surfaced token-by-token.
- **Prompt-prefix stability is sacred**: static content (instructions, tools) goes first; variable content goes last; the previous prompt is an *exact prefix* of the next one, so prompt caching turns per-turn cost from quadratic to linear. Mid-conversation config changes are *appended* as new messages rather than editing earlier ones, precisely to preserve cache hits.
- **Automatic compaction**: when tokens exceed `auto_compact_limit`, Codex calls a server-side `/responses/compact` endpoint that returns a compact item list (with opaque `encrypted_content` preserving latent understanding). Earlier a "summaries of summaries" degradation existed and was fixed with a clean template.
- **Parallel tool calls** in one turn; a built-in `update_plan` tool; **retry-with-escalation** on tool denial.
- **`unified_exec`**: PTY-backed persistent shell sessions (`exec_command` + `write_stdin`) for `cd`, venvs, REPLs, dev servers, interactive prompts.
- **`apply_patch`**: a distinct file-edit protocol surface validated by a formal Lark grammar, decoupled from shell for recoverability.
- **OS-level sandboxing** of the whole spawned process tree (Seatbelt / Landlock+seccomp / Windows restricted tokens).
- **Skills** (`SKILL.md`), **web search on by default**, **project/team config** layering (`AGENTS.md`, `.codex/`).

Keep one asymmetry in mind throughout: Codex is a **single-process, memory-first, coding-specialised** harness. AbstractFramework is a **durable, multi-tenant, multi-modal workflow runtime** where the agent loop is one workload among many, every step is a replayable effect, and the target models include weak/local ones. Several "weaknesses" below are the direct cost of capabilities Codex does not even attempt (crash-resumable runs, day-long human-in-the-loop waits, cross-client reattach, non-native-tool-calling model support). The report tries to keep that trade in view rather than scoring the framework against a harness with a narrower mission.

---

## 1. Architecture map of the agency stack

The agent loop is assembled from five layers:

- **`abstractcore`** — provider abstraction, tool-call parsing across formats (native function-calling, XML-wrapped, pythonic, special-token), token estimation, prompt-cache control planes for local backends.
- **`abstractagent`** — the *pure logic* of each agent (`logic/react.py`, `logic/codeact.py`, `logic/memact.py`: build prompt, parse response) and *runtime adapters* (`adapters/react_runtime.py`, etc.) that compile that logic into a durable `WorkflowSpec`.
- **`abstractruntime`** — the durable kernel. Each loop node returns a `StepPlan` (a pure transition or an `Effect`); `Runtime.tick()` (`abstractruntime/src/abstractruntime/core/runtime.py:1366`) executes it, records `StepRecord`s to a ledger, and persists full run state. Effects (`LLM_CALL`, `TOOL_CALLS`, `ASK_USER`, `MEMORY_*`, `START_SUBWORKFLOW`, …) are handled by registered handlers, chiefly in `integrations/abstractcore/effect_handlers.py`.
- **`abstractgateway`** — the FastAPI control plane. `GatewayRunner` (`abstractgateway/src/abstractgateway/runner.py`) is a background tick loop that advances `RUNNING` runs on a thread pool; the shipped `basic-agent`/`ln` bundle wraps the ReAct workflow as an async child run; ledger records are streamed to clients over SSE.
- **`abstractcode` / `abstractflow` / `abstractassistant`** — thin clients. `abstractcode` is a chat/CLI over the gateway; `abstractflow` is the visual editor whose "Agent" node compiles (via `visualflow_compiler/`) to the same ReAct workflow.

**The defining design choice is the durable-effect indirection.** In Codex, the agent loop holds the rollout in RAM and journals asynchronously. Here, every LLM call and every tool batch is a persisted effect with an idempotency key (`sha256(run_id, node_id, effect_payload)`, `core/policy.py:169-190`), so a run survives process death and can be replayed exactly. This is the framework's biggest genuine differentiator — and, as Sections 6–7 show, the source of most of its per-step latency.

**One iteration of the flagship ReAct loop** (`adapters/react_runtime.py:1599-1612`) is the node chain:

```
init → reason → parse → (act → observe)* → done | max_iterations
```

- `reason` re-validates the toolset, increments the iteration counter, drains a guidance inbox, builds the system prompt, sanitizes `context.messages` into OpenAI-shaped chat messages, and emits an `LLM_CALL` effect.
- `parse` extracts `content` + `tool_calls`; tool calls → `act`, otherwise final-answer/retry heuristics.
- `act` batches consecutive non-builtin tools into one `TOOL_CALLS` effect; builtins (`ask_user`, `recall_memory`, `remember`, `compact_memory`, `delegate_agent`, …) are dispatched one at a time to native effects.
- `observe` appends each result as a `role="tool"` message and loops back.

---

## 2. The ReAct loop (quality of agency)

### 2.1 What is genuinely good

- **Native tool calling, no forced "Thought:/Action:" text protocol.** The system prompt (`abstractagent/src/abstractagent/logic/react.py:91-120`) instructs the model to call functions and to *stop when it emits no tool calls*; tool specs go through the structured `tools` param. The classic ReAct text-parsing anti-pattern is avoided.
- **Robust malformed-tool-call recovery** for weak/local models: `MappingToolExecutor` JSON-parses string arguments, unwraps `{"name","arguments"}` wrappers, normalizes key morphology (`filePath`→`file_path`), applies a synonym table, filters unknown kwargs, and retries once on `TypeError` (`integrations/abstractcore/tool_executor.py:117-354`). Codex, being native-tool-calling-centric, does not need this — but here it matters.
- **Graceful budget exhaustion.** On `max_iterations`, instead of a hard stop, the loop runs a tool-free "conclusion" LLM call to synthesize a progress report + best answer + next steps (`react_runtime.py:1459-1573`), with a strict retry if the model leaks tool markup. This is better than most harnesses' abrupt termination.
- **A duplicate-side-effect guard**: exact-repeat side-effect batches after a successful cycle are skipped with a corrective inbox note (`react_runtime.py:987-1051`).

### 2.2 The weaknesses versus Codex-class agency

- **No verification or plan step on the flagship path.** ReAct — the workflow behind `abstractcode`, the gateway `basic-agent`, and every visual Agent node — finishes the moment the model emits prose without tool calls. There is no `finish`/`submit` tool, no test-gated completion. A structured verifier exists **only in CodeAct** (`adapters/codeact_runtime.py:931-1176`). Worse, it is *dead config on ReAct*: `ReactAgent(review_mode=True, review_max_rounds=3)` is the default and is written into `_runtime` (`agents/react.py:68,176-178`), but `react_runtime.py` never reads `review`/`review_mode` (verified by grep — zero matches). Codex gates completion on plans and checks; here the flagship loop cannot.
- **No plan/todo instrument.** No plan tool, no structured task list in ReAct. CodeAct's plan is an off-by-default single upfront prose checklist scraped from a `Plan Update:` suffix (`codeact_runtime.py:279-299`). Across 20–50 iterations of a multi-file task there is no anchor against goal drift — exactly what Codex's `update_plan` exists for.
- **Thought amnesia.** When the model calls tools, its reasoning is dropped from the transcript (the assistant message is stored with `content=""`, `react_runtime.py:1054-1060`) and survives only as a 600-char-truncated scratchpad line for the last 6 cycles. On iteration 15 the model cannot re-read why it chose an approach on iteration 3 — precisely the multi-step coherence a coding agent needs.
- **Heuristic, English-only stop/continue control.** Completion and "you said you'd act but didn't" detection rest on regex word-lists (`_FINALISH_RE`, `_looks_like_deferred_action`, `react_runtime.py:268-346`). One sub-regex is *confirmed dead code*: `r"(?m)^(#{1,6}\s+\\S|\\*\\*\\S)"` (line 339) has a double-escaped `\\S` that matches a literal backslash, so `## Summary`/`**Bold` never match. An explicit `finish` tool would be deterministic and language-neutral.
- **Crippled delegation.** `delegate_agent` runs children **inline, synchronously**, capped at `max_iterations=10`, stripped of `ask_user`/`delegate_agent`, returning a single text blob (`react_runtime.py:1239-1299`). No parallel fan-out/join. Codex-style "explore in N subagents, then synthesize" is impossible.
- **No effect-level retries in production configs.** `DefaultEffectPolicy.default_max_attempts=1` (`core/policy.py:149`); neither the gateway nor the local factory installs a `RetryPolicy`. A single raised exception in a tool executor, or a provider hiccup that escapes AbstractCore's internal retry, fails the whole run (`runtime.py:1541-1550`). Idempotency keys already make retries safe — they are simply not turned on.
- **Tool denial is a dead end.** Denial yields per-call `"Denied by user"` errors (`runtime.py:1749-1752`) with no escalation loop; the model typically re-attempts (tripping the repeat guard) or gives up. Codex retries with escalation (ask, narrow the command, explain).
- **Four inconsistent `max_iterations` defaults**: 25 in `ReactAgent` and `ensure_react_vars`, 50 in the VisualFlow compiler, 20 pinned in the shipped `basic-agent` bundle. Three answers for one knob.

---

## 3. Memory & context

This is where the framework is simultaneously most sophisticated and most self-defeating.

### 3.1 In-loop context: every budget mechanism is switched off

The ReAct adapter, by explicit written policy, disables all trimming and capping in `init_node`:

```806:818:abstractagent/src/abstractagent/adapters/react_runtime.py
        # Disable runtime-level input trimming for ReAct loops.
        if isinstance(runtime_ns, dict):
            runtime_ns.setdefault("disable_input_trimming", True)
        # Disable all truncation/capping knobs for ReAct runs (policy: full context for now).
        # These can be re-enabled later once correctness is proven.
        if isinstance(limits, dict):
            limits["max_output_tokens"] = None
            limits["max_input_tokens"] = None
            limits["max_history_messages"] = -1
            limits["max_message_chars"] = -1
            limits["max_tool_message_chars"] = -1
```

Consequences:

- **Full history is re-sent on every LLM call**, and each tool result appends a `role="tool"` message. Observations are **double-carried**: also stored in `scratchpad.cycles` and re-rendered into the system prompt (last 6 cycles), so recent tool output is paid for twice.
- **Token accounting exists but is decorative.** Real usage is recorded into `_limits.estimated_tokens_used` (`core/runtime.py:1521-1537`) and `check_limits()` warns at 80% (`core/runtime.py:1185-1224`), but no agent node consumes the warning. The only in-prompt signal to the model is `Iteration: i/max`.
- **Overflow has no typed error and no recovery.** There is no `ContextLengthExceededError` in `abstractcore/exceptions`; `validate_token_usage` (`core/interface.py:406`) is never called. On API providers a context-overflow 400 becomes a generic effect failure → `RunStatus.FAILED`. On Ollama there is no `num_ctx` management anywhere, so the server **silently truncates** — degraded answers with no signal, the worst failure mode.

**Correction (re: the `max_in_tokens` pin).** An earlier draft of this report called the pin "dead code / a broken lever." That was wrong, and it matters. The pin *is* written by `_build_sub_vars` into `_limits.max_input_tokens` (`visualflow_compiler/compiler.py:1080-1081`) and then nulled by ReAct's `init_node` — but that nulling is a **deliberate ADR-0026 safeguard**, not a defect. `max_input_tokens` drives `trim_messages_to_max_input_tokens` (`memory/token_budget.py:41-85`), which drops the oldest non-system messages — i.e. *arbitrary lossy truncation*, the exact operation ADR-0026 names (line 33) and forbids on critical/agentic paths. Disabling blunt drop-oldest truncation inside a reasoning loop is the correct call: an agent (or the runtime) guessing which past tool output is safe to delete is precisely how important context gets silently destroyed. So the real gap is **not** "make the pin truncate again." It is that the loop has *no ADR-0026-approved budget mechanism wired in either* — no automatic compaction (compress-with-provenance) and no retrieval-to-fit. The framework already has the approved mechanism (rehydratable compaction spans, §3.3); it just never triggers inside the loop. Where `max_in_tokens` *should* be honored, and documented per ADR-0008/0026: (a) as a **trigger threshold that fires compaction**, never as a silent truncation cap; (b) on **one-shot / stateless `LLM Call` nodes** where the input is a single retrieved blob and drop-oldest is acceptable and explicit; (c) for **bounded sub-agents / delegated tasks** given a deliberately small window; and (d) for **small-context local models** where the input physically must fit — and even there the action is compact-to-fit, not clip.

### 3.2 Session memory: client-side full-history re-injection

"Session memory replay" is not a server-side conversation store. `BaseAgent.session_messages` mirrors the last run's full message list (`agents/base.py:56,88-102`) and each new run seeds `context.messages` with a full copy (`agents/react.py:172`, `workflow_agent.py:769`). That copy is then persisted again in `complete_output.messages` and in the ledger — so cross-run cost and run-store size grow **O(n²)** in conversation length, with no pruning or reference-based seeding (even though rehydratable spans already exist).

### 3.3 Compaction: real, better-than-Codex provenance — but manual and unwired

`MEMORY_COMPACT` archives older messages to the ArtifactStore, inserts a `[CONVERSATION HISTORY SUMMARY span_id=…]` marker, preserves N recent, and indexes the span (`core/runtime.py:3644-3984`). Crucially, `split_for_compaction` sets all system messages aside (`memory/compaction.py:66-85`), so **prior summaries are never re-summarized** — no "summaries of summaries" degradation, and any span can be losslessly rehydrated (`memory/active_context.py:272-455`). This is strictly better auditability than Codex's opaque `/responses/compact` latent state.

But **nothing triggers it automatically.** And auto-compaction *already exists one layer down and is unused*: `BasicSession(auto_compact=True, auto_compact_threshold=6000)` in `abstractcore/core/session.py` has zero consumers in the runtime/agent stack. All the pieces for Codex-parity long-session survival exist; they are simply never connected.

### 3.4 The `abstractmemory` engine is not wired into any coding loop

The `abstractmemory` engine (append-only journal, activation as a pure fold with rank-distance decay, ACT-R spreading over Hebbian co-selection trails, exact/keyword/vector/participants channels fused into a budgeted shelf) is a serious, novel piece of work. **But a workspace-wide search shows its seam handlers are consumed only by `abstractruntime/identity/chat.py`, `abstractgateway/entity_gate.py`, and tests/demos** — i.e. summoned entities, not coding agents. The default runtime factory registers no `MEMORY_RECALL` handlers (`integrations/abstractcore/factory.py`); the runtime binds `abstractmemory` lazily and only for the entity/identity path (`integrations/abstractmemory/seam_handlers.py:70`).

What ReAct/CodeAct get instead is `recall_memory` → `MEMORY_QUERY`: metadata-first substring/tag/time filtering over compaction spans, explicitly *"embedding-free (semantic retrieval belongs in AbstractMemory)"* (`core/runtime.py:2871-2896`). So the day-to-day retrieval path is grep-grade while a spreading-activation engine with vector channels sits unused next door. The entity chat driver (`identity/chat.py`) *is* the Codex-class retrieval-first loop (recall → render under budget → LLM → commit → form episode, raw transcript capped at 10 turns) — but it serves Castor, not coding sessions.

### 3.5 No project memory (AGENTS.md)

No agent host loads a repo-level instruction file — verified: zero `AGENTS.md`/`CLAUDE.md`/rules loading in `abstractcode`/`abstractagent`/`gateway`. Codex's `AGENTS.md`/team config is one of its highest-leverage features, and this repository's *own* development process (the root `AGENTS.md`) demonstrates the value daily. The mechanism to add it already exists (`_runtime.system_prompt_extra`, `react_runtime.py:391-404`).

---

## 4. Tools

### 4.1 The execution path

`make_tool_calls_handler` (`integrations/abstractcore/effect_handlers.py:2066`) builds a `WorkspaceScope`, applies an optional per-node allowlist, rewrites filesystem arguments under workspace scope, interleaves runtime-owned tools (`open_attachment`) with host tools preserving order, and dispatches through a strategy-pattern executor (`Mapping`/`AbstractCore`/`Passthrough`/`Mcp`/`Delegating`/`Approval`). Idempotency includes arguments in the hash; approvals become durable `WaitState`s resumed with `{"approved": bool}`.

The default host toolset (`default_tools.py:99-157`): files (`list_files, skim_folders, search_files, analyze_code, skim_files, read_file, write_file, edit_file`), web (`skim_websearch, skim_url, web_search, fetch_url`), system (`execute_command`), opt-in comms. There are **no coding-specialised tools** — `abstractcode` reuses these generic tools.

### 4.2 The gaps versus Codex

- **No OS sandbox anywhere.** A search for `seatbelt|sandbox-exec|landlock|seccomp|bubblewrap|nsjail|firejail|pledge` finds only docs/backlog. Safety is a **regex blocklist** (`common_tools.py:_validate_command_security`) bypassable with `allow_dangerous=True`, plus approval prompts, plus path rewriting *only when `workspace_root` is set* (otherwise `scope=None` and file tools run raw across the whole filesystem). The maintainers concede this in backlog `0062` ("execute_command is the single tool that breaks tenant isolation in-process"; OS-confinement tiers are proposed, not built). Codex makes the OS the boundary.
- **No persistent shell / PTY.** `execute_command` is a one-shot `subprocess.run(shell=True, …)` (`common_tools.py:7829-7837`): `cd` doesn't persist, no `write_stdin`, no background/detached processes, no streaming. Codex's `unified_exec` keeps PTY sessions alive across calls (venvs, REPLs, `npm run dev`, interactive prompts). This is the single biggest ergonomics gap for real dev work.
- **No formal patch grammar; `edit_file` defaults to replace-all.** `max_replacements` defaults to `-1` (`common_tools.py:7102`), so an ambiguous literal pattern silently rewrites *every* occurrence. The unified-diff mode is a hand-rolled, line-number-anchored parser with no offset fuzzing (`_apply_unified_diff:6808-6847`) — drifted line numbers → "Context mismatch". Codex's `apply_patch` is grammar-validated and context-located. (Credit where due: the framework's Python `ast.parse` refuse-on-syntax-error, `common_tools.py:7549-7601`, is *better* than Codex here — but Python-only.)
- **No centralized type coercion → weak-model flag bugs.** For prompted/XML formats all args arrive as strings; `edit_file` never coerces `use_regex`/`max_replacements`/`preview_only`, so `use_regex="false"` is truthy (literal replace becomes a regex compile) and `preview_only="false"` is truthy (the edit is silently previewed and never written). The `AGENTS.md` 2026-02-20 note flags "centralize schema-aware coercion" as a direction; it is not shipped.
- **Tool tiering (`capability_class` tier0/1/2) is design-only** — it exists in a2a threads, with no tier gate in the tool path. **Skills (`SKILL.md`) are not wired into execution** either (`abstractskill` is unreferenced by the core/runtime/agent/gateway loop).
- **`execute_command` output is not artifact-offloaded** (unlike `read_file` at 256 KB), so big build/test logs bloat the ledger while the model sees only a 20 K-char preview.

---

## 5. Performance / speed

Tracing one hosted iteration (HTTP start → runner tick → effects → SSE) surfaces a consistent theme: **the durability model and the prompt construction, not the model, dominate avoidable latency and cost.**

- **No token streaming to clients.** The runtime aggregates even `stream=True` generations into one final dict — the docstring says so: *"even when the underlying provider streams we aggregate into one final dict"* (`integrations/abstractcore/llm_client.py:4725-4729`). Progress events exist only for media outputs. Users watch a spinner for the full generation; Codex streams tokens live. This is the largest *perceived*-latency gap.
- **Prompt-prefix caching is defeated by construction** (see 5.1) — the largest *actual* cost/latency gap.
- **O(N²) ledger I/O.** Idempotency does a **full-ledger scan per effect** (`ledger_store.list(run_id)` reads and parses every line, `runtime.py:2163-2176`); SSE clients re-read as well. The default `JsonlLedgerStore.append` (`storage/json_files.py:392-397`) is a plain append with **no `fsync` and no `flock`** (verified: zero `fsync`/`flock`/`LOCK_EX` in `abstractruntime/`), relying on OS `O_APPEND` atomicity with best-effort recovery of concatenated JSON on read. *(Note: the root `AGENTS.md` says "ledger appends are serialized with a file lock + fsync"; that does not match the current default store — either aspirational or removed. Durability against power loss is weaker than the note implies.)* The SQLite store runs ~4 statements per append in a transaction (`storage/sqlite.py:551`). LLM_CALL payloads embed the full message history inline in the ledger, so the file grows quadratically.
- **Full-state persistence per step.** Every transition and effect completion calls `run_store.save(run)`, which pretty-prints (`indent=2`) the entire vars — full transcript + scratchpad with duplicated tool outputs — with an atomic rename (`storage/json_files.py:107-131`). Roughly 4+ such dumps per iteration.
- **Fixed poll-alignment latency.** `GatewayRunner` polls at 0.25 s (`runner.py:69`); every wait→resume hop (each tool batch, each approval) waits on that cadence. The performance audit estimates ~300–750 ms of added alignment latency per exchange (an inference from the 250 ms interval, not a measurement).
- **Serial everything within a run.** Batched tool calls execute in a plain `for` loop (`tool_executor.py:321-369`) — no threads, no asyncio in the tool path. Built-in effect-tools are worse: one per `act`/`observe` round-trip, each with 2+ state saves. The only concurrency is *between* runs (4 tick workers).

### 5.1 The prompt-prefix cache is destroyed every iteration

Three independent audits converged on this as the highest-leverage fix. Even with caching enabled, these mutations guarantee ~0% prefix reuse:

1. **`Iteration: N/M` is the first line of the system prompt** (`logic/react.py:92`) — byte 0 changes every cycle.
2. **The per-cycle scratchpad is appended to the system prompt** (`react_runtime.py:913-915`).
3. **A fresh per-second timestamp is injected into `message[0]`**: `_normalize_turn_grounding` scans back to the last `user` message (in a tool loop, the task at index 0) and re-injects `<runtime_metadata>{"local_datetime":"…":seconds}</runtime_metadata>` on every call (`llm_client.py:715-726,806-823,926-940`). The contract line is cache-safe; the envelope's second-resolution entropy is not.
4. **The attachment index is prepended and rewritten**: `messages = injected + cleaned` (`effect_handlers.py:1476-1498`), and every `read_file` registers a new session attachment — so a coding agent reading files mutates the top of the conversation mid-session.
5. **Prompt caching is off by default**, three opt-in layers deep (`_runtime.prompt_cache` / `ABSTRACTGATEWAY_PROMPT_CACHE` / AbstractCode `/cache`), despite the derived-key plumbing, gateway routes, and Anthropic/OpenAI support all existing.

The fixes are surgical: move the iteration counter, scratchpad, and guidance to the **tail** of the message list; clamp grounding to minute resolution or a trailing message; append (don't prepend) the attachment index; flip caching on by default. This contradicts the framework's *own* `prompt_cache_key` machinery — a cache key that routes to a cache that can never hit on prefix.

---

## 6. Head-to-head with Codex CLI 0.89

| Dimension | Codex CLI 0.89 | AbstractFramework | Verdict |
|---|---|---|---|
| Inference streaming | Token-by-token SSE to UI | Aggregated to one dict (`llm_client.py:4725`) | Codex |
| Prompt caching | Prefix-stable by design; linear cost | Plumbing exists; defeated by per-call prefix mutation; off by default | Codex |
| Long-session survival | Auto-compaction at threshold (server-side, latent-preserving) | Manual compaction only; nothing auto-triggers; overflow → FAIL or silent truncation | Codex |
| Compaction provenance | Opaque `encrypted_content` | Artifact-backed, rehydratable spans; no summary-of-summary | **AbstractFramework** |
| Retrieval quality | Model + web search | Grep-grade for coding loops; spreading-activation engine unused there | Codex (for coding) |
| Planning | `update_plan` tool | None on ReAct; off-by-default prose plan in CodeAct | Codex |
| Verification before finishing | Plan/checks | Verifier exists in CodeAct only; `review_mode` dead on ReAct | Codex |
| Parallel tool calls | Yes, concurrent | Batched but executed serially | Codex |
| Subagents | Parallel exploration | Inline, synchronous, capped at 10 iters | Codex |
| Mid-run steering | "Keep typing while it works" | Local API only; no gateway `inject_guidance` command | Codex |
| Shell | `unified_exec` PTY sessions | One-shot `subprocess.run(shell=True)` | Codex |
| File edits | `apply_patch` (Lark grammar) | `edit_file` replace-all default; hand-rolled diff; **Python ast-refuse is better** | Mixed |
| Sandboxing | Seatbelt/Landlock/seccomp on the process tree | Regex blocklist + approval + path policy; no OS boundary | Codex |
| Project memory | `AGENTS.md` / team config | None in the product loops | Codex |
| Skills | `SKILL.md`, model- or user-invoked | Package exists; unwired | Codex |
| Weak/local model tool-calling | Native-only focus | Multi-format parser + arg recovery (`parser.py`, `tool_executor.py`) | **AbstractFramework** |
| Durable resume | Client-side transcript | Ledger-replayed; survives process death mid-tool-call | **AbstractFramework** |
| Human-in-the-loop | Approval prompts | Durable multi-day waits; cross-client reattach | **AbstractFramework** |
| Multi-scope / entity memory | None | run/session/global spans + a novel usage-weighted engine | **AbstractFramework** (unused by coding loops) |

**Reading of the table:** Codex is strictly better on the *coding-agent-in-the-moment* axes (streaming, caching, compaction, planning, verification, parallelism, shell, sandbox, project memory). AbstractFramework is strictly better on *durability, auditability, provenance, weak-model support, and long-horizon/entity memory* — axes Codex does not target. The tragedy in the middle is that the framework has *already built* Codex-class answers to several of its own gaps (auto-compaction in `BasicSession`, the retrieval-first entity chat loop, the prompt-cache control plane, the `review_mode` verifier) and simply has not wired them into the coding loops.

---

## 7. Consolidated improvement backlog (ranked)

The strongest signal is **convergence**: findings reached independently by two or more audits are listed first, because independent adversarial agents arriving at the same conclusion from different mandates is the best evidence available short of profiling.

### Tier 1 — Convergent, high impact

| # | Improvement | Impact | Effort | Found by |
|---|---|---|---|---|
| 1 | **Restore prompt-prefix stability + enable caching by default.** Move `Iteration:`, scratchpad, and guidance to the message tail; clamp/relocate the `<runtime_metadata>` timestamp; append (not prepend) the attachment index; default caching on. | Critical (cost + TTFT every iteration, every provider) | Low–Med | ReAct, Memory, Perf |
| 2 | **Wire automatic compaction into the interactive loop.** Connect the existing `estimated_tokens_used` + model context window to an automatic `MEMORY_COMPACT` trigger (the `BasicSession.auto_compact` prior art + ledger-safe spans already exist). | Critical (long-session survival) | Med | ReAct, Memory |
| 3 | **Stream LLM tokens to clients** through the progress-event/ledger path; persist only the final outcome. | High (perceived latency) | Med | ReAct, Perf |
| 4 | **Remove O(N²) ledger/history cost.** In-memory idempotency index per run; store LLM payloads by artifact reference instead of inline; drop `indent=2`; reference-based cross-run seeding instead of full-history copies. | High (long-run latency + storage) | Med | ReAct, Memory, Perf |
| 5 | **Parallelize read-only tool batches** (results already merge positionally); batch consecutive builtins. | High (N× on the dominant read/search batches) | Med | ReAct, Tools |

### Tier 2 — High impact, mostly single-audit

| # | Improvement | Impact | Effort | Found by |
|---|---|---|---|---|
| 6 | **Default `RetryPolicy` for LLM/tool effects** (idempotency already makes it safe). | High (transient failures stop killing runs) | Trivial | ReAct |
| 7 | **Make `max_in_tokens` a compaction trigger, not a truncation cap** (ADR-0026). Keep ReAct's drop-oldest disabled; when the budget is exceeded, fire `MEMORY_COMPACT` (compress-with-provenance) instead of clipping. Honor the pin literally only on one-shot `LLM Call` nodes and bounded sub-agents; document every use per ADR-0008/0026. | High (correctness without silent context loss) | Small–Med | Memory (reframed) |
| 8 | **Load `AGENTS.md`/project memory** into `_runtime.system_prompt_extra` at workspace root. | High (answer quality per token) | Small | Memory |
| 9 | **Wire the `abstractmemory` engine (or a `MEMORY_RECALL`-backed composer) into ReAct** + per-task episode formation; the MemAct composer proves the shape. | High (retrieval quality) | Med–Large | Memory |
| 10 | **Add gateway `inject_guidance` command** → `_runtime.inbox` (single-writer, race-free) for real mid-run steering. | High (steerability) | Low | ReAct |
| 11 | **Centralized schema-aware argument coercion** at dispatch (fix `use_regex="false"` truthiness class). | High (weak-model correctness/safety) | Low | Tools |
| 12 | **`edit_file` default `max_replacements=1`** + fail on ambiguous multi-match. | High (silent-corruption risk) | Low | Tools |

### Tier 3 — Structural / larger bets

| # | Improvement | Impact | Effort | Found by |
|---|---|---|---|---|
| 13 | **Persistent PTY shell session** (`unified_exec`-style: persistent cwd/env, `write_stdin`, background handles, incremental reads). | High (real-dev ergonomics) | High | Tools |
| 14 | **OS-level sandbox** for `execute_command`/`execute_python` (Seatbelt/Landlock+seccomp), per backlog 0062; make the blocklist defense-in-depth. Ship behind capability reporting so the gateway never advertises isolation it can't verify. | High (the only real safety boundary) | High | Tools |
| 15 | **Port the CodeAct verifier into ReAct** (behind the already-plumbed `review_mode`) or add a `finish(summary, evidence)` tool that runs it; add an `update_plan` tool. | High (completion quality on the flagship path) | Med | ReAct |
| 16 | **Typed context-overflow error + catch-compact-retry** in the LLM_CALL handler (mirror the existing output-truncation retry). | Med (reliability) | Small–Med | Memory |
| 17 | **Artifact-offload `execute_command` output**, symmetric with `read_file`; stop re-inlining text attachments per call. | Med (cost + ledger bloat) | Low | Tools, Memory |
| 18 | **Context-anchored, offset-tolerant diff application**; add JSON/YAML parse-refuse to extend the Python-only guard. | Med (edit reliability for weak models) | Med | Tools |
| 19 | **Keep assistant thought content in the transcript**; drop the redundant system-prompt scratchpad copy. | Med (multi-step coherence + fewer tokens) | Low | ReAct, Memory |
| 20 | **Async multi-child `delegate_agent`** with join (the runtime already supports `async+wait`); unify the four `max_iterations` defaults. | Med (long-horizon + parallel exploration) | Med | ReAct |

---

## 8. Honest caveats

- **No code was modified.** This is an assessment, not a change set.
- **Millisecond figures are inferences from code structure**, not profiler measurements. The 0.25 s poll math is exact from the code; JSON parse/write and ledger-scan costs scale with real run sizes that a read-only audit cannot measure. Before acting on speed items, profile a representative long session.
- **Two claims worth live-verifying** before investing: (1) whether Anthropic's top-level `cache_control` toggle actually yields cache hits (the Messages API expects block-level markers), and (2) how much the mtime run-cache softens the 4 Hz directory scans on a large runs directory.
- **The memory engine came out cleaner than expected**: its reads are SQL-bounded to the attention window and its writes are batched WAL transactions; its known 24/7 window-saturation issue is behavioral, not a latency tax on the chat path. The problem is *non-use in coding loops*, not engine cost.
- **The `AGENTS.md` "file lock + fsync" note is stale** relative to the current default JSONL store; worth reconciling in that file.

## 9. Bottom line

The agency substrate is genuinely differentiated where it chose to be: durable, replayable, auditable, weak-model-tolerant, and equipped with a memory engine and entity loop that have no Codex counterpart. It loses to Codex 0.89 on the coding-agent-in-the-moment axes for a specific and fixable reason — the flagship ReAct loop pays the full price of durability on every step, defeats provider caching by construction, ships with every context-management mechanism switched off, executes nothing in parallel within a run, cannot verify or plan on its default path, and cannot be steered once hosted.

The encouraging part: the two highest-impact fixes (prompt-prefix stability + caching on, and automatic compaction) are low-to-medium effort and reuse machinery that already exists in the codebase. The framework does not need to become Codex; it needs to connect the Codex-class parts it has already built to the loop that users actually run.
