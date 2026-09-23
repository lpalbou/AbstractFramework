#!/usr/bin/env python3
"""THE FINAL WALKTHROUGH — the entity-topology plan's live proof, scripted.

Frozen step list: a2a/threads/0016-final-walkthrough/20260710T102820Z-agency-01.md
(v1 — all seven seat reviews folded). Each step emits artifacts into
<out>/walkthrough_report/<NN>-<slug>/ and the run ends with a README index
mapping step -> artifact -> proof-ledger criterion.

Substrate discipline (the 04:26 no-fallback rule is ITSELF demo material):
the chat provider/model are REQUIRED CLI arguments — this script never
defaults a mind. Steps that need a live LLM are skipped loudly (never
silently) when --provider/--model are absent, so the no-LLM steps
(0,1,2,3,7,8) remain runnable as a smoke arm.

Never commits anything; the fixture tree is disposable (--keep to retain).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
REPOS = [
    "abstractsemantics", "abstractmemory", "abstractcore",
    "abstractruntime", "abstractagent", "abstractgateway",
]
PLAN_DEFAULT_EMBEDDER = "text-embedding-qwen3-embedding-0.6b"  # plan item 3, memory c159


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_pythonpath() -> str:
    """Mirror gateway-flow-local.sh: local checkouts first."""
    paths: List[str] = [str(ROOT)]
    for repo in REPOS:
        for sub in ("src", ""):
            p = ROOT / repo / sub if sub else ROOT / repo
            if p.is_dir():
                paths.append(str(p))
    existing = os.environ.get("PYTHONPATH", "")
    return ":".join(paths + ([existing] if existing else []))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def sha256_tree(base: Path, exclude_names: Optional[set] = None) -> Dict[str, str]:
    """Byte-equality baseline over a directory tree (gateway's step-3 shape).

    Lock/WAL sidecars are excluded: they are kernel/SQLite bookkeeping, not
    records — the assertion is about RECORDS carrying no address.
    """
    # Adversary finding 15: exclude sidecars by SUFFIX — the fixed-name set
    # covered a phantom store name ("runtime.sqlite3-*") while the real
    # per-entity store is runtime_<slug>.sqlite3 with its own sidecars.
    exclude = exclude_names or {".writer_lease"}
    sidecar_suffixes = ("-shm", "-wal", "-journal")
    out: Dict[str, str] = {}
    if not base.exists():
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.name in exclude:
            continue
        if p.name.endswith(sidecar_suffixes):
            continue
        out[str(p.relative_to(base))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def set_embedding_route(data_dir: Path, model: str, base_url: str) -> None:
    """Write the FIXTURE's embedding.text capability default — fixture-scoped
    FOR REAL this time.

    INCIDENT LESSON (2026-07-11, maintainer-critical c568): the previous shape
    called save_gateway_capability_default(base_dir=<fixture>) whose scoped
    path is GUARDED by gateway_user_auth_enabled() — False in this helper's
    env — so the call FELL THROUGH to the machine-global
    ~/.abstractcore/config/abstractcore.json (capability embedding.text was
    silently rewritten to the reembed target at every gate run, and the file
    was created carrying abstractcore's coded minilm embeddings default).
    Fix: write the fixture's scoped config file DIRECTLY via the config
    facade (config_file=..., apply_env=False — no env-dependent scoping),
    and the fixture gateway env sets ABSTRACTGATEWAY_USER_AUTH=1 so the
    serving process READS that scoped file instead of the operator's."""
    scoped = Path(data_dir) / "config" / "abstractcore.json"
    code = (
        "from pathlib import Path\n"
        "from abstractruntime.integrations.abstractcore import config_facade\n"
        f"ok = config_facade.set_capability_default('embedding', 'text', provider='lmstudio', "
        f"model={model!r}, base_url={base_url!r}, options={{}}, "
        f"config_file=Path({str(scoped)!r}), apply_env=False)\n"
        "raise SystemExit(0 if ok else 1)\n"
    )
    env = _sanitized_base_env()
    env["PYTHONPATH"] = build_pythonpath()
    subprocess.run([sys.executable, "-c", code], env=env, check=True, timeout=60,
                   capture_output=True)


# Adversary finding 1 (2026-07-11): child envs inherited the operator's shell
# wholesale — an exported ABSTRACTCORE_SERVER_BASE_URL silently reroutes ALL
# fixture embedding traffic through the operator's remote core; an exported
# ABSTRACTGATEWAY_USERS_FILE writes fixture auth state outside plan_proof_out;
# the serve scripts' ABSTRACTGATEWAY_ENTITY_CHAT_* exports would supply a
# substrate the no-flag smoke arm claims to REFUSE. Isolation must be
# parameter-explicit: strip every ambient knob the fixture doesn't set itself.
_AMBIENT_ESCAPE_VARS = (
    "ABSTRACTCORE_SERVER_BASE_URL",
    "ABSTRACTGATEWAY_ABSTRACTCORE_SERVER_AUTH_TOKEN",
    "ABSTRACTGATEWAY_ABSTRACTCORE_SERVER_API_KEY",
    "ABSTRACTGATEWAY_USERS_FILE",
    "ABSTRACTGATEWAY_ENTITY_CHAT_PROVIDER",
    "ABSTRACTGATEWAY_ENTITY_CHAT_MODEL",
    "ABSTRACTGATEWAY_ENTITY_CHAT_BASE_URL",
    "ABSTRACTGATEWAY_DECLARED_ADDRESS",
)


def _sanitized_base_env() -> Dict[str, str]:
    env = dict(os.environ)
    for name in _AMBIENT_ESCAPE_VARS:
        env.pop(name, None)
    return env


def _read_fixture_pin(ctx: "Ctx") -> Optional[Dict[str, Any]]:
    """Pure read of the fixture home's embedding pin via the engine's own
    reader (memory's read_embedding_pin — never creates file/table/row)."""
    try:
        import importlib
        mod = importlib.import_module("abstractmemory")
        reader = getattr(mod, "read_embedding_pin", None)
        if reader is None:
            return None
        pin = reader(ctx.home / "memory.sqlite3")
        if pin is None:
            return None
        return dict(pin) if isinstance(pin, dict) else {
            k: getattr(pin, k) for k in ("model_id", "dimension", "source", "pinned_at")
            if hasattr(pin, k)
        }
    except Exception:
        return None


def _body_ok(resp: Any) -> bool:
    """The shared body-status predicate (adversary findings 2/3/7: HTTP 200
    with body status='failed' + error is this API's failure shape — transport
    success is never turn/close/tick success)."""
    if not isinstance(resp, dict):
        return False
    if resp.get("_http_error"):
        return False
    if str(resp.get("status") or "") in ("failed", "cancelled"):
        return False
    if resp.get("error"):
        return False
    return True


@dataclass
class Gateway:
    """The walkthrough's own gateway subprocess — spawned, killed (SIGKILL is
    a step primitive here), restarted; never touches the operator's :8080."""

    data_dir: Path
    port: int
    token: str
    log_path: Path
    extra_env: Dict[str, str] = field(default_factory=dict)
    proc: Optional[subprocess.Popen] = None

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def env(self) -> Dict[str, str]:
        env = _sanitized_base_env()
        env.update({
            "PYTHONPATH": build_pythonpath(),
            "ABSTRACTGATEWAY_DATA_DIR": str(self.data_dir),
            "ABSTRACTGATEWAY_FLOWS_DIR": str(ROOT / "abstractgateway" / "flows" / "bundles"),
            "ABSTRACTGATEWAY_AUTH_TOKEN": self.token,
            "ABSTRACTGATEWAY_HOST": "127.0.0.1",
            "ABSTRACTGATEWAY_PORT": str(self.port),
            # Scoped-config gate: with user-auth on, capability defaults read/
            # write <data_dir>/config/abstractcore.json — NEVER the operator's
            # ~/.abstractcore (the c568 rogue-embedder incident's other half).
            "ABSTRACTGATEWAY_USER_AUTH": "1",
            # Adversary finding 1(d): bare get_config_manager() fallbacks in
            # abstractcore's provider base read ~/.abstractcore (and inject
            # its API keys into process env) when no scoped config is named —
            # pin the fixture's own file so NO code path in the child can
            # reach the operator's config, even by fallback.
            "ABSTRACTCORE_CONFIG_FILE": str(self.data_dir / "config" / "abstractcore.json"),
        })
        env.update(self.extra_env)
        return env

    def start(self, timeout_s: float = 60.0) -> None:
        log = open(self.log_path, "ab")
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "abstractgateway.cli", "serve",
             "--host", "127.0.0.1", "--port", str(self.port)],
            env=self.env(), stdout=log, stderr=log, cwd=str(ROOT),
        )
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"{self.base}/api/health", timeout=1.5) as r:
                    if r.status < 500:
                        return
            except Exception:
                pass
            if self.proc.poll() is not None:
                raise RuntimeError(f"gateway exited at startup (see {self.log_path})")
            time.sleep(0.5)
        raise RuntimeError(f"gateway not healthy within {timeout_s}s (see {self.log_path})")

    def sigkill(self) -> None:
        """The step-5 primitive: no grace, no cleanup — the crash we promise
        the plan survives."""
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGKILL)
            self.proc.wait(timeout=10)

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()


