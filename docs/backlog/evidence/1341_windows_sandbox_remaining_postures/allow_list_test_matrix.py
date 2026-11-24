"""Windows sandbox prototype: re-runnable experiment matrix.

    <py312>\\python.exe test_matrix.py [section ...]      (no section = all)

Every ACL change stays under the scratch folder (w1). Needs the test AppContainer profile
(acprofile.py create) for the appcontainer mode.
"""
import ctypes, json, os, statistics, subprocess, sys, time
from harness import *  # noqa
import win_sandbox_proto as wsp

SECTIONS = {}


def section(fn):
    SECTIONS[fn.__name__] = fn
    return fn


def write(p, text="data"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


def cmd_ops(root, mode, rules, ops):
    """cmd.exe built-ins inside the sandbox: one launch per op, prints OK/DENIED."""
    out = {}
    for label, line in ops:
        r = sbx(["cmd.exe", "/d", "/s", "/c", f"({line}) >nul 2>&1 && echo OK || echo DENIED"], rules, mode, cwd=root)
        out[label] = (r.stdout.strip() or f"rc={r.returncode & 0xFFFFFFFF:#x} {r.stderr.strip()[-120:]}")
    return out


# ------------------------------------------------------------------------- precedence
@section
def precedence():
    """Nested rules: most specific row wins, refusal wins a tie, ro beats rw on a tie."""
    for mode in ("rec", "restricted", "appcontainer"):
        print(f"\n##### precedence [{mode}]")
        # rw > ro
        t = fresh(f"prec_rw_ro_{mode}")
        o, i = t, os.path.join(t, "inner")
        write(os.path.join(o, "f.txt")); write(os.path.join(i, "f.txt")); write(os.path.join(i, "g.txt"))
        os.makedirs(os.path.join(i, "d"))
        rules = [(o, "rw"), (i, "ro")]
        show("rw > ro (outer rw, inner ro): python", probe([
            ["outer read", "read", os.path.join(o, "f.txt")],
            ["outer write new", "write", os.path.join(o, "new.txt")],
            ["outer append", "append", os.path.join(o, "f.txt")],
            ["inner read", "read", os.path.join(i, "f.txt")],
            ["inner list", "list", i],
            ["inner write new (deny)", "write", os.path.join(i, "new.txt")],
            ["inner append (deny)", "append", os.path.join(i, "f.txt")],
            ["inner delete (deny)", "delete", os.path.join(i, "f.txt")],
            ["inner mkdir (deny)", "mkdir", os.path.join(i, "nd")],
            ["inner rmdir empty d (deny)", "rmdir", os.path.join(i, "d")],
            ["move inner/g -> outer (deny)", "rename", os.path.join(i, "g.txt"), os.path.join(o, "g.txt")],
            ["move outer/f -> inner (deny)", "rename", os.path.join(o, "f.txt"), os.path.join(i, "f2.txt")],
            ["rename inner dir (deny)", "rename", i, os.path.join(o, "inner2")],
        ], rules, mode))
        show("rw > ro: cmd.exe", cmd_ops(o, mode, rules, [
            ("type inner\\f.txt", "type inner\\f.txt"),
            ("dir inner", "dir inner"),
            ("echo > inner\\x.txt (deny)", "echo x> inner\\x.txt"),
            ("echo >> inner\\f.txt (deny)", "echo x>> inner\\f.txt"),
            ("del inner\\f.txt (deny)", "del inner\\f.txt && if exist inner\\f.txt exit 1"),
            ("mkdir inner\\m (deny)", "mkdir inner\\m"),
            ("ren inner\\f.txt (deny)", "ren inner\\f.txt f9.txt"),
            ("echo > outer\\y.txt", "echo y> y.txt"),
            ("del outer\\y.txt", "del y.txt && if not exist y.txt ver"),
        ]))
        # ro > rw
        t = fresh(f"prec_ro_rw_{mode}")
        o, i = t, os.path.join(t, "inner")
        write(os.path.join(o, "f.txt")); write(os.path.join(i, "f.txt")); write(os.path.join(i, "g.txt"))
        rules = [(o, "ro"), (i, "rw")]
        show("ro > rw (outer ro, inner rw): python", probe([
            ["outer read", "read", os.path.join(o, "f.txt")],
            ["outer write new (deny)", "write", os.path.join(o, "new.txt")],
            ["outer append (deny)", "append", os.path.join(o, "f.txt")],
            ["outer delete (deny)", "delete", os.path.join(o, "f.txt")],
            ["inner write new", "write", os.path.join(i, "new.txt")],
            ["inner append", "append", os.path.join(i, "f.txt")],
            ["inner mkdir", "mkdir", os.path.join(i, "nd")],
            ["inner rename within", "rename", os.path.join(i, "new.txt"), os.path.join(i, "new2.txt")],
            ["inner delete", "delete", os.path.join(i, "new2.txt")],
            ["move inner/g -> outer (deny)", "rename", os.path.join(i, "g.txt"), os.path.join(o, "g.txt")],
            ["move outer/f -> inner (deny)", "rename", os.path.join(o, "f.txt"), os.path.join(i, "f3.txt")],
            ["rename inner root (deny)", "rename", i, os.path.join(o, "inner2")],
        ], rules, mode))
        show("ro > rw: cmd.exe", cmd_ops(o, mode, rules, [
            ("echo > f.txt outer (deny)", "echo x> f.txt"),
            ("echo > inner\\z.txt", "echo z> inner\\z.txt"),
            ("del inner\\z.txt", "del inner\\z.txt && if not exist inner\\z.txt ver"),
            ("mkdir inner\\mm", "mkdir inner\\mm"),
            ("rmdir inner\\mm", "rmdir inner\\mm"),
        ]))
        # rw > deny > rw
        t = fresh(f"prec_rw_deny_rw_{mode}")
        o, m, i = t, os.path.join(t, "mid"), os.path.join(t, "mid", "inner")
        write(os.path.join(o, "f.txt")); write(os.path.join(m, "secret.txt")); write(os.path.join(i, "f.txt"))
        rules = [(o, "rw"), (m, "deny"), (i, "rw")]
        show("rw > deny > rw: python", probe([
            ["outer write", "write", os.path.join(o, "n.txt")],
            ["mid read secret (deny)", "read", os.path.join(m, "secret.txt")],
            ["mid list (deny)", "list", m],
            ["mid stat secret (deny)", "stat", os.path.join(m, "secret.txt")],
            ["mid write (deny)", "write", os.path.join(m, "n.txt")],
            ["mid delete secret (deny)", "delete", os.path.join(m, "secret.txt")],
            ["rename mid (deny)", "rename", m, os.path.join(o, "mid2")],
            ["inner read", "read", os.path.join(i, "f.txt")],
            ["inner write", "write", os.path.join(i, "n.txt")],
            ["inner list", "list", i],
            ["move inner/f -> outer (deny?)", "rename", os.path.join(i, "f.txt"), os.path.join(o, "f_from_inner.txt")],
            ["move outer/f -> inner (deny?)", "rename", os.path.join(o, "f.txt"), os.path.join(i, "f_from_outer.txt")],
        ], rules, mode))
        show("rw > deny > rw: cmd.exe", cmd_ops(o, mode, rules, [
            ("type mid\\secret.txt (deny)", "type mid\\secret.txt"),
            ("dir mid (deny)", "dir mid"),
            ("type mid\\inner\\f.txt", "type mid\\inner\\f.txt"),
            ("cd mid\\inner && echo > a", "cd mid\\inner && echo a> a.txt"),
        ]))
        # deny > ro
        t = fresh(f"prec_deny_ro_{mode}")
        o, i = t, os.path.join(t, "inner")
        write(os.path.join(o, "secret.txt")); write(os.path.join(i, "f.txt"))
        rules = [(o, "deny"), (i, "ro")]
        show("deny > ro: python", probe([
            ["outer read (deny)", "read", os.path.join(o, "secret.txt")],
            ["outer list (deny)", "list", o],
            ["inner read", "read", os.path.join(i, "f.txt")],
            ["inner list", "list", i],
            ["inner write (deny)", "write", os.path.join(i, "n.txt")],
            ["inner delete (deny)", "delete", os.path.join(i, "f.txt")],
        ], rules, mode))
        # same path: rw + deny ; ro + rw ; read + deny
        t = fresh(f"prec_same_{mode}")
        a, b = os.path.join(t, "a"), os.path.join(t, "b")
        write(os.path.join(a, "f.txt")); write(os.path.join(b, "f.txt"))
        rules = [(a, "rw"), (a, "deny"), (b, "rw"), (b, "ro")]
        show("same path: a = rw+deny, b = rw+ro: python", probe([
            ["a read (deny wins)", "read", os.path.join(a, "f.txt")],
            ["a write (deny wins)", "write", os.path.join(a, "n.txt")],
            ["b read (ro)", "read", os.path.join(b, "f.txt")],
            ["b write (ro wins -> deny)", "write", os.path.join(b, "n.txt")],
            ["b append (ro wins -> deny)", "append", os.path.join(b, "f.txt")],
        ], rules, mode))
        # deny > rw > ro > rw (deep alternation) and a deny on a FILE inside rw
        t = fresh(f"prec_deep_{mode}")
        l1, l2, l3, l4 = t, os.path.join(t, "l2"), os.path.join(t, "l2", "l3"), os.path.join(t, "l2", "l3", "l4")
        for d in (l1, l2, l3, l4):
            write(os.path.join(d, "f.txt"))
        write(os.path.join(l2, "secret.env"))
        rules = [(l1, "deny"), (l2, "rw"), (l3, "ro"), (l4, "rw"), (os.path.join(l2, "secret.env"), "deny")]
        show("deny > rw > ro > rw + deny on a FILE in rw: python", probe([
            ["l1 read (deny)", "read", os.path.join(l1, "f.txt")],
            ["l2 write", "write", os.path.join(l2, "n.txt")],
            ["l2/secret.env read (file deny)", "read", os.path.join(l2, "secret.env")],
            ["l2/secret.env overwrite (file deny)", "write", os.path.join(l2, "secret.env")],
            ["l2/secret.env delete (file deny)", "delete", os.path.join(l2, "secret.env")],
            ["l3 read", "read", os.path.join(l3, "f.txt")],
            ["l3 write (deny)", "write", os.path.join(l3, "n.txt")],
            ["l4 write", "write", os.path.join(l4, "n.txt")],
        ], rules, mode))
        print("    icacls of l3/f.txt (inherited ACE order):\n" + icacls(os.path.join(l3, "f.txt")))


# ------------------------------------------------------------------------- shared env
def run_env(ws):
    """The environment a command gets (the integration sets TEMP/TMP to the private .tmp)."""
    tmp = os.path.join(ws, ".tmp")
    os.makedirs(tmp, exist_ok=True)
    return dict(os.environ, TEMP=tmp, TMP=tmp, TMPDIR=tmp)


def short(r, n=160):
    rc = r.returncode & 0xFFFFFFFF
    return f"rc={rc:#x} out={r.stdout.strip()[:n]!r} err={r.stderr.strip()[:n]!r}"


GIT = r"C:\Program Files\Git\cmd\git.exe"


# ------------------------------------------------------------------------- tools
@section
def tools():
    """Which programs run and behave under each mode."""
    for mode in ("rec", "restricted", "appcontainer"):
        print(f"\n##### tools [{mode}]")
        ws = fresh(f"tools_{mode}")
        repo = os.path.join(ws, "repo")
        os.makedirs(os.path.join(repo, "sub"))
        subprocess.run([GIT, "init", "-q", repo], check=True)
        write(os.path.join(repo, "a.txt"))
        env = run_env(ws)
        git_env = dict(env, GIT_CEILING_DIRECTORIES=ws, HOME=ws)
        rules = [(ws, "rw")]
        cases = [
            ("cmd /d /s /c echo", ["cmd.exe", "/d", "/s", "/c", "echo hello"], env, ws),
            ("cmd pipe dir|findstr", ["cmd.exe", "/d", "/s", "/c", "dir /b C:\\Windows | findstr /i /x system32"], env, ws),
            ("cmd >nul redirect", ["cmd.exe", "/d", "/s", "/c", "echo x >nul && echo nul-ok"], env, ws),
            ("cmd nested cmd", ["cmd.exe", "/d", "/s", "/c", "cmd /c echo nested-ok"], env, ws),
            ("powershell 5.1", ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString(); Get-ChildItem . | Measure-Object | % Count"], env, ws),
            ("pwsh (WindowsApps alias)", ["pwsh.exe", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"], env, ws),
            ("python venv", [VPY, "-c", "import sys,ssl,sqlite3,json; print(sys.version.split()[0], sys.prefix == sys.base_prefix)"], env, ws),
            ("python nested subprocess", [VPY, "-c", "import subprocess,sys; print(subprocess.run([sys.executable,'-c','print(42)'],capture_output=True,text=True).stdout.strip(), subprocess.run('echo via-shell', shell=True, capture_output=True, text=True).stdout.strip())"], env, ws),
            ("python DEVNULL", [VPY, "-c", "import subprocess; subprocess.run(['cmd','/c','echo x'], stdout=subprocess.DEVNULL); print('devnull-ok')"], env, ws),
            ("git --version", [GIT, "--version"], env, ws),
            ("git status (raw env)", [GIT, "status", "--short", "--branch"], env, repo),
            ("git status (CEILING+HOME)", [GIT, "status", "--short", "--branch"], git_env, repo),
            ("git init new (CEILING+HOME)", [GIT, "init", "-q", os.path.join(ws, "new")], git_env, ws),
            ("git init new RELATIVE path", [GIT, "init", "-q", "new2"], git_env, ws),
            ("git add (CEILING+HOME)", [GIT, "add", "a.txt"], git_env, repo),
            ("git commit (CEILING+HOME)", [GIT, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "m"], git_env, repo),
            ("git log", [GIT, "log", "--oneline"], git_env, repo),
            ("git status from a SUBDIR w/o CEILING", [GIT, "status", "--short"], env, os.path.join(repo, "sub")),
            ("where cmd", ["where.exe", "cmd"], env, ws),
            ("integrity label", ["cmd.exe", "/d", "/s", "/c", "whoami /groups | findstr /i Label"], env, ws),
            ("where python (PATH entries in the profile)", ["where.exe", "python"], env, ws),
            ("whoami /groups", ["whoami.exe", "/groups", "/fo", "csv", "/nh"], env, ws),
            ("node", ["node.exe", "-e", "console.log(process.version, require('os').tmpdir())"], env, ws),
            ("npm --version", ["cmd.exe", "/d", "/s", "/c", "npm --version"], env, ws),
            ("npm (cache in ws)", ["cmd.exe", "/d", "/s", "/c", "npm --version"], dict(env, npm_config_cache=os.path.join(ws, ".tmp", "npm")), ws),
        ]
        for label, argv, e, cwd in cases:
            r = sbx(argv, rules, mode, cwd=cwd, env=e)
            if label == "whoami /groups":
                rows = [l.split('","') for l in r.stdout.strip().splitlines()]
                print(f"  {label:28} rc={r.returncode & 0xFFFFFFFF:#x} " + "; ".join(f"{x[0].strip(chr(34))}[{x[3].strip(chr(34))[:40]}]" for x in rows if len(x) > 3)[:700])
                continue
            print(f"  {label:28} {short(r)}")


# ------------------------------------------------------------------------- confinement
PROBE_FILE = "af_sandbox_probe.txt"


def _rm(p):
    """Remove something a probe created outside scratch. Some system folders (tracing) let a
    user create but not delete: the user OWNS the new file, so grant itself DELETE first."""
    for attempt in range(2):
        try:
            (os.rmdir if os.path.isdir(p) else os.remove)(p)
            print(f"    !! cleaned up {p}")
            return
        except PermissionError:
            subprocess.run(["icacls", p, "/grant", f"{os.environ['USERNAME']}:(D)"], capture_output=True)
    print(f"    !! COULD NOT REMOVE {p}")


@section
def confinement():
    """Is user data unreadable? What is writable outside the rows? (real writes, cleaned up)"""
    home = os.path.expanduser("~")
    reads = [
        ["Documents", "list", os.path.join(home, "Documents")],
        ["Desktop", "list", os.path.join(home, "Desktop")],
        ["profile root", "list", home],
        ["~/.ssh", "list", os.path.join(home, ".ssh")],
        ["%APPDATA% gateway pyvenv.cfg", "read", os.path.join(os.environ["APPDATA"], "uv", "tools", "abstractgateway", "pyvenv.cfg")],
        ["C:\\abstractframework (list)", "list", r"C:\abstractframework"],
        ["abstractcore sandbox.py (read)", "read", r"C:\abstractframework\AbstractFramework\abstractcore\abstractcore\tools\sandbox.py"],
        ["C:\\ root (list)", "list", "C:\\"],
        ["C:\\Users (list)", "list", r"C:\Users"],
        ["C:\\Users\\Public (list)", "list", r"C:\Users\Public"],
        ["C:\\ProgramData (list)", "list", r"C:\ProgramData"],
        ["C:\\Windows\\win.ini", "read", r"C:\Windows\win.ini"],
        ["Program Files (list)", "list", r"C:\Program Files"],
    ]
    targets = [os.path.join(d, PROBE_FILE) for d in (
        os.environ["TEMP"], os.path.join(os.environ["LOCALAPPDATA"], "Temp", "Low"), r"C:\Users\Public", r"C:\Users\Public\Documents",
        r"C:\ProgramData", r"C:\Windows\Temp", r"C:\Windows\Tasks", r"C:\Windows\tracing",
        r"C:\Windows\System32\spool\drivers\color", "C:\\", r"C:\abstractframework", r"C:\tmp")]
    writes = [[f"write {t}", "write", t] for t in targets] + [[f"mkdir {os.path.dirname(t)}\\af_probe_dir", "mkdir", os.path.join(os.path.dirname(t), "af_probe_dir")] for t in targets[2:5]]
    for mode in ("rec", "restricted", "appcontainer"):
        ws = fresh(f"conf_{mode}")
        res = probe(reads + writes, [(ws, "rw")], mode, cwd=ws)
        show(f"confinement [{mode}]", res)
        for t in targets:  # cleanup anything that got created
            for p in (t, os.path.join(os.path.dirname(t), "af_probe_dir")):
                if os.path.exists(p):
                    _rm(p)


@section
def floor():
    """Root-level folders inherit Users:RX from C:\\ (readable under the Users base). A
    'floor' deny row on such a folder closes it while allowed rows inside keep working.
    Simulated in scratch (explicit Users:(OI)(CI)RX like a root-level folder)."""
    root = fresh("floor_rootlike")
    proj = os.path.join(root, "proj")
    write(os.path.join(root, "private.txt")); write(os.path.join(proj, "src.txt"))
    subprocess.run(["icacls", root, "/grant", "*S-1-5-32-545:(OI)(CI)(RX)"], capture_output=True, check=True)
    ws = fresh("floor_ws")
    ops = [["root-like list", "list", root], ["root-like read", "read", os.path.join(root, "private.txt")],
           ["proj read", "read", os.path.join(proj, "src.txt")], ["proj write", "write", os.path.join(proj, "n.txt")]]
    show("no floor rule, proj rw", probe(ops, [(ws, "rw"), (proj, "rw")], "rec", cwd=ws))
    show("floor deny on root-like + proj rw", probe(ops, [(ws, "rw"), (root, "deny"), (proj, "rw")], "rec", cwd=ws))
    # which REAL root-level folders could the host put a floor ACE on? (read-only check:
    # open with WRITE_DAC access, write nothing)
    ok, no = [], []
    for n in sorted(os.listdir("C:\\")):
        p = os.path.join("C:\\", n)
        if not os.path.isdir(p) or n.lower() in ("windows", "program files", "program files (x86)", "programdata", "users", "$recycle.bin", "system volume information", "recovery", "$winreagent", "documents and settings"):
            continue
        h = wsp.CreateFileW(p, wsp.WRITE_DAC, wsp.FILE_SHARE_ALL, None, wsp.OPEN_EXISTING, wsp.FILE_FLAG_BACKUP_SEMANTICS, None)
        if h and h != wsp.INVALID_HANDLE:
            wsp.CloseHandle(h); ok.append(n)
        else:
            no.append(n)
    print(f"    root-level folders the user CAN put a floor ACE on: {ok}")
    print(f"    root-level folders the user CANNOT (stay readable via Users): {no}")


# ------------------------------------------------------------------------- escapes
@section
def escapes():
    """Registry, scheduled tasks, other processes, COM/WMI, UI/clipboard."""
    sleeper = subprocess.Popen([HOST_PY, "-c", "import time; time.sleep(600)"])
    try:
        for mode in ("rec", "rec_logon", "restricted", "restricted_logon", "appcontainer"):
            ws = fresh(f"esc_{mode}")
            ops = [
                ["HKCU\\Software read", "regread", "HKEY_CURRENT_USER\\Software"],
                ["HKCU Run read", "regread", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"],
                ["HKLM Windows\\CurrentVersion read", "regread", r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion"],
                ["HKCU\\Software\\AfSandboxProbe create", "regwrite", r"HKEY_CURRENT_USER\Software\AfSandboxProbe"],
                ["HKCU Run value write", "regwrite", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run", "AfSandboxProbe"],
                ["HKCU Environment value write", "regwrite", r"HKEY_CURRENT_USER\Environment", "AfSandboxProbe"],
                ["HKCU AppDataLow key create", "regwrite", r"HKEY_CURRENT_USER\Software\AppDataLow\AfSandboxProbe"],
                ["OpenProcess QUERY_LIMITED (other)", "openproc", sleeper.pid, 0x1000],
                ["OpenProcess VM_READ (other)", "openproc", sleeper.pid, 0x0410],
                ["OpenProcess TERMINATE (other)", "openproc", sleeper.pid, 0x0001],
                ["OpenProcess ALL_ACCESS (other)", "openproc", sleeper.pid, 0x1FFFFF],
                ["OpenProcess VM_READ (gateway/host process)", "openproc", "PARENT", 0x0410],
                ["windows + clipboard", "windows"],
            ]
            ops = [[o[0], o[1], *(str(os.getpid()) if x == "PARENT" else x for x in o[2:])] for o in ops]
            show(f"registry/process/UI [{mode}]", probe(ops, [(ws, "rw")], mode, cwd=ws))
            r = sbx(["reg.exe", "add", r"HKCU\Software\AfSandboxProbe", "/v", "x", "/d", "1", "/f"], [(ws, "rw")], mode, cwd=ws)
            print(f"    reg add HKCU\\Software\\AfSandboxProbe: {short(r, 90)}")
            r = sbx(["schtasks.exe", "/create", "/tn", "AfSandboxProbe", "/tr", "cmd /c exit", "/sc", "once", "/st", "23:59", "/f"], [(ws, "rw")], mode, cwd=ws)
            print(f"    schtasks /create: {short(r, 120)}")
            target = os.path.join(W, f"escape_com_{mode}.txt")
            ps = ("$sw = [activator]::CreateInstance([type]::GetTypeFromCLSID('9BA05972-F6A8-11CF-A442-00A0C90A8F39'));"
                  f"$sw.Item().Document.Application.ShellExecute('cmd.exe','/c echo escaped> \"{target}\"','','open',0); 'called'")
            r = sbx(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps], [(ws, "rw")], mode, cwd=ws, timeout=60)
            time.sleep(2)
            print(f"    COM ShellWindows->explorer ShellExecute: {short(r, 120)}; file created outside? {os.path.exists(target)}")
            target3 = os.path.join(W, f"escape_js_{mode}.txt")
            jsf = os.path.join(TOOLS, "esc.js")
            with open(jsf, "w") as fh:
                fh.write('try { var sw = new ActiveXObject("Shell.Application").Windows(); WScript.Echo("windows=" + sw.Count);'
                         'var app = (sw.Count > 0) ? sw.Item(0).Document.Application : new ActiveXObject("Shell.Application");'
                         'app.ShellExecute("cmd.exe", "/c echo escaped> \\"' + target3.replace("\\", "\\\\") + '\\"", "", "open", 0); WScript.Echo("called"); }'
                         'catch (e) { WScript.Echo("ERR " + e.message); }')
            r = sbx(["cscript.exe", "//nologo", jsf], [(ws, "rw")], mode, cwd=ws, timeout=60)
            time.sleep(2)
            print(f"    JScript Shell.Application.Windows()->ShellExecute: {short(r, 100)}; file created outside? {os.path.exists(target3)}")
            r = sbx(["powershell.exe", "-NoProfile", "-Command", "$ExecutionContext.SessionState.LanguageMode"], [(ws, "rw")], mode, cwd=ws)
            print(f"    PowerShell language mode (TEMP = private .tmp): {r.stdout.strip()}")
            target2 = os.path.join(W, f"escape_wmi_{mode}.txt")
            ps = f"Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{CommandLine='cmd.exe /c echo escaped> \"{target2}\"'}} | % ReturnValue"
            r = sbx(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps], [(ws, "rw")], mode, cwd=ws, timeout=60)
            time.sleep(2)
            print(f"    WMI Win32_Process.Create: {short(r, 120)}; file created outside? {os.path.exists(target2)}")
            r = sbx(["explorer.exe", W], [(ws, "rw")], mode, cwd=ws, timeout=30)
            print(f"    explorer.exe <folder> (shell handoff): {short(r, 60)}")
            # cleanup of anything that unexpectedly succeeded
            for t in (target, target2, target3):
                if os.path.exists(t):
                    os.remove(t); print(f"    !! ESCAPE: {t} was created (removed)")
            for key in (r"HKCU\Software\AfSandboxProbe", r"HKCU\Software\AppDataLow\AfSandboxProbe"):
                if subprocess.run(["reg", "query", key], capture_output=True).returncode == 0:
                    subprocess.run(["reg", "delete", key, "/f"], capture_output=True); print(f"    !! cleaned up {key}")
            for key in (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run", r"HKCU\Environment"):
                if subprocess.run(["reg", "query", key, "/v", "AfSandboxProbe"], capture_output=True).returncode == 0:
                    subprocess.run(["reg", "delete", key, "/v", "AfSandboxProbe", "/f"], capture_output=True); print(f"    !! cleaned up {key}\\AfSandboxProbe")
            if subprocess.run(["schtasks", "/query", "/tn", "AfSandboxProbe"], capture_output=True).returncode == 0:
                subprocess.run(["schtasks", "/delete", "/tn", "AfSandboxProbe", "/f"], capture_output=True); print("    !! cleaned up scheduled task AfSandboxProbe")
        # one sandboxed launch opening another one's process (per-launch SID in default DACL)
        ws = fresh("esc_sibling")
        pidf = os.path.join(ws, "pid.txt")
        a = subprocess.Popen([HOST_PY, "-I", HELPER, policy([(ws, "rw")], "rec"), "--", VPY, "-c",
                              f"import os,time; open(r'{pidf}','w').write(str(os.getpid())); time.sleep(60)"])
        for _ in range(100):
            if os.path.exists(pidf) and open(pidf).read():
                break
            time.sleep(0.1)
        sib = int(open(pidf).read())
        ws2 = fresh("esc_sibling2")
        show("sibling sandbox (rec) opening another launch's process", probe(
            [["QUERY_LIMITED", "openproc", sib, 0x1000], ["VM_READ", "openproc", sib, 0x0410], ["TERMINATE", "openproc", sib, 1]], [(ws2, "rw")], "rec", cwd=ws2))
        a.kill()
    finally:
        sleeper.kill()


# ------------------------------------------------------------------------- network
@section
def network():
    import socket, ssl, threading, http.server
    pem = os.path.join(TOOLS, "host-cas.pem")
    with open(pem, "w") as f:
        for der in ssl.create_default_context().get_ca_certs(binary_form=True):
            f.write(ssl.DER_cert_to_PEM_cert(der))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    py_get = "import urllib.request,sys; print(urllib.request.urlopen(sys.argv[1], timeout=15).status)"
    for mode in ("rec", "restricted", "appcontainer"):
        print(f"\n##### network [{mode}]")
        ws = fresh(f"net_{mode}")
        env = run_env(ws)
        cases = [
            ("python http", [VPY, "-c", py_get, "http://example.com"], env),
            ("python https (system store)", [VPY, "-c", py_get, "https://example.com"], env),
            ("python https (SSL_CERT_FILE)", [VPY, "-c", py_get, "https://example.com"], dict(env, SSL_CERT_FILE=pem)),
            ("python loopback to host server", [VPY, "-c", py_get, f"http://127.0.0.1:{port}/"], env),
            ("curl.exe https (schannel)", ["curl.exe", "-sS", "-o", os.path.join(ws, "o.html"), "-w", "%{http_code}", "https://example.com"], env),
            ("curl.exe http", ["curl.exe", "-sS", "-o", os.path.join(ws, "o.html"), "-w", "%{http_code}", "http://example.com"], env),
            ("powershell IWR https", ["powershell.exe", "-NoProfile", "-Command", "(Invoke-WebRequest -UseBasicParsing https://example.com).StatusCode"], env),
            ("git ls-remote https (openssl)", [GIT, "ls-remote", "https://github.com/git/git", "HEAD"], dict(env, GIT_CEILING_DIRECTORIES=ws, HOME=ws)),
            ("node https", ["node.exe", "-e", "require('https').get('https://example.com',r=>{r.resume();r.on('end',()=>{console.log(r.statusCode);process.exit(0)})}).on('error',e=>console.log('ERR',e.code))"], env),
            ("git ls-remote https, GIT_DIR set", [GIT, "ls-remote", "https://github.com/git/git", "HEAD"], dict(env, GIT_DIR=os.path.join(ws, "nogit"), HOME=ws)),
        ]
        for label, argv, e in cases:
            r = sbx(argv, [(ws, "rw")], mode, cwd=ws, env=e, timeout=90)
            print(f"  {label:34} {short(r, 110)}")
    srv.shutdown()


# ------------------------------------------------------------------------- named pipes
@section
def pipes():
    """Named pipes with the DEFAULT security descriptor (creator-owner full, Everyone read):
    the restricted pass has no SID for the owner, so a client open for write fails."""
    import shutil
    shutil.copy2(os.path.join(W, "tools_namedpipe.py"), os.path.join(TOOLS, "namedpipe.py"))
    ws = fresh("pipes_ws")
    write(os.path.join(ws, "package.json"), '{"name":"p","version":"1.0.0","scripts":{"hello":"echo hello-from-npm-script"}}')
    mp = "import multiprocessing as m\nif __name__ == '__main__':\n    with m.Pool(2) as p: print(p.map(abs, [-1, -2]))"
    write(os.path.join(ws, "mp.py"), mp)
    cases = [
        ("libuv-style pipe pair (ctypes)", [VPY, "-I", os.path.join(TOOLS, "namedpipe.py")]),
        ("python subprocess PIPE", [VPY, "-c", "import subprocess; print(subprocess.run(['cmd','/c','echo piped'],capture_output=True,text=True).stdout.strip())"]),
        ("python multiprocessing.Pool", [VPY, os.path.join(ws, "mp.py")]),
        ("node spawnSync (pipes)", ["node.exe", "-e", "const r=require('child_process').spawnSync('cmd.exe',['/c','echo child'],{encoding:'utf8'});console.log(r.error?('ERR '+r.error.code):r.stdout.trim())"]),
        ("node spawnSync (stdio inherit)", ["node.exe", "-e", "const r=require('child_process').spawnSync('cmd.exe',['/c','echo child'],{stdio:'inherit'});console.log(r.error?('ERR '+r.error.code):'ok')"]),
        ("npm run hello", ["cmd.exe", "/d", "/s", "/c", "npm run hello"]),
    ]
    for mode in ("rec", "restricted"):
        print(f"\n##### pipes [{mode}]")
        for label, argv in cases:
            try:
                r = sbx(argv, [(ws, "rw")], mode, cwd=ws, timeout=60)
                print(f"  {label:32} {short(r, 200)}")
            except subprocess.TimeoutExpired:
                print(f"  {label:32} TIMEOUT")


# ------------------------------------------------------------------------- paths
@section
def paths():
    base = fresh("paths")
    real = os.path.join(base, "Real Folder")
    os.makedirs(real)
    write(os.path.join(real, "f.txt"))
    outside = fresh("paths_outside")
    write(os.path.join(outside, "secret.txt"))
    junc = os.path.join(base, "junc")
    subprocess.run(["cmd", "/c", "mklink", "/J", junc, real], capture_output=True, check=True)
    shortp = ctypes.create_unicode_buffer(1024)
    ctypes.windll.kernel32.GetShortPathNameW(real, shortp, 1024)
    forms = {
        "long": real, "8.3 short": shortp.value, "upper": real.upper(), "lower drive": real[0].lower() + real[1:],
        "trailing sep": real + "\\", "forward slashes": real.replace("\\", "/"), "\\\\?\\ prefix": "\\\\?\\" + real,
        "via junction": junc, "dotdot": os.path.join(real, "..", "Real Folder"),
        "non-existent": os.path.join(base, "nope", "deeper"), "file": os.path.join(real, "f.txt"),
        "UNC admin share": "\\\\localhost\\C$" + real[2:],
    }
    want = wsp.rule_sid("rw", real, "restricted")
    print("    normalize_rule_path / same SID as the long form:")
    for k, v in forms.items():
        try:
            n = wsp.normalize_rule_path(v)
            print(f"      {k:16} {n[-60:]:62} same={wsp.rule_sid('rw', v, 'restricted') == want}")
        except Exception as e:
            print(f"      {k:16} ERR {e}")
    print("    os.path.realpath of the 8.3 form:", os.path.realpath(shortp.value)[-50:])
    # junction INSIDE an rw row pointing OUTSIDE it (made by the user before the run)
    ws = fresh("paths_ws")
    subprocess.run(["cmd", "/c", "mklink", "/J", os.path.join(ws, "escape_j"), outside], capture_output=True, check=True)
    show("junction in rw -> outside (rec)", probe([
        ["read via junction", "read", os.path.join(ws, "escape_j", "secret.txt")],
        ["list via junction", "list", os.path.join(ws, "escape_j")],
        ["write via junction", "write", os.path.join(ws, "escape_j", "n.txt")],
        ["sandbox makes its own junction", "spawn", f"mklink /J \"{os.path.join(ws, 'j2')}\" \"{outside}\" && type \"{os.path.join(ws, 'j2', 'secret.txt')}\""],
        ["sandbox symlink to outside", "symlink", os.path.join(outside, "secret.txt"), os.path.join(ws, "s.txt")],
    ], [(ws, "rw")], "rec", cwd=ws))
    print("    icacls outside (no rule ACE must appear):\n" + icacls(outside))
    # a rule given through the junction path: where does the ACE land?
    ws2 = fresh("paths_ws2")
    tgt = fresh("paths_jtarget")
    write(os.path.join(tgt, "t.txt"))
    jr = os.path.join(ws2, "jrule")
    subprocess.run(["cmd", "/c", "mklink", "/J", jr, tgt], capture_output=True, check=True)
    wsp.ensure_rule_aces(jr, "ro", "restricted")
    print("    rule given as a junction path: ensure realpaths it, so the ACE lands on the TARGET:\n" + icacls(tgt))
    # non-existent deny row inside rw: the sandbox can create it and use it
    ws3 = fresh("paths_ws3")
    show("deny row that does not exist yet, inside rw (rec)", probe([
        ["mkdir denied path", "mkdir", os.path.join(ws3, "secrets")],
        ["write into it", "write", os.path.join(ws3, "secrets", "x.txt")],
        ["read back", "read", os.path.join(ws3, "secrets", "x.txt")],
    ], [(ws3, "rw"), (os.path.join(ws3, "secrets"), "deny")], "rec", cwd=ws3))
    # rule on a FILE: ro file inside an rw folder
    ws4 = fresh("paths_ws4")
    write(os.path.join(ws4, "ro.txt"))
    show("ro rule on a FILE inside rw (rec)", probe([
        ["read", "read", os.path.join(ws4, "ro.txt")], ["overwrite", "write", os.path.join(ws4, "ro.txt")],
        ["delete", "delete", os.path.join(ws4, "ro.txt")], ["rename", "rename", os.path.join(ws4, "ro.txt"), os.path.join(ws4, "r2.txt")],
    ], [(ws4, "rw"), (os.path.join(ws4, "ro.txt"), "ro")], "rec", cwd=ws4))


# ------------------------------------------------------------------------- links / moves
@section
def links():
    outside = fresh("links_outside")
    write(os.path.join(outside, "secret.txt")); write(os.path.join(outside, "secret2.txt")); write(os.path.join(outside, "moved.txt"))
    ws = fresh("links_ws")
    os.link(os.path.join(outside, "secret.txt"), os.path.join(ws, "hardlink.txt"))  # made BEFORE the first run
    show("hard link made by the user before ACEs (rec)", probe([
        ["read via link in rw", "read", os.path.join(ws, "hardlink.txt")],
        ["read via ORIGINAL outside path", "read", os.path.join(outside, "secret.txt")],
        ["write via ORIGINAL outside path", "append", os.path.join(outside, "secret.txt")],
        ["sandbox hard-links an outside file", "hardlink", os.path.join(outside, "secret2.txt"), os.path.join(ws, "hl2.txt")],
    ], [(ws, "rw")], "rec", cwd=ws))
    print("    icacls of the OUTSIDE file (propagation wrote the rule ACE onto it):\n" + icacls(os.path.join(outside, "secret.txt")))
    os.replace(os.path.join(outside, "moved.txt"), os.path.join(ws, "moved.txt"))  # moved in after ACEs
    show("file MOVED into rw after the ACEs (rec)", probe([["read moved", "read", os.path.join(ws, "moved.txt")]], [(ws, "rw")], "rec", cwd=ws))
    print("    icacls moved.txt:\n" + icacls(os.path.join(ws, "moved.txt")))
    # moved from rw into a refused folder: keeps its rw allow, lacks the deny
    ws2 = fresh("links_ws2")
    deny = os.path.join(ws2, "denied")
    os.makedirs(deny)
    write(os.path.join(ws2, "f.txt")); write(os.path.join(deny, "orig.txt"))
    rules = [(ws2, "rw"), (deny, "deny")]
    probe([["warmup", "cwd"]], rules, "rec", cwd=ws2)  # writes the ACEs
    os.replace(os.path.join(ws2, "f.txt"), os.path.join(deny, "f_moved_in.txt"))
    show("file moved by the user from rw INTO the refused folder (rec)", probe([
        ["read original denied file", "read", os.path.join(deny, "orig.txt")],
        ["read moved-in file", "read", os.path.join(deny, "f_moved_in.txt")],
    ], rules, "rec", cwd=ws2))
    # protected (non-inheriting) ACL inside rw
    ws3 = fresh("links_ws3")
    p = os.path.join(ws3, "protected.txt")
    write(p)
    subprocess.run(["icacls", p, "/inheritance:r", "/grant:r", f"{os.environ['USERNAME']}:F"], capture_output=True, check=True)
    show("protected-ACL file inside rw (rec)", probe([["read", "read", p], ["write", "append", p]], [(ws3, "rw")], "rec", cwd=ws3))


# ------------------------------------------------------------------------- ownership
@section
def ownership():
    ws = fresh("own_ws")
    r = sbx(["cmd", "/c", "echo should-not-run"], [(ws, "rw"), (r"C:\Windows\System32\drivers\etc", "ro")], "rec", cwd=ws)
    print(f"    rule on C:\\Windows\\System32\\drivers\\etc: {short(r, 300)}")
    locked = fresh("own_locked")
    # owner loses implicit WRITE_DAC through an OWNER RIGHTS ACE; protected so nothing grants it back
    subprocess.run(["icacls", locked, "/inheritance:r", "/grant:r", "*S-1-3-4:(OI)(CI)M", "/grant:r", f"{os.environ['USERNAME']}:(OI)(CI)M", "*S-1-5-18:(OI)(CI)F"], capture_output=True, check=True)
    h = wsp.CreateFileW(locked, wsp.WRITE_DAC, wsp.FILE_SHARE_ALL, None, wsp.OPEN_EXISTING, wsp.FILE_FLAG_BACKUP_SEMANTICS, None)
    print(f"    detection: CreateFileW(dir, WRITE_DAC) on the locked folder -> {'opened' if h and h != wsp.INVALID_HANDLE else 'ERROR ' + str(ctypes.get_last_error())}")
    if h and h != wsp.INVALID_HANDLE:
        wsp.CloseHandle(h)
    r = sbx(["cmd", "/c", "echo should-not-run"], [(ws, "rw"), (locked, "rw")], "rec", cwd=ws)
    print(f"    rule on a folder without WRITE_DAC: {short(r, 300)}")
    # a child inside the rule that denies WRITE_DAC: does propagation report it?
    parent = fresh("own_parent")
    child = os.path.join(parent, "child")
    os.makedirs(child)
    write(os.path.join(child, "c.txt"))
    subprocess.run(["icacls", child, "/deny", "*S-1-3-4:(WDAC)"], capture_output=True, check=True)
    t0 = time.perf_counter()
    try:
        wrote = wsp.ensure_rule_aces(parent, "ro", "restricted")
        print(f"    ensure on parent whose child denies WRITE_DAC: returned {wrote} ({(time.perf_counter() - t0) * 1000:.1f} ms)")
    except Exception as e:
        print(f"    ensure on parent whose child denies WRITE_DAC: RAISED {e}")
    try:
        wsp.ensure_rule_aces(parent, "ro", "restricted")
        print("    second ensure: returned (no failure seen!)")
    except Exception as e:
        print(f"    second ensure still fails closed (root ACE rolled back): {str(e)[:90]}")
    print("    child ACL after:\n" + icacls(child))
    show("sandbox access to that child's file (rec)", probe([["read child file", "read", os.path.join(child, "c.txt")]], [(ws, "rw"), (parent, "ro")], "rec", cwd=ws))


# ------------------------------------------------------------------------- ACE cost on a Python tree
@section
def acecost():
    import shutil
    src = PY_BASE
    dst = os.path.join(CASES, "py312_acecost")
    if os.path.exists(dst):
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", dst], capture_output=True)
    shutil.copytree(src, dst)  # copied files inherit the destination ACL (no rule ACEs)
    n = sum(len(f) + len(d) for _, d, f in os.walk(dst))
    t0 = time.perf_counter()
    wrote = wsp.ensure_rule_aces(dst, "read", "restricted")
    t1 = time.perf_counter()
    print(f"    first ensure (read ACE, propagation over {n} entries, {sum(os.path.getsize(os.path.join(a, x)) for a, _, fs in os.walk(dst) for x in fs) // 2**20} MB): wrote={wrote} {(t1 - t0) * 1000:.0f} ms")
    times = []
    for _ in range(50):
        t0 = time.perf_counter()
        wrote = wsp.ensure_rule_aces(dst, "read", "restricted")
        times.append((time.perf_counter() - t0) * 1000)
    print(f"    repeated ensure (already applied): wrote={wrote} median {statistics.median(times):.3f} ms, max {max(times):.3f} ms")
    deep = os.path.join(dst, "Lib", "json", "decoder.py")
    print("    a deep file got the inherited ACE:\n" + icacls(deep))
    r = sbx([os.path.join(dst, "python.exe"), "-c", "import json, ssl, sqlite3; print('copied python ok')"], [(fresh("acecost_ws"), "rw"), (dst, "read")], "rec")
    print(f"    the copied python runs sandboxed with only its 'read' rule: {short(r)}")


# ------------------------------------------------------------------------- overhead
@section
def overhead():
    ws = fresh("ovh_ws")
    rules = [(ws, "rw")]
    pol = policy(rules, "rec")
    gw_py = os.path.join(os.environ["APPDATA"], "uv", "tools", "abstractgateway", "Scripts", "python.exe")

    def med(argv, n=20, **kw):
        ts = []
        for _ in range(n):
            t0 = time.perf_counter()
            subprocess.run(argv, capture_output=True, **kw)
            ts.append((time.perf_counter() - t0) * 1000)
        return f"median {statistics.median(ts):6.1f} ms  (min {min(ts):.1f}, max {max(ts):.1f})"

    target = ["cmd.exe", "/d", "/c", "exit 0"]
    sbx(target, rules, "rec", cwd=ws)  # ACEs already applied afterwards
    print("    cmd /c exit 0 unsandboxed            :", med(target, cwd=ws))
    print("    helper (py312 -I helper.py), rec     :", med([HOST_PY, "-I", HELPER, pol, "--"] + target, cwd=ws))
    print("    helper (gateway python -I helper.py) :", med([gw_py, "-I", HELPER, pol, "--"] + target, cwd=ws))
    print("    python -I -c pass (interpreter only) :", med([HOST_PY, "-I", "-c", "pass"]))
    print("    helper: import only (-c import)      :", med([HOST_PY, "-I", "-c", f"import sys; sys.path.insert(0, r'{W}'); import win_sandbox_proto"]))
    print("    gateway python -c 'import abstractcore.tools.sandbox':", med([gw_py, "-c", "import abstractcore.tools.sandbox"], n=10))
    r = subprocess.run([gw_py, "-X", "importtime", "-c", "import abstractcore.tools.sandbox"], capture_output=True, text=True)
    rows = [l for l in r.stderr.splitlines() if l.startswith("import time:") and "|" in l]
    parsed = []
    for l in rows[1:]:
        parts = l.split("|")
        try:
            parsed.append((int(parts[1]), parts[2].rstrip()))
        except ValueError:
            pass
    top = sorted(parsed, reverse=True)[:8]
    print("    -X importtime, top cumulative (us):", "; ".join(f"{name.strip()} {us}" for us, name in top))
    t0 = time.perf_counter()
    h = wsp.build_restricted_token(list(wsp.RESTRICTED_BASE_SIDS) + [wsp.rule_sid("rw", ws, "restricted"), wsp.launch_sid()], ["S-1-5-18"], "low")
    wsp.CloseHandle(h)
    print(f"    in-process: build_restricted_token {(time.perf_counter() - t0) * 1000:.2f} ms")
    t0 = time.perf_counter()
    d = wsp._Desktop("S-1-5-18", wsp.launch_sid()); d.close()
    print(f"    in-process: private window station + desktop {(time.perf_counter() - t0) * 1000:.2f} ms")


# ------------------------------------------------------------------------- process behaviour
def _alive(pid):
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = ctypes.c_void_p
    h = k.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    code = ctypes.c_ulong()
    k.GetExitCodeProcess(ctypes.c_void_p(h), ctypes.byref(code))
    k.CloseHandle(ctypes.c_void_p(h))
    return code.value == 259


@section
def process():
    import signal
    ws = fresh("proc_ws")
    rules = [(ws, "rw")]
    tree = ("import subprocess,sys,os,time; g=subprocess.Popen([sys.executable,'-c','import time;time.sleep(300)']);"
            "print(os.getpid(), g.pid, flush=True); time.sleep(300)")
    for how in ("taskkill /F (no /T)", "Popen.terminate()", "CTRL_BREAK_EVENT"):
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if how == "CTRL_BREAK_EVENT" else 0
        p = subprocess.Popen([HOST_PY, "-I", HELPER, policy(rules, "rec"), "--", VPY, "-c", tree], stdout=subprocess.PIPE, text=True, cwd=ws, creationflags=flags)
        child, grand = map(int, p.stdout.readline().split())
        before = (_alive(child), _alive(grand))
        t0 = time.perf_counter()
        if how.startswith("taskkill"):
            subprocess.run(["taskkill", "/PID", str(p.pid), "/F"], capture_output=True)
        elif how.startswith("Popen"):
            p.terminate()
        else:
            os.kill(p.pid, signal.CTRL_BREAK_EVENT)
        p.wait(30)
        time.sleep(0.3)
        print(f"    {how:22}: helper rc={p.returncode & 0xFFFFFFFF:#x}; alive before {before}, after child={_alive(child)} grandchild={_alive(grand)} ({(time.perf_counter() - t0) * 1000:.0f} ms)")
    for code in ("exit 42", "exit -1073741819"):
        r = sbx(["cmd", "/d", "/c", code], rules, "rec", cwd=ws)
        print(f"    exit code pass-through `{code}`: {r.returncode & 0xFFFFFFFF:#x}")
    r = sbx([VPY, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"], rules, "rec", cwd=ws)
    print(f"    stdout/stderr separate: {short(r)}")
    r = sbx([VPY, "-c", "print(input()[::-1])"], rules, "rec", cwd=ws, input="hello sandbox\n")
    print(f"    stdin pass-through: {short(r)}")
    t0 = time.perf_counter()
    r = sbx([VPY, "-c", "import sys; sys.stdout.write('x' * 10_000_000); sys.stderr.write('y' * 2_000_000)"], rules, "rec", cwd=ws)
    print(f"    10 MB stdout + 2 MB stderr: got {len(r.stdout)} / {len(r.stderr)} bytes rc={r.returncode} in {(time.perf_counter() - t0) * 1000:.0f} ms")
    r = sbx([VPY, "-c", "import time; time.sleep(5)"], rules, "rec", cwd=ws, timeout=60)
    t0 = time.perf_counter()
    try:
        sbx([VPY, "-c", "import time; time.sleep(30)"], rules, "rec", cwd=ws, timeout=2)
    except subprocess.TimeoutExpired:
        print(f"    subprocess.run(timeout=2) on the helper raised TimeoutExpired after {(time.perf_counter() - t0):.1f}s (run() kills the helper)")
    for label, flags in (("CREATE_NO_WINDOW", subprocess.CREATE_NO_WINDOW), ("DETACHED_PROCESS", subprocess.DETACHED_PROCESS)):
        opsf = os.path.join(TOOLS, "ops_console.json")
        json.dump([["console", "console"]], open(opsf, "w"))
        r = sbx([VPY, "-I", PROBE, "@" + opsf], rules, "rec", cwd=ws, creationflags=flags)
        r2 = sbx(["cmd", "/d", "/c", "echo hi-from-cmd"], rules, "rec", cwd=ws, creationflags=flags)
        print(f"    parent {label:17}: child console {r.stdout.strip()}  cmd output={r2.stdout.strip()!r}")
    # the sandboxed process cannot open its own launcher (helper) or escape the job
    r = sbx([VPY, "-c", "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','pass'], creationflags=0x01000000); p.wait(); print('breakaway', p.returncode)"], rules, "rec", cwd=ws)
    print(f"    CREATE_BREAKAWAY_FROM_JOB inside: {short(r, 120)}")



# ------------------------------------------------------------------------- owner rights
@section
def owner():
    """Owner implicit rights (READ_CONTROL | WRITE_DAC) on user-owned objects outside the
    rows: if they applied in the restricted pass, the sandbox could rewrite any ACL."""
    ws = fresh("owner_ws")
    outside = fresh("owner_outside")
    write(os.path.join(outside, "secret.txt")); write(os.path.join(ws, "mine.txt"))
    home = os.path.expanduser("~")
    ops = []
    for label, path in (("outside folder (user-owned, no rule)", outside), ("outside file", os.path.join(outside, "secret.txt")),
                        ("profile Documents", os.path.join(home, "Documents")), ("C:\\abstractframework", r"C:\abstractframework"),
                        ("file inside rw row", os.path.join(ws, "mine.txt"))):
        for aname, acc in (("READ_CONTROL", 0x20000), ("WRITE_DAC", 0x40000), ("WRITE_OWNER", 0x80000)):
            ops.append([f"{label}: {aname}", "openraw", path, acc])
    ops.append(["icacls /grant Everyone on outside file", "spawn", f'icacls "{os.path.join(outside, "secret.txt")}" /grant *S-1-1-0:F'])
    ops.append(["icacls /grant Everyone on file in rw", "spawn", f'icacls "{os.path.join(ws, "mine.txt")}" /grant *S-1-1-0:F'])
    for mode in ("rec", "restricted"):
        show(f"owner rights [{mode}]", probe(ops, [(ws, "rw")], mode, cwd=ws))


# ------------------------------------------------------------------------- scan
@section
def scan():
    """Walk system trees from INSIDE the sandbox: every directory where FILE_ADD_FILE opens,
    every root-level folder that lists, every registry key that opens for write (no writes)."""
    import shutil
    shutil.copy2(os.path.join(W, "scan.py"), os.path.join(TOOLS, "scan.py"))
    ws = fresh("scan_ws")
    skip = ("windows", "programdata", "program files", "program files (x86)", "users")
    roots = [os.path.join("C:\\", n) for n in os.listdir("C:\\") if os.path.isdir(os.path.join("C:\\", n))]
    cfg = {"trees": [["C:\\", 1], [r"C:\Windows", 4], [r"C:\ProgramData", 4], [r"C:\Program Files", 3], [r"C:\Program Files (x86)", 3], [r"C:\Users", 3]]
                    + [[r, 3] for r in roots if os.path.basename(r).lower() not in skip],
           "roots": roots + [os.path.expanduser("~"), os.environ["LOCALAPPDATA"]],
           "reg": [["HKEY_CURRENT_USER", "Software", 3], ["HKEY_LOCAL_MACHINE", "SOFTWARE", 3]]}
    for mode in ("rec", "restricted", "appcontainer"):
        r = sbx([VPY, "-I", os.path.join(TOOLS, "scan.py"), json.dumps(cfg)], [(ws, "rw")], mode, cwd=ws, timeout=1200)
        try:
            res = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            print(f"    [{mode}] scan failed: {short(r, 300)}")
            continue
        wr = res["add_file"]
        groups = {}
        for pth in wr:
            key = next((g for g in ("DriverStore", "ProgramData", "Program Files (x86)", "Program Files") if g.lower() in pth.lower()), "other")
            groups.setdefault(key, []).append(pth)
        print(f"\n    [{mode}] {res['dirs']} dirs walked; {len(wr)} writable (FILE_ADD_FILE) dirs outside the rows: " + ", ".join(f"{k}={len(v)}" for k, v in groups.items()))
        for pth in groups.get("other", []) + groups.get("ProgramData", [])[:6]:
            print(f"        {pth}")
        print(f"      add-subdirectory only: {res['add_subdir']}")
        print(f"      listable root-level folders ({len(res['root_listable'])}): {[os.path.basename(x) or x for x in res['root_listable']]}")
        print(f"      writable registry keys ({len(res['reg_writable'])}): {res['reg_writable'][:20]}")


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(SECTIONS)
    for name in wanted:
        print(f"\n================ {name} ================")
        t0 = time.perf_counter()
        SECTIONS[name]()
        print(f"({name}: {time.perf_counter() - t0:.1f}s)")
