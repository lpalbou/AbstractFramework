# Agency-parity: executable BEFORE/AFTER evidence

> **INCIDENT ADDENDUM + METHODOLOGY CORRECTIONS (2026-07-09, after adversarial review of this
> directory).** Hours after these artifacts were produced, production failed anyway: a gateway
> assistant's FIRST message 400'd on OVH (`Qwen3.5-397B-A17B`) — "System message must be at the
> beginning." — triggered by the wave's tail-injected system-role attachment index. NOTHING in
> this directory covered that surface: every probe ran in-process (no gateway), with no session
> attachments, on the one OVH model whose template tolerates the shape. The adversarial review's
> verdict stands: this was a confirmatory instrument pointed at the fixed past. Corrections
> below are marked [CORRECTED]; the evidence protocol at the bottom is now binding for any
> "live-verified" claim in this track. The production-parity probe that would have caught the
> incident now exists: `ab_strict_model_attachment_probe.py`.

The maintainer's challenge (2026-07-09): "if you can't show me the reality / proofs that you did
better, then it's theoric and unverified and it's false." Fair. This directory holds executable
A/B proofs where the BEFORE arm is real old code (git HEAD — all wave changes are uncommitted
working-tree modifications, so HEAD is the genuine pre-wave state, runnable via git worktrees)
or the shipped feature flag. Every artifact here was produced by the scripts next to it; re-run
them to reproduce.

Setup for the old-world arms:

```bash
git -C abstractcore worktree add /tmp/proof_old_abstractcore HEAD
```

## 1. edit_file corruption + refusal + string-flag bug — deterministic, no LLM
Script: `ab_edit_file_and_coercion.py` · Artifacts: `ab_results_old.json`, `ab_results_new.json`

| Probe | OLD (git HEAD) | NEW (working tree) |
|---|---|---|
| Edit one value in a CRLF file | **whole file silently rewritten to LF** (`silently_rewritten_to_lf: true` — byte dump in the artifact) | CRLF preserved byte-for-byte |
| Unified diff deleting a `-- ` SQL comment | **refused**: "Invalid unified diff: missing '+++ ' header" (valid patch rejected) | applied; file correct |
| `preview_only="false"` (string, as prompted-format models send) through the registry dispatch | tool answered "Preview …" and **silently discarded the edit** — file unchanged while the agent believes it edited | coerced to real `False`; file actually edited |

## 2. Prompt-prefix cache — real OpenAI billing metadata (gpt-5-mini)
Script: `ab_cache_money_openai.py` · Artifacts: `ab_cache_openai_old.json`, `ab_cache_openai_new.json`
Same task, same model, same tools; the OLD arm reinstates git HEAD's exact prompt shape
(`Iteration: N/M` as the first system-prompt line, old `logic/react.py:91`).

| | OLD shape | NEW shape |
|---|---|---|
| Distinct system prompts across 5 calls | 5 (mutates every call) | 1 (byte-stable) |
| `cached_tokens` per call (OpenAI-reported) | 0, 0, 0, 0, 0 | 0, 2048, 2048, 2048, 2048 |
| Cached share of 13.2k input tokens | **0.0%** | **62.0%** |

The counter's ~6 bytes at position 0 destroyed 100% of cache reuse. This is provider billing
metadata, not our instrumentation.

## 3. Thought retention — OVH gpt-oss-120b, ledger request payloads
Script: `ab_thought_retention_ovh.py` · Artifacts: `ab_thought_old.json`, `ab_thought_new.json`
[CORRECTED — the original claim overstated the baseline] The OLD arm is a SIMPLIFIED
REPRODUCTION: it reinstates HEAD's `content=""` transcript storage but does NOT reinstate
HEAD's compensating channel — at real HEAD, the last 6 cycles' thoughts (600-char truncated)
were rendered into the system prompt via the scratchpad. So "the model could not re-read why"
is FALSE at real HEAD within a 4-cycle window; what this A/B actually shows is the CHANNEL
move (transcript vs mutating system prompt). HEAD's real deficits — thoughts lost beyond 6
cycles, 600-char truncation, double-carried tokens, and the cache destruction the scratchpad
caused (proven in §2) — are documented in 0212/0213, not proven by this table.

| | OLD (simplified: no transcript thoughts, no scratchpad) | NEW |
|---|---|---|
| Assistant tool-call msgs in final request | 4 | 4 |
| …carrying non-empty reasoning | 0 (all `""`) | 4 ("We need to read notes_a…", …) |

## 4. Verifier — same task, shipped flag off vs on (OVH gpt-oss-120b)
Script: `ab_verifier_ovh.py` · Artifacts: `ab_verifier_off.json`, `ab_verifier_on.json`
(git HEAD never read `review_mode`, so flag-off IS the old behavior.)

| | review OFF (old behavior) | review ON |
|---|---|---|
| Run status | COMPLETED | COMPLETED |
| Deliverable (`summary.txt`) on disk | **MISSING** — the run declared itself done without the required artifact; nothing caught it | **written** |
| Verifier verdicts | none (no verifier) | [CORRECTED] **6** `complete:false` verdicts (the README originally said 4 — miscounted against its own artifact) |