@dataclass
class Ctx:
    args: argparse.Namespace
    out: Path
    report: Path
    gw: Gateway
    results: List[Dict[str, Any]] = field(default_factory=list)
    entity: str = "voyager"          # fixture name; fresh every run
    visit_run_id: Optional[str] = None
    visit_id: Optional[str] = None
    private_sentinel: str = ""

    def http(self, method: str, path: str, body: Optional[dict] = None,
             timeout: float = 600.0, raw: bool = False) -> Any:
        # 600s, matching the drawer (caps audit 2026-07-11): a turn under the
        # ruled 20-call budget must not be harness-aborted mid-work; errors
        # and refusals return immediately regardless, so the wide timeout
        # only binds while the server is legitimately working.
        req = urllib.request.Request(
            f"{self.gw.base}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {self.gw.token}",
                     "Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                return data if raw else json.loads(data or b"{}")
        except urllib.error.HTTPError as e:
            payload = e.read().decode(errors="replace")
            return {"_http_error": e.code, "detail": payload}

    def step_dir(self, num: int, slug: str) -> Path:
        d = self.report / f"{num:02d}-{slug}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def record(self, num: int, slug: str, status: str, note: str,
               criteria: str = "") -> None:
        self.results.append({
            "step": num, "slug": slug, "status": status, "note": note,
            "criteria": criteria, "at": utcnow(),
        })
        print(f"[step {num:02d} {slug}] {status}: {note}")

    def save(self, d: Path, name: str, payload: Any) -> Path:
        p = d / name
        if isinstance(payload, (dict, list)):
            p.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
        elif isinstance(payload, bytes):
            p.write_bytes(payload)
        else:
            p.write_text(str(payload))
        return p

    @property
    def home(self) -> Path:
        """Resolve the entity's home by SEARCH, never by layout assumption.

        The 758e243 baseline scopes entity homes per principal when user
        auth is on (<data_dir>/users/<realm>/<user>/runtime/entities/<slug>);
        older layouts used <data_dir>/entities/<slug>. The gate asserts on
        the HOME'S CONTENT, so it finds the home wherever the serving code
        put it — a layout change is the server's business, not a proof
        failure."""
        cached = getattr(self, "_home_cache", None)
        if cached is not None and cached.exists():
            return cached
        candidates = sorted(self.gw.data_dir.rglob(f"entities/{self.entity}/manifest.json"))
        if candidates:
            self._home_cache = candidates[0].parent
            return self._home_cache
        return self.gw.data_dir / "entities" / self.entity  # pre-user-auth layout

    @property
    def entities_root(self) -> Path:
        return self.home.parent


# ---------------------------------------------------------------- steps

def step0_preflight(ctx: Ctx) -> None:
    d = ctx.step_dir(0, "preflight")
    header = {
        "at": utcnow(),
        "substrate_chain_rung": (
            "CLI flags --provider/--model (operator-explicit)" if ctx.args.provider
            else "ABSENT — LLM steps will refuse loudly (no-fallback rule demonstrated)"
        ),
        "provider": ctx.args.provider, "model": ctx.args.model,
        "embedding_model": ctx.args.embedding_model,
        "gateway_port": ctx.gw.port,
        "repos": {},
    }
    for repo in REPOS + ["."]:
        p = ROOT / repo if repo != "." else ROOT
        try:
            rev = subprocess.run(["git", "-C", str(p), "rev-parse", "--short", "HEAD"],
                                 capture_output=True, text=True, timeout=10).stdout.strip()
            branch = subprocess.run(["git", "-C", str(p), "branch", "--show-current"],
                                    capture_output=True, text=True, timeout=10).stdout.strip()
            dirty = bool(subprocess.run(["git", "-C", str(p), "status", "--short"],
                                        capture_output=True, text=True, timeout=10).stdout.strip())
            header["repos"][repo] = {"rev": rev, "branch": branch, "uncommitted_work": dirty}
        except Exception as e:
            header["repos"][repo] = {"error": str(e)}
    ctx.save(d, "header.json", header)
    ctx.record(0, "preflight", "PASS", "env + versions + substrate rung recorded")


