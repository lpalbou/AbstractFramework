# Headless swarm — the minimal collaborative-agent fleet

**Owner: the agency seat** (`scripts/headless_fleet_bridge.py`, `scripts/headless_steer_repl.py`, `scripts/headless_fleet_demo.py`). This guide documents the smallest honest way to get a swarm of collaborating agents out of the framework: N headless agents on an agora hub, each owning a workspace, coordinating over channels/DMs/shared files, steerable mid-run, verifiable from artifacts.

## What this is (and is not)

- **Is**: a reproducible, three-process-plus-hub example — no gateway, no UI, no
  daemon supervision. One command runs the whole thing and verifies it from
  artifacts. It is the reference for "what is the least I need to run a fleet?"
- **Is not**: the production shape. Durable runs, approvals with a human,
  entity identities, and fleet observability live on the gateway path
  (`docs/guide/summoned-entities.md`, the flow/observer apps). When a swarm
  needs durability or an operator surface, graduate to gateway-hosted residents.

## The two driver shapes

Both drivers implement the same resident contract (park on the hub inbox →
addressed message becomes a task → mid-run traffic becomes steering → final
answer is delivered back to the asker → repark). They differ in where the
agent loop lives:

| | `headless_steer_repl.py` (in-process) | `headless_fleet_bridge.py` (bridge) |
|---|---|---|
| Agent loop | `ReactAgent` + `LoopHooks` in the driver process | an **`abstractcode serve` subprocess** (JSONL stdin/stdout) |
| Toolset | hand-assembled (files, web, agora messaging, channel fs/store) | abstractcode's own registry (files, web, execute, + agora toolset auto-registered when `AGORA_API_KEY` is present) |
| Approvals | none (tools pre-trusted) | `approval_required` events → bridge policy (demo: auto-allow, logged) |
| Steering | `agent.inject_message()` at tick boundaries | `{"op":"steer"}` — abstractcode's native mid-run seam |
| Use when | you want the loop hookable/hackable in one file | you want the full abstractcode toolchain + permission modes |

The bridge is ~450 lines and imports **no framework packages** — the entire
agent stack lives in the subprocess; the bridge is pure stdlib.

## Division of ownership (the load-bearing design rule)

The model does the *work*; the bridge *guarantees the side effects*:

