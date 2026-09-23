"""Production-parity probe (added after the 2026-07-09 incident, per adversarial review):
the REAL attachment-index injection path against the STRICT production model.

A session attachment is registered exactly as the runtime does it (artifact tagged
kind=attachment under the session-memory owner run), so the LLM_CALL handler injects the tail
attachment-index message on every call — the shape that 400'd production on OVH
Qwen3.5-397B-A17B ("System message must be at the beginning."). Two arms in one run:
  raw:   provider normalization disabled at the transport -> must reproduce the incident 400
  fixed: current code -> the same first message must complete
Writes ab_strict_model_attachment.json. This is the regression gate for message-shape changes.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "<workspace>/abstractagent/src")

from abstractcore.providers.openai_compatible_provider import OpenAICompatibleProvider
from abstractagent.agents.react import create_react_agent
from abstractcore.tools.common_tools import read_file
from abstractruntime import RunStatus
from abstractruntime.integrations.abstractcore.session_attachments import (
    list_session_attachments,
    session_memory_owner_run_id,
)

MODEL = "Qwen3.5-397B-A17B"
SESSION = "strict-probe-session"

result = {"model": MODEL, "provider": "endpoint:ovh-provider"}


def _mk_agent():
    agent = create_react_agent(
        provider="endpoint:ovh-provider", model=MODEL,
        tools=[read_file], max_iterations=4, review_mode=False, session_id=SESSION,
    )
    # Register a session attachment the way the runtime does (kind=attachment under the
    # session-memory owner run) so the LLM_CALL handler injects the tail index.
    store = agent.runtime._artifact_store
    meta = store.store(
        content=b"quarterly report: all green\n",
        content_type="text/plain",
        run_id=session_memory_owner_run_id(SESSION),
        tags={"kind": "attachment", "filename": "report.txt", "path": "@report.txt", "source": "probe"},
    )
    entries = list_session_attachments(artifact_store=store, session_id=SESSION)
    result["attachment_registered"] = bool(entries)
    result["attachment_id"] = str(getattr(meta, "artifact_id", "") or "")
    return agent


def _run_first_message(agent):
    run_id = agent.start("Say READY. Do not call any tool.")
    state = None
    for _ in range(30):
        state = agent.step()
        if state.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            break
    out = state.output if isinstance(state.output, dict) else {}
    # Non-vacuous check: the attachment index must actually reach the PROVIDER request.
    # (The ledger's effect payload is recorded BEFORE handler injection, so we read the
    # provider-request echo captured in the completed result metadata; on the strict raw arm
    # the 400 itself is the proof the index was sent.)
    injected = False
    for rec in agent.runtime._ledger_store.list(run_id):
        eff = rec.get("effect") or {}
        if str(eff.get("type") or "") != "llm_call":
            continue
        md = (rec.get("result") or {}).get("metadata") or {}
        req = (md.get("_provider_request") or {}).get("payload") or {}
        for m in req.get("messages") or []:
            if "report.txt" in str(m.get("content") or ""):
                injected = True
    return str(state.status), str(state.error or "")[:200], str(out.get("answer") or "")[:60], injected


# ---- RAW arm: transport normalization disabled -> expect the incident 400 ----
# NOTE: restore must re-wrap in staticmethod — assigning the bare function back would turn it
# into an instance method (self passed as msgs) and silently break the fixed arm.
orig_fn = OpenAICompatibleProvider._normalize_system_messages_for_strict_servers
OpenAICompatibleProvider._normalize_system_messages_for_strict_servers = staticmethod(lambda msgs: msgs)
try:
    status, error, answer, injected = _run_first_message(_mk_agent())
    result["raw_arm"] = {
        "status": status, "error_head": error, "attachment_index_reached_provider": injected,
        "reproduced_incident_400": "System message must be at the beginning" in error,
    }
finally:
    OpenAICompatibleProvider._normalize_system_messages_for_strict_servers = staticmethod(orig_fn)

# ---- FIXED arm: current code -> must complete ----
status, error, answer, injected = _run_first_message(_mk_agent())
result["fixed_arm"] = {
    "status": status, "error_head": error, "answer_head": answer,
    "attachment_index_reached_provider": injected,
}
result["PRODUCTION_PARITY_OK"] = (
    result["raw_arm"]["reproduced_incident_400"]
    and result["fixed_arm"]["status"] == "RunStatus.COMPLETED"
    and result["fixed_arm"]["attachment_index_reached_provider"]
)

out_path = Path(__file__).parent / "ab_strict_model_attachment.json"
out_path.write_text(json.dumps(result, indent=1))
print(json.dumps(result, indent=1))
print("WROTE", out_path)