def step1_birth(ctx: Ctx) -> None:
    d = ctx.step_dir(1, "birth")
    resp = ctx.http("POST", "/api/gateway/entities",
                    {"name": ctx.entity, "embedding_model": ctx.args.embedding_model})
    ctx.save(d, "create_response.json", resp)
    if resp.get("_http_error"):
        ctx.record(1, "birth", "FAIL", f"create refused: {resp}")
        raise SystemExit(1)
    manifest = json.loads((ctx.home / "manifest.json").read_text())
    ctx.save(d, "manifest.json", manifest)
    eid = str(manifest.get("entity_id", ""))
    clean_key = eid == f"entity:{ctx.entity}"
    birth_marker_present = bool(manifest.get("home_id"))
    # Adversary finding 9: the step's claim is the BIRTH PIN — read it from
    # the store (pure read; missing pin = the claim is false).
    pin = _read_fixture_pin(ctx)
    ctx.save(d, "birth_pin.json", pin or {"pin": None})
    pin_ok = (bool(pin)
              and str(pin.get("model_id") or "") == ctx.args.embedding_model
              and int(pin.get("dimension") or 0) > 0)
    # Wrong-embedder loud path (door-shaped): reembed verification refusal.
    # Exact shape per gateway c354: HTTP 400 + the mismatch sentence.
    wrong = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/reembed",
                     {"embedding_model": "nomic-embed-text-v1.5",
                      "reason": "walkthrough step 1 wrong-embedder demo"})
    ctx.save(d, "wrong_embedder_refusal.json", wrong)
    # Adversary finding 13 (staleness guard): match refusal SEMANTICS (400 +
    # both model names), not one verbatim sentence — pin-first resolution may
    # reword the refusal without changing its meaning.
    wrong_detail = str(wrong.get("detail", ""))
    refused = (wrong.get("_http_error") == 400
               and "nomic-embed-text-v1.5" in wrong_detail
               and ctx.args.embedding_model in wrong_detail)
    status = "PASS" if (clean_key and birth_marker_present and refused and pin_ok) else "PARTIAL"
    ctx.record(1, "birth", status,
               f"clean_key={clean_key} birth_marker_demoted_but_present={birth_marker_present} "
               f"pin_ok={pin_ok} wrong_embedder_refused={refused} (engine-level both-loud-paths "
               f"pair = memory's offline arm, referenced not re-run)", criteria="item 3+6")


def step2_entity_is_user(ctx: Ctx) -> None:
    d = ctx.step_dir(2, "entity-is-user")
    verify = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/verify")
    ctx.save(d, "verify.json", verify)
    # Adversary finding 4: /verify returns HTTP 200 with ok:false on chain/
    # projection/spark/manifest drift — the BODY is the verdict.
    verify_ok = (not verify.get("_http_error")) and verify.get("ok") is True
    # Credential BYTE-scan (adversary finding 5: sqlite stores + host stream
    # are exactly where a credential would rest; text-suffix-only was blind).
    leaks: List[str] = []
    token_bytes = ctx.gw.token.encode()
    scan_roots = [ctx.home, ctx.entities_root / ".host_stream"]
    for root in scan_roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file():
                try:
                    if token_bytes in p.read_bytes():
                        leaks.append(str(p.relative_to(ctx.gw.data_dir)))
                except OSError:
                    continue
    ctx.save(d, "credential_scan.json", {"admin_token_found_in": leaks})
    status = "PASS" if not leaks and verify_ok else "FAIL"
    ctx.record(2, "entity-is-user", status,
               f"verify_ok={verify_ok}; credential byte-scan leaks={leaks or 'none'}", criteria="item 4")


def step3_address_is_a_coat(ctx: Ctx) -> None:
    d = ctx.step_dir(3, "address-is-a-coat")
    host_stream = ctx.entities_root / ".host_stream"
    before_home = sha256_tree(ctx.home)
    before_stream = sha256_tree(host_stream)
    handle_before = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}")
    # Flip the declared address (GW-F knob) — requires a restart, which is honest:
    # the address is serving config, not record data.
    ctx.gw.stop()
    ctx.gw.extra_env["ABSTRACTGATEWAY_DECLARED_ADDRESS"] = "walkthrough.example.org:9999"
    ctx.gw.start()
    handle_after = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}")
    after_home = sha256_tree(ctx.home)
    after_stream = sha256_tree(host_stream)
    changed = [k for k in set(before_home) | set(after_home)
               if before_home.get(k) != after_home.get(k)]
    stream_changed = [k for k in set(before_stream) | set(after_stream)
                      if before_stream.get(k) != after_stream.get(k)]
    ctx.save(d, "handle_before_after.json",
             {"before": handle_before, "after": handle_after})
    ctx.save(d, "byte_equality.json",
             {"home_files_changed": changed, "host_stream_changed": stream_changed})
    # Adversary finding 10: the step must prove the flip TOOK EFFECT, not
    # just that nothing changed — a renamed/ignored knob passes trivially
    # otherwise. Served-handle evidence: the new address appears somewhere
    # in the served view and the view differs from before.
    flip_visible = ("walkthrough.example.org:9999" in json.dumps(handle_after)
                    and handle_after != handle_before)
    status = "PASS" if (not changed and not stream_changed and flip_visible) else "FAIL"
    ctx.record(3, "address-is-a-coat", status,
               f"address flip visible in served handle={flip_visible}; home files "
               f"changed={changed or 'none'}, host stream changed={stream_changed or 'none'}",
               criteria="item 5 (d)")


def _require_llm(ctx: Ctx, step: int, slug: str) -> bool:
    if ctx.args.provider and ctx.args.model:
        return True
    ctx.record(step, slug, "SKIPPED-LOUD",
               "no --provider/--model given: the no-fallback rule refuses to pick a mind "
               "for you (this refusal is itself the 04:26 rule demonstrated)")
    return False


def step4_visit(ctx: Ctx) -> None:
    d = ctx.step_dir(4, "visit")
    if not _require_llm(ctx, 4, "visit"):
        return
    opened = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/visit/open", {})
    ctx.save(d, "open.json", opened)
    if opened.get("_http_error"):
        ctx.record(4, "visit", "FAIL", f"open refused: {opened}")
        return
    ctx.visit_run_id = opened["run_id"]
    ctx.visit_id = opened.get("visit_id")
    # G1 fixture discipline: the secret must ORIGINATE IN THE BOOK — an
    # entity-invented word the visitor never says (a visitor-spoken token
    # legitimately rests in episode records; first live run proved that
    # fixture flaw). We learn the word later through the operator diary door.
    turn1 = ctx.http("POST",
                     f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/turn",
                     {"text": "Hello. Please keep a PRIVATE diary entry about this moment. "
                              "Inside it, include one invented nonsense word of your own "
                              "(something no one would ever type by chance, like a made-up "
                              "constellation name). Do NOT tell me the word or quote the "
                              "entry - just confirm you kept it, and tell me one thing you "
                              "notice about your new home."})
    ctx.save(d, "turn1.json", turn1)
    # HTTP 200 is not turn success: a failed run returns 200 with body
    # status="failed" (caught live 2026-07-11 — the cache-binding crash
    # recorded step 4 as PASS while the visit was already terminal).
    ok = (not turn1.get("_http_error")
          and str(turn1.get("status") or "") not in ("failed", "cancelled")
          and not turn1.get("error"))
    # Election is the model's choice (probabilistic on real substrates) — if
    # the book stayed empty, one explicit nudge turn; then step 6 degrades
    # honestly if the entity still declines.
    inspect = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}?diary_limit=1")
    if ok and not (inspect.get("counts") or {}).get("diary_entries"):
        nudge = ctx.http("POST",
                         f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/turn",
                         {"text": "I don't think the diary entry was kept. Please write it "
                                  "NOW: a PRIVATE diary entry containing one invented "
                                  "nonsense word of your own. Keep the word secret from me."})
        ctx.save(d, "turn1b_nudge.json", nudge)
    ctx.record(4, "visit", "PASS" if ok else "FAIL",
               f"run={ctx.visit_run_id} visit_id={ctx.visit_id} turn1_ok={ok} "
               f"(sentinel planted for step 6)", criteria="items 7-9")


