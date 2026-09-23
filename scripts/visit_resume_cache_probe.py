#!/usr/bin/env python3
"""Core's step-1 co-sign-by-running: cache behavior through a durable visit resume.

The committed slot from plans/durable-visits-reincarnation.md §6 step 1 (core):
verify G-A live on the REAL visit workflow — kill the host mid-visit, resume in
a fresh process, and show that:
  1. the visit CONTINUES correctly from the durable transcript (not from KV) —
     the resumed entity answers a question whose answer only exists in a
     pre-kill turn;
  2. the resume pays exactly ONE honest cold prefill (fresh in-process MLX
     provider, cache of unknown composition -> full feed once);
  3. the delta lane RE-ENGAGES from that call on (the next turn feeds only the
     suffix — fed-token counts prove it).

Two phases, two real processes (a real SIGKILL between them, no cleanup):
  --phase a  : create scratch entity home -> open visit -> 2 turns (delta lane
               warms: turn 2 must already be a suffix feed) -> SIGKILL self.
  --phase b  : fresh process over the same home -> parked run found -> turn 3
               ("what is my cat's name?" — answer lives in turn 1) -> turn 4
               (delta re-engaged) -> close (reflection runs on the real model).

Instrumentation (written to <workdir>/probe_log.jsonl by the LLM handler):
per LLM_CALL: wall seconds, usage tokens, and core's prompt-cache stats
(fed_token_count per key — the honest meter for cold-vs-delta).

Run (from abstractcore/, venv with mlx installed):
  python ../scripts/visit_resume_cache_probe.py --phase a --workdir /tmp/visitprobe
  python ../scripts/visit_resume_cache_probe.py --phase b --workdir /tmp/visitprobe
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for pkg in ("abstractcore", "abstractruntime/src", "abstractmemory/src", "abstractgateway/src"):
    p = ROOT / pkg
    if p.is_dir():
        sys.path.insert(0, str(p))

MODEL = os.environ.get("VISIT_PROBE_MODEL", "mlx-community/Qwen3-4B-Instruct-2507-4bit")
CACHE_KEY = "visit-probe-session"


def log_path(workdir: Path) -> Path:
    return workdir / "probe_log.jsonl"


def append_log(workdir: Path, row: dict) -> None:
    with log_path(workdir).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


class MlxVisitLLM:
    """LLM_CALL handler backed by core's MLXProvider — the in-process lane
    whose KV genuinely DIES with this process (the G-A case; a server-side
    provider would survive the kill and prove nothing)."""

    def __init__(self, workdir: Path, phase: str) -> None:
        from abstractcore import create_llm

        self.workdir = workdir
        self.phase = phase
        self.call_n = 0
        t0 = time.perf_counter()
        self.llm = create_llm("mlx", model=MODEL, max_tokens=16384)
        append_log(workdir, {"phase": phase, "event": "provider_loaded",
                             "load_s": round(time.perf_counter() - t0, 2), "model": MODEL})

    def __call__(self, run, effect, dnn=None):
        from abstractruntime.core.runtime import EffectOutcome

        payload = dict(effect.payload or {})
        self.call_n += 1
        messages = payload.get("messages") or []
        system_prompt = payload.get("system_prompt")
        t0 = time.perf_counter()
        resp = self.llm.generate(
            messages=list(messages),
            system_prompt=system_prompt,
            prompt_cache_key=CACHE_KEY,
            max_output_tokens=300,
            temperature=0.0,
        )
        wall = time.perf_counter() - t0

        stats = {}
        try:
            raw = self.llm.get_prompt_cache_stats()
            for key, meta in (raw.get("meta_by_key") or {}).items():
                stats[key] = {
                    "fed_token_count": meta.get("fed_token_count"),
                    "model": meta.get("model"),
                }
        except Exception as e:  # instrumentation must never fail the visit
            stats = {"error": str(e)}

        usage = dict(resp.usage or {})
        append_log(self.workdir, {
            "phase": self.phase,
            "event": "llm_call",
            "call": self.call_n,
            "wall_s": round(wall, 3),
            "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens"),
            "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens"),
            "cache_stats": stats,
            "reply_head": (resp.content or "")[:110],
        })
        return EffectOutcome.completed({"content": resp.content or ""})


def make_home(workdir: Path) -> Path:
    import yaml
    from abstractmemory import (
        DEFAULT_SPARK_TEMPLATE, MemorySystem, SQLiteJournal, SQLiteTripleStore,
        engram, lint_spark,
    )

    home_dir = workdir / "entities" / "probeling"
    home_dir.mkdir(parents=True, exist_ok=True)
    entity_id = "entity:probeling@home-cacheprobe"
    spark = copy.deepcopy(dict(DEFAULT_SPARK_TEMPLATE))
    spark["name"] = "Probeling"
    assert lint_spark(spark) == []
    (home_dir / "spark.yaml").write_text(yaml.safe_dump(spark, sort_keys=False), encoding="utf-8")
    (home_dir / "manifest.json").write_text(json.dumps({"entity_id": entity_id}), encoding="utf-8")
    db = home_dir / "memory.sqlite3"
    store = SQLiteTripleStore(db)
    journal = SQLiteJournal(db)
    ms = MemorySystem(store=store, journal=journal)
    assert engram(ms, spark, owner_id=entity_id).created is True
    store.close()
    journal.close()
    return home_dir


def open_visit(home_dir: Path, workdir: Path, phase: str):
    from abstractruntime.core.models import EffectType
    from abstractruntime.identity.entity_runtime import open_entity_runtime
    from abstractruntime.identity.visit_workflow import build_visit_workflow

    llm = MlxVisitLLM(workdir, phase)
    ert = open_entity_runtime(home_dir, extra_handlers={EffectType.LLM_CALL: llm})
    wf = build_visit_workflow(
        ert.home,
        participants=["person:albou"],
        idle_seconds=3600,
        model_info={"provider": "mlx", "model": MODEL},
        visit_id="visit-cacheprobe",
    )
    return ert, wf


def phase_a(workdir: Path) -> None:
    from abstractruntime.core.models import RunStatus
    from abstractruntime.identity.visit_workflow import VISITOR_WAIT_KEY

    workdir.mkdir(parents=True, exist_ok=True)
    log = log_path(workdir)
    if log.exists():
        log.unlink()
    home_dir = make_home(workdir)
    ert, wf = open_visit(home_dir, workdir, "a")

    run_id = ert.runtime.start(workflow=wf, vars={}, session_id="visit-probe")
    state = ert.runtime.tick(workflow=wf, run_id=run_id, max_steps=80)
    assert state.status == RunStatus.WAITING, f"expected parked visit, got {state.status}"
    (workdir / "run_id.txt").write_text(run_id, encoding="utf-8")

    state = ert.runtime.resume(
        workflow=wf, run_id=run_id, wait_key=VISITOR_WAIT_KEY,
        payload={"text": "Hello! One fact to hold: my cat is named Tolstoy. Please acknowledge briefly.",
                 "speaker": "person:albou"},
        max_steps=200,
    )
    assert state.status == RunStatus.WAITING
    state = ert.runtime.resume(
        workflow=wf, run_id=run_id, wait_key=VISITOR_WAIT_KEY,
        payload={"text": "Thanks. In one short sentence: what do you value?", "speaker": "person:albou"},
        max_steps=200,
    )
    assert state.status == RunStatus.WAITING
    append_log(workdir, {"phase": "a", "event": "sigkill_self", "run_id": run_id})
    os.kill(os.getpid(), signal.SIGKILL)  # the host dies HERE — no close, no cleanup


def phase_b(workdir: Path) -> None:
    from abstractruntime.core.models import RunStatus
    from abstractruntime.identity.visit_workflow import VISITOR_WAIT_KEY

    home_dir = workdir / "entities" / "probeling"
    run_id = (workdir / "run_id.txt").read_text(encoding="utf-8").strip()
    ert, wf = open_visit(home_dir, workdir, "b")
    try:
        parked = ert.runtime.get_state(run_id)
        assert parked.status == RunStatus.WAITING, f"expected parked run post-kill, got {parked.status}"
        assert parked.waiting.wait_key == VISITOR_WAIT_KEY
        append_log(workdir, {"phase": "b", "event": "parked_run_found", "run_id": run_id})

        state = ert.runtime.resume(
            workflow=wf, run_id=run_id, wait_key=VISITOR_WAIT_KEY,
            payload={"text": "Quick check after the interruption: what is my cat's name?",
                     "speaker": "person:albou"},
            max_steps=200,
        )
        assert state.status == RunStatus.WAITING
        state = ert.runtime.resume(
            workflow=wf, run_id=run_id, wait_key=VISITOR_WAIT_KEY,
            payload={"text": "Good. One short sentence: what did we talk about?", "speaker": "person:albou"},
            max_steps=200,
        )
        assert state.status == RunStatus.WAITING
        state = ert.runtime.resume(
            workflow=wf, run_id=run_id, wait_key=VISITOR_WAIT_KEY,
            payload={"kind": "close"}, max_steps=300,
        )
        assert state.status == RunStatus.COMPLETED
        append_log(workdir, {"phase": "b", "event": "visit_closed",
                             "turns": state.output.get("turns"),
                             "close_reason": state.output.get("close_reason")})
    finally:
        ert.close()


def report(workdir: Path) -> None:
    rows = [json.loads(l) for l in log_path(workdir).read_text(encoding="utf-8").splitlines()]
    calls = [r for r in rows if r.get("event") == "llm_call"]
    print(f"\n{'phase':>5} {'call':>4} {'wall_s':>8} {'in_tok':>7} {'out_tok':>8}  {'fed_total':>9}  reply")
    for r in calls:
        fed = 0
        for _, m in (r.get("cache_stats") or {}).items():
            if isinstance(m, dict) and isinstance(m.get("fed_token_count"), int):
                fed = max(fed, m["fed_token_count"])
        print(f"{r['phase']:>5} {r['call']:>4} {r['wall_s']:>8.2f} {str(r.get('input_tokens')):>7} "
              f"{str(r.get('output_tokens')):>8}  {fed:>9}  {r.get('reply_head', '')[:80]}")
    tolstoy = [r for r in calls if r["phase"] == "b" and "tolstoy" in (r.get("reply_head") or "").lower()]
    print(f"\nDurable-transcript correctness: {'PASS — Tolstoy recalled post-kill' if tolstoy else 'CHECK reply texts'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["a", "b", "report"], required=True)
    ap.add_argument("--workdir", type=Path, required=True)
    args = ap.parse_args()
    if args.phase == "a":
        phase_a(args.workdir)
    elif args.phase == "b":
        phase_b(args.workdir)
    else:
        report(args.workdir)