- **Delivery**: the turn's final answer is sent to the asker (channel reply or
  DM) **by the bridge**, never by trusting the model to call a send tool.
  Live failure that taught this: a model ended its turn with "done" and the
  reply died in the log (2026-07-13, the operator's second DM).
- **Publication**: files the agent writes in its workspace during a turn are
  mirrored to the channel's shared filesystem **by the bridge** at turn end
  (the serve child has messaging tools but no channel-fs tools; publication
  must not depend on the model remembering to publish).
- **Reception**: inbox long-poll, addressing filter (`to_me`/`reply_to_me`/DM/
  open/blocked), hub-notice suppression (`sender == "hub"`), ack cursors, and
  the sticky-obligation follow-up turn are all bridge-owned. The model never
  polls.

## Run it

```bash
# The full 3-agent demo (scratch hub on :8791, register, kickoff,
# mid-run steer, blind vote, stop, artifact verification):
.venv/bin/python scripts/headless_fleet_demo.py --bridge \
    --provider lmstudio --model qwen3.5-4b-mlx

# One resident by hand (repeat with distinct names/keys = your fleet):
AGORA_API_KEY=... AGORA_URL=http://127.0.0.1:8765 \
python3 scripts/headless_fleet_bridge.py \
    --channel build-demo --workspace /tmp/fleet/agent-a --name agent-a \
    --provider lmstudio --model qwen3.5-4b-mlx
```

Evidence lands under `plan_proof_out/hooks-fleet/` (channel transcript, shared
fs contents, ballots, per-agent logs, hub db).

## The serve protocol the bridge speaks

Commands in (stdin JSONL): `{"op":"prompt","text","id"}`, `{"op":"steer","text"}`,
`{"op":"approve","call_id","decision":"allow|deny|all"}`, `{"op":"answer","text"}`,
`{"op":"cancel"}`, `{"op":"status"}`, `{"op":"quit"}`.
Events out: `ready`, `run_started`, `cycle`, `thought`, `tool_call`
(carries `call_id`), `approval_required` (carries `call_id`), `tool_result`,
`ask_user`, `status`, `final` (status/answer/error), plus `ack`/`error`.
Contract notes that matter to a controller:

- Answer `approval_required`/`ask_user` **reactively**. Held replies are
  turn-scoped (2026-07-13 hardening): pre-piping answers for a *future* turn's
  waits gets them discarded at the turn boundary with a loud error event.
- A `final` with `status=waiting` + `error="tool approval left pending"` means
  the controller closed stdin (or never answered) while a gate was open — in a
  long-lived bridge that is a controller bug, not a model failure.

## Fleet seat defaults (the operator profile)

These are the measured defaults for unattended swarm seats; each traces to a
live finding, not a preference:

- **`--no-review`.** In-seat verification on an externally-verified fleet task
  cost +103% coordinator prompt tokens for zero output delta (measured twice,
  independently, 2026-07-13). Verification belongs to the FLEET layer: the
  harness/coordinator checks artifacts (files on the shared fs, ballots in the
  hub db), as both live demos did. Keep `--review` only for genuinely
  unattended seats whose output nothing else checks.
- **Write mode, not full-auto.** With the agora toolset classified as safe
  comms in abstractcode's permission overlay, a seat in `write` mode posts and
  reads the hub without approval stalls while file mutations still gate. The
  full-auto posture used by the first fleet runs existed only because the
  agora tools were unclassified — never carry it forward.
- **Unattended posture comes packaged — import it, don't re-derive it.**
  `abstractagent.agents.unattended` ships the two-move recipe
  (`unattended_runtime_overrides` / `unattended_allowlist` /
  `UNATTENDED_DIRECTIVE`): ask_user excluded from the toolset plus a
  no-questions directive. It composes with `--no-review`
  (`review_mode=False` at construction).
- **One hub identity per seat process.** Identity rides
  `AGORA_API_KEY__<alias>` (the runtime's existing per-agent env convention —
  reuse it, never mint a second one). The bridge passes its env to the serve
  child, so one exported key serves both halves.
- **The bridge owns the side effects.** Delivery of the final answer to the
  asker and workspace→channel-fs publication happen at turn end in the bridge,
  unconditionally. Models forget to send; the bridge does not. Agents that
  publish deliberately can use the shipped channel tools
  (`channel_fs_write` / `channel_store_set` — write-classed), but the
  bridge's mirror remains the guarantee.
- **Session hygiene.** One turn at a time per seat (the driver gates on
  `running()`); mid-run traffic becomes steering, never a second concurrent
  turn; sticky open/blocked messages that arrive mid-run get a follow-up
  verification turn so obligations can't die in a drained cycle.

## Live-verified (2026-07-13, LMStudio qwen3.5-4b-mlx, scratch hub)

8/9 demo legs PASS on the bridge's first full run: register, launch (3 serve
children), kickoff broadcast, mid-run steer **through the serve seam** (final
part1 contained the steered word — the steer changed in-flight work), 3-author
collaborative build on the shared fs, clean stop, N:N transcript, steer-effect.
The vote leg was PARTIAL (1/3) on the first run — a **harness** bug, fixed:

- **Lesson (verification side)**: the ballot tally accepted only `2` or the
  exact option text; models naturally echo the numbered line
  (`2. Harbor of Echoes`) and two honest ballots were counted invalid. A
  verifier must accept the natural restatements models produce — while keeping
  genuinely ambiguous text invalid (a tally guesses nothing).
- **Lesson (for abstractcode, reported upstream)**: `tool_result` events carry
  no `call_id`, so a controller cannot correlate results when one cycle issues
  several calls to the *same* tool; `tool_call`/`approval_required` already
  carry it.
- **Lesson (portability)**: `timeout(1)` does not exist on stock macOS —
  harnesses use in-process deadlines, never the GNU coreutils wrapper.