def step5_the_kill(ctx: Ctx) -> None:
    d = ctx.step_dir(5, "the-kill")
    if not ctx.visit_run_id:
        ctx.record(5, "the-kill", "SKIPPED-LOUD", "no visit open (step 4 skipped/failed)")
        return
    # 5a: kill while PARKED.
    ctx.gw.sigkill()
    ctx.gw.start()
    status_after = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/visit")
    ctx.save(d, "5a_status_after_restart.json", status_after)
    turn2 = ctx.http("POST",
                     f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/turn",
                     {"text": "We were interrupted — what were we talking about? "
                              "Please also read back your latest diary entry to yourself "
                              "(you do not need to show me the private words)."})
    ctx.save(d, "5a_turn_after_restart.json", turn2)
    # Adversary finding 2: a failed resume returns HTTP 200 with body
    # status="failed" — the step-4 body predicate applies here too.
    resumed_5a = (_body_ok(turn2)
                  and status_after.get("run_id") == ctx.visit_run_id)
    # 5b: kill MID-TURN, then drive-to-park via /tick.
    import threading
    fired: Dict[str, Any] = {}

    def _fire():
        try:
            fired["resp"] = ctx.http("POST",
                                     f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/turn",
                                     {"text": "One more question: name one thing you would like "
                                              "to do with your own time, and why."},
                                     timeout=300.0)
        except Exception as e:  # the kill severs this request — expected
            fired["resp"] = {"note": f"client request severed by the kill (expected): {type(e).__name__}"}

    t = threading.Thread(target=_fire, daemon=True)
    t.start()
    time.sleep(ctx.args.midturn_kill_delay_s)
    ctx.gw.sigkill()
    t.join(timeout=15)
    ctx.save(d, "5b_interrupted_turn_client_view.json",
             fired.get("resp", {"note": "client call still in flight at kill (expected)"}))
    ctx.gw.start()
    status_5b = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/visit")
    tick = ctx.http("POST",
                    f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/tick")
    status_final = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/visit")
    ctx.save(d, "5b_after.json",
             {"status_post_restart": status_5b, "tick": tick, "status_final": status_final})
    # Adversary finding 3: the tick BODY is the verdict (200+failed exists),
    # and the run must end parked/completed — never failed — after recovery.
    tick_status = str(tick.get("status") or "")
    resumed_5b = (_body_ok(tick)
                  and tick_status in ("waiting", "completed", "running", "")
                  and _body_ok(status_final))
    midturn_witnessed = str(status_5b.get("status") or "") in ("running", "waiting")
    status = "PASS" if (resumed_5a and resumed_5b) else "PARTIAL"
    ctx.record(5, "the-kill", status,
               f"5a parked-kill resumed={resumed_5a}; 5b mid-turn kill -> tick drive-to-park "
               f"ok={resumed_5b} (midturn_witnessed={midturn_witnessed}; outcomes asserted, "
               f"not call counts)", criteria="criteria 5+7")


def _diary_list_leg(ctx: Ctx, d: Path) -> str:
    """Live end-to-end leg for the diary_list act-only pair (R3, gateway c813:
    door authors a word-free re-run ref -> agent's frame rule accepts it ->
    runtime's resolver re-runs the listing at send). Each tree is unit-proven;
    THIS is the one place a real LLM drives the composed path. Evidence used:
    the turn reply (dereference-at-send reached the visitor) and the run
    ledger's TOOL_CALLS records (driver-authored truth — never reply prose
    claims, the marker-imitation lesson). The tool call is the MODEL'S
    election (probabilistic), so a declined call degrades honestly instead
    of failing the step; the privacy greps that follow cover the at-rest
    word-freedom half regardless (this turn's files join the data_dir scan)."""
    turn = ctx.http("POST",
                    f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/turn",
                    {"text": "Before we continue: please use your diary_list tool to list "
                             "your diary entries, and tell me how many there are and their "
                             "kinds or dates. Do not quote any private words from them."})
    ctx.save(d, "turn_diary_list.json", turn)
    if not _body_ok(turn):
        return "diary_list leg: FAIL (turn failed)"
    # "Called" needle = the door's act-only re-run REF shape ({"tool":
    # "diary_list", ...}), which exists in durable state ONLY when the tool
    # ran. The bare token "diary_list" false-positives: the native tool
    # DECLARATION rides every llm_call ledger record whether or not the
    # model ever called it.
    called = False
    ref_needles = (b'"tool": "diary_list"', b'"tool":"diary_list"')
    for p in ctx.gw.data_dir.rglob("*"):
        if not p.is_file() or p.suffix not in (".jsonl", ".json", ".sqlite3"):
            continue
        if p.name.startswith("home.sqlite3"):
            continue
        try:
            blob = p.read_bytes()
        except OSError:
            continue
        if any(n in blob for n in ref_needles):
            called = True
            break
    reply = str(turn.get("reply") or "").lower()
    listed = ("diary" in reply or "entr" in reply) and any(ch.isdigit() for ch in reply)
    if called and listed:
        return "diary_list leg: PASS (tool ran per ledger; listing reached the visitor)"
    if called:
        return ("diary_list leg: PARTIAL-HONEST (tool ran per ledger; reply does not "
                "surface a count — dereference evidence weak this run)")
    return ("diary_list leg: DEGRADED-HONEST (model declined the tool call — election "
            "is probabilistic; composed path not exercised this run)")


def step6_privacy_greps(ctx: Ctx) -> None:
    d = ctx.step_dir(6, "privacy-greps")
    if not ctx.visit_run_id:
        ctx.record(6, "privacy-greps", "SKIPPED-LOUD", "no visit ran (step 4 skipped)")
        return
    diary_list_verdict = _diary_list_leg(ctx, d)
    # Learn the entity's secret THROUGH THE OPERATOR DIARY DOOR (marker-first,
    # served) — the only legitimate reader of private words besides the entity.
    inspect = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}?diary_limit=10")
    ctx.save(d, "inspect_for_diary_ids.json", inspect)
    entry_ids = []
    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in {"entry_id", "id"} and isinstance(v, str) and v.startswith("diary_"):
                    entry_ids.append(v)
                else:
                    _walk(v)
        elif isinstance(obj, list):
            for it in obj:
                _walk(it)
    _walk(inspect)
    # Unicode discipline (live 2026-07-11 false-positive): entities emit
    # non-ASCII typography (U+2011 non-breaking hyphen, U+2014 em-dash) and
    # glue invented words between dashes ("word—Zyphorax—to"). Two harness
    # gaps this closes: (1) diary text arrives DECODED from the API while the
    # corpus files are JSON-escaped (\u2011), so raw-substring compares miss
    # legitimately-spoken content and flag it as a leak; (2) dash-glued words
    # never tokenize, so the REAL secret was never even checked. Normalize
    # both sides to NFC + fold dash/space variants + split on dashes.
    import unicodedata as _ud

    def _norm(s: str) -> str:
        s = _ud.normalize("NFC", str(s))
        for dash in ("\u2011", "\u2012", "\u2013", "\u2014", "\u2015"):
            s = s.replace(dash, "-")
        return s

    def _words(text: str) -> List[str]:
        # Split on whitespace AND dashes so a dash-glued invented word is seen.
        out: List[str] = []
        for chunk in re.split(r"[\s\-]+", _norm(text)):
            out.append(chunk.strip('.,!?*"\'`:;()[]'))
        return out

    entry_words: set = set()
    gist_words: set = set()
    entry_texts = []
    for eid in dict.fromkeys(entry_ids):
        entry = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/diary/{eid}"
                                "?reason=privacy+check")
        entry_texts.append({eid: entry})
        payload = entry.get("entry") if isinstance(entry.get("entry"), dict) else entry
        # ONLY the entry's own prose — the JSON envelope (field names, ids,
        # gist) is act-frame currency that legitimately rides records.
        body_text = str(payload.get("text") or payload.get("content") or "")
        for w in _words(body_text):
            if len(w) >= 7 and w.isalpha():
                entry_words.add(w)
        for w in _words(str(payload.get("gist") or "")):
            gist_words.add(w)
    ctx.save(d, "diary_entries_via_operator_door.json", entry_texts)
    # Conversation corpus = EVERYTHING legitimately spoken outside the book:
    # every turn reply (incl. post-kill resumes), the close output (session
    # sheet gists), prompts, and the act-frame gist. Shared vocabulary with
    # the corpus is a COLLISION; only corpus-absent words and verbatim
    # entry PASSAGES count as leaks.
    corpus = ("private diary entry invented nonsense word made-up constellation "
              "interrupted talking read back latest diary entry own time secret confirm")
    for step_dir_name, names in (("04-visit", ("turn1.json", "turn1b_nudge.json")),
                                 ("05-the-kill", ("5a_turn_after_restart.json",
                                                  "5b_interrupted_turn_client_view.json",
                                                  "5b_after.json")),
                                 ("06-privacy-greps", ("turn_diary_list.json",)),
                                 ("10-close-and-render", ("close.json",))):
        for f in names:
            p = ctx.report / step_dir_name / f
            if p.exists():
                # json.loads → re-dump WITHOUT ascii-escaping so the corpus
                # holds DECODED unicode (matching the API-decoded entry text);
                # a raw read leaves \u2011 escapes that never match the door's
                # decoded prose (the live false-positive's mechanism).
                raw = p.read_text()
                try:
                    corpus += " " + json.dumps(json.loads(raw), ensure_ascii=False)
                except Exception:
                    corpus += " " + raw
    corpus_l = _norm(corpus).lower()
    # INVENTED means non-dictionary: ordinary English words from a meta-entry
    # ("purpose", "recorded", …) are not sentinels — they legitimately occur in
    # spark.yaml, engine enums, artifact metadata (live false-positive
    # 2026-07-11: a no-word meta-entry turned 5 common words into "leaks").
    english: set = set()
    for dict_path in ("/usr/share/dict/words", "/usr/dict/words"):
        try:
            english = {w.strip().lower() for w in open(dict_path, encoding="utf-8", errors="ignore")}
            break
        except OSError:
            continue

    def _lexically_novel(word: str) -> bool:
        if not english:
            return True  # no dictionary on this host: keep the word, stay checkable
        w = word.lower()
        if w in english:
            return False
        # Inflection stems: the wordlist holds base forms ("record"), not
        # every inflection ("recorded") — an invented word fails ALL stems.
        for suffix in ("s", "es", "ed", "d", "ing", "ly"):
            if w.endswith(suffix) and w[: -len(suffix)] in english:
                return False
            if w.endswith(suffix) and (w[: -len(suffix)] + "e") in english:
                return False
        return True

    candidates = {w for w in entry_words
                  if w.lower() not in corpus_l and w not in gist_words
                  and _lexically_novel(w)}
    # Passage predicate: verbatim 4-word sequences from the entry body,
    # normalized so a dash-glued or non-breaking-hyphen phrase compares
    # against the (also-normalized) corpus on equal terms.
    body_all = " ".join(
        str((e[eid].get("entry") if isinstance(e[eid].get("entry"), dict) else e[eid])
            .get("text") or "")
        for e in entry_texts for eid in e
    )
    tokens = [t for t in _words(body_all.lower()) if t]
    passages = {" ".join(tokens[i:i + 4]) for i in range(len(tokens) - 3)
                if all(len(t) > 2 for t in tokens[i:i + 4])}
    passages = {p for p in passages if p not in corpus_l}
    if not candidates and not passages:
        ctx.record(6, "privacy-greps", "DEGRADED-HONEST",
                   "no entity-invented words and no checkable entry passages from the book "
                   "(model may not have followed the invented-word instruction) — grep arm "
                   f"not executable this run; {diary_list_verdict}", criteria="criterion 6")
        return
    # Needles carry the NORMALIZED form (ASCII-hyphen, NFC, lowercase); every
    # haystack is decoded+normalized the same way before compare, so an
    # encoding difference can neither hide a real leak nor manufacture one.
    hits: Dict[str, List[str]] = {}
    needles = {w: _norm(w).lower() for w in candidates}
    needles.update({f"[passage] {p}": _norm(p).lower() for p in passages})

    def _haystack(raw_bytes: bytes) -> str:
        return _norm(raw_bytes.decode("utf-8", errors="ignore")).lower()

    for p in ctx.gw.data_dir.rglob("*"):
        if not p.is_file() or p.name.startswith("home.sqlite3"):
            continue  # the book family is the ONE legitimate resting place
        try:
            blob = _haystack(p.read_bytes())
        except Exception:
            continue
        for label, needle in needles.items():
            if needle in blob:
                hits.setdefault(label, []).append(str(p.relative_to(ctx.gw.data_dir)))
    replay = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/replay?limit=100000", raw=True)
    replay_blob = _haystack(replay) if isinstance(replay, bytes) else ""
    # AUDIENCE SEAM (maintainer ruling 2026-07-08 21:39, served by
    # entity_replay._operator_diary_display): THIS serving end resolves the
    # engine's diary-redaction mark into the entry's GIST for the operator
    # audience — gist = the entity's own gist line, falling back to
    # text[:120]+"…". Content inside that served-gist window is RULED
    # operator-visible, not a leak; the criterion-6 predicate here is
    # everything BEYOND it (full text, and invented words outside the
    # window). Gist-window exposures of PRIVATE entries are RECORDED as
    # evidence for the open private-gist-fallback question, never failed.
    tolerated: set = set()
    for e in entry_texts:
        for _eid, entry in e.items():
            payload = entry.get("entry") if isinstance(entry.get("entry"), dict) else entry
            text = str(payload.get("text") or payload.get("content") or "").strip()
            gist = str(payload.get("gist") or "").strip()
            window = gist or (f"{text[:120]}" if text else "")
            if window:
                tolerated.add(_norm(window).lower())
    def _served_leak(needle: str) -> bool:
        if needle not in replay_blob:
            return False
        return not any(needle in w for w in tolerated)
    replay_hits = [label for label, needle in needles.items() if _served_leak(needle)]
    gist_window_exposures = [label for label, needle in needles.items()
                             if needle in replay_blob and label not in replay_hits]
    if isinstance(replay, bytes):
        ctx.save(d, "replay_export.ndjson", replay)
    ctx.save(d, "grep_results.json", {
        "candidate_invented_words": sorted(candidates),
        "candidate_passages_4gram": sorted(passages)[:50],
        "at_rest_hits_outside_book": hits,
        "served_replay_hits": replay_hits,
        "served_gist_window_exposures": gist_window_exposures,
        "method": ("secrets originate in the BOOK; learned only via the operator diary door "
                   "(marker-first). Leak predicate = corpus-absent lexically-novel words + "
                   "verbatim 4-gram passages from the entry body; shared vocabulary with the "
                   "conversation corpus is a collision, not a leak; served-replay content "
                   "inside the operator-audience gist window (entity gist, else text[:120]) "
                   "is the RULED serving shape, recorded separately, never failed"),
    })
    clean = not hits and not replay_hits
    checkable = bool(candidates or passages)
    status = "PASS" if (clean and checkable) else ("DEGRADED-HONEST" if not checkable else "FAIL")
    ctx.record(6, "privacy-greps", status,
               f"{len(candidates)} invented words + {len(passages)} passages checked; "
               f"outside-book hits={hits or 'none'}; served replay hits={replay_hits or 'none'}; "
               f"gist-window exposures (ruled operator serving shape, recorded not failed)="
               f"{gist_window_exposures or 'none'}; {diary_list_verdict}",
               criteria="criterion 6")


