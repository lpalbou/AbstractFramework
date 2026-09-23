"""Executable BEFORE/AFTER proof: thought retention in the transcript (OVH gpt-oss-120b).

OLD (git HEAD react_runtime.py:1054-1060): assistant tool-call turns were stored with
content="" ("thought is stored in scratchpad") — by iteration N the model could not re-read
WHY it chose an approach earlier. NEW: the reasoning rides the transcript message.

  python ab_thought_retention_ovh.py old|new

The proof artifact is the FINAL LLM request payload from the run ledger: how many assistant
tool-call messages carry non-empty reasoning content. Writes ab_thought_<world>.json.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "<workspace>/abstractagent/src")

WORLD = sys.argv[1]

from abstractagent.adapters import react_runtime as rr  # noqa: E402
from abstractagent.agents.react import create_react_agent  # noqa: E402
from abstractcore.tools.common_tools import list_files, read_file, write_file  # noqa: E402
from abstractruntime import RunStatus  # noqa: E402

if WORLD == "old":
    # Reproduce git-HEAD behavior exactly: content="" on assistant tool-call messages.
    _orig = rr._new_assistant_message_with_tool_calls

    def _old_style(ctx, *, content, tool_calls, metadata=None):
        return _orig(ctx, content="", tool_calls=tool_calls, metadata=metadata)

    rr._new_assistant_message_with_tool_calls = _old_style

workdir = Path(tempfile.mkdtemp(prefix=f"thought_{WORLD}_"))
(workdir / "notes_a.txt").write_text("Fact A: the launch window opens Tuesday.\n")
(workdir / "notes_b.txt").write_text("Fact B: the payload weighs 412 kg.\n")
(workdir / "notes_c.txt").write_text("Fact C: the booster is reused from flight 7.\n")

agent = create_react_agent(
    provider="endpoint:ovh-provider", model="gpt-oss-120b",
    tools=[list_files, read_file, write_file],
    max_iterations=10, review_mode=False,
)
task = (
    f"Work in {workdir}. Read notes_a.txt, then notes_b.txt, then notes_c.txt (one read_file "
    "per response), then write summary.txt combining the three facts, then finish."
)

run_id = agent.start(task)
state = None
for _ in range(100):
    state = agent.step()
    if state.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
        break

reason_payloads = []
for rec in agent.runtime._ledger_store.list(run_id):
    eff = rec.get("effect") or {}
    if str(eff.get("type") or "") == "llm_call" and rec.get("node_id") == "reason" and rec.get("status") == "started":
        reason_payloads.append(eff.get("payload") or {})

final_msgs = (reason_payloads[-1].get("messages") or []) if reason_payloads else []
tc_msgs = [m for m in final_msgs if isinstance(m, dict) and m.get("role") == "assistant" and m.get("tool_calls")]
with_thought = [m for m in tc_msgs if str(m.get("content") or "").strip()]

result = {
    "world": WORLD,
    "status": str(state.status),
    "llm_calls": len(reason_payloads),
    "final_request_assistant_toolcall_msgs": len(tc_msgs),
    "with_nonempty_reasoning_content": len(with_thought),
    "example_thoughts": [str(m.get("content") or "")[:90] for m in tc_msgs[:4]],
    "task_done": (workdir / "summary.txt").exists(),
}
out = Path(__file__).parent / f"ab_thought_{WORLD}.json"
out.write_text(json.dumps(result, indent=1))
print(json.dumps(result, indent=1))
print("WROTE", out)
shutil.rmtree(workdir, ignore_errors=True)
