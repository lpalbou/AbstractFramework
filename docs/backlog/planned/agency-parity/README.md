# Agency Parity backlog track

## Status
Planned (with one design-first item)

## Purpose
Close the highest-impact gaps between AbstractFramework's flagship ReAct agent loop and a
Codex-CLI-0.89-class coding harness, on both **quality** (task completion, self-correction,
retrieval) and **speed/cost** (prompt-prefix caching, parallel tools, context growth). The gaps
were found by four independent read-only adversarial audits (2026-07-07) and cross-checked against
the code; the synthesis lives in `docs/backlog/fable-opinions/agency_deep_dive_and_codex_comparison.md`.

The guiding constraint is ADR-0026: **never satisfy a budget by silent lossy truncation.** Every
item here either preserves full fidelity, or compresses/evicts *with provenance* and an explicit
marker. This track does not reintroduce drop-oldest truncation into the loop.

## Items
- `0212_react_prompt_prefix_cache_stability.md`: keep the ReAct request prefix byte-stable so
  provider prompt caching can hit (iteration counter, scratchpad, grounding envelope placement;
  default caching on). Builds on the research in `planned/130_react_scratchpad_prompt_flow_and_best_practice_review.md`.
- `0213_react_context_fidelity_thought_retention_dedup.md`: keep the model's own reasoning reachable
  across cycles, stop double-carrying observations, and tag every bounded preview per ADR-0026.
- `0214_parallel_readonly_tool_execution.md`: execute independent read-only tool calls concurrently
  instead of serially; keep side-effecting tools ordered.
- `0215_persistent_exec_session_and_output_offload.md`: add a persistent (PTY-backed) shell session
  alongside the one-shot `execute_command`, and artifact-offload large command output symmetrically
  with `read_file`.
- `0216_edit_file_safety_and_patch_robustness.md`: default `edit_file` to a single replacement, fail
  on ambiguous matches, make unified-diff application context-anchored and offset-tolerant, and
  extend the pre-write parse-refuse guard beyond Python.
- `0217_react_verifier_plan_steering_and_retry.md`: wire the existing CodeAct verifier + an
  `update_plan` tool into ReAct, add a gateway `inject_guidance` command for mid-run steering, and
  default a `RetryPolicy` for LLM/tool effects.
- `0218_interactive_context_budget_survival.md`: (design-first) survive long sessions without lossy
  compaction — typed context-overflow error + catch/evict-to-artifact retry + Ollama `num_ctx`.
- `0219_react_retrieval_and_project_memory.md`: (backlog only, work is owned elsewhere) give the
  coding loop retrieval-first context and load repo `AGENTS.md` project memory.
- `0222_mid_loop_steering_and_soft_interrupt.md`: TOP PRIORITY (maintainer ruling 2026-07-08) —
  type into a running agent loop + redirect/stop without terminal cancel. Design converged after
  2 adversarial reviews + a verified Codex 1:1 (adopt drain gate/CAS steer/ack lifecycle; durable
  sidecar beats Codex on crash safety). Implementation gated on a runtime/gateway seam handshake
  (agora commons seq 82); wave 1 (kernel DirectiveStore + local API, collision-free) unblocked.
- `0221_unified_prompt_caching_strategy.md`: WAVE 1 DONE (2026-07-08, live-falsified) — the
  Anthropic top-level `cache_control` mapping paid the full-prompt write premium every call with
  zero reads; replaced with an explicit breakpoint on the system head (write→read live-verified)
  + normalized `cached_input_tokens`/`cache_write_tokens` usage keys across providers. Mechanism
  knowledge lives on provider classes; the registry gets tuning values only; endpoint quirks
  (OVH field rejection) live in endpoint profiles/learned markers. Waves 2-3 planned.
- `0220_persistent_shell_tool_exposure.md`: DONE (2026-07-08) — `shell_exec`/`shell_write_stdin`/
  `shell_close` shipped opt-in (`ABSTRACT_ENABLE_SHELL_TOOLS=1`, not in default toolsets),
  approval-gated, run-id-namespaced at the handler trust boundary, terminal-hook teardown (incl.
  cancel), honestly labeled non-durable. Live-verified on OVH `gpt-oss-120b` (venv workflow;
  one-shot arm of the A/B silently polluted the wrong environment — the exact class this closes).
  Inherits the 0062 OS sandbox when it lands (maintainer ruling 2026-07-08).