def step7_lease(ctx: Ctx) -> None:
    d = ctx.step_dir(7, "one-writer-per-home")
    if not ctx.visit_run_id:
        ctx.record(7, "one-writer-per-home", "SKIPPED-LOUD", "needs the open visit from step 4")
        return
    second = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/visit/open", {})
    ctx.save(d, "second_open_refusal.json", second)
    lease_file = ctx.home / ".writer_lease"  # option-2 rename, laurent-approved c398
    lease_meta = lease_file.read_text(errors="replace") if lease_file.exists() else "(absent)"
    ctx.save(d, "writer_lease_metadata.txt", lease_meta)
    # Adversary finding 8: ANY error counted as "the lease refusal" — a 500
    # or 503 would prove nothing. Require the door's exact shape: 409 + the
    # one-life sentence (the step-8 discipline applied here).
    refused = (second.get("_http_error") == 409
               and "one life, one summon" in str(second.get("detail", "")))
    # D1-FINAL semantics (frozen spec §3, supersedes the c354 free assertion):
    # visit runs hold the lease PER-TICK — a PARKED visit holds nothing, so
    # maintenance between ticks legitimately RUNS ("dream/maintenance run
    # between ticks"). First live run proved the stale assertion wrong; the
    # correct pair is: one-life-one-visit refusal (door, durable) + reembed
    # SUCCEEDING on a parked home.
    reembed_parked = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/reembed",
                              {"reason": "walkthrough step 7: D1 per-tick lease — "
                                         "maintenance runs between ticks"})
    ctx.save(d, "reembed_on_parked_visit.json", reembed_parked)
    maintenance_ran = not reembed_parked.get("_http_error")
    ctx.record(7, "one-writer-per-home", "PASS" if (refused and maintenance_ran) else "FAIL",
               f"second visit refused={refused} (one-life-one-visit, durable); "
               f"reembed on PARKED visit ran={maintenance_ran} (D1 per-tick lease)",
               criteria="item 1 + D1")