Nondeterminism note, honestly: the planted batching violation did not occur in either arm this
run; the off-arm instead failed differently (missing deliverable) — which the bare loop
accepted silently and the verifier arm did not. [CORRECTED — additional honesty from review]
The verdicts' `missing_head` names the read-cadence rule while `violation_batched_reads` is
false, and the artifact retains no per-cycle tool trace, so it cannot adjudicate which
requirement was genuinely unmet; and the run ended COMPLETED with all verdicts incomplete —
the round CAP ended review, the verifier never approved. What the arm-pair still supports:
review-off accepted a missing deliverable silently; review-on produced the deliverable. n=1,
one model — an existence demonstration, not a success-rate claim.

## Claims verified by true A/B elsewhere (not re-run here)
- Persistent shell vs one-shot `execute_command` (both arms live on OVH): one-shot arm claimed
  success while silently installing into the WRONG environment (the host venv — found and
  cleaned); persistent arm installed inside the task venv. Recorded in 0220.
- Parallel read-only tools: the same model-emitted 4-call batch replayed with the parallel path
  disabled vs enabled — 3.06s vs 1.46s median (2.09x). Recorded in 0214.
- Anthropic cache mapping old-vs-new request shape (live billing metadata): old top-level
  cache_control = full-prompt 1.25x WRITE every call, 0 reads; new head breakpoint = write 6302
  once, read 6302 after. Recorded in 0221.

## 5. Multi-turn agency — live 3-turn session on the current code (OVH gpt-oss-120b)
Script: `ab_multiturn_session_ovh.py` · Artifact: `ab_multiturn_result.json`
The maintainer's question: did the wave break turn-over-turn agency? Verified end-to-end:
turn 1 does tool work (writes a secret code to disk), turn 2 recalls it from session memory
alone ("4832" — no tools allowed), turn 3 asks the user mid-run (durable ASK_USER wait),
resumes with the answer, and combines the fresh answer with the turn-1 fact ("Your favorite
color is ultramarine and the code is 4832"). Transcript hygiene from durable state + the final
provider payload: zero [loop]-tail leakage, zero attachment-index leakage, zero orphaned
tool_call ids. `MULTI_TURN_AGENCY_OK: true`.

BONUS FIND (the check paid for itself): the hygiene probe exposed a PRE-EXISTING multi-turn bug
— `ask_user` leaves an unanswered assistant `tool_calls` turn in durable history (its answer is
a user message by design), and native OpenAI 400s the next request, FAILING the run. Reproduced
on git HEAD (same probe, same 400) — i.e. NOT introduced by this wave — and fixed in the
sanitizer (payload-boundary orphan repair; durable history untouched; cache-prefix stable).
Post-fix, the identical probe completes on native OpenAI. Regression-pinned in
`test_react_loop_context_transcript_levels.py::test_ask_user_orphaned_tool_calls_repaired_in_llm_payload`.

## 6. Production-parity probe (added post-incident): strict model + session attachment
Script: `ab_strict_model_attachment_probe.py` · Artifact: `ab_strict_model_attachment.json`
The run the review said should have existed: the REAL attachment-index injection path
(session attachment registered, LLM_CALL handler injects the tail index) against the strict
production model (OVH `Qwen3.5-397B-A17B`). Pre-fix shape reproduces the exact production 400;
current code must complete. This probe is now the regression gate for message-shape changes.

## Evidence protocol (binding for "live-verified" claims in this track)
1. Production-parity arm mandatory: full serving path, current production provider+model,
   first message AND resumed session, at least one session attachment.
2. Message-shape changes run a provider-template matrix: one strict OpenAI-compatible endpoint
   (OVH Qwen-class), one tolerant, native OpenAI, Anthropic. Template strictness is
   per-model-endpoint; a family is never assumed tolerant from one model.
3. Every KNOWN LIMITATION comment gets a live probe or an evidence entry the same day.
4. n >= 3 per arm on nondeterministic substrates; report all runs. Deterministic probes n=1 OK.
5. Baselines are real old code (worktree + world assertion); monkeypatch arms are labeled
   "simplified reproduction" and enumerate the HEAD behaviors NOT reinstated.
6. No vacuous hygiene checks: an "X does not leak" assertion runs where X exists.
7. Artifacts self-auditing: raw traces, model/endpoint/temperature/commit fingerprint; every
   README number re-derivable from a retained artifact.
8. Negative results and rewritten checks reported in their original form.
9. Cost claims state cadence assumptions (TTL, gaps, break-even).
10. "Live-verified" always carries its surface qualifier; unqualified = false.

## Claims NOT proven by A/B (honest labels)
- Output offload, LLM retry defaults, >50MB push-back: unit-tested behavior + git diff
  provenance; no live before/after run. The "before" is visible in `git diff` (offload absent;
  no RetryPolicy default), but no old-world live run was performed.
- "Quality improved overall" as a general statement: what is proven is the specific failure
  classes above (cache-destroying prompt shape, thought amnesia, silent CRLF corruption, valid
  patches refused, preview-and-discard edits, missing-deliverable completions). No end-to-end
  task-success-rate benchmark was run; that remains open (0218-era work would be the vehicle).