Related existing item (not renumbered): `planned/039_tool_argument_type_coercion.md` — centralized
schema-aware argument coercion. It is part of this track's implementation wave.

## Reading order
0212 and 0213 first (shared file `react_runtime.py`, implement together to avoid churn), then 0214,
0215, 0216, 039 in parallel (disjoint files), then 0217 (re-enters `react_runtime.py`), then 0218
and 0219 as design/planning.

## Governing ADRs
- ADR-0026 (truncation policy) — the binding constraint for the whole track.
- ADR-0008 (token terminology) — `max_tokens`/`max_output_tokens`/`max_input_tokens` semantics.
- ADR-0002 (effect system), ADR-0006 (durable tool execution), ADR-0016 (tool-calling pipeline).
- ADR-0007/0009 (active context vs stored memory; provenance) — for 0218/0219.

## Scope
ReAct loop prompt assembly, tool execution path, tool implementations, gateway run controls, and
the abstractcore provider/tooling touched by the above. Prove quality/speed deltas with A/B runs.

## Non-goals
- No drop-oldest truncation in reasoning loops (ADR-0026).
- No change to the durable-effect/ledger contract or the entity-memory engine.
- 0218/0219 are not implementation commitments in this wave.

## Notes for future agents
Baseline and after numbers must be produced against the local OpenAI-compatible endpoint
`http://127.0.0.1:8317/v1` (model `gpt-5.4-mini`, reasoning enabled) so speed/usage claims are
evidence, not inference. Do not edit files outside your item's ownership without coordinating —
several items sit in the same hot files (`react_runtime.py`, `common_tools.py`).

## Live evidence (2026-07-08, maintainer-requested)

Endpoint-based proofs for the implemented wave, run against OVH `gpt-oss-120b` (primary) and
OpenAI `gpt-5-mini` (one cheap run for provider-side cache metrics). Ledger `llm_call` payloads
are the ground truth for what was sent.

- **0212 prefix stability**: 12-call ReAct run — ONE distinct system prompt across all calls
  (2,155 bytes, no `Iteration:` counter); after classifying the deliberate volatile tail
  ([loop] message, attachment index, grounding envelope), every request's stable message list is
  an EXACT prefix of the next (12/12); per-call prefix reuse 85–100%.
- **0212 real cache hits (OpenAI gpt-5-mini)**: `usage.prompt_tokens_details.cached_tokens` =
  2048 on every call from iteration 2 onward; **60.9% of total input tokens served from cache**
  (8,192 of 13,455) in a 4-iteration run. Prefix stability converts to actual provider cache
  hits.
- **0213 thought retention**: the final request's transcript carried ALL 5 assistant tool-call
  messages with non-empty reasoning content ("We need to read notes_a.txt…"), matching the
  model's per-cycle thinking (gpt-oss surfaces it via the reasoning channel; previously these
  were stored as `content=""`).
- **0214 parallel read-only tools**: the model emitted a real 4-call `skim_url` batch in one
  response; replaying that exact batch through `MappingToolExecutor`: median 3.06 s serial vs
  1.46 s parallel — **2.09× speedup** (live batch act→observe: 1.45 s, matching parallel).
- **0216 edit_file live traps**: ambiguous pattern targeted correctly (only `secondary()`
  changed), CRLF file stayed CRLF byte-for-byte after edit, and a unified diff with header line
  numbers off by 10 applied via context anchoring — 3/3 correct, 29.5k in / 2.1k out tokens.
- **0217 verifier live catch**: `review` ran on the flagship path and returned a real structured
  verdict — `{"complete": false, "missing": ["The three read_file calls must be made in three
  separate responses…"]}` — catching an instruction violation and forcing another round;
  `update_plan` persisted to scratchpad and rendered in the [plan] tail.
- **Not live-tested**: `inject_guidance` (gateway runner machinery; covered by unit tests) and
  the 0218/0219 design items.

## Adversarial verification outcomes (2026-07-08)

Four read-only adversarial verifiers reviewed the wave. Findings and dispositions:

FIXED (with regression tests):
- **0217b verifier-forced tool calls orphaned the transcript (run-killer on strict OpenAI-compatible
  providers, review_mode on by default)** → `review_parse_node` now synthesizes the preceding
  assistant tool-calls message with matching call_ids before entering `act`; a final-transcript
  orphan scan guards it.
- **0217b `update_plan` was never advertised to the model (dead in production)** → added
  `UPDATE_PLAN_TOOL` and prepended it to `ReactAgent`'s builtin schemas; regression test asserts it
  is advertised.