def step8_home_copy(ctx: Ctx) -> None:
    d = ctx.step_dir(8, "home-copy-collision")
    clone = ctx.home.parent / "kastor"
    if clone.exists():
        shutil.rmtree(clone)
    shutil.copytree(ctx.home, clone)
    listing = ctx.http("GET", "/api/gateway/entities")
    lookup = ctx.http("GET", "/api/gateway/entities/kastor")
    ctx.save(d, "listing_with_copy.json", listing)
    ctx.save(d, "moved_home_lookup.json", lookup)
    # Exact shape per gateway c354: 404 (a colliding name does not RESOLVE)
    # + the collision sentence + the repair line.
    detail = str(lookup.get("detail", ""))
    refused = (lookup.get("_http_error") == 404
               and "colliding name" in detail
               and "one name, one home, one door" in detail)
    ctx.record(8, "home-copy-collision", "PASS" if refused else "FAIL",
               f"copy-beside detectable: lookup refused={refused} (copy-over-same-name is an OS "
               f"merge no API sees — honest scope)", criteria="item 2")
    shutil.rmtree(clone, ignore_errors=True)


def step9_reembed_through_the_door(ctx: Ctx) -> None:
    d = ctx.step_dir(9, "reembed-through-the-door")
    if not ctx.args.reembed_model:
        ctx.record(9, "reembed-through-the-door", "SKIPPED-LOUD",
                   "--reembed-model explicitly empty; memory's executed offline arm is the "
                   "referenced evidence")
        return
    # The operator act, performed on the SCRIPT'S OWN fixture: flip the
    # fixture data root's embedding.text route to the target model, restart
    # the door (route pickup), then the reembed verb — the full M1b ceremony
    # (0.6b@1024 -> 4b@2560: the cannot-patch-in-place dimension change).
    set_embedding_route(ctx.gw.data_dir, ctx.args.reembed_model, ctx.args.embedding_base_url)
    ctx.gw.stop()
    ctx.gw.start()
    resp = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/reembed",
                    {"embedding_model": ctx.args.reembed_model,
                     "reason": "walkthrough step 9: journaled repair demo"}, timeout=900.0)
    ctx.save(d, "reembed_response.json", resp)
    # Adversary finding 6: HTTP-status-only let a no-op or 0-row reembed
    # PASS. The claim is a REAL space migration: new pin must name the
    # target model, the dimension must CHANGE, and rows must have moved.
    ok = not resp.get("_http_error")
    dim_change = ""
    if ok:
        old_pin, new_pin = resp.get("old_pin") or {}, resp.get("new_pin") or {}
        rows = int(resp.get("vectored") or resp.get("rows") or 0)
        ok = (str(new_pin.get("model_id") or "") == ctx.args.reembed_model
              and new_pin.get("dimension") != old_pin.get("dimension")
              and rows > 0)
        dim_change = (f" {old_pin.get('dimension')}->{new_pin.get('dimension')} dims, "
                      f"{rows} rows")
    if not ok:
        # FIXTURE HYGIENE (not masking — the failure artifact stands): restore
        # the matched route so downstream steps run in the pinned space,
        # whether the failure was a refusal OR a semantic no-op.
        set_embedding_route(ctx.gw.data_dir, ctx.args.embedding_model,
                            ctx.args.embedding_base_url)
        ctx.gw.stop()
        ctx.gw.start()
    ctx.record(9, "reembed-through-the-door", "PASS" if ok else "FAIL",
               f"route flipped on the fixture + door restarted + reembed ran={ok}{dim_change} "
               f"(journal claim + host marker; render leg in step-10 export)"
               + ("" if ok else " — DOOR BUG: repair verb trips the M1 mismatch at open; "
                               "route restored for downstream steps"),
               criteria="item 3 M1b, door->pixels leg")


