"""Experiments for the Windows "any_except_denied" backend (see anyexcept_proto.py).

    python anyexcept_tests.py [A B1 B2 B3 C D WORK OUTSIDE ...]   (default: all)

Everything it creates, and every ACL / label it changes, lives under ./lab.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anyexcept_proto as P  # noqa: E402

_spec = importlib.util.spec_from_file_location("af_sandbox", r"C:\abstractframework\AbstractFramework\abstractcore\abstractcore\tools\sandbox.py")
SB = importlib.util.module_from_spec(_spec)
sys.modules["af_sandbox"] = SB
_spec.loader.exec_module(SB)

PY = os.path.join(os.environ["APPDATA"], "uv", "tools", "abstractgateway", "Scripts", "python.exe")
PROBE = os.path.join(HERE, "probe.py")
L = os.path.join(HERE, "lab")
USER = os.environ["USERNAME"]
FAILS = []


def j(*p):
    return os.path.join(L, *p)


def say(*a):
    print(*a, flush=True)


def icacls(path):
    out = subprocess.run(["icacls", path], capture_output=True, text=True).stdout
    return "\n".join(line.rstrip() for line in out.splitlines() if line.strip() and not line.startswith("Successfully"))


# ---------------------------------------------------------------------------------------
# lab
# ---------------------------------------------------------------------------------------
def dd(tok):
    """Default DACL for a restricting set without the user SID (else the child dies 0xC0000142)."""
    m = P.mirror_sids()
    P.set_default_dacl(tok, [m[0], "S-1-5-18", [s for s in m if s.startswith("S-1-5-5-")][0], "S-1-5-12"])


def wipe_lab():
    if os.path.exists(L):
        subprocess.run(["icacls", L, "/reset", "/T", "/C", "/Q"], capture_output=True)
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", L], capture_output=True)
        # labels may survive /reset: clear and retry
        if os.path.exists(L):
            for root, dirs, files in os.walk(L):
                for n in dirs + files:
                    try:
                        P.set_label(os.path.join(root, n), None)
                    except OSError:
                        pass
            shutil.rmtree(L, ignore_errors=True)


def write(p, text="data\n"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


def build_lab(bulk=0):
    wipe_lab()
    for rel, text in [
        (("world", "plain.txt"), "plain world file"),
        (("refused", "secret.txt"), "TOP SECRET refused"),
        (("refused", "rwin", "f.txt"), "rw row inside refused"),
        (("refused", "roin", "f.txt"), "ro row inside refused"),
        (("refused", "protchild", "p.txt"), "protected child of refused"),
        (("rorow", "f.txt"), "ro row file"),
        (("rorow", "rwin", "f.txt"), "rw inside ro"),
        (("tie", "f.txt"), "refused+rw same path"),
        (("tiero", "f.txt"), "ro+rw same path"),
        (("onefile", "secret1.txt"), "SECRET single file"),
        (("onefile", "victim_replace.txt"), "SECRET (replace target)"),
        (("onefile", "victim_delete.txt"), "SECRET (delete target)"),
        (("onefile", "sibling_delete.txt"), "plain sibling"),
        (("anc", "rorow2", "f.txt"), "ro row whose ancestor is in the writable world"),
        (("onefile", "other.txt"), "sibling of refused file"),
        (("pw", "readme.txt"), "private workspace"),
        (("pw", ".tmp", "t.txt"), "tmp"),
    ]:
        write(j(*rel), text + "\n")
    for i in range(bulk):
        write(j("refused", "bulk", f"{i // 100}", f"f{i}.txt"), "bulk\n")
    # a child that does not inherit from refused (protected DACL) - set BEFORE the rules
    subprocess.run(["icacls", j("refused", "protchild"), "/inheritance:d"], capture_output=True)
    # junction outside the refused folder pointing into it; symlink attempt; hard link
    subprocess.run(["cmd", "/c", "mklink", "/J", j("world", "jn"), j("refused")], capture_output=True)
    sl = subprocess.run(["cmd", "/c", "mklink", "/D", j("world", "sl"), j("refused")], capture_output=True, text=True)
    os.link(j("refused", "secret.txt"), j("world", "hl.txt"))
    return (sl.stdout + sl.stderr).strip()


def lab_spec(default_mode="rw"):
    return SB.normalize_spec(SB.SandboxSpec(
        private_workspace=j("pw"), posture="any_except_denied", default_mode=default_mode,
        allowed=(SB.SandboxRow(j("refused", "rwin"), "rw"), SB.SandboxRow(j("refused", "roin"), "ro"),
                 SB.SandboxRow(j("rorow"), "ro"), SB.SandboxRow(j("rorow", "rwin"), "rw"),
                 SB.SandboxRow(j("tie"), "rw"), SB.SandboxRow(j("tiero"), "ro"), SB.SandboxRow(j("tiero"), "rw"),
                 SB.SandboxRow(j("anc", "rorow2"), "ro")),
        refused=(j("refused"), j("tie"), j("onefile", "secret1.txt"), j("onefile", "victim_replace.txt"), j("onefile", "victim_delete.txt")),
    ))


def rules_for(spec):
    base, builtin = SB._ordered_rules(spec, user_roots=())
    out = []
    for r in base + builtin:
        if r.action == "read" and not r.path.lower().startswith(L.lower()):
            continue  # never touch ACLs outside the lab (see report: emit "read" only under a refused row)
        out.append((r.action, r.path))
    return out


def env_for(spec):
    env = dict(os.environ)
    tmp = SB.private_tmpdir(spec)
    for k in ("TMP", "TEMP", "TMPDIR"):
        env[k] = tmp
    return env


def probe(token, ops, env=None, cwd=None):
    opsfile = os.path.join(HERE, "_out", f"ops_{time.time_ns()}.json")
    os.makedirs(os.path.dirname(opsfile), exist_ok=True)
    with open(opsfile, "w") as f:
        json.dump(ops, f)
    if token is None:
        p = subprocess.run([PY, PROBE, "@" + opsfile], capture_output=True, text=True, env=env, cwd=cwd)
        rc, out = p.returncode, p.stdout + p.stderr
    else:
        rc, out = P.run([PY, PROBE, "@" + opsfile], token, env=env, cwd=cwd)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return [f"probe failed rc={rc}: {out[-400:]}"] * len(ops)


def verdict(res):
    if isinstance(res, dict):
        return "ok"
    return "ok" if str(res).startswith("ok") else "DENY"


def check_table(title, token, cases, env=None):
    """cases: [(label, op, expected 'ok'|'DENY'|'?')]"""
    say(f"\n--- {title}")
    res = probe(token, [c[1] for c in cases], env=env)
    for (label, op, exp), r in zip(cases, res):
        got = verdict(r)
        mark = "    " if exp == "?" else ("PASS" if got == exp else "FAIL")
        if mark == "FAIL":
            FAILS.append(f"{title}: {label}")
        say(f"  {mark} {label:58s} expect={exp:4s} got={got:4s} {str(r)[:70]}")
    return res


def cmd_table(title, token, cases, env=None):
    say(f"\n--- {title}")
    for case in cases:
        label, line, exp = case[:3]
        rc, out = P.run(["cmd", "/d", "/s", "/c", line], token, env=env, cwd=L)
        got = "ok" if rc == 0 else "DENY"
        if len(case) > 3:  # verifier run OUTSIDE the sandbox (cmd's del returns 0 even when it fails)
            got = "ok" if case[3]() else "DENY"
        mark = "    " if exp == "?" else ("PASS" if got == exp else "FAIL")
        if mark == "FAIL":
            FAILS.append(f"{title}: {label}")
        say(f"  {mark} {label:44s} expect={exp:4s} rc={rc:<3d} {' '.join(out.split())[:80]}")


def apply(spec, owner_fix=True, label_low=False, **fixes):
    rules = rules_for(spec)
    t0 = time.perf_counter()
    applied = P.apply_rules(rules, owner_fix=owner_fix, **fixes)
    t1 = time.perf_counter()
    labelled = []
    if label_low:
        for action, path in rules:
            if action == "rw":
                P.set_label(path, P.LOW_IL)
                labelled.append(path)
    say(f"  applied {len(applied)} rules in {t1 - t0:.2f}s (+labels {time.perf_counter() - t1:.2f}s on {len(labelled)} rw roots)")
    for a, p in rules:
        say(f"    {a:5s} {os.path.relpath(p, L)}  sid={P.rule_sid(a, p)}")
    return rules, applied, labelled


def matrix_cases(mode):
    rw = mode == "rw"
    W = "ok" if rw else "DENY"  # writes in the plain world
    s = j("refused", "secret.txt")
    return [
        ("world: read", ["read", j("world", "plain.txt")], "ok"),
        ("world: create file", ["create", j("world", f"new_{mode}.txt")], W),
        ("world: mkdir", ["mkdir", j("world", f"d_{mode}")], W),
        ("refused: read file", ["read", s], "DENY"),
        ("refused: list", ["list", j("refused")], "DENY"),
        ("refused: stat file", ["stat", s], "DENY"),
        ("refused: create", ["create", j("refused", "x.txt")], "DENY"),
        ("refused: append", ["append", s], "DENY"),
        ("refused: mkdir", ["mkdir", j("refused", "d")], "DENY"),
        ("refused: rename file out", ["rename", s, j("world", "stolen.txt")], "DENY"),
        ("refused: delete file", ["delete", s], "DENY"),
        ("refused ⊃ rw: read", ["read", j("refused", "rwin", "f.txt")], "ok"),
        ("refused ⊃ rw: list", ["list", j("refused", "rwin")], "ok"),
        ("refused ⊃ rw: create", ["create", j("refused", "rwin", f"n_{mode}.txt")], "ok"),
        ("refused ⊃ rw: append", ["append", j("refused", "rwin", "f.txt")], "ok"),
        ("refused ⊃ rw: delete own new file", ["delete", j("refused", "rwin", f"n_{mode}.txt")], "ok"),
        ("refused ⊃ rw: mkdir", ["mkdir", j("refused", "rwin", f"d_{mode}")], "ok"),
        ("refused ⊃ ro: read", ["read", j("refused", "roin", "f.txt")], "ok"),
        ("refused ⊃ ro: create", ["create", j("refused", "roin", "n.txt")], "DENY"),
        ("refused ⊃ ro: append", ["append", j("refused", "roin", "f.txt")], "DENY"),
        ("refused ⊃ ro: delete", ["delete", j("refused", "roin", "f.txt")], "DENY"),
        ("ro row: read", ["read", j("rorow", "f.txt")], "ok"),
        ("ro row: list", ["list", j("rorow")], "ok"),
        ("ro row: create", ["create", j("rorow", "n.txt")], "DENY"),
        ("ro row: append", ["append", j("rorow", "f.txt")], "DENY"),
        ("ro row: delete file", ["delete", j("rorow", "f.txt")], "DENY"),
        ("ro row: rename file", ["rename", j("rorow", "f.txt"), j("rorow", "g.txt")], "DENY"),
        ("ro row: mkdir", ["mkdir", j("rorow", "d")], "DENY"),
        ("ro ⊃ rw: create", ["create", j("rorow", "rwin", f"n_{mode}.txt")], "ok"),
        ("ro ⊃ rw: append", ["append", j("rorow", "rwin", "f.txt")], "ok"),
        ("tie refused+rw: read", ["read", j("tie", "f.txt")], "DENY"),
        ("tie refused+rw: create", ["create", j("tie", "n.txt")], "DENY"),
        ("tie ro+rw: read", ["read", j("tiero", "f.txt")], "ok"),
        ("tie ro+rw: create", ["create", j("tiero", "n.txt")], "DENY"),
        ("refused FILE: read", ["read", j("onefile", "secret1.txt")], "DENY"),
        ("refused FILE: append", ["append", j("onefile", "secret1.txt")], "DENY"),
        ("refused FILE: sibling read", ["read", j("onefile", "other.txt")], "ok"),
        ("refused FILE: sibling list dir", ["list", j("onefile")], "ok"),
        ("protected child of refused: read", ["read", j("refused", "protchild", "p.txt")], "DENY"),
        ("junction world\\jn -> refused: read", ["read", j("world", "jn", "secret.txt")], "DENY"),
        ("junction world\\jn -> refused ⊃ rw: read", ["read", j("world", "jn", "rwin", "f.txt")], "ok"),
        ("hard link world\\hl.txt -> refused\\secret.txt: read", ["read", j("world", "hl.txt")], "DENY"),
        ("private workspace: create", ["create", j("pw", f"n_{mode}.txt")], "ok"),
        ("private .tmp: create", ["create", j("pw", ".tmp", f"n_{mode}.txt")], "ok"),
        # parent-FILE_DELETE_CHILD paths (rights on the parent, not on the rule's object)
        ("refused FILE: replace by rename-over", ["replace", j("pw", "readme.txt"), j("onefile", "victim_replace.txt")], "DENY"),
        ("refused FILE: delete", ["delete", j("onefile", "victim_delete.txt")], "DENY"),
        ("refused FILE: plain sibling delete", ["delete", j("onefile", "sibling_delete.txt")], W),
        ("ro row ROOT: rename the row folder", ["rename", j("tiero"), j("tiero_moved")], "DENY"),
        ("refused ROOT: rename the refused folder", ["rename", j("tie"), j("tie_moved")], "DENY"),
        ("ro row: rename its ANCESTOR (world\\anc)", ["rename", j("anc"), j("anc_moved")], "?"),
        ("  then mkdir anc\\rorow2 again", ["mkdir", j("anc")], "?"),
        ("  and write a file at the ro row's path", ["mkdir", j("anc", "rorow2")], "?"),
        ("  (create anc\\rorow2\\f2.txt)", ["create", j("anc", "rorow2", "f2.txt")], "?"),
    ]


def restore_moves():
    for a, b in [("tiero_moved", "tiero"), ("tie_moved", "tie")]:
        if os.path.exists(j(a)) and not os.path.exists(j(b)):
            os.rename(j(a), j(b))
    if os.path.exists(j("anc_moved")):
        shutil.rmtree(j("anc"), ignore_errors=True)
        os.rename(j("anc_moved"), j("anc"))
    if not os.path.exists(j("pw", "readme.txt")):
        write(j("pw", "readme.txt"), "private workspace\n")


# ---------------------------------------------------------------------------------------
# A: default_mode rw
# ---------------------------------------------------------------------------------------
def sec_A():
    say("\n================ A. any_except_denied + rw: mirror token + rule SIDs")
    sl = build_lab(bulk=2000)
    say(f"  mklink /D (symlink) without admin: {sl!r}")
    spec = lab_spec("rw")
    rules, applied, _ = apply(spec)
    say("\n  icacls evidence:")
    for rel in [("refused",), ("refused", "secret.txt"), ("refused", "rwin"), ("refused", "roin"), ("refused", "protchild", "p.txt"),
                ("rorow",), ("rorow", "rwin"), ("tie",), ("tiero",), ("onefile", "secret1.txt"), ("world", "hl.txt")]:
        say("   " + icacls(j(*rel)).replace("\n", "\n   "))
    sids = [P.rule_sid(a, p) for a, p in rules]
    tok = P.posture_token(sids, "rw")
    env = env_for(spec)
    check_table("A rw: python open()/os ops inside the sandbox", tok, matrix_cases("rw"), env=env)
    restore_moves()
    s = r"refused\secret.txt"
    cmd_table("A rw: cmd builtins inside the sandbox", tok, [
        ("type refused file", f"type {s}", "DENY"),
        ("dir refused", r"dir /b refused", "DENY"),
        ("echo > refused\\new", r"echo x> refused\new.txt", "DENY"),
        ("del refused file", f"del {s}", "DENY", lambda: not os.path.exists(j("refused", "secret.txt"))),
        ("mkdir refused\\d", r"mkdir refused\d", "DENY"),
        ("ren refused file", f"ren {s} s2.txt", "DENY"),
        ("type rw-in-refused", r"type refused\rwin\f.txt", "ok"),
        ("echo > rw-in-refused", r"echo x> refused\rwin\c.txt", "ok"),
        ("del rw-in-refused", r"del refused\rwin\c.txt", "ok"),
        ("mkdir rw-in-refused", r"mkdir refused\rwin\cd", "ok"),
        ("ren rw-in-refused file", r"ren refused\rwin\f.txt f2.txt && ren refused\rwin\f2.txt f.txt", "ok"),
        ("type ro-in-refused", r"type refused\roin\f.txt", "ok"),
        ("echo >> ro-in-refused", r"echo x>> refused\roin\f.txt", "DENY"),
        ("type ro row", r"type rorow\f.txt", "ok"),
        ("echo > ro row", r"echo x> rorow\c.txt", "DENY"),
        ("del ro row file", r"del rorow\f.txt & if exist rorow\f.txt exit 1", "DENY"),
        ("ren ro row file", r"ren rorow\f.txt g.txt", "DENY"),
        ("mkdir ro row\\d", r"mkdir rorow\cd", "DENY"),
        ("echo > world", r"echo x> world\c.txt", "ok"),
        ("type via junction", r"type world\jn\secret.txt", "DENY"),
        ("type hard link", r"type world\hl.txt", "DENY"),
        ("type refused single file", r"type onefile\secret1.txt", "DENY"),
        ("del refused single file", r"del onefile\secret1.txt", "DENY", lambda: not os.path.exists(j("onefile", "secret1.txt"))),
        ("del ro row file (verified outside)", r"del rorow\f.txt", "DENY", lambda: not os.path.exists(j("rorow", "f.txt"))),
    ], env=env)
    say("  (del: cmd's del prints an error but returns 0, hence the 'if exist' checks)")
    # the user's other (unsandboxed) processes are unaffected
    check_table("A rw: the SAME ops from an unsandboxed process (must be unaffected)", None, [
        ("refused: read", ["read", j("refused", "secret.txt")], "ok"),
        ("refused: list", ["list", j("refused")], "ok"),
        ("ro row: append", ["append", j("rorow", "f.txt")], "ok"),
        ("refused FILE: read", ["read", j("onefile", "secret1.txt")], "ok"),
    ])
    # bulk: propagation cost + revert
    t0 = time.perf_counter()
    P.revert_rules(applied)
    say(f"\n  revert of {len(applied)} rules (incl. propagation to 2000 bulk files): {time.perf_counter() - t0:.2f}s")
    say("   after revert: " + icacls(j("refused", "bulk", "0", "f0.txt")).replace("\n", " | "))
    say("   after revert: " + icacls(j("refused")).replace("\n", " | "))


def sec_A_nofix():
    say("\n================ A-nofix. the naive recipe (inheritable ACE on the rule root only)")
    build_lab()
    spec = lab_spec("rw")
    rules, applied, _ = apply(spec, parent_fix=False, walk_protected=False)
    tok = P.posture_token([P.rule_sid(a, p) for a, p in rules], "rw")
    check_table("A-nofix rw (the 'ok' results here are the holes the fixes close)", tok, [
        ("protected child of refused: read", ["read", j("refused", "protchild", "p.txt")], "DENY"),
        ("refused FILE: replace by rename-over", ["replace", j("pw", "readme.txt"), j("onefile", "victim_replace.txt")], "DENY"),
        ("refused FILE: delete", ["delete", j("onefile", "victim_delete.txt")], "DENY"),
        ("ro row ROOT: rename the row folder", ["rename", j("tiero"), j("tiero_moved")], "DENY"),
        ("ro row ROOT: create a new folder at the ro path", ["mkdir", j("tiero")], "DENY"),
    ], env=env_for(spec))
    P.revert_rules(applied)


def sec_A_owner():
    say("\n================ A-owner. the owner's implicit WRITE_DAC (strip the deny from inside)")
    for fix in (False, True):
        build_lab()
        spec = lab_spec("rw")
        rules, applied, _ = apply(spec, owner_fix=fix)
        tok = P.posture_token([P.rule_sid(a, p) for a, p in rules], "rw")
        say(f"\n  owner_fix={fix}: OWNER RIGHTS ACE present on refused = {'S-1-3-4' in icacls(j('refused')) or 'OWNER RIGHTS' in icacls(j('refused'))}")
        cmd_table(f"A-owner owner_fix={fix}", tok, [
            ("icacls replace DACL of refused\\secret.txt", rf"icacls refused\secret.txt /inheritance:r /grant:r {USER}:F", "DENY"),
            ("then type it", r"type refused\secret.txt", "DENY"),
            ("icacls remove deny on ro row file", rf"icacls rorow\f.txt /inheritance:r /grant:r {USER}:F", "DENY"),
            ("then append to ro row file", r"echo x>> rorow\f.txt", "DENY"),
            ("icacls on the refused ROOT (explicit deny)", rf"icacls refused /remove:d *{P.rule_sid('deny', j('refused'))}", "DENY"),
            ("takeown refused file", r"takeown /f refused\secret.txt", "DENY"),
        ], env=env_for(spec))
        check_table(f"A-owner owner_fix={fix}: open WRITE_DAC only + set a NULL DACL, then read", tok, [
            ("open refused\\secret.txt READ_CONTROL only", ["openfile", j("refused", "secret.txt"), 0x20000], "DENY"),
            ("open refused\\secret.txt WRITE_DAC only", ["openfile", j("refused", "secret.txt"), 0x40000], "DENY"),
            ("NULL DACL on refused\\secret.txt", ["nulldacl", j("refused", "secret.txt")], "DENY"),
            ("read refused\\secret.txt", ["read", j("refused", "secret.txt")], "DENY"),
            ("NULL DACL on refused single FILE", ["nulldacl", j("onefile", "secret1.txt")], "DENY"),
            ("read refused single FILE", ["read", j("onefile", "secret1.txt")], "DENY"),
            ("NULL DACL on ro row file", ["nulldacl", j("rorow", "rwin", "..", "f.txt")], "DENY"),
            ("NULL DACL on the refused ROOT folder", ["nulldacl", j("refused")], "DENY"),
            ("list refused ROOT", ["list", j("refused")], "DENY"),
        ], env=env_for(spec))
        say("   refused\\secret.txt now: " + icacls(j("refused", "secret.txt")).replace("\n", " | "))
        P.revert_rules(applied)
    # unsandboxed user can still administer the folders while the OWNER RIGHTS ace is there
    build_lab()
    rules, applied, _ = apply(lab_spec("rw"))
    r = subprocess.run(["icacls", j("refused", "secret.txt"), "/grant", f"{USER}:R"], capture_output=True, text=True)
    say(f"  unsandboxed owner can still edit the DACL with the OWNER RIGHTS ace present: rc={r.returncode}")
    P.revert_rules(applied)


def sec_A_misc():
    say("\n================ A-misc. refused path that does not exist yet")
    build_lab()
    ghost = j("ghost")
    try:
        P.add_rule(ghost, "deny")
        say("  add_rule on a missing path: succeeded (?)")
    except OSError as e:
        say(f"  add_rule on a missing path: {e}")
    # what the sandbox could do if the rule is simply skipped
    spec = lab_spec("rw")
    rules, applied, _ = apply(spec)
    tok = P.posture_token([P.rule_sid(a, p) for a, p in rules] + [P.rule_sid("deny", ghost)], "rw")
    check_table("A-misc: refused ghost path skipped -> the sandbox creates it", tok, [
        ("mkdir ghost", ["mkdir", ghost], "?"),
        ("create ghost\\f", ["create", os.path.join(ghost, "f.txt")], "?"),
    ], env=env_for(spec))
    shutil.rmtree(ghost, ignore_errors=True)
    # placeholder variant: create the folder (empty) and deny it
    os.mkdir(ghost)
    gsid = P.add_rule(ghost, "deny")
    write(os.path.join(ghost, "later.txt"), "appeared after the rule\n")  # the user's own process writes later
    check_table("A-misc: placeholder created + denied, content appears later", tok, [
        ("read ghost\\later.txt", ["read", os.path.join(ghost, "later.txt")], "DENY"),
        ("create ghost\\x", ["create", os.path.join(ghost, "x.txt")], "DENY"),
    ], env=env_for(spec))
    P.remove_sids(ghost, [gsid])
    # a refused FILE that does not exist yet: placeholder file?
    say("  (a refused FILE path cannot get a placeholder without guessing file vs folder)")
    P.revert_rules(applied)
    # two runs share the same deterministic rule SID: run A reverts while run B still runs
    check_table("A-misc: run B's token after run A reverted the shared deny rule (deterministic SIDs)", tok, [
        ("read refused\\secret.txt", ["read", j("refused", "secret.txt")], "DENY"),
    ], env=env_for(spec))


def sec_OUTSIDE():
    say("\n================ OUTSIDE. refused rows the user may not own (read-only AccessCheck probing)")
    prof = os.environ["USERPROFILE"]
    for p in [r"C:\Windows", r"C:\Windows\System32", r"C:\Windows\System32\config", r"C:\Program Files", r"C:\ProgramData",
              r"C:\ProgramData\Microsoft\Windows\Start Menu", r"C:\Users\Default", r"C:\Users\Public", r"C:\Users\Public\Documents",
              r"C:\System Volume Information", r"C:\Windows\Temp", prof, os.path.join(prof, "Documents"),
              os.path.join(prof, "AppData", "LocalLow"), os.path.join(os.environ["APPDATA"], "uv"), r"C:\abstractframework"]:
        try:
            say(f"  {P.can_deny(p):22s} {p}")
        except OSError as e:
            say(f"  error {e} {p}")


# ---------------------------------------------------------------------------------------
# ordinary work
# ---------------------------------------------------------------------------------------
def work_cmds(repo):
    return [
        ("cmd", ["cmd", "/d", "/s", "/c", "echo hi & ver"]),
        ("powershell", ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString(); (Get-Item Env:TEMP).Value; 'ok'"]),
        ("python+tempfile+ssl", [PY, "-c", "import ssl,sqlite3,tempfile,os;f=tempfile.NamedTemporaryFile(delete=False);f.write(b'x');f.close();os.remove(f.name);print('ok', tempfile.gettempdir())"]),
        ("python -m pip --version", [PY, "-m", "pip", "--version"]),
        ("pip --version (PATH)", ["cmd", "/d", "/c", "pip --version"]),
        ("git status (repo not writable in ro)", ["git", "-C", repo, "status", "--short", "--branch"]),
        ("git commit (repo in private ws)", ["cmd", "/d", "/c", f"cd /d {j('pw', 'repo')} && echo %RANDOM%>> a.txt && git add a.txt && git -c user.name=t -c user.email=t@t commit -q -m x && echo committed"]),
        ("node", ["node", "-e", "console.log(process.version, require('os').tmpdir())"]),
        ("npm --version", ["cmd", "/d", "/c", "npm --version"]),
        ("curl -I https://example.com", ["curl.exe", "-sS", "-I", "-m", "15", "https://example.com"]),
        ("reg query HKCU\\Environment", ["reg", "query", r"HKCU\Environment"]),
        ("whoami /priv", ["whoami", "/priv"]),
    ]


def make_repos():
    for repo in (j("world", "repo"), j("pw", "repo")):
        os.makedirs(repo, exist_ok=True)
        subprocess.run(["git", "init", "-q", repo], capture_output=True)
        write(os.path.join(repo, "a.txt"), "a\n")
        subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
        subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"], capture_output=True)


def sec_WORK():
    say("\n================ WORK. ordinary commands: unsandboxed vs mirror(DMP) vs mirror(no DMP) vs ro(Low IL)")
    build_lab()
    make_repos()
    spec = lab_spec("rw")
    rules, applied, _ = apply(spec)
    sids = [P.rule_sid(a, p) for a, p in rules]
    env = env_for(spec)
    toks = {"rw+DMP": P.posture_token(sids, "rw"), "rw-noDMP": P.posture_token(sids, "rw", flags=0)}
    for a, p in rules:
        if a == "rw":
            P.set_label(p, P.LOW_IL)
    toks["ro(Low)"] = P.posture_token(sids, "ro")
    for name, argv in work_cmds(j("world", "repo")):
        p = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=L)
        base = (p.returncode, " ".join((p.stdout + p.stderr).split())[:90])
        say(f"\n  {name}\n    {'unsandboxed':9s} rc={base[0]:<4d} {base[1]}")
        for tn, tok in toks.items():
            rc, out = P.run(argv, tok, env=env, cwd=L)
            say(f"    {tn:9s} rc={rc:<4d} {' '.join(out.split())[:90]}")
    # %TEMP% (the real one) and HKCU writability, without creating anything
    real_temp = os.environ["TEMP"]
    ops = [["openfile", real_temp, 0x2], ["regopen", r"Software", 0x4], ["regopen", r"Environment", 0x2],
           ["openfile", os.path.join(os.environ["USERPROFILE"], "AppData", "LocalLow"), 0x2],
           ["regopen", r"Software\AppDataLow", 0x4], ["openfile", r"\\.\NUL", 0x40000000]]
    say("\n  open-for-write probes (nothing is created): real %TEMP% add-file, HKCU\\Software create-subkey, HKCU\\Environment set-value, LocalLow add-file, HKCU\\Software\\AppDataLow create-subkey, NUL write")
    say(f"    unsandboxed {probe(None, ops)}")
    for tn, tok in toks.items():
        say(f"    {tn:11s} {probe(tok, ops, env=env)}")
    for a, p in rules:
        if a == "rw":
            P.set_label(p, None)
    P.revert_rules(applied)


# ---------------------------------------------------------------------------------------
# B: default_mode ro
# ---------------------------------------------------------------------------------------
def sec_B1():
    say("\n================ B1. any_except_denied + ro: mirror + rule SIDs + Low IL; rw places labelled Low")
    build_lab()
    spec = lab_spec("ro")
    rules, applied, labelled = apply(spec, label_low=True)
    say("  label evidence: " + icacls(j("pw")).replace("\n", " | "))
    say("  label evidence (child): " + icacls(j("pw", "readme.txt")).replace("\n", " | "))
    tok = P.posture_token([P.rule_sid(a, p) for a, p in rules], "ro")
    env = env_for(spec)
    check_table("B1 ro: python ops inside the sandbox", tok, matrix_cases("ro"), env=env)
    restore_moves()
    check_table("B1 ro: write leaks outside the rows (open-for-write, nothing created)", tok, [
        ("%USERPROFILE%\\AppData\\LocalLow add-file", ["openfile", os.path.join(os.environ["USERPROFILE"], "AppData", "LocalLow"), 0x2], "?"),
        ("real %TEMP% add-file", ["openfile", os.environ["TEMP"], 0x2], "DENY"),
        ("%TEMP%\\Low add-file (if it exists)", ["openfile", os.path.join(os.environ["TEMP"], "Low"), 0x2], "?"),
        ("HKCU\\Software\\AppDataLow create-subkey", ["regopen", r"Software\AppDataLow", 0x4], "?"),
        ("HKCU\\Software create-subkey", ["regopen", r"Software", 0x4], "DENY"),
    ], env=env)
    # the side effect: while labelled Low, ANY Low-IL process of the user can write there
    base = P.own_token()
    lowtok = P.make_token(P.mirror_sids(), flags=0, integrity=P.LOW_IL)  # stands in for e.g. a browser's Low-IL helper
    check_table("B1 side effect: an unrelated Low-IL process of the user (no rule SIDs)", lowtok, [
        ("write into Low-labelled private ws", ["create", j("pw", "by_other_low.txt")], "?"),
        ("write into Low-labelled rw row", ["create", j("rorow", "rwin", "by_other_low.txt")], "?"),
        ("write into the unlabelled world", ["create", j("world", "by_other_low.txt")], "DENY"),
    ])
    P.CloseHandle(base)
    # labels of files the sandbox created
    rc, out = P.run(["cmd", "/d", "/c", r"echo x> pw\made_by_sandbox.txt"], tok, env=env, cwd=L)
    say("\n  file created by the Low sandbox: " + icacls(j("pw", "made_by_sandbox.txt")).replace("\n", " | "))
    # revert
    for p in labelled:
        P.set_label(p, None)
    say("  after removing the root labels:")
    for rel in [("pw",), ("pw", "readme.txt"), ("pw", "made_by_sandbox.txt"), ("pw", "by_other_low.txt")]:
        if os.path.exists(j(*rel)):
            say("    " + icacls(j(*rel)).replace("\n", " | "))
    check_table("B1 after revert: Low-IL process writes again?", lowtok, [
        ("write into private ws", ["create", j("pw", "after_revert.txt")], "DENY"),
        ("append to the file the sandbox created", ["append", j("pw", "made_by_sandbox.txt")], "?"),
    ])
    check_table("B1 shared row: run B still running after run A reverted the label", tok, [
        ("run B writes its rw row", ["create", j("rorow", "rwin", "runB.txt")], "?"),
    ], env=env)
    # label setting on something not writable-owner (read-only probing: AccessCheck WRITE_OWNER is what SetNamedSecurityInfo(LABEL) needs)
    me = P.own_token()
    for p in [os.environ["USERPROFILE"], r"C:\Program Files", r"C:\ProgramData"]:
        say(f"  WRITE_OWNER (needed to set a label) on {p}: {'yes' if P.access_check(p, me, 0x80000) else 'no'}")
    P.revert_rules(applied)


def sec_B1SCAN():
    say("\n================ B1-scan. folders a Low-IL mirror token can add files to (AccessCheck, read-only walk)")
    tok = P.posture_token([], "ro")
    roots = [(os.environ["USERPROFILE"], 3), ("C:\\", 2)]
    hits, n = [], 0
    for root, depth in roots:
        base = root.rstrip("\\").count("\\")
        for dirpath, dirs, _ in os.walk(root):
            if dirpath.count("\\") - base >= depth:
                dirs[:] = []
            dirs[:] = [d for d in dirs if not P._is_junction(os.path.join(dirpath, d)) and not os.path.islink(os.path.join(dirpath, d))]
            n += 1
            try:
                if P.access_check(dirpath, tok, 0x2):
                    hits.append(dirpath)
            except OSError:
                pass
    say(f"  checked {n} folders; writable at Low IL ({len(hits)}):")
    for h in hits:
        say(f"    {h}")


def sec_B2():
    say("\n================ B2. no integrity level: restricting set WITHOUT the user SID (well-known groups + rule SIDs)")
    build_lab()
    spec = lab_spec("ro")
    rules, applied, _ = apply(spec)
    sids = [P.rule_sid(a, p) for a, p in rules]
    groups = [s for s in P.mirror_sids()[1:] if not s.startswith("S-1-5-21-")]  # Everyone, Users, Auth Users, INTERACTIVE, logon...
    env = env_for(spec)
    for label, extra, d in (("without RESTRICTED", [], False), ("with RESTRICTED S-1-5-12", ["S-1-5-12"], False),
                            ("+ default DACL (user, SYSTEM, logon, RESTRICTED)", ["S-1-5-12"], True)):
        t = P.make_token(groups + extra + sids)
        if d:
            dd(t)
        rc, out = P.run([r"C:\Windows\System32\cmd.exe", "/d", "/c", "echo cmd starts"], t, env=env)
        say(f"  cmd under B2 {label}: rc={rc} {hex(rc)} {' '.join(out.split())[:100]}")
    groups = groups + ["S-1-5-12"]
    say(f"  restricting = {groups} + {len(sids)} rule SIDs; default DACL set")
    tok = P.make_token(groups + sids)
    dd(tok)
    rc, out = P.run([PY, "-c", "print('python starts')"], tok, env=env)
    say(f"  gateway python (under %APPDATA%) under B2: rc={rc} {hex(rc)} {' '.join(out.split())[:120]}")
    for k, n in (("S-1-5-12 granted by", "desktop Default + WinSta0 DACLs (see desk.py): RESTRICTED is how sandboxes get a desktop"),):
        say(f"  ({k} {n})")
    cmd_table("B2 inside the sandbox (cmd builtins: python cannot start)", tok, [
        ("type lab world file (user-only ACL)", r"type world\plain.txt", "ok"),
        ("echo > lab world", r"echo x> world\b2.txt", "DENY"),
        ("echo > private ws", r"echo x> pw\b2.txt", "ok"),
        ("type refused", r"type refused\secret.txt", "DENY"),
        ("type C:\\Windows\\win.ini", r"type C:\Windows\win.ini", "ok"),
        ("dir %USERPROFILE%", r"dir /b %USERPROFILE%", "ok"),
    ], env=env)
    say("\n  read coverage of the B2 token (AccessCheck FILE_READ_DATA|LIST, nothing opened):")
    prof = os.environ["USERPROFILE"]
    for p in [prof, os.path.join(prof, "Documents"), os.path.join(os.environ["APPDATA"], "uv", "python"), os.environ["LOCALAPPDATA"],
              r"C:\abstractframework", j("world"), r"C:\Windows\System32", r"C:\Program Files", r"C:\Program Files\Git", r"C:\ProgramData"]:
        try:
            say(f"    {'readable  ' if P.access_check(p, tok, 0x1) else 'UNREADABLE'} {p}")
        except OSError as e:
            say(f"    error {e} {p}")
    say("\n  write leaks of the well-known groups (AccessCheck, B2 token, nothing created): add-file / add-subdir")
    for p in [r"C:" + "\\", r"C:\ProgramData", r"C:\Windows\Temp", r"C:\Windows\Tasks", r"C:\Windows\System32\spool\drivers\color",
              r"C:\Users\Public", r"C:\Users\Public\Documents", r"C:\Program Files"] + [f"{d}:\\" for d in "DEFGH" if os.path.exists(f"{d}:\\")]:
        try:
            say(f"    {p:45s} add-file={'YES' if P.access_check(p, tok, 0x2) else 'no '} add-subdir={'YES' if P.access_check(p, tok, 0x4) else 'no '}")
        except OSError as e:
            say(f"    {p:45s} {e}")
    P.revert_rules(applied)


def sec_B3():
    say("\n================ B3. WRITE_RESTRICTED token: restricting = rule SIDs only (checked for WRITE access only)")
    build_lab()
    make_repos()
    spec = lab_spec("ro")
    rules, applied, _ = apply(spec)
    sids = [P.rule_sid(a, p) for a, p in rules]
    env = env_for(spec)
    t0 = P.make_token(sids, flags=P.DISABLE_MAX_PRIVILEGE | P.WRITE_RESTRICTED)
    dd(t0)
    rc, out = P.run(["cmd", "/d", "/c", "echo hi"], t0, env=env)
    say(f"  WRITE_RESTRICTED, rule SIDs only (+default DACL): cmd rc={rc} {hex(rc)}")
    logon = [s for s in P.mirror_sids() if s.startswith("S-1-5-5-")][0]
    sids = sids + ["S-1-5-12", logon]
    say("  restricting = rule SIDs + RESTRICTED + logon SID (the minimum that starts a process, found by b2start.py: + Everyone)")
    tok = P.make_token(sids + ["S-1-1-0"], flags=P.DISABLE_MAX_PRIVILEGE | P.WRITE_RESTRICTED)
    dd(tok)
    check_table("B3 inside the sandbox", tok, [
        ("refused read (Deny-all ACE for a restricting SID)", ["read", j("refused", "secret.txt")], "DENY"),
        ("refused list", ["list", j("refused")], "DENY"),
        ("refused append", ["append", j("refused", "secret.txt")], "DENY"),
        ("world read", ["read", j("world", "plain.txt")], "ok"),
        ("world create", ["create", j("world", "b3.txt")], "DENY"),
        ("private ws create", ["create", j("pw", "b3.txt")], "ok"),
        ("rw row create", ["create", j("rorow", "rwin", "b3.txt")], "ok"),
        ("ro row append", ["append", j("rorow", "f.txt")], "DENY"),
        ("NUL write", ["openfile", r"\\.\NUL", 0x40000000], "?"),
    ], env=env)
    # combination: WRITE_RESTRICTED (writes) + Low-IL? no: try WRITE_RESTRICTED + refused rows given a
    # Medium NO_READ_UP label: no-read-up only bites a token BELOW Medium, so this needs Low IL anyway.
    for name, argv in [("cmd", ["cmd", "/d", "/c", "echo hi"]), ("python", [PY, "-c", "import tempfile;print('hi', tempfile.gettempdir())"]),
                       ("powershell", ["powershell", "-NoProfile", "-Command", "'hi'"]), ("git status", ["git", "-C", j("world", "repo"), "status", "--short"]),
                       ("curl https", ["curl.exe", "-sS", "-o", "NUL", "-w", "%{http_code}", "-m", "15", "https://example.com"])]:
        rc, out = P.run(argv, tok, env=env, cwd=L)
        say(f"  B3 {name:11s} rc={rc:<4d} {' '.join(out.split())[:100]}")
    say("\n  write leaks of the B3 set (AccessCheck add-file/add-subdir; RESTRICTED/Everyone/logon grants):")
    for p in [r"C:" + "\\", r"C:\ProgramData", r"C:\Users\Public", r"C:\Windows\Tasks", r"C:\Windows\System32\spool\drivers\color", os.environ["USERPROFILE"]]:
        try:
            say(f"    {p:45s} add-file={'YES' if P.access_check(p, tok, 0x2) else 'no '} add-subdir={'YES' if P.access_check(p, tok, 0x4) else 'no '}")
        except OSError as e:
            say(f"    {p:45s} {e}")
    P.revert_rules(applied)


# ---------------------------------------------------------------------------------------
# C / D: escapes
# ---------------------------------------------------------------------------------------
def sec_C():
    say("\n================ C. escapes through other processes / persistence")
    build_lab()
    target = subprocess.Popen([PY, "-c", "import time; time.sleep(600)"])
    time.sleep(1.0)
    # the venv python.exe is a redirector: the real interpreter is its child; either is an unsandboxed same-user process
    try:
        results = {}
        for mode in ("rw", "ro", "ro-B4"):
            build_lab()
            spec, tok, cleanup = setup_mode(mode)
            env = env_for(spec)
            leak = j("world", f"spoof_{mode}.json")
            spoof_cmd = subprocess.list2cmdline([PY, PROBE, json.dumps([["self"], ["read", j("refused", "secret.txt")]]), leak])
            late = j("world", f"spoof_late_{mode}.json")
            late_cmd = subprocess.list2cmdline([PY, PROBE, json.dumps([["sleep", 4], ["self"], ["read", j("refused", "secret.txt")]]), late])
            startup = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
            check_table(f"C {mode}: against unsandboxed pid {target.pid}", tok, [
                ("OpenProcess PROCESS_ALL_ACCESS", ["openproc", target.pid, 0x1FFFFF], "?"),
                ("OpenProcess VM_READ", ["openproc", target.pid, 0x10], "?"),
                ("OpenProcess VM_WRITE|VM_OPERATION|CREATE_THREAD", ["openproc", target.pid, 0x20 | 0x8 | 0x2], "?"),
                ("OpenProcess CREATE_PROCESS", ["openproc", target.pid, 0x80], "?"),
                ("child with PARENT_PROCESS=unsandboxed reads refused", ["spoofparent", target.pid, spoof_cmd], "?"),
                ("same, not waited for (does it outlive the job?)", ["spoofparent_nowait", target.pid, late_cmd], "?"),
                ("HKCU ...\\CurrentVersion\\Run KEY_SET_VALUE (open only)", ["regopen", r"Software\Microsoft\Windows\CurrentVersion\Run", 0x2], "?"),
                ("Startup folder add-file (open only)", ["openfile", startup, 0x2], "?"),
            ], env=env)
            if os.path.exists(leak):
                say(f"    spoofed child reported: {open(leak).read()}")
            time.sleep(6)
            say(f"    not-waited spoofed child, 6s after the job was closed: {open(late).read() if os.path.exists(late) else '(no report: killed with the job or never started)'}")
            # scheduled task: create, run, delete (always deleted from outside too)
            tn = f"w4probe_{mode}_{os.getpid()}"
            out = j("world", f"task_{mode}.json")
            with open(j("world", "task_ops.json"), "w") as f:
                json.dump([["self"], ["read", j("refused", "secret.txt")]], f)
            with open(j("world", "t.cmd"), "w") as f:  # /tr is limited to 261 chars: a wrapper prepared outside
                f.write(subprocess.list2cmdline([PY, PROBE, "@" + j("world", "task_ops.json"), out]) + "\r\n")
            tr = j("world", "t.cmd")
            rc1, o1 = P.run(["schtasks", "/create", "/tn", tn, "/tr", tr, "/sc", "once", "/st", "23:59", "/f"], tok, env=env)
            rc2, o2 = P.run(["schtasks", "/run", "/tn", tn], tok, env=env)
            ps = (f"$a=New-ScheduledTaskAction -Execute '{tr}'; Register-ScheduledTask -TaskName '{tn}_ps' -Action $a -Force | Out-Null; "
                  f"Start-ScheduledTask -TaskName '{tn}_ps'; 'registered+started'")
            rc3, o3 = P.run(["powershell", "-NoProfile", "-Command", ps], tok, env=env)
            say(f"    Register-ScheduledTask (COM/CIM) from sandbox: rc={rc3} {' '.join(o3.split())[:140]}")
            time.sleep(4)
            d2 = subprocess.run(["schtasks", "/delete", "/tn", tn + "_ps", "/f"], capture_output=True, text=True)
            say(f"    cleanup {tn}_ps: rc={d2.returncode} {' '.join((d2.stdout + d2.stderr).split())[:80]}")
            d = subprocess.run(["schtasks", "/delete", "/tn", tn, "/f"], capture_output=True, text=True)
            say(f"    schtasks /create from sandbox: rc={rc1} {' '.join(o1.split())[:100]}")
            say(f"    schtasks /run    from sandbox: rc={rc2} {' '.join(o2.split())[:100]}")
            say(f"    cleanup schtasks /delete (unsandboxed): rc={d.returncode} {' '.join((d.stdout + d.stderr).split())[:80]}")
            if os.path.exists(out):
                say(f"    task ran and reported: {open(out).read()}")
            cleanup()
    finally:
        target.kill()
        subprocess.run(["taskkill", "/f", "/t", "/pid", str(target.pid)], capture_output=True)
        q = subprocess.run(["schtasks", "/query", "/fo", "csv"], capture_output=True, text=True).stdout
        say(f"  leftover w4probe tasks: {[l for l in q.splitlines() if 'w4probe' in l]}")


def sec_D():
    say("\n================ D. grandchildren")
    for mode in ("rw", "ro", "ro-B4"):
        build_lab()
        spec, tok, cleanup = setup_mode(mode)
        env = env_for(spec)
        opsf = j("pw", "d_ops.json")
        with open(opsf, "w") as f:
            json.dump([["self"], ["read", j("refused", "secret.txt")]], f)
        outs = {}

        def pc(tag):
            o = j("pw", f"d_{tag}.json")
            outs[tag] = o
            return f"{PY} {PROBE} @{opsf} {o}"

        cases = [
            ("direct child (python subprocess)", [PY, PROBE, json.dumps([["spawn", pc('subprocess').split(' ')]]) ]),
            ("cmd /c start", f'cmd /d /c start "" /wait {pc("start")}'),
            ("powershell Start-Process", ["powershell", "-NoProfile", "-Command", f"Start-Process -Wait -FilePath '{PY}' -ArgumentList '{PROBE}','@{opsf}','{j('pw', 'd_startprocess.json')}'"]),
            ("wmic process call create", f'cmd /d /c wmic process call create "{pc("wmic")}"'),
            ("Invoke-CimMethod Win32_Process Create", ["powershell", "-NoProfile", "-Command", f"Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{CommandLine='{pc('cim')}'}} | Select-Object ReturnValue,ProcessId | Format-List"]),
            ("Shell.Application.ShellExecute (in-proc) + wait", ["powershell", "-NoProfile", "-Command", f"(New-Object -ComObject Shell.Application).ShellExecute('{PY}', '{PROBE} @{opsf} {j('pw', 'd_shellapp.json')}'); Start-Sleep 4"]),
            ("ShellWindows -> explorer.exe ShellExecute (DCOM)", ["powershell", "-NoProfile", "-Command",
             "$w=[activator]::CreateInstance([type]::GetTypeFromCLSID('9BA05972-F6A8-11CF-A442-00A0C90A8F39')); "
             f"$i=$w.Item(); if(-not $i){{'no shell window'; exit 3}}; $i.Document.Application.ShellExecute('{PY}', '{PROBE} @{opsf} {j('pw', 'd_explorer.json')}', '', 'open', 0); 'sent'"]),
        ]
        outs["explorer"] = j("pw", "d_explorer.json")
        # survival after the job is closed (IsProcessInJob(NULL) is always true here: the test host itself runs in a job)
        sleepf = j("pw", "d_ops_sleep.json")
        with open(sleepf, "w") as f:
            json.dump([["sleep", 6], ["self"], ["read", j("refused", "secret.txt")]], f)
        outs["cim_late"] = j("pw", "d_cim_late.json")
        outs["start_late"] = j("pw", "d_start_late.json")
        cases += [
            ("CIM create, child sleeps 6s (outlives the job?)", ["powershell", "-NoProfile", "-Command",
             f"Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{CommandLine='{PY} {PROBE} @{sleepf} {outs['cim_late']}'}} | Select-Object ReturnValue | Format-List"]),
            ("cmd start (no wait), child sleeps 6s (killed with the job?)", f'cmd /d /c start "" {PY} {PROBE} @{sleepf} {outs["start_late"]}'),
        ]
        outs["startprocess"] = j("pw", "d_startprocess.json")
        outs["shellapp"] = j("pw", "d_shellapp.json")
        say(f"\n--- D {mode}")
        for name, argv in cases:
            rc, out = P.run(argv, tok, env=env, cwd=L, timeout=60)
            say(f"  {name:48s} rc={rc:<6d} {' '.join(out.split())[:110]}")
        time.sleep(9)
        for tag, o in outs.items():
            say(f"    {tag:13s} -> {open(o).read() if os.path.exists(o) else '(no report: the grandchild did not run / could not write its report)'}")
        cleanup()


def setup_mode(mode):
    """(spec, token, cleanup) for 'rw' (A), 'ro' (B1) or 'ro-B4'."""
    spec = lab_spec("rw" if mode == "rw" else "ro")
    rules = rules_for(spec)
    applied = P.apply_rules(rules)
    labels = {}
    if mode == "ro":
        labels = {p: (P.LOW_IL, 0x1) for a, p in rules if a == "rw"}
    elif mode == "ro-B4":
        for a, p in rules:
            labels[p] = {"rw": (P.LOW_IL, 0x1), "ro": (P.MEDIUM_IL, 0x1), "deny": (P.MEDIUM_IL, 0x3), "read": (P.MEDIUM_IL, 0x1)}[a]
    for p, (il, pol) in labels.items():
        P.set_label(p, il, flags=P.OI_CI if os.path.isdir(p) else 0, policy=pol)
    sids = [P.rule_sid(a, p) for a, p in rules]
    if mode == "ro-B4":
        logon = [s for s in P.mirror_sids() if s.startswith("S-1-5-5-")][0]
        tok = P.make_token(sids + ["S-1-5-12", logon, "S-1-1-0"], flags=P.DISABLE_MAX_PRIVILEGE | P.WRITE_RESTRICTED, integrity=P.LOW_IL)
        dd(tok)
    else:
        tok = P.posture_token(sids, "rw" if mode == "rw" else "ro")

    def cleanup():
        for p in labels:
            P.set_label(p, None)
        P.revert_rules(applied)
    return spec, tok, cleanup


def sec_B4():
    say("\n================ B4. combination: WRITE_RESTRICTED (writes) + Low IL + labels (refused reads via NO_READ_UP)")
    build_lab()
    spec = lab_spec("ro")
    rules = rules_for(spec)
    applied = P.apply_rules(rules)  # deny-write ACEs stay useful (honoured for writes under WRITE_RESTRICTED)
    labels = {}
    for action, path in rules:  # later rules at the same path win (rw < ro < deny on a tie)
        labels[path] = {"rw": (P.LOW_IL, 0x1), "ro": (P.MEDIUM_IL, 0x1), "deny": (P.MEDIUM_IL, 0x3), "read": (P.MEDIUM_IL, 0x1)}[action]
    for path, (il, pol) in labels.items():
        P.set_label(path, il, flags=P.OI_CI if os.path.isdir(path) else 0, policy=pol)
        for p in P.protected_descendants(path):
            pass  # SACL protection is independent of DACL protection; not exercised here
    say("  refused label: " + icacls(j("refused")).splitlines()[-1].strip())
    say("  ro-in-refused label: " + icacls(j("refused", "roin")).splitlines()[-1].strip())
    logon = [s for s in P.mirror_sids() if s.startswith("S-1-5-5-")][0]
    rw_sids = [P.rule_sid(a, p) for a, p in rules]
    tok = P.make_token(rw_sids + ["S-1-5-12", logon, "S-1-1-0"], flags=P.DISABLE_MAX_PRIVILEGE | P.WRITE_RESTRICTED, integrity=P.LOW_IL)
    dd(tok)
    env = env_for(spec)
    check_table("B4 ro: python ops inside the sandbox", tok, matrix_cases("ro"), env=env)
    restore_moves()
    check_table("B4 ro: the B1 leaks", tok, [
        ("%USERPROFILE%\\AppData\\LocalLow add-file", ["openfile", os.path.join(os.environ["USERPROFILE"], "AppData", "LocalLow"), 0x2], "DENY"),
        ("HKCU\\Software\\AppDataLow create-subkey", ["regopen", r"Software\AppDataLow", 0x4], "DENY"),
        ("HKCU\\Software create-subkey", ["regopen", r"Software", 0x4], "DENY"),
    ], env=env)
    for name, argv in [("python", [PY, "-c", "import tempfile,os;f=tempfile.NamedTemporaryFile(delete=False);f.close();os.remove(f.name);print('ok')"]),
                       ("powershell", ["powershell", "-NoProfile", "-Command", "'hi'"]), ("git status", ["git", "-C", j("world"), "status", "--short"]),
                       ("node", ["node", "-e", "console.log('hi')"])]:
        rc, out = P.run(argv, tok, env=env, cwd=L)
        say(f"  B4 {name:11s} rc={rc:<4d} {' '.join(out.split())[:100]}")
    for path in labels:
        P.set_label(path, None)
    P.revert_rules(applied)


def sec_TLS():
    say("\n================ TLS. network / TLS stacks under the restricted token")
    build_lab()
    spec = lab_spec("rw")
    env = env_for(spec)
    toks = {
        "DMP only, no restricting SIDs": P.make_token([], flags=P.DISABLE_MAX_PRIVILEGE),
        "mirror (restricted)": P.posture_token([], "rw"),
        "mirror, no DMP": P.posture_token([], "rw", flags=0),
        "mirror + Low IL": P.posture_token([], "ro"),
        "unrestricted + Low IL": P.make_token([], flags=0, integrity=P.LOW_IL),
    }
    cmds = [
        ("curl http:// (no TLS)", ["curl.exe", "-sS", "-o", "NUL", "-w", "%{http_code}", "-m", "15", "http://example.com"]),
        ("curl https (schannel)", ["curl.exe", "-sS", "-o", "NUL", "-w", "%{http_code}", "-m", "15", "https://example.com"]),
        ("python urllib https (OpenSSL)", [PY, "-c", "import urllib.request as u;print(u.urlopen('https://example.com',timeout=15).status)"]),
        ("node https (OpenSSL)", ["node", "-e", "require('https').get('https://example.com',r=>{console.log(r.statusCode);process.exit(0)}).on('error',e=>{console.log(e.message);process.exit(1)})"]),
        ("powershell Invoke-WebRequest (.NET/schannel)", ["powershell", "-NoProfile", "-Command", "(Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 https://example.com).StatusCode"]),
        ("git ls-remote https", ["git", "ls-remote", "https://github.com/git/git", "HEAD"]),
        ("whoami /priv", ["cmd", "/d", "/c", "whoami /priv | findstr Se"]),
    ]
    for name, argv in cmds:
        p = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=L)
        say(f"\n  {name}\n    {'unsandboxed':30s} rc={p.returncode:<4d} {' '.join((p.stdout + p.stderr).split())[:110]}")
        for tn, tok in toks.items():
            rc, out = P.run(argv, tok, env=env, cwd=L, timeout=60)
            say(f"    {tn:30s} rc={rc:<4d} {' '.join(out.split())[:110]}")


SECTIONS = {"ANOFIX": sec_A_nofix, "A": sec_A, "AOWNER": sec_A_owner, "AMISC": sec_A_misc, "OUTSIDE": sec_OUTSIDE,
            "WORK": sec_WORK, "TLS": sec_TLS, "B1": sec_B1, "B1SCAN": sec_B1SCAN,"B2": sec_B2, "B3": sec_B3, "B4": sec_B4, "C": sec_C, "D": sec_D}

if __name__ == "__main__":
    names = [a.upper() for a in sys.argv[1:]] or list(SECTIONS)
    s = P.token_summary(P.own_token())
    say(f"host: {sys.getwindowsversion()} user={s['user']} il={s['integrity']} python={sys.version.split()[0]}")
    for n in names:
        try:
            SECTIONS[n]()
        except Exception as e:  # keep going; report
            import traceback
            traceback.print_exc()
            FAILS.append(f"{n}: crashed {e}")
    say("\n================ summary")
    say(f"FAIL (mismatch with the nesting rule / expectation): {len(FAILS)}")
    for f in FAILS:
        say("  " + f)
    wipe_lab()
