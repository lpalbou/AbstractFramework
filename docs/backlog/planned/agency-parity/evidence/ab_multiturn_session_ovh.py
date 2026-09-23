"""Multi-turn agency verification on the CURRENT code (OVH gpt-oss-120b).

The maintainer's concern: did the agency-parity wave break turn-over-turn agency?
This exercises the full multi-turn surface in one live session:
  TURN 1: tool work establishes a fact (writes a file with a secret number).
  TURN 2: new turn, same session — "without reading any file, what was the number?"
          (only durable session memory can answer).
  TURN 3: a turn that must ask_user mid-run (durable WAIT), gets resumed with an answer,
          and must combine the turn-1 fact with the just-given answer.
Transcript hygiene asserted from durable state + final request payload:
  - no volatile [loop] tail leaked into durable history
  - no attachment-index message persisted into durable history
  - no orphan assistant tool_calls (every id has a matching tool result)
Writes ab_multiturn_result.json next to this script.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "<workspace>/abstractagent/src")

from abstractagent.agents.react import create_react_agent  # noqa: E402
from abstractcore.tools.common_tools import list_files, read_file, write_file  # noqa: E402
from abstractruntime import RunStatus  # noqa: E402

workdir = Path(tempfile.mkdtemp(prefix="mt_"))
agent = create_react_agent(
    provider="endpoint:ovh-provider", model="gpt-oss-120b",
    tools=[list_files, read_file, write_file],
    max_iterations=10, review_mode=False, session_id="mt-session-1",
)

def run_turn(task, answer_ask_user=None):
    run_id = agent.start(task)
    state = None
    for _ in range(120):
        state = agent.step()
        if state.status == RunStatus.WAITING and state.waiting is not None:
            if answer_ask_user is None:
                break
            state = agent.runtime.resume(
                workflow=agent.workflow, run_id=run_id,
                wait_key=state.waiting.wait_key,
                payload={"response": answer_ask_user}, max_steps=1,
            )
            continue
        if state.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            break
    out = state.output if isinstance(state.output, dict) else {}
    return run_id, state, str(out.get("answer") or "")

# TURN 1 — establish the fact via tools.
_, s1, a1 = run_turn(
    f"Work in {workdir}. Invent a 4-digit code, write it to {workdir}/code.txt using write_file, "
    "then finish by stating: 'The code is <code>.'"
)
code = "".join(ch for ch in (workdir / "code.txt").read_text() if ch.isdigit())[:4] if (workdir / "code.txt").exists() else ""

# TURN 2 — durable session memory, no tools allowed.
_, s2, a2 = run_turn(
    "WITHOUT calling any tool and without reading any file: what was the 4-digit code from "
    "earlier in this conversation? Answer with just the digits."
)

# TURN 3 — mid-run ask_user wait + combine turn-1 memory with the fresh answer.
rid3, s3, a3 = run_turn(
    "Use the ask_user tool to ask me for my favorite color (you MUST ask, do not guess). "
    "Then finish by stating the color AND the 4-digit code from earlier, together in one sentence.",
    answer_ask_user="ultramarine",
)

# ---- transcript hygiene from durable state ----
run3 = agent.runtime._run_store.load(rid3)
durable_msgs = ((run3.vars.get("context") or {}).get("messages") or [])
loop_leak = [m for m in durable_msgs if "[loop]" in str((m or {}).get("content") or "")]
attn_leak = [m for m in durable_msgs
             if str(((m or {}).get("metadata") or {}).get("kind") or "") == "attachment_index"]

# Orphan check on WHAT THE PROVIDER RECEIVES: the final llm_call payload from turn 3's ledger.
# (Durable history legitimately holds an unanswered ask_user tool_calls turn — its answer is a
# user message by design; the sanitizer synthesizes the adjacent tool result at the payload
# boundary, which is exactly what strict providers require. Found live 2026-07-09; pre-existing
# at git HEAD where the same probe 400s on native OpenAI.)
final_payload_msgs = []
for rec in agent.runtime._ledger_store.list(rid3):
    eff = rec.get("effect") or {}
    if str(eff.get("type") or "") == "llm_call" and rec.get("status") == "started":
        final_payload_msgs = (eff.get("payload") or {}).get("messages") or []

orphans = []
for idx, m in enumerate(final_payload_msgs):
    if isinstance(m, dict) and m.get("role") == "assistant" and m.get("tool_calls"):
        ids = {str(tc.get("id")) for tc in m["tool_calls"] if tc.get("id")}
        j = idx + 1
        while j < len(final_payload_msgs) and final_payload_msgs[j].get("role") == "tool":
            ids.discard(str(final_payload_msgs[j].get("tool_call_id") or ""))
            j += 1
        orphans.extend(sorted(ids))

result = {
    "turn1_status": str(s1.status), "code_on_disk": code, "turn1_answer_head": a1[:90],
    "turn2_status": str(s2.status), "turn2_answer": a2[:60],
    "turn2_recalled_code_from_session_memory": bool(code) and code in a2,
    "turn3_status": str(s3.status), "turn3_answer_head": a3[:140],
    "turn3_waited_and_resumed": "ultramarine" in a3.lower(),
    "turn3_combined_old_fact": bool(code) and code in a3,
    "durable_messages_total": len(durable_msgs),
    "hygiene_loop_tail_leaked": len(loop_leak),
    "hygiene_attachment_index_leaked": len(attn_leak),
    "hygiene_orphan_tool_call_ids": orphans,
    "MULTI_TURN_AGENCY_OK": (
        str(s2.status) == "RunStatus.COMPLETED" and bool(code) and code in a2
        and "ultramarine" in a3.lower() and code in a3
        and not loop_leak and not attn_leak and not orphans
    ),
}
out = Path(__file__).parent / "ab_multiturn_result.json"
out.write_text(json.dumps(result, indent=1))
print(json.dumps(result, indent=1))
print("WROTE", out)
shutil.rmtree(workdir, ignore_errors=True)
