"""Executable BEFORE/AFTER proof on real money: OpenAI cached_tokens with the OLD prompt shape
(iteration counter as the first line of the system prompt — verbatim from git HEAD
abstractagent/logic/react.py:91, `Iteration: {N}/{M}` prefix) vs the NEW byte-stable prefix.

  python ab_cache_money_openai.py old|new

Same task, same model (gpt-5-mini), same tools. Per-call usage.prompt_tokens_details.cached_tokens
comes from OpenAI's own billing metadata — not from our code.
Writes ab_cache_openai_<world>.json next to this script.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "<workspace>/abstractagent/src")

WORLD = sys.argv[1]

from abstractagent.logic.react import ReActLogic  # noqa: E402
from abstractagent.agents.react import create_react_agent  # noqa: E402
from abstractcore.tools.common_tools import list_files, read_file, write_file  # noqa: E402
from abstractruntime import RunStatus  # noqa: E402

if WORLD == "old":
    # Reproduce git-HEAD behavior exactly: the volatile counter as the FIRST bytes of the
    # system prompt (old react.py:91 began `Iteration: {iteration}/{max_iterations}\n\n`).
    _orig = ReActLogic.build_request

    def _old_style(self, *, task, messages, guidance="", iteration=1, max_iterations=10, vars=None):
        import dataclasses

        req = _orig(self, task=task, messages=messages, guidance=guidance,
                    iteration=iteration, max_iterations=max_iterations, vars=vars)
        return dataclasses.replace(
            req,
            system_prompt=f"Iteration: {int(iteration)}/{int(max_iterations)}\n\n" + (req.system_prompt or ""),
        )

    ReActLogic.build_request = _old_style

workdir = Path(tempfile.mkdtemp(prefix=f"cash_{WORLD}_"))
(workdir / "notes_a.txt").write_text("Fact A: the launch window opens Tuesday.\n" * 4)
(workdir / "notes_b.txt").write_text("Fact B: the payload weighs 412 kg.\n" * 4)
(workdir / "notes_c.txt").write_text("Fact C: the booster is reused from flight 7.\n" * 4)

agent = create_react_agent(
    provider="openai", model="gpt-5-mini",
    tools=[list_files, read_file, write_file],
    max_iterations=8, review_mode=False,
)
task = (
    f"Work in {workdir}. Read notes_a.txt, then notes_b.txt, then notes_c.txt — exactly ONE "
    "read_file call per response. Then write summary.txt combining the three facts and finish."
)

run_id = agent.start(task)
state = None
for _ in range(80):
    state = agent.step()
    if state.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
        break

calls = []
sys_prompts = set()
for rec in agent.runtime._ledger_store.list(run_id):
    eff = rec.get("effect") or {}
    if str(eff.get("type") or "") != "llm_call" or rec.get("status") != "completed":
        continue
    payload = eff.get("payload") or {}
    sys_prompts.add(str(payload.get("system_prompt") or ""))
    u = (rec.get("result") or {}).get("usage") or {}
    d = u.get("prompt_tokens_details") or {}
    calls.append({"prompt_tokens": u.get("prompt_tokens"), "cached_tokens": d.get("cached_tokens")})

total_in = sum(int(c["prompt_tokens"] or 0) for c in calls)
total_cached = sum(int(c["cached_tokens"] or 0) for c in calls)
result = {
    "world": WORLD,
    "status": str(state.status),
    "distinct_system_prompts_across_calls": len(sys_prompts),
    "system_prompt_first_line_example": sorted(sys_prompts)[0].split("\n", 1)[0][:60] if sys_prompts else "",
    "per_call": calls,
    "total_prompt_tokens": total_in,
    "total_cached_tokens": total_cached,
    "cached_pct": round(100 * total_cached / max(1, total_in), 1),
}
out = Path(__file__).parent / f"ab_cache_openai_{WORLD}.json"
out.write_text(json.dumps(result, indent=1))
print(json.dumps(result, indent=1))
print("WROTE", out)
shutil.rmtree(workdir, ignore_errors=True)
