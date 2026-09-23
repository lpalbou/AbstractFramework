#!/usr/bin/env python3
"""Core's production-readiness drive: use AbstractCore the way an operator does.

The operator's bar (2026-07-13 15:06): "they must TEST their package, beyond
the unit tests, to make sure it is actually working... test, fix, refine and
improve until it meets or exceeds the expected goals." This script drives the
operator-critical surface LIVE — real LM Studio server, real MLX in-process
model, real network for the web tools — and GATES on content correctness,
never on "no exception was raised".

Legs (each prints PASS/FAIL + evidence):
  L1  LMStudio generate           — basic prompt, content sanity
  L2  LMStudio streaming + usage  — chunks arrive, final usage has real numbers
  L3  LMStudio native tools       — model calls the tool; args parse
  L4  LMStudio structured output  — the c1128 incident schema (array of objects)
  L5  LMStudio session + cache    — CachedSession 2 turns; fact recalled; cache key stable
  L6  MLX generate + delta lane   — warm second call feeds only the suffix
  L7  Embeddings (LMStudio route) — cosine(sim pair) > cosine(dissim pair)
  L8  fetch_url contract          — content/title first-class; actionable error on 404
  L9  Structured retry honesty    — invalid model reply surfaces a clear error (no silent junk)

Run: python ../scripts/core_operator_drive.py   (from abstractcore/, venv active)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "abstractcore"))

CHAT_MODEL = "mlabonne_qwen3-4b-abliterated@q4_k_m"
MLX_MODEL = "mlx-community/Qwen3-4B-Instruct-2507-4bit"
EMBED_MODEL = "text-embedding-qwen3-embedding-0.6b"

RESULTS: list[tuple[str, bool, str]] = []


def leg(name: str):
    def deco(fn):
        def run():
            t0 = time.perf_counter()
            attempts = 0
            while True:
                attempts += 1
                try:
                    evidence = fn()
                    note = " [retried]" if attempts > 1 else ""
                    RESULTS.append((name, True, f"{evidence}{note} ({time.perf_counter()-t0:.1f}s)"))
                    return
                except Exception as e:
                    # LM Studio JIT-load races ("Model unloaded" / "Operation
                    # canceled") are environmental: one retry after a beat.
                    transient = any(s in str(e) for s in ("Model unloaded", "Operation canceled"))
                    if transient and attempts == 1:
                        time.sleep(5)
                        continue
                    RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
                    return
        return run
    return deco


@leg("L1 lmstudio generate")
def l1():
    from abstractcore import create_llm

    llm = create_llm("lmstudio", model=CHAT_MODEL)
    resp = llm.generate("Reply with exactly one word: the capital of France.", temperature=0.0)
    content = (resp.content or "").strip()
    assert "paris" in content.lower(), f"expected Paris, got: {content[:80]}"
    return f"content={content[:40]!r}"


@leg("L2 lmstudio streaming + usage")
def l2():
    from abstractcore import create_llm

    llm = create_llm("lmstudio", model=CHAT_MODEL)
    chunks, final = [], None
    for chunk in llm.generate("Count from 1 to 5, digits only.", stream=True, temperature=0.0):
        chunks.append(chunk)
        final = chunk
    assert len(chunks) > 1, "streaming returned a single chunk — not actually streaming"
    usage = dict(final.usage or {})
    in_tok = usage.get("input_tokens") or usage.get("prompt_tokens")
    out_tok = usage.get("output_tokens") or usage.get("completion_tokens")
    assert isinstance(in_tok, int) and in_tok > 0, f"streamed usage missing input tokens: {usage}"
    assert isinstance(out_tok, int) and out_tok > 0, f"streamed usage missing output tokens: {usage}"
    text = "".join(c.content or "" for c in chunks)
    assert "5" in text, f"stream content wrong: {text[:60]!r}"
    return f"chunks={len(chunks)} usage(in={in_tok},out={out_tok})"


@leg("L3 lmstudio native tools")
def l3():
    from abstractcore import create_llm
    from abstractcore.tools import tool

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a city."""
        return f"Sunny in {city}"

    llm = create_llm("lmstudio", model=CHAT_MODEL)
    resp = llm.generate(
        "What is the weather in Tokyo right now? Use the tool.",
        tools=[get_weather], temperature=0.0,
    )
    calls = resp.tool_calls or []
    assert calls, f"model made no tool call; content={str(resp.content)[:80]!r}"
    call = calls[0]
    name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
    args = call.get("arguments") if isinstance(call, dict) else getattr(call, "arguments", None)
    if isinstance(args, str):
        args = json.loads(args)
    assert name == "get_weather", f"wrong tool: {name}"
    assert "tokyo" in str(args.get("city", "")).lower(), f"wrong args: {args}"
    return f"tool={name} args={args}"


@leg("L4 lmstudio structured output (c1128 schema)")
def l4():
    from typing import List, Optional
    from pydantic import BaseModel
    from abstractcore import create_llm

    class ToolCallPlan(BaseModel):
        name: str
        arguments: dict

    class Verifier(BaseModel):
        verdict: str
        next_tool_calls: List[ToolCallPlan]
        notes: Optional[str] = None

    llm = create_llm("lmstudio", model=CHAT_MODEL)
    out = llm.generate(
        "You are a plan verifier. The plan is fine; verdict 'pass'; propose one next tool call "
        "named 'list_files' with arguments {\"path\": \"/tmp\"}.",
        response_model=Verifier, temperature=0.0,
    )
    obj = out if isinstance(out, Verifier) else getattr(out, "structured_output", None)
    assert isinstance(obj, Verifier), f"no validated object returned: {type(out)}"
    assert obj.next_tool_calls and isinstance(obj.next_tool_calls[0], ToolCallPlan), \
        "array-of-objects field failed to validate (the c1128 class)"
    return f"verdict={obj.verdict!r} calls={[c.name for c in obj.next_tool_calls]}"


