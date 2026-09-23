#!/usr/bin/env python3
"""Live prompt-cache probe: MLX / GGUF / HF transformers (in-process backends).

Usage (from the monorepo root):
    .venv/bin/python scripts/cache_probe_local_backends.py            # all three lanes
    .venv/bin/python scripts/cache_probe_local_backends.py --only mlx # one lane

Model paths below point at local caches on this box (LM Studio dirs + HF hub);
adjust the `lanes` dict for other machines. Verified 2026-07-12, all three PASS:
  MLX  Llama-3.2-1B-4bit   : cold 3.5s -> warm 0.29s (x12, 12.7k-token prefix)
  GGUF Llama-3.2-1B-Q8     : cold 8.0s -> warm 0.33s (x24)
  HF   Qwen/Qwen3.5-4B bf16: cold 31.5s -> warm 1.28s (x24, 16.4k-token prefix;
       --hf-model Qwen/Qwen3.5-4B --hf-facts 700; thinking disabled in-probe)

Shape mirrors the ReAct lane: every call re-sends the full transcript via
`messages` with one shared `prompt_cache_key`. A LONG system prompt makes
prefill dominate so cache reuse is visible in wall time:

  call1  cold   (key, transcript T1)            -> full prefill
  call2  warm   (key, T1 + one more exchange)   -> should prefill ~only the tail
  call3  nokey  (same transcript as call2)      -> full prefill baseline

PASS = call2 clearly cheaper than call3 (same bytes, warm cache vs none)
       AND non-empty, coherent output on every call.
"""
import sys, time, json

sys.path.insert(0, "<workspace>/abstractcore")

from abstractcore import create_llm

def long_sys(n_facts: int) -> str:
    return (
        "You are a precise assistant. Answer in one short sentence. "
        + "Context ledger (verbatim, do not repeat): "
        + " ".join(f"fact_{i}: the sky over station {i} was clear at {i%24}:00;" for i in range(n_facts))
    )

BASE_MSGS = [
    {"role": "user", "content": "What is 2+2? Answer with the number only."},
    {"role": "assistant", "content": "4"},
]
TAIL_Q = "What is 3+5? Answer with the number only."