- **0217b `review_count` never reset (verification budget was run-lifetime, not per-answer)** →
  reset in `observe_node` after tools execute, mirroring CodeAct.
- **0217b nudge re-review was a no-op that leaked to the main model** → removed; incomplete-without-
  tools now steers via next_prompt or accepts, no idempotency-blocked re-review.
- **0217b unbounded plan tail render** → capped at 4000 chars with a truncation marker (full plan
  stays durable in scratchpad).
- **039 registry retry path skipped coercion** → the `except TypeError` retry branch now coerces
  like the happy path; `preview_only="false"` can no longer arrive truthy on that path.
- **0214 `_build_result` raised on non-dict batch entries** → now returns an error result (honors
  the never-raises contract).
- **0217c `inject_guidance` could resurrect a COMPLETED run (sqlite backend)** → terminal-status
  guard + re-check before save; a stale RUNNING snapshot can never overwrite a terminal state. A
  narrow best-effort loss window remains (documented); the full single-writer routing is a follow-up.
- **0217a remote path had NO retries** → `create_remote_runtime` now defaults `RetryPolicy` like the
  local factory.
- **0215 shell engine**: close() now process-group-kills (no orphaned/zombie children); reader uses
  `errors="replace"` (binary output no longer wedges the session); unterminated final output is
  preserved (no silent loss); post-timeout stale output is drained on the next call.

DEFERRED (documented; not fixed this pass):
- ~~**0212 attachment index dropped on native OpenAI/Anthropic**~~ FIXED for the two NATIVE
  providers (OpenAI passes system messages through at position; Anthropic merges a leading run
  and wraps non-leading ones in `<system_instruction>` user turns, tool-adjacency preserved) —
  pinned by `test_mid_stream_system_messages_unit.py` (11 tests: 4 native-OpenAI, 5
  native-Anthropic, 2 BasicSession) + `test_server_system_message_passthrough.py` (stub role
  fidelity). **CORRECTION (2026-07-09 incident): the earlier "delivered on all providers" claim
  was an overclaim — those 11 tests contained ZERO openai_compatible/vLLM coverage, and
  "delivered" (survives the provider layer) had been silently substituted for "accepted" (server
  takes the request). OVH's Qwen template hard-rejects non-leading system messages and a
  production first message 400'd on exactly the tail attachment index.** Now fixed at the
  openai_compatible transport (leading-run merge + `<system_instruction>` wrapping, deferred past
  tool runs) and pinned INCLUDING the wire path
  (`test_openai_compatible_strict_system_messages.py`, 7 tests, one driving real `generate()` to
  the HTTP boundary) + the production-parity probe
  (`evidence/ab_strict_model_attachment_probe.py`, raw arm reproduces the incident 400 on
  Qwen3.5-397B, fixed arm completes).
- ~~**0215 stdin-consuming commands** desync the sentinel-over-stdin boundary~~ **FIXED**: the
  engine was rewritten on a PTY transport (sentinel over the PTY line, no stdin collision); `cat`,
  `set -x`, and binary output are covered by tests. Exposure as an agent tool is now its own item
  (**0220**) per maintainer ruling. Offload follow-up also resolved 2026-07-08: stdout+stderr on
  any exit code + any tool's large string output; 50 MB retention cap with an explicit >cap
  push-back notice (never silent).
- ~~**0216 edit_file CRLF files silently rewritten to LF** and **`-- `-prefixed deletion lines
  misparse**~~ **FIXED 2026-07-08** (maintainer-directed): line endings preserved end-to-end
  (dominant-style restore at the write boundary, mixed-endings note), and the diff hunk collector
  count-arbitrates the `--- ` prefix collision (multi-file diffs still refused). 12 new tests;
  68-test edit_file corpus green.
