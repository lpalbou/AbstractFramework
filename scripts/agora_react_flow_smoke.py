#!/usr/bin/env python3
"""Live smoke of the agora ReAct workflow (abstractflow/examples/flows/agora-react-agent.json).

What it does (against the LOCAL agora hub + a local LLM):
1. Registers a `flow-react` agent on the hub (admin key from ~/.agora/config.json),
   storing its API key in ~/.agora/keys.json like the agora CLI does.
2. As the `runtime` agent: creates a demo channel, invites flow-react, posts an
   addressed `status=open` message (an obligation the flow agent owes an answer to).
3. Runs the workflow in-process (create_local_runtime + default tool map, which
   includes the agora toolset because AGORA_API_KEY is set for flow-react).
4. Prints the flow's final report and the channel tail so a human can verify the
   reply + ack actually landed on the hub.

Usage:
    python3 scripts/agora_react_flow_smoke.py [--provider lmstudio] [--model MODEL]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "abstractruntime" / "src"))

AGORA_CONFIG = Path.home() / ".agora" / "config.json"
AGORA_KEYS = Path.home() / ".agora" / "keys.json"
FLOW_PATH = REPO / "abstractflow" / "examples" / "flows" / "agora-react-agent.json"

AGENT_ID = "flow-react"
CHANNEL = "flow-react-demo"


def _http(method: str, url: str, token: str, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", **({"Content-Type": "application/json"} if data else {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        raise RuntimeError(f"{method} {url} -> HTTP {e.code}: {detail}") from e


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="lmstudio")
    parser.add_argument("--model", default="qwen3.5-4b")
    args = parser.parse_args()

    cfg = json.loads(AGORA_CONFIG.read_text())
    hub_url = cfg["url"].rstrip("/")
    admin_key = cfg["admin_key"]
    keys = json.loads(AGORA_KEYS.read_text()) if AGORA_KEYS.exists() else {}

    runtime_key = keys[f"{hub_url}::runtime"]

    # 1. Register (or reuse) the flow-react agent identity.
    key_slot = f"{hub_url}::{AGENT_ID}"
    if key_slot in keys:
        flow_key = keys[key_slot]
        print(f"[setup] reusing registered agent '{AGENT_ID}'")
    else:
        out = _http(
            "POST",
            f"{hub_url}/agents",
            admin_key,
            {
                "id": AGENT_ID,
                "name": "AbstractFlow ReAct agent",
                "about": (
                    "A hand-built VisualFlow ReAct agent (LLM + loop nodes). Wakes, triages its agora inbox "
                    "by priority, replies where an answer is owed, acks handled traffic. Owned by the flow agent."
                ),
            },
        )
        flow_key = out["api_key"]
        keys[key_slot] = flow_key
        AGORA_KEYS.write_text(json.dumps(keys, indent=1))
        print(f"[setup] registered agent '{AGENT_ID}' (key stored in {AGORA_KEYS})")

    # 2. Channel + obligation, as the runtime agent.
    try:
        _http("POST", f"{hub_url}/channels", runtime_key, {"name": CHANNEL, "private": True})
        print(f"[setup] created channel #{CHANNEL}")
    except RuntimeError as e:
        print(f"[setup] channel create: {e} (likely exists; continuing)")
    try:
        invite = _http("POST", f"{hub_url}/channels/{CHANNEL}/invites", runtime_key, {"agent_id": AGENT_ID})
        _http("POST", f"{hub_url}/channels/{CHANNEL}/join", flow_key, {"invite_token": invite["invite_token"]})
        print(f"[setup] {AGENT_ID} joined #{CHANNEL}")
    except RuntimeError as e:
        print(f"[setup] invite/join: {e} (likely already a member; continuing)")

    ask = _http(
        "POST",
        f"{hub_url}/channels/{CHANNEL}/messages",
        runtime_key,
        {
            "title": "smoke: confirm sight",
            "body": (
                "flow-react, this is the runtime agent. Please confirm you can see this message, "
                "and tell me which priority signals you used to decide it needed an answer."
            ),
            "status": "open",
            "urgency": "next_turn",
            "to": [AGENT_ID],
        },
    )
    print(f"[setup] posted open ask (id={ask['id']}, seq={ask['seq']})")

    # 3. Run the workflow as flow-react.
    os.environ["AGORA_URL"] = hub_url
    os.environ["AGORA_API_KEY"] = flow_key
    os.environ["ABSTRACT_ENABLE_AGORA_TOOLS"] = "1"

    from abstractruntime.integrations.abstractcore.default_tools import build_default_tool_map
    from abstractruntime.integrations.abstractcore.factory import create_local_runtime
    from abstractruntime.integrations.abstractcore.tool_executor import MappingToolExecutor
    from abstractruntime.visualflow_compiler import compile_visualflow

    spec = compile_visualflow(json.loads(FLOW_PATH.read_text()))
    runtime = create_local_runtime(
        provider=args.provider,
        model=args.model,
        tool_executor=MappingToolExecutor(build_default_tool_map()),
    )

    print(f"[run] starting flow with {args.provider}:{args.model} ...")
    run_id = runtime.start(workflow=spec, vars={"channel": CHANNEL, "max_iterations": 6})
    state = runtime.tick(workflow=spec, run_id=run_id)

    print(f"[run] status={state.status.value}")
    output = state.output if isinstance(state.output, dict) else {}
    print(f"[run] iterations={output.get('iterations')}")
    print("[run] final report:")
    print("      " + str(output.get("answer") or "").replace("\n", "\n      "))

    # 4. Verify on the hub, as the runtime agent.
    msgs = _http("GET", f"{hub_url}/channels/{CHANNEL}/messages?since={ask['seq']}&limit=20", runtime_key)
    print(f"[verify] channel tail after the ask ({len(msgs)} message(s)):")
    for m in msgs:
        print(f"  seq={m['seq']} sender={m['sender']} status={m['status']} reply_to={m.get('reply_to')}")
        print(f"    {m['body'][:300]}")

    replies = [m for m in msgs if m["sender"] == AGENT_ID]
    if replies:
        print("[verify] PASS: flow-react answered on the hub")
        return 0
    print("[verify] FAIL: no reply from flow-react in the channel")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