def probe(provider_id: str, model: str, n_facts: int = 700, **kw):
    print(f"\n=== {provider_id} :: {model} ===", flush=True)
    sys_prompt = long_sys(n_facts)
    t0 = time.time()
    llm = create_llm(provider_id, model=model, **kw)
    print(f"load: {time.time()-t0:.1f}s", flush=True)

    def call(msgs, key, label):
        t = time.time()
        # thinking=False: reasoning models would otherwise spend the whole
        # token budget inside <think> and return empty visible content.
        kwargs = {"messages": msgs, "system_prompt": sys_prompt, "max_tokens": 16,
                  "temperature": 0.0, "seed": 7, "thinking": False}
        if key:
            kwargs["prompt_cache_key"] = key
        r = llm.generate("", **kwargs)
        dt = time.time() - t
        content = (r.content or "").strip().replace("\n", " ")[:60]
        usage = r.usage or {}
        print(f"  {label:22s} {dt:7.2f}s  in={usage.get('input_tokens')} out={usage.get('output_tokens')}"
              f"  finish={r.finish_reason}  content={content!r}", flush=True)
        return dt, r

    key = f"probe-{provider_id}"
    t1, r1 = call(BASE_MSGS, key, "call1 cold (key A, T1)")
    msgs2 = BASE_MSGS + [{"role": "user", "content": TAIL_Q},
                         {"role": "assistant", "content": "8"},
                         {"role": "user", "content": "What is 10-3? Number only."}]
    t2, r2 = call(msgs2, key, "call2 warm (key A, T2)")
    # Honest baseline: SAME transcript T2 on a FRESH key — identical bytes,
    # identical decode at temperature 0; the only difference is the cold
    # prefill. (A no-key call is not a baseline: llama.cpp keeps internal
    # state, and decode-length differences would confound small models.)
    t3, r3 = call(msgs2, f"{key}-fresh", "call3 cold (key B, T2)")

    ok_output = all((r.content or "").strip() and r.finish_reason != "error" for r in (r1, r2, r3))
    # CONTENT correctness: the warm call must see the NEW context. Strongest
    # honest check: identical bytes at temperature 0 → warm output must match
    # the fresh-key cold output (call3). A stale-context cache answers the
    # PREVIOUS question and diverges. (Tiny models may answer 10-3 wrongly —
    # equally wrongly cold and warm; correctness of the CACHE is the match.)
    warm_correct = ("7" in (r2.content or "")) or ((r2.content or "").strip() == (r3.content or "").strip())
    # Two honest comparisons, either suffices (mechanisms differ per backend):
    # (a) warm T2 beats cold T1 on the SAME key (T2 is a superset of T1 — only
    #     possible if the prefix KV was reused);
    # (b) warm T2 beats the SAME BYTES cold on a fresh key (isolates prefill
    #     when decode lengths would otherwise confound, e.g. tiny HF models).
    # (llama.cpp keeps instance-internal eval state, so (b) under-measures
    # GGUF; (a) is its honest signal.)
    win_vs_own_cold = t2 < t1 * 0.6
    win_vs_fresh_cold = t2 < t3 * 0.6
    verdict = "PASS" if (ok_output and warm_correct and (win_vs_own_cold or win_vs_fresh_cold)) else "FAIL"
    print(f"  -> warm {t2:.2f}s | cold-T1(same key) {t1:.2f}s | cold-T2(fresh key) {t3:.2f}s"
          f"  outputs_ok={ok_output} warm_correct={warm_correct}  {verdict}", flush=True)

    # Backend internals, best-effort.
    try:
        stats = llm.get_prompt_cache_stats()
        meta = (stats.get("meta_by_key") or {}).get(key) or {}
        interesting = {k: v for k, v in meta.items() if k in ("fed_token_count", "token_count", "backend", "chat_format")}
        print(f"  key meta: {json.dumps(interesting)}", flush=True)
        assert "fed_token_ids" not in meta, "raw ids leaked into stats!"
    except Exception as e:
        print(f"  (stats unavailable: {e})", flush=True)
    try:
        tok = llm.prompt_cache_token_count(key)
        print(f"  cache token count: {tok}", flush=True)
    except Exception:
        pass
    return verdict


results = {}
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--only", default=None)
ap.add_argument("--hf-model", default="HuggingFaceTB/SmolLM2-135M-Instruct",
                help="transformers-lane model (HF id or local path)")
ap.add_argument("--hf-facts", type=int, default=350,
                help="ledger size for the transformers lane (sized to the model's window)")
args = ap.parse_args()

lanes = {
    "mlx": lambda: probe("mlx", "~/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit"),
    # max_tokens sizes the llama.cpp n_ctx allocation (KV window), which must
    # hold the ~12.7k-token probe transcript.
    "gguf": lambda: probe("huggingface", "~/.lmstudio/models/lmstudio-community/Llama-3.2-1B-Instruct-GGUF/Llama-3.2-1B-Instruct-Q8_0.gguf", max_tokens=16384),
    # Default SmolLM2 (window 8192 → 350 facts keeps the probe inside it);
    # override with --hf-model Qwen/Qwen3.5-4B --hf-facts 700 for a serious run.
    "hf": lambda: probe("huggingface", args.hf_model, n_facts=args.hf_facts),
}
for name, fn in lanes.items():
    if args.only and name != args.only:
        continue
    try:
        results[name] = fn()
    except Exception as e:
        import traceback; traceback.print_exc()
        results[name] = f"ERROR: {e}"

print("\n=== SUMMARY ===")
for k, v in results.items():
    print(f"  {k}: {v}")