- **0217a retry backoff blocks a tick worker** [CORRECTED per Critic-4 audit 2026-07-09: the
  earlier 6h estimate undercounted by 3x]: there are TWO stacked retry loops — the runtime's
  RetryPolicy (3 attempts) wraps abstractcore's per-provider internal RetryManager (up to 3
  attempts on timeout/network/rate-limit) — so a hung provider can bind a tick worker for up to
  9 x 7200s ≈ **18 hours**, with uninterruptible backoff sleeps and no cancel preemption.
  2026-07-09 mitigations shipped: deterministic 4xx now fail once (EffectOutcome.retryable +
  status-code-first classifier; 408/409/425/429 stay transient), truncation exhaustion and
  structured-repair failures are non-retryable (killed the x9/x6 self-inflicted burns), and the
  user-facing agent-failure answer is now a human sentence instead of raw provider JSON.
  REMAINING (open): collapse the double retry stack (single-attempt provider retry_config when
  constructed for runtime use), attach status_code at the native-OpenAI/Anthropic/remote-client
  wrap sites (openai native streaming still stringifies the type away), cancellable backoff, and
  attempt-aware UI rendering (one turn's 3 retries currently render as 3 identical error
  banners; ledger records per attempt are correct, the Flow mapper is attempt-blind).
- **`RetryPolicy()` bare default is `tool_max_attempts=2`** (only the factory's explicit `=1` keeps
  tools non-retried); direct constructors should pass `tool_max_attempts=1`.

## 2026-07-09 five-critic adversarial wave (post-incident audit) — verdicts + shipped fixes

Five independent read-only critics audited the whole agency-parity wave after the OVH incident.
Convergent verdict: the incident fix itself is correct at the right layer; the failures were
**testing-scope gaps and overclaimed language**, not wrong designs. Shipped same-night:

- **Loop-tail adjacency guard** (Critic-3 #1): the volatile `[loop]`/plan/guidance tail now MERGES
  into a trailing user message when one ends the payload (first turn, post-ask_user turns) —
  removes the `user,user` shape that alternation-strict templates (Mistral/Gemma-class) 400 on,
  and puts the grounding envelope back onto the real task message. Tool-loop turns unchanged.
  Trade: iteration-1 task message is not prefix-reusable into iteration 2 (one message, once).
- **Recovered-reasoning fallback: Critic-3's cap proposal REJECTED (ADR-0026)** — a same-night
  1200-char cap was reverted as a maintainer-caught ADR violation. The recovered reasoning is
  the model's own thought and is model-facing context; slicing it is forbidden regardless of
  markers. The real pathological case (generation cut mid-reasoning by an output cap) never
  reaches the transcript: `parse_node` retries `finish_reason in {"length","max_tokens"}` turns
  without appending, and ReAct disables output caps by default. Growth from faithful retention
  is the designed fidelity trade — mitigated by 0212 prefix caching and explicit user-opted
  compaction, never silent truncation. Critic-3's residual concern (reasoning-prose imitation
  pressure) stands recorded as an observation, not a license to truncate.
- **`review_mode` default → opt-in** (Critic-3 #3): the verifier is live-proven but a
  verifier-side deterministic 400 fails a run already holding a valid answer, and forced tool
  calls bypass the duplicate-side-effect guard. Opt-in until review failures degrade to
  accept-with-`#FALLBACK`. (`review_mode=True` was dead config at HEAD; 0217 made it live.)
- **Orphan-repair honesty guard** (Critic-1 + Critic-3): "handled interactively" is now claimed
  ONLY for interactive builtins (`ask_user`); other unanswered ids get
  `[tool result missing (host error): <name>]` so real tool-result loss stays observable; orphan
  TOOL messages (history cuts) fold to an inert user note instead of 400ing strict servers.
- **Normalizer hardening** (Critic-1): content-part lists text-extracted (never Python reprs);
  all-empty leading system run emits nothing; async path gained the sync "no user message"
  fallback. 9 tests pin the strict-server contract.

OPEN (recorded, not yet built):
- **Wire-shape validator** (Critic-1's structural fix, endorsed by Critic-3): a per-template
  request-shape contract (roles/adjacency/ordering) checked at the provider boundary, so template
  strictness differences are caught by construction instead of per-incident. Candidate for 0221
  wave 2 or its own item.
- **Verifier failure containment**: degrade review-LLM failures to accept-with-`#FALLBACK`
  (unblocks re-defaulting `review_mode=True`); route verifier-forced calls through the parse-node
  duplicate-side-effect guard.
- **Family misconfig** (Critic-1 F2): a strict vLLM server configured as native `openai` provider
  bypasses the compatible-layer normalization and can resurrect the 400; native providers could
  normalize when `base_url` is non-OpenAI. Recorded, heuristic — needs a ruling.
- Critic-2/4/5 items already folded in above (overclaim corrections, retry-stack collapse plan,
  evidence-protocol rules) — see the CORRECTION markers through this README and the evidence
  README's binding protocol.