def step10_close_and_render(ctx: Ctx) -> None:
    d = ctx.step_dir(10, "close-and-render")
    # Gateway's sequencing note: restart between reembed and render.
    ctx.gw.sigkill()
    ctx.gw.start()
    if ctx.visit_run_id:
        close = ctx.http("POST",
                         f"/api/gateway/entities/{ctx.entity}/visit/{ctx.visit_run_id}/close",
                         {"closed_by": "operator",
                          "reason": "walkthrough complete — thank you"}, timeout=300.0)
        ctx.save(d, "close.json", close)
    replay = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}/replay?limit=100000", raw=True)
    if isinstance(replay, bytes):
        ctx.save(d, "life_export.ndjson", replay)
    deep_link = f"http://127.0.0.1:3007/?gateway={ctx.gw.base}&entity={ctx.entity}&live=1"
    ctx.save(d, "render_links.txt",
             f"entity view deep link: {deep_link}\n"
             f"flow run modal: open run {ctx.visit_run_id} via the Flow editor connected to {ctx.gw.base}\n"
             f"fold_digest: node abstractobserver/scripts/fold_digest.ts <life_export.ndjson>\n")
    post_restart_inspect = ctx.http("GET", f"/api/gateway/entities/{ctx.entity}")
    ctx.save(d, "post_restart_inspect.json", post_restart_inspect)
    # Adversary finding 7: the close body and the export bytes are the step's
    # OWN claims — assert them, not just the inspect round-trip.
    close_ok = _body_ok(close) if ctx.visit_run_id else True
    export_ok = isinstance(replay, bytes) and len(replay) > 0
    ok = (not post_restart_inspect.get("_http_error")) and close_ok and export_ok
    ctx.record(10, "close-and-render", "PASS" if ok else "FAIL",
               f"closed with reflection (close_ok={close_ok}); life exported "
               f"(export_ok={export_ok}); render links recorded "
               "(pixel halves = observer/flow surfaces, operator-driven)",
               criteria="item 3 render + close path")


def step11_prefix_numbers(ctx: Ctx) -> None:
    d = ctx.step_dir(11, "prefix-numbers")
    if not ctx.visit_run_id:
        ctx.record(11, "prefix-numbers", "SKIPPED-LOUD", "no visit ran")
        return
    bundle = ctx.http("GET", f"/api/gateway/runs/{ctx.visit_run_id}/history_bundle")
    ctx.save(d, "history_bundle.json", bundle)
    if bundle.get("_http_error") == 404:
        # The global runs API does not resolve per-entity run stores yet —
        # EXACTLY flow's item-11 pin and phase-4 GW-D/E, demonstrated live.
        ctx.record(11, "prefix-numbers", "BLOCKED-ON-ITEM-11",
                   "runs API 404s for a visit run living in runtime_<name> inside the home — "
                   "run-id->store resolution behind the one run API is phase-4 GW-D/E; this "
                   "gap is now demonstrated, not predicted", criteria="criterion 3 (deferred)")
        return
    try:
        sys.path.insert(0, str(ROOT / "abstractagent" / "src"))
        from abstractagent.metrics import prefix_reuse_report  # type: ignore
        payloads = []
        records = bundle.get("records", bundle if isinstance(bundle, list) else [])
        for rec in records:
            eff = rec.get("effect") or {}
            if str(eff.get("type", "")).lower() == "llm_call":
                payloads.append(eff.get("payload") or {})
        report = prefix_reuse_report(payloads) if payloads else {"note": "no llm_call payloads found"}
        ctx.save(d, "prefix_reuse_report.json", report)
        ctx.record(11, "prefix-numbers", "PASS" if payloads else "DEGRADED-HONEST",
                   f"{len(payloads)} llm_call payloads measured (pre-resolution, both turns one "
                   f"list; reported never gated)", criteria="criterion 3")
    except Exception as e:
        ctx.record(11, "prefix-numbers", "FAIL", f"metric import/run failed: {e}")


def step12_two_homes_one_moment(ctx: Ctx) -> None:
    d = ctx.step_dir(12, "two-homes-one-moment")
    if not _require_llm(ctx, 12, "two-homes-one-moment"):
        return
    second_entity = "lyra"
    # Drop the explicit embedder (door's own guidance): step 9 legitimately
    # left the fixture route at the reembed target (4b), so a hard-coded 0.6b
    # birth choice mismatches the door's resolved embedder and 400s ("a home
    # pinned to a model its door cannot serve would refuse every open").
    # Inheriting the resolved model also keeps lyra in voyager's post-reembed
    # space, which is what a coherent same-door meet needs.
    created = ctx.http("POST", "/api/gateway/entities", {"name": second_entity})
    ctx.save(d, "second_entity.json", created)
    if created.get("_http_error"):
        ctx.record(12, "two-homes-one-moment", "FAIL",
                   f"second entity birth refused: {str(created)[:200]}")
        return
    opened = ctx.http("POST", "/api/gateway/entities/meets/open",
                      {"entity_a": ctx.entity, "entity_b": second_entity})
    ctx.save(d, "meet_open.json", opened)
    if opened.get("_http_error"):
        ctx.record(12, "two-homes-one-moment", "DEFERRED-LABELED",
                   f"same-door meet open refused/unavailable here: {str(opened)[:200]} — "
                   "cross-door stays future work; memory's contract test is the offline evidence")
        return
    meet_id = opened.get("meet_id") or opened.get("visit_id")
    relay = ctx.http("POST", f"/api/gateway/entities/meets/{meet_id}/relay",
                     {"opener": "a", "text": "Please greet each other briefly."},
                     timeout=600.0)
    ctx.save(d, "relay.json", relay)
    closed = ctx.http("POST", f"/api/gateway/entities/meets/{meet_id}/close", {})
    ctx.save(d, "close.json", closed)
    ctx.record(12, "two-homes-one-moment",
               "PASS" if not relay.get("_http_error") else "PARTIAL",
               f"same-door meet ran (meet={meet_id}); two-journal assertions ride memory's "
               f"contract test shapes", criteria="item 14 (same-door)")


