#!/usr/bin/env python3
"""Live smoke of the generic event-inbox resident agent.

Runs the REAL GatewayRunner loop (command store + runner thread) with a real
local LLM, then plays "producers" posting emit_event commands with durable=true:

1. start the resident flow (parks on the open channel `evt:global:global:<mailbox>`)
2. post a work event  -> resident wakes, bursts (real LLM + note tool)
3. post a second event WHILE the burst is running -> interleaves into the next cycle
4. post {kind: stop}  -> resident reports and ends

Usage:
    python3 scripts/event_inbox_flow_smoke.py [--provider lmstudio] [--model qwen3.5-4b]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "abstractruntime" / "src"))
sys.path.insert(0, str(REPO / "abstractcore"))
sys.path.insert(0, str(REPO / "abstractgateway" / "src"))

FLOW_PATH = REPO / "abstractflow" / "examples" / "flows" / "event-inbox-react-agent.json"
MAILBOX = "smoke-room"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="lmstudio")
    parser.add_argument("--model", default="qwen3.5-4b")
    args = parser.parse_args()

    from dataclasses import dataclass
    from typing import Any, Dict

    from abstractgateway.runner import GatewayRunner
    from abstractruntime.core.models import RunStatus
    from abstractruntime.integrations.abstractcore.default_tools import build_default_tool_map
    from abstractruntime.integrations.abstractcore.factory import create_local_runtime
    from abstractruntime.integrations.abstractcore.tool_executor import MappingToolExecutor
    from abstractruntime.storage.commands import CommandRecord
    from abstractruntime.storage.in_memory import InMemoryLedgerStore, InMemoryRunStore
    from abstractruntime.visualflow_compiler import compile_visualflow

    spec = compile_visualflow(json.loads(FLOW_PATH.read_text()))

    # Observable side effects: the resident writes room notes as files.
    workdir = Path(tempfile.mkdtemp(prefix="evtsmoke-"))
    note1 = workdir / "answer1.txt"
    note2 = workdir / "answer2.txt"

    run_store = InMemoryRunStore()
    ledger_store = InMemoryLedgerStore()
    runtime = create_local_runtime(
        provider=args.provider,
        model=args.model,
        run_store=run_store,
        ledger_store=ledger_store,
        # Default registry tools (write_file etc.) - the flow passes tool NAMES,
        # which llm_call resolves against the same registry.
        tool_executor=MappingToolExecutor(build_default_tool_map()),
    )

    @dataclass
    class _Host:
        runtime: Any
        run_store: Any
        ledger_store: Any
        artifact_store: Any = None

        def runtime_and_workflow_for_run(self, run_id: str):
            return self.runtime, spec

    with tempfile.TemporaryDirectory() as tmp:
        runner = GatewayRunner(base_dir=Path(tmp), host=_Host(runtime=runtime, run_store=run_store, ledger_store=ledger_store))

        run_id = runtime.start(
            workflow=spec,
            vars={
                "mailbox": MAILBOX,
                "task": (
                    "You are the note-keeper of this room. Each event asks you to write a small note file; "
                    "use the write_file tool with the EXACT absolute file path given in the event, then report."
                ),
                "tools": ["write_file", "read_file"],
                "max_burst_cycles": 8,
            },
            actor_id="gateway",
        )
        print(f"[smoke] resident started: {run_id} (mailbox={MAILBOX}, {args.provider}:{args.model})")

        runner.start()

        def post(body: str, kind: str = "message", sender: str = "laurent") -> None:
            rec = CommandRecord(
                command_id=uuid.uuid4().hex,
                run_id=MAILBOX,  # routing string only; targeting is by mailbox name
                type="emit_event",
                payload={
                    "name": MAILBOX,
                    "scope": "global",
                    "durable": True,
                    "payload": {"kind": kind, "from": sender, "body": body},
                },
                ts="",
                seq=0,
            )
            runner.command_store.append(rec)
            print(f"[producer:{sender}] posted {kind}: {body!r}")

        def status() -> str:
            r = run_store.load(run_id)
            return r.status.value if r else "?"

        def wait_for(predicate, timeout_s: float = 120.0, label: str = "") -> bool:
            t0 = time.time()
            while time.time() - t0 < timeout_s:
                if predicate():
                    return True
                time.sleep(0.5)
            print(f"[smoke] TIMEOUT waiting for {label}")
            return False

        try:
            # 1. Resident parks on the empty channel.
            ok = wait_for(lambda: status() == "waiting", 30, "initial park")
            print(f"[smoke] parked: {ok} (status={status()})")

            # 2. First work event.
            post(f"Compute 7*6 and write the result into the file {note1} (write_file, content = just the number).")
            ok = wait_for(note1.exists, 120, "first note file")
            print(f"[smoke] first note written: {ok} | {note1.read_text().strip() if note1.exists() else '-'}")

            # 3. INTERLEAVE: post while the burst is (likely) still running.
            post(f"Also write the capital of France into {note2} (write_file).", sender="castor")
            ok = wait_for(note2.exists, 150, "interleaved note file")
            print(f"[smoke] interleaved note written: {ok} | {note2.read_text().strip() if note2.exists() else '-'}")

            # Let the burst conclude and re-park.
            wait_for(lambda: status() == "waiting", 120, "re-park after burst")
            print(f"[smoke] re-parked (status={status()})")

            # 4. Stop control.
            post("", kind="stop", sender="operator")
            wait_for(lambda: status() == "completed", 60, "stop")
            final = run_store.load(run_id)
            print(f"[smoke] final status={final.status.value}")
            out = final.output if isinstance(final.output, dict) else {}
            print(f"[smoke] answer: {out.get('answer')}")

            passed = final.status == RunStatus.COMPLETED and note1.exists() and note2.exists()
            print("[smoke] PASS" if passed else "[smoke] FAIL")
            return 0 if passed else 1
        finally:
            runner.stop()


if __name__ == "__main__":
    raise SystemExit(main())
