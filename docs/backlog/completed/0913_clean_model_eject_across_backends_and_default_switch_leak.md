# 0913 — Clean model eject across backends, the default-switch leak, lock-aware ejects and honest memory figures

> Package: abstractcore (`providers/process_residency.py`, `hf_residency.py`, embeddings, server unload); abstractruntime (MultiLocal client, summarizer, claims); abstractgateway (console, tray, host state)
> Type: bug
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: memory, residency, eject, mlx, hf, gguf, embeddings, mission-wave-2026-09-25, unreleased

## Summary

Completed record for missions M1 and M2 of the 2026-09-25/26 wave and the gateway display work in G2
(committed locally, not released; release staged, waiting for the operator's go). Ejecting a model
now frees its memory on MLX, Hugging Face, GGUF and embeddings, from the gateway and from the core
server; switching the default model releases the previous one before the new one loads; an eject
never takes a model another client has locked; and the console and tray say what holds memory and on
what basis. A chat-latency regression found while proving the switch was traced to the workspace
deny list and fixed (see [0900](0900_chat_turn_latency_regression_in_switch_v3.md)).

## Why

Operator requests, as recorded by the orchestrator (`PLAN.md`): M1 "prove clean MLX eject with the
operator's MTP model, hermetic"; M2 "finish/verify HF, GGUF, embeddings eject; default-switch leak;
core server eject; commit the stalled agent's work". Follows the 2026-09-25 MLX eject leak (86 GB of
Metal held with no model loaded).

## What landed

- **Proof first** (M1, no code): with `Jundot/Qwen3.8-27B-oQ4e-mtp` on a hermetic gateway, eject
  took IOAccelerator 17.6 GB → 3 MB over two cycles with no growth (PASS). Found: switching the
  default left the old model resident (17.36 GB, pinned by the chat summarizer built at boot:
  `MLXProvider ← BasicSummarizer ← AbstractCoreChatSummarizer ← Runtime ← WorkflowBundleGatewayHost`);
  `ttl_s`/`keep_alive` silently ignored by MLX; the MTP drafter could not be exercised.
- **abstractcore**: process-wide HF/GGUF + embeddings residency with eject (`64a80ba`);
  `process_held_bytes` + `process_held_basis` + device fields (`fa940c0`); MLX load reports
  `ttl_s`/`keep_alive` as not applied (`cf8caae`); server `/acore/models/unload` and `unload_after`
  eject every in-process holder (`5b6e801`); owner/claims registry and `eject_unclaimed()` under
  both locks, server unload → 409 `model_locked` / `model_in_use` (`613e9e0`); embeddings drain
  in-flight encodes up to 30 s else refuse (`8694164`); CUDA basis `cuda_device_counter` (`88c4441`);
  docs `b965e09`, `3c6e5ea`, `a0f0377`.
- **abstractruntime**: the summarizer resolves the current default per call (`a5d0463`); eject on
  default switch, embedding rows, unload by `runtime_id` (`2319624`); the dropped model is ejected
  BEFORE the new default loads (`760fd70`); every MultiLocal client registers its pool/overrides/
  locks as claims, delayed eject re-checked under the lock, `pending_ejects` / `last_switch_ejects`
  diagnostics, `ttl_s` reported on every load path (`6969d17`, `6a86397`, `8596a23`); repair of the
  claims code reverted by a stale-tree commit (`46590e9`); an explicit eject respects other clients'
  locks unless `force` (`5518da3`) and holds the core residency lock across check and eject
  (`ceb04a3`).
- **abstractgateway**: M2 patch applied and memory shown with its basis and holders
  (`5ea67da`); tray shows basis, holders and pending/failed ejects (`4c84ab2`);
  `residency_diagnostics` in host state (`54a5cc0`).

## Completion report

- Hermetic proofs: `M2/evidence/switch-v2` and `switch-v3` — A ejected during the switch (peak
  14.1 GiB), eject B → IOAccelerator ~3 MB, MLX active 1,148 B; embeddings 269 MB → 0 → reload → 0;
  torch's Metal counter tracks MLX (+/−2 GiB) and GGUF (+3.59 GB, all returned).
  `E2E/REPORT.md` check 7: `models unload` freed 19.5 GB, IOAccelerator 3,408 KB after 5 s.
- Tests: runtime 2476 → 2615 passed / 26 skipped; core providers+embeddings+utils+server 2044 →
  2055 passed; 7 + 11 mutants red.
- Reviews: REVIEW/08 ACCEPT-WITH-FIXES (S1 the server's "still in use" guard was case- and
  alias-blind while the eject was not — an unload spelled differently ejected a LOCKED runtime,
  proven; S2 one client's switch ejected another client's locked model) → REVIEW/16 core ACCEPT,
  runtime **BLOCKING** (commit `079c0fc` from a stale tree had reverted the claims registry) →
  repaired `46590e9`; REVIEW/20 (a) ACCEPT `5518da3`.
- Latency regression (0900) discovered in `switch-v3` (33 s / 45 s vs 8.5 s / 6.5 s): not memory
  code; closed by the workspace fix recorded in 0910.
- Follow-ups: MLX idle/TTL unload does not exist → [0895](../proposed/0895_mlx_idle_ttl_unload.md);
  drafter eject unmeasured → [0896](../proposed/0896_verify_mtp_drafter_eject_on_a_host_with_the_companion.md);
  standalone Local clients do not register claims →
  [0897](../proposed/0897_standalone_local_llm_clients_register_residency_claims.md). Release: the
  runtime's abstractcore floor must include `613e9e0` and `8d59974` (STAGING).
- Process lesson: agents sharing `llm_client.py` must rebase, never commit from a stale tree; a guard
  test on `residency_claims` usage now exists.
- ADR state: none (ADR-0026 "no silent caps" applied: ignored options are reported).

## Receipts

- `untracked/missions-2026-09-25/M1/REPORT.md` (+ `M1/evidence/`), `M2/REPORT.md` (+ `M2/evidence/switch-v2`, `switch-v3`, `embeddings`), `G2/REPORT.md`, `E2E/REPORT.md` (check 7)
- `untracked/missions-2026-09-25/REVIEW/08-memory.md`, `16-memory-recheck-latency.md`, `20-recheck-eject-core-g2.md`