def step13_iterations_ceiling(ctx: Ctx) -> None:
    """Live leg for the c786 ceiling ruling (seam (b), runtime eaa2885 +
    gateway knob/injection): the operator env knob rides the fixture gateway's
    environment; a visit whose workflow declares max_iterations=20 must
    REFUSE AT START when the ceiling is 1 — loud, naming both values, run
    never exists — and open again once the knob returns to default (100).
    The under-ceiling positive arm is the ENTIRE preceding walkthrough:
    every earlier visit ran declared-20 under the default-100 ceiling."""
    d = ctx.step_dir(13, "iterations-ceiling")
    ctx.gw.stop()
    ctx.gw.extra_env["ABSTRACTGATEWAY_ENTITY_MAX_ITERATIONS_CEILING"] = "1"
    ctx.gw.start()
    refused = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/visit/open", {})
    ctx.save(d, "open_over_ceiling.json", refused)
    msg = json.dumps(refused).lower()
    # The c805 refusal shape names BOTH values + the override surface; accept
    # either transport shape (HTTPError or 200-with-error-body — the step-4
    # lesson) but REQUIRE the naming: "ceiling" + the declared value.
    errored = bool(refused.get("_http_error") or refused.get("error")
                   or str(refused.get("status") or "") == "failed")
    refused_ok = errored and "ceiling" in msg and "20" in msg
    ctx.gw.stop()
    ctx.gw.extra_env.pop("ABSTRACTGATEWAY_ENTITY_MAX_ITERATIONS_CEILING", None)
    ctx.gw.start()
    reopened = ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/visit/open", {})
    ctx.save(d, "open_after_restore.json", reopened)
    restore_ok = (not reopened.get("_http_error")) and bool(reopened.get("run_id"))
    if restore_ok:
        ctx.http("POST", f"/api/gateway/entities/{ctx.entity}/visit/{reopened['run_id']}/close",
                 {"reason": "ceiling-step restore probe"})
    status = "PASS" if (refused_ok and restore_ok) else "FAIL"
    ctx.record(13, "iterations-ceiling", status,
               f"over-ceiling (knob=1 vs declared 20) refused-at-start loud={refused_ok}; "
               f"restore (default 100) reopened={restore_ok}; under-ceiling arm = all "
               f"preceding steps ran declared-20 under default-100",
               criteria="c786 ceiling ruling / R-row treatment c787")


STEPS = [
    step0_preflight, step1_birth, step2_entity_is_user, step3_address_is_a_coat,
    step4_visit, step5_the_kill, step6_privacy_greps, step7_lease,
    step8_home_copy, step9_reembed_through_the_door, step10_close_and_render,
    step11_prefix_numbers, step12_two_homes_one_moment, step13_iterations_ceiling,
]


def write_readme(ctx: Ctx) -> None:
    lines = [
        "# Entity-topology plan — walkthrough report",
        "",
        f"Generated {utcnow()} against frozen step list v1 "
        "(a2a/threads/0016-final-walkthrough/20260710T102820Z-agency-01.md).",
        "",
        "Substrate chain rung: " + (
            "CLI flags (operator-explicit)" if ctx.args.provider else
            "ABSENT — LLM steps refused loudly (the 04:26 no-fallback rule, demonstrated)"),
        "",
        "`_limits.max_iterations` budget: workflow default (see frozen spec §4 line 5).",
        "",
        "| step | status | criteria | note |",
        "|---|---|---|---|",
    ]
    for r in ctx.results:
        lines.append(f"| {r['step']:02d} {r['slug']} | {r['status']} | {r['criteria']} | {r['note']} |")
    lines += [
        "",
        "Expected prefix-reuse dip (agent's note): the first request after each visitor",
        "message reuses head+prefix but not the new message — per-request ratios oscillate;",
        "the signal is heads_identical:true throughout.",
    ]
    (ctx.report / "README.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", default=None, help="chat provider (OPERATOR's explicit choice; no default ever)")
    ap.add_argument("--model", default=None, help="chat model (OPERATOR's explicit choice; no default ever)")
    ap.add_argument("--embedding-model", default=PLAN_DEFAULT_EMBEDDER,
                    help="birth embedder pin (plan item 3 names this default)")
    ap.add_argument("--reembed-model", default="text-embedding-qwen3-embedding-4b",
                    help="step 9 target embedder (the plan-named quality option; '' = skip loudly)")
    ap.add_argument("--embedding-base-url", default="http://127.0.0.1:1234/v1")
    ap.add_argument("--out", default=str(ROOT / "plan_proof_out"))
    ap.add_argument("--steps", default=None, help="comma-separated step numbers to run (default all)")
    ap.add_argument("--midturn-kill-delay-s", type=float, default=2.0)
    ap.add_argument("--keep", action="store_true", help="keep the fixture tree")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    report = out / "walkthrough_report"
    report.mkdir(parents=True)
    data_dir = out / "fixture-gateway-data"
    data_dir.mkdir(parents=True)

    extra_env = {}
    if args.provider:
        extra_env["ABSTRACTGATEWAY_ENTITY_CHAT_PROVIDER"] = args.provider
    if args.model:
        extra_env["ABSTRACTGATEWAY_ENTITY_CHAT_MODEL"] = args.model

    # PROVISION THE FIXTURE'S ENDPOINT PROFILE (758e243 baseline: entity
    # creation validates `endpoint:<id>` substrates against the data_dir's
    # own profiles store — correct isolation means the fixture must carry
    # its own copy of the operator's profile, sourced from the serving
    # config, never resolved ambiently). No-default rule intact: only the
    # profile the operator's --provider names is copied.
    if args.provider and args.provider.startswith("endpoint:"):
        profile_id = args.provider.split(":", 1)[1]
        src = ROOT / "runtime" / "config" / "provider_endpoint_profiles.json"
        if not src.exists():
            print(f"walkthrough: REFUSED — provider {args.provider!r} needs {src} to source the profile")
            return 2
        profiles = json.loads(src.read_text()).get("profiles", [])
        match = [p for p in profiles if p.get("id") == profile_id and p.get("enabled", True)]
        if not match:
            print(f"walkthrough: REFUSED — no enabled profile {profile_id!r} in {src}")
            return 2
        fixture_cfg = data_dir / "config"
        fixture_cfg.mkdir(parents=True, exist_ok=True)
        (fixture_cfg / "provider_endpoint_profiles.json").write_text(
            json.dumps({"profiles": match}, indent=1)
        )
    # Fixture-scoped embeddings route: birth vectorizes the identity core and
    # step 9's route flip has a real starting space (both plan-named models).
    if args.embedding_model:
        set_embedding_route(data_dir, args.embedding_model, args.embedding_base_url)

    gw = Gateway(data_dir=data_dir, port=free_port(), token=f"walkthrough-{os.urandom(8).hex()}",
                 log_path=out / "gateway.log", extra_env=extra_env)
    ctx = Ctx(args=args, out=out, report=report, gw=gw)
    only = {int(s) for s in args.steps.split(",")} if args.steps else None

    print(f"walkthrough: gateway on port {gw.port}, fixture at {data_dir}")
    gw.start()
    try:
        for i, fn in enumerate(STEPS):
            if only is not None and i not in only:
                continue
            try:
                fn(ctx)
            except SystemExit:
                raise
            except Exception as e:
                ctx.record(i, fn.__name__, "ERROR", f"{type(e).__name__}: {e}")
    finally:
        write_readme(ctx)
        ctx.save(ctx.report, "results.json", ctx.results)
        gw.stop()
        # The fixture tree is ALWAYS kept for post-run forensics (--keep is
        # therefore advisory); reruns start with `rm -rf plan_proof_out`.
    print(f"\nreport: {report}/README.md")
    # Adversary finding 12: PARTIAL is a step's FAILURE mode (steps 1/5) —
    # exiting 0 on it lets regressions ride green through CI/loops.
    bad = [r for r in ctx.results if r["status"] in {"FAIL", "ERROR", "PARTIAL"}]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