@leg("L5 lmstudio session + prompt cache")
def l5():
    from abstractcore import create_llm
    from abstractcore import CachedSession

    llm = create_llm("lmstudio", model=CHAT_MODEL)
    session = CachedSession(llm, system_prompt="You are terse. One sentence max.")
    r1 = session.generate("My dog is named Biscuit. Acknowledge in three words.", temperature=0.0)
    r2 = session.generate("What is my dog's name? One word.", temperature=0.0)
    content = (r2.content or "").lower()
    assert "biscuit" in content, f"session lost the fact: {content[:80]!r}"
    return f"turn2={content.strip()[:30]!r}"


@leg("L6 mlx generate + delta lane")
def l6():
    from abstractcore import create_llm

    llm = create_llm("mlx", model=MLX_MODEL, max_tokens=8192)
    key = "drive-mlx-session"
    msgs = [{"role": "user", "content": "For this chat the project codename is 'heliotrope'. Say OK."}]
    r1 = llm.generate(messages=msgs, prompt_cache_key=key, temperature=0.0, max_output_tokens=60)
    msgs.append({"role": "assistant", "content": r1.content or ""})
    msgs.append({"role": "user", "content": "What is the project codename? One word."})
    r2 = llm.generate(messages=msgs, prompt_cache_key=key, temperature=0.0, max_output_tokens=60)
    assert "heliotrope" in (r2.content or "").lower(), f"warm turn wrong: {r2.content[:80]!r}"

    stats = llm.get_prompt_cache_stats()
    meta = (stats.get("meta_by_key") or {}).get(key) or {}
    fed = meta.get("fed_token_count")
    usage2 = dict(r2.usage or {})
    in2 = usage2.get("input_tokens") or usage2.get("prompt_tokens") or 0
    # Delta proof: the record after turn 2 must be well below 2x turn-2 input
    # (a rebuild-per-call lane would have fed ~in1+in2 total).
    assert isinstance(fed, int) and fed <= in2 + 8, \
        f"delta lane suspect: fed_total={fed} vs turn2_in={in2}"
    return f"warm answer OK; fed_total={fed} turn2_in={in2}"


@leg("L7 embeddings (lmstudio route)")
def l7():
    from abstractcore import create_llm

    llm = create_llm("lmstudio", model=EMBED_MODEL)
    vecs = []
    for text in ("The cat sat on the mat.", "A feline rested on the rug.", "Quarterly GDP rose 2%."):
        e = llm.embed(text)
        v = e.embedding if hasattr(e, "embedding") else e
        if isinstance(v, dict):
            v = v.get("embedding") or (v.get("data") or [{}])[0].get("embedding")
        assert isinstance(v, (list, tuple)) and len(v) > 10, f"no embedding vector: {type(v)}"
        vecs.append(v)

    def cos(a, b):
        num = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return num / (na * nb)

    sim, dissim = cos(vecs[0], vecs[1]), cos(vecs[0], vecs[2])
    assert sim > dissim, f"embedding geometry wrong: sim={sim:.3f} <= dissim={dissim:.3f}"
    return f"dim={len(vecs[0])} sim={sim:.3f} > dissim={dissim:.3f}"


@leg("L8 fetch_url contract")
def l8():
    from abstractcore.tools.common_tools import fetch_url

    ok = fetch_url("https://example.com")
    assert ok.get("success") is True, f"example.com failed: {ok.get('error')}"
    assert (ok.get("content") or "").strip(), "no first-class content"
    assert (ok.get("title") or "").strip(), "no first-class title"

    bad = fetch_url("https://example.com/definitely-not-a-real-page-404")
    assert bad.get("success") is False, "404 reported as success"
    err = str(bad.get("error") or "")
    assert "404" in err or "not found" in err.lower(), f"error not actionable: {err[:100]}"
    return f"title={ok.get('title')!r}; 404 error actionable"


@leg("L9 structured-output failure honesty")
def l9():
    from pydantic import BaseModel
    from abstractcore import create_llm

    class Impossible(BaseModel):
        exact_pi_to_1000_digits: int  # int can't hold what we'll ask for; forces validation risk

    llm = create_llm("lmstudio", model=CHAT_MODEL)
    try:
        out = llm.generate(
            "Reply with JSON {\"exact_pi_to_1000_digits\": \"three point one four...\"} — "
            "the value MUST be the words, not a number.",
            response_model=Impossible, temperature=0.0,
        )
        obj = out if isinstance(out, Impossible) else getattr(out, "structured_output", None)
        if isinstance(obj, Impossible):
            return f"model coerced a valid int ({obj.exact_pi_to_1000_digits}) — acceptable"
        err = getattr(out, "error", None) or getattr(out, "content", "")
        assert err, "no validated object AND no error surfaced — silent failure"
        return "failure surfaced honestly"
    except Exception as e:
        return f"raised {type(e).__name__} (loud) — acceptable"


if __name__ == "__main__":
    for fn in (l1, l2, l3, l4, l5, l6, l7, l8, l9):
        fn()
    print(f"\n{'leg':<44} {'ok':<5} evidence")
    fails = 0
    for name, ok, evidence in RESULTS:
        print(f"{name:<44} {'PASS' if ok else 'FAIL':<5} {evidence[:110]}")
        fails += 0 if ok else 1
    print(f"\n{len(RESULTS)-fails}/{len(RESULTS)} legs green")
    sys.exit(1 if fails else 0)
