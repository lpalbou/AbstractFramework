"""Prototype: Windows backend for the "any_except_denied" posture (stdlib + ctypes only).

Token recipe
  rw (default_mode "rw"):  CreateRestrictedToken(own primary token, DISABLE_MAX_PRIVILEGE,
      restricting SIDs = MIRROR (user SID + every ENABLED group incl. the logon SID; never the
      deny-only or integrity SIDs) + one synthetic SID per rule).  The second access check then
      equals the first, except where an ACE names a rule SID.
  ro (default_mode "ro"):  the same token, plus TokenIntegrityLevel = Low (S-1-16-4096); the
      writable places (rw rows, private workspace, .tmp) get an inheritable Low label.

File rules (explicit, inheritable (OI)(CI) ACEs on the rule's real path, for the rule's SID)
  deny : Deny FILE_ALL_ACCESS
  ro   : Deny write-type rights + Allow RX
  rw   : Allow Modify
  read : Allow RX                      (system roots that must stay readable)
  and on every deny/ro root an inheritable "OWNER RIGHTS: Allow READ_CONTROL" ACE, which
  removes the owner's implicit WRITE_DAC (without it the sandbox rewrites the DACL of its own
  files and strips the deny ACE: see anyexcept_tests.py, test A-owner).

Launch: CreateProcessAsUserW(restricted token, CREATE_SUSPENDED) -> AssignProcessToJobObject
(KILL_ON_JOB_CLOSE, no breakaway) -> ResumeThread.
"""
from __future__ import annotations

import ctypes
import hashlib
import msvcrt
import os
import subprocess
import time
from ctypes import wintypes as W

advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PSID = ctypes.c_void_p
PACL = ctypes.c_void_p
PSD = ctypes.c_void_p


def _f(dll, name, restype, *argtypes):
    fn = getattr(dll, name)
    fn.restype = restype
    fn.argtypes = list(argtypes)
    return fn


def _check(ok, what):
    if not ok:
        err = ctypes.get_last_error()
        raise OSError(err, f"{what}: {ctypes.FormatError(err).strip()} ({err})")
    return ok


def _check_err(rc, what):
    if rc != 0:
        raise OSError(rc, f"{what}: {ctypes.FormatError(rc).strip()} ({rc})")


# ---------------------------------------------------------------------------------------
# structures
# ---------------------------------------------------------------------------------------
class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", PSID), ("Attributes", W.DWORD)]


class TOKEN_MANDATORY_LABEL(ctypes.Structure):
    _fields_ = [("Label", SID_AND_ATTRIBUTES)]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR), ("lpTitle", W.LPWSTR),
                ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
                ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", W.HANDLE), ("hStdOutput", W.HANDLE),
                ("hStdError", W.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("R", "W", "O", "RB", "WB", "OB")]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", W.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class ACE_HEADER(ctypes.Structure):
    _fields_ = [("AceType", ctypes.c_ubyte), ("AceFlags", ctypes.c_ubyte), ("AceSize", W.WORD)]


class GENERIC_MAPPING(ctypes.Structure):
    _fields_ = [("GenericRead", W.DWORD), ("GenericWrite", W.DWORD), ("GenericExecute", W.DWORD), ("GenericAll", W.DWORD)]


# ---------------------------------------------------------------------------------------
# functions
# ---------------------------------------------------------------------------------------
GetCurrentProcess = _f(kernel32, "GetCurrentProcess", W.HANDLE)
CloseHandle = _f(kernel32, "CloseHandle", W.BOOL, W.HANDLE)
LocalFree = _f(kernel32, "LocalFree", ctypes.c_void_p, ctypes.c_void_p)
OpenProcessToken = _f(advapi32, "OpenProcessToken", W.BOOL, W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE))
GetTokenInformation = _f(advapi32, "GetTokenInformation", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD))
SetTokenInformation = _f(advapi32, "SetTokenInformation", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD)
CreateRestrictedToken = _f(advapi32, "CreateRestrictedToken", W.BOOL, W.HANDLE, W.DWORD, W.DWORD, ctypes.c_void_p,
                           W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.POINTER(SID_AND_ATTRIBUTES), ctypes.POINTER(W.HANDLE))
DuplicateTokenEx = _f(advapi32, "DuplicateTokenEx", W.BOOL, W.HANDLE, W.DWORD, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(W.HANDLE))
ConvertStringSidToSidW = _f(advapi32, "ConvertStringSidToSidW", W.BOOL, W.LPCWSTR, ctypes.POINTER(PSID))
ConvertSidToStringSidW = _f(advapi32, "ConvertSidToStringSidW", W.BOOL, PSID, ctypes.POINTER(W.LPWSTR))
GetLengthSid = _f(advapi32, "GetLengthSid", W.DWORD, PSID)
EqualSid = _f(advapi32, "EqualSid", W.BOOL, PSID, PSID)
CreateProcessAsUserW = _f(advapi32, "CreateProcessAsUserW", W.BOOL, W.HANDLE, W.LPCWSTR, W.LPWSTR, ctypes.c_void_p,
                          ctypes.c_void_p, W.BOOL, W.DWORD, ctypes.c_void_p, W.LPCWSTR, ctypes.POINTER(STARTUPINFOW),
                          ctypes.POINTER(PROCESS_INFORMATION))
CreateJobObjectW = _f(kernel32, "CreateJobObjectW", W.HANDLE, ctypes.c_void_p, W.LPCWSTR)
SetInformationJobObject = _f(kernel32, "SetInformationJobObject", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD)
AssignProcessToJobObject = _f(kernel32, "AssignProcessToJobObject", W.BOOL, W.HANDLE, W.HANDLE)
TerminateJobObject = _f(kernel32, "TerminateJobObject", W.BOOL, W.HANDLE, W.UINT)
ResumeThread = _f(kernel32, "ResumeThread", W.DWORD, W.HANDLE)
WaitForSingleObject = _f(kernel32, "WaitForSingleObject", W.DWORD, W.HANDLE, W.DWORD)
GetExitCodeProcess = _f(kernel32, "GetExitCodeProcess", W.BOOL, W.HANDLE, ctypes.POINTER(W.DWORD))
GetNamedSecurityInfoW = _f(advapi32, "GetNamedSecurityInfoW", W.DWORD, W.LPCWSTR, ctypes.c_int, W.DWORD,
                           ctypes.POINTER(PSID), ctypes.POINTER(PSID), ctypes.POINTER(PACL), ctypes.POINTER(PACL), ctypes.POINTER(PSD))
SetNamedSecurityInfoW = _f(advapi32, "SetNamedSecurityInfoW", W.DWORD, W.LPWSTR, ctypes.c_int, W.DWORD, PSID, PSID, PACL, PACL)
GetSecurityDescriptorControl = _f(advapi32, "GetSecurityDescriptorControl", W.BOOL, PSD, ctypes.POINTER(W.WORD), ctypes.POINTER(W.DWORD))
InitializeAcl = _f(advapi32, "InitializeAcl", W.BOOL, PACL, W.DWORD, W.DWORD)
GetAce = _f(advapi32, "GetAce", W.BOOL, PACL, W.DWORD, ctypes.POINTER(ctypes.c_void_p))
AddAce = _f(advapi32, "AddAce", W.BOOL, PACL, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD)
AddAccessAllowedAceEx = _f(advapi32, "AddAccessAllowedAceEx", W.BOOL, PACL, W.DWORD, W.DWORD, W.DWORD, PSID)
AddAccessDeniedAceEx = _f(advapi32, "AddAccessDeniedAceEx", W.BOOL, PACL, W.DWORD, W.DWORD, W.DWORD, PSID)
AddMandatoryAce = _f(advapi32, "AddMandatoryAce", W.BOOL, PACL, W.DWORD, W.DWORD, W.DWORD, PSID)
GetFileSecurityW = _f(advapi32, "GetFileSecurityW", W.BOOL, W.LPCWSTR, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD))
AccessCheck = _f(advapi32, "AccessCheck", W.BOOL, ctypes.c_void_p, W.HANDLE, W.DWORD, ctypes.POINTER(GENERIC_MAPPING),
                 ctypes.c_void_p, ctypes.POINTER(W.DWORD), ctypes.POINTER(W.DWORD), ctypes.POINTER(W.BOOL))

# token / security constants
TOKEN_ALL_ACCESS = 0xF01FF
TokenUser, TokenGroups, TokenRestrictedSids, TokenIntegrityLevel, TokenPrivileges = 1, 2, 11, 25, 3
SE_GROUP_ENABLED, SE_GROUP_USE_FOR_DENY_ONLY, SE_GROUP_INTEGRITY, SE_GROUP_LOGON_ID = 0x4, 0x10, 0x20, 0xC0000000
DISABLE_MAX_PRIVILEGE, WRITE_RESTRICTED = 0x1, 0x8
SE_FILE_OBJECT = 1
OWNER_SI, GROUP_SI, DACL_SI, LABEL_SI = 0x1, 0x2, 0x4, 0x10
PROTECTED_DACL_SI, UNPROTECTED_DACL_SI = 0x80000000, 0x20000000
SE_DACL_PROTECTED = 0x1000
OI_CI = 0x3
INHERITED_ACE = 0x10
ACL_REVISION = 2
FILE_ALL = 0x1F01FF
FILE_RX = 0x1200A9
FILE_MODIFY = 0x1301BF
# write-type rights: WriteData/AddFile, AppendData/AddSubdir, WriteEA, DeleteChild, WriteAttributes, DELETE, WRITE_DAC, WRITE_OWNER
FILE_WRITE_TYPE = 0x2 | 0x4 | 0x10 | 0x40 | 0x100 | 0x10000 | 0x40000 | 0x80000
READ_CONTROL = 0x20000
FILE_MAPPING = GENERIC_MAPPING(0x120089, 0x120116, 0x1200A0, 0x1F01FF)
OWNER_RIGHTS = "S-1-3-4"
LOW_IL, MEDIUM_IL = "S-1-16-4096", "S-1-16-8192"


class Sid:
    """An owned binary SID (from a string)."""

    def __init__(self, text: str):
        p = PSID()
        _check(ConvertStringSidToSidW(text, ctypes.byref(p)), f"ConvertStringSidToSid {text}")
        n = GetLengthSid(p)
        self.buf = ctypes.create_string_buffer(ctypes.string_at(p, n), n)
        LocalFree(p)
        self.text = text

    @property
    def ptr(self):
        return ctypes.cast(self.buf, PSID)


def sid_text(psid) -> str:
    s = W.LPWSTR()
    _check(ConvertSidToStringSidW(psid, ctypes.byref(s)), "ConvertSidToStringSid")
    out = s.value
    LocalFree(s)
    return out


def rule_sid(action: str, path: str) -> str:
    """Deterministic synthetic SID per (action, real path): S-1-9-<4 x 32 bit of sha256>.
    Authority 9 (resource manager) never resolves to an account and never triggers a lookup."""
    h = hashlib.sha256(f"abstractframework-sandbox\0{action}\0{os.path.normcase(os.path.realpath(path))}".encode()).digest()
    parts = [int.from_bytes(h[i:i + 4], "little") for i in range(0, 16, 4)]
    return "S-1-9-" + "-".join(str(p) for p in parts)


# ---------------------------------------------------------------------------------------
# token
# ---------------------------------------------------------------------------------------
def _token_info(tok, cls):
    n = W.DWORD()
    GetTokenInformation(tok, cls, None, 0, ctypes.byref(n))
    buf = ctypes.create_string_buffer(n.value)
    _check(GetTokenInformation(tok, cls, buf, n, ctypes.byref(n)), "GetTokenInformation")
    return buf


def _groups(buf):
    count = W.DWORD.from_buffer(buf).value
    off = ctypes.sizeof(ctypes.c_void_p)  # DWORD padded to pointer alignment
    arr = (SID_AND_ATTRIBUTES * count).from_buffer(buf, off)
    return [(sid_text(g.Sid), g.Attributes) for g in arr]


def own_token():
    tok = W.HANDLE()
    _check(OpenProcessToken(GetCurrentProcess(), TOKEN_ALL_ACCESS, ctypes.byref(tok)), "OpenProcessToken")
    return tok


def token_summary(tok) -> dict:
    user = sid_text(SID_AND_ATTRIBUTES.from_buffer(_token_info(tok, TokenUser)).Sid)
    groups = _groups(_token_info(tok, TokenGroups))
    restricted = _groups(_token_info(tok, TokenRestrictedSids))
    il = sid_text(TOKEN_MANDATORY_LABEL.from_buffer(_token_info(tok, TokenIntegrityLevel)).Label.Sid)
    return {"user": user, "groups": groups, "restricted": restricted, "integrity": il}


def mirror_sids(tok=None) -> list:
    """User SID + every enabled, non-deny-only, non-integrity group (incl. the logon SID)."""
    tok = tok or own_token()
    s = token_summary(tok)
    out = [s["user"]]
    for sid, attr in s["groups"]:
        if attr & SE_GROUP_ENABLED and not attr & SE_GROUP_USE_FOR_DENY_ONLY and not attr & SE_GROUP_INTEGRITY:
            out.append(sid)
    return out


def make_token(restricting, *, flags=DISABLE_MAX_PRIVILEGE, integrity=None):
    """A restricted primary token derived from this process's token."""
    base = own_token()
    sids = [Sid(t) for t in dict.fromkeys(restricting)]
    arr = (SID_AND_ATTRIBUTES * max(1, len(sids)))()
    for i, s in enumerate(sids):
        arr[i].Sid, arr[i].Attributes = s.ptr, 0
    new = W.HANDLE()
    _check(CreateRestrictedToken(base, flags, 0, None, 0, None, len(sids), arr, ctypes.byref(new)), "CreateRestrictedToken")
    CloseHandle(base)
    if integrity:
        il = Sid(integrity)
        tml = TOKEN_MANDATORY_LABEL()
        tml.Label.Sid, tml.Label.Attributes = il.ptr, SE_GROUP_INTEGRITY
        _check(SetTokenInformation(new, TokenIntegrityLevel, ctypes.byref(tml), ctypes.sizeof(tml) + GetLengthSid(il.ptr)), "SetTokenInformation(IL)")
    return new


def set_default_dacl(tok, sids):
    """Default DACL (GENERIC_ALL for each SID) for objects the process creates, incl. its own
    process/thread objects: needed for a restricting set WITHOUT the user SID (else 0xC0000142)."""
    objs = [Sid(s) for s in sids]
    acl = ctypes.create_string_buffer(8 + sum(16 + GetLengthSid(o.ptr) for o in objs))
    _check(InitializeAcl(acl, len(acl), ACL_REVISION), "InitializeAcl")
    for o in objs:
        _check(AddAccessAllowedAceEx(acl, ACL_REVISION, 0, 0x10000000, o.ptr), "AddAccessAllowedAceEx")
    pacl = ctypes.c_void_p(ctypes.addressof(acl))
    _check(SetTokenInformation(tok, 6, ctypes.byref(pacl), ctypes.sizeof(pacl)), "SetTokenInformation(DefaultDacl)")


def posture_token(rule_sids, default_mode="rw", *, flags=DISABLE_MAX_PRIVILEGE):
    """The recipe: mirror + rule SIDs; Low IL when default_mode is "ro"."""
    return make_token(mirror_sids() + list(rule_sids), flags=flags, integrity=LOW_IL if default_mode == "ro" else None)


# ---------------------------------------------------------------------------------------
# launch
# ---------------------------------------------------------------------------------------
def _env_block(env):
    s = "".join(f"{k}={v}\0" for k, v in sorted(env.items(), key=lambda kv: kv[0].upper())) + "\0"
    return ctypes.create_unicode_buffer(s, len(s))


def run(argv, token, *, cwd=None, env=None, timeout=120, keep_job=False):
    """Run argv (list or command line) under token inside a kill-on-close job. Returns
    (exit code, combined stdout+stderr text[, job handle])."""
    cmdline = argv if isinstance(argv, str) else subprocess.list2cmdline(argv)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out", f"{os.getpid()}_{time.time_ns()}.txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fout = open(out_path, "wb")
    fin = open(os.devnull, "rb")
    hout, hin = msvcrt.get_osfhandle(fout.fileno()), msvcrt.get_osfhandle(fin.fileno())
    os.set_handle_inheritable(hout, True)
    os.set_handle_inheritable(hin, True)
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    si.dwFlags = 0x100  # STARTF_USESTDHANDLES
    si.hStdInput, si.hStdOutput, si.hStdError = hin, hout, hout
    pi = PROCESS_INFORMATION()
    job = CreateJobObjectW(None, None)
    _check(job, "CreateJobObject")
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE (no BREAKAWAY_OK)
    _check(SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)), "SetInformationJobObject")
    block = _env_block(env) if env is not None else None
    buf = ctypes.create_unicode_buffer(cmdline)
    flags = 0x4 | 0x400 | 0x08000000  # SUSPENDED | UNICODE_ENVIRONMENT | NO_WINDOW
    try:
        _check(CreateProcessAsUserW(token, None, buf, None, None, True, flags, block, cwd, ctypes.byref(si), ctypes.byref(pi)), "CreateProcessAsUser")
    finally:
        fout.close()
        fin.close()
    try:
        _check(AssignProcessToJobObject(job, pi.hProcess), "AssignProcessToJobObject")
        ResumeThread(pi.hThread)
        rc = WaitForSingleObject(pi.hProcess, int(timeout * 1000))
        code = W.DWORD()
        if rc != 0:
            TerminateJobObject(job, 1)
            code.value = 0xDEADBEEF
        else:
            GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    finally:
        CloseHandle(pi.hThread)
        CloseHandle(pi.hProcess)
        if not keep_job:
            CloseHandle(job)  # kills whatever is left in the job
    time.sleep(0.05)
    with open(out_path, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    try:
        os.remove(out_path)
    except OSError:
        pass
    return (code.value, text, job) if keep_job else (code.value, text)


# ---------------------------------------------------------------------------------------
# DACL rules
# ---------------------------------------------------------------------------------------
def _explicit_aces(path):
    """(list of (raw ace bytes, type, flags, sid text|None), protected flag)."""
    dacl, sd = PACL(), PSD()
    _check_err(GetNamedSecurityInfoW(path, SE_FILE_OBJECT, DACL_SI, None, None, ctypes.byref(dacl), None, ctypes.byref(sd)), f"GetNamedSecurityInfo {path}")
    ctrl, rev = W.WORD(), W.DWORD()
    GetSecurityDescriptorControl(sd, ctypes.byref(ctrl), ctypes.byref(rev))
    out = []
    if dacl:
        count = ctypes.c_ushort.from_address(dacl.value + 4).value  # ACL.AceCount
        for i in range(count):
            p = ctypes.c_void_p()
            GetAce(dacl, i, ctypes.byref(p))
            h = ACE_HEADER.from_address(p.value)
            if h.AceFlags & INHERITED_ACE:
                continue
            sid = sid_text(p.value + 8) if h.AceType in (0, 1) else None
            out.append((ctypes.string_at(p.value, h.AceSize), h.AceType, h.AceFlags, sid))
    LocalFree(sd)
    return out, bool(ctrl.value & SE_DACL_PROTECTED)


def _write_dacl(path, denies, allows, keep, protected):
    """denies/allows: [(sid, mask, flags)]; keep: existing explicit raw aces (in order)."""
    sids = {s: Sid(s) for s, _, _ in denies + allows}
    size = 8 + sum(len(a[0]) for a in keep) + sum(16 + GetLengthSid(sids[s].ptr) for s, _, _ in denies + allows)
    acl = ctypes.create_string_buffer(size + 64)
    _check(InitializeAcl(acl, len(acl), ACL_REVISION), "InitializeAcl")
    for s, m, fl in denies:
        _check(AddAccessDeniedAceEx(acl, ACL_REVISION, fl, m, sids[s].ptr), "AddAccessDeniedAceEx")
    for raw, t, _, _ in keep:
        if t == 1:
            _check(AddAce(acl, ACL_REVISION, 0xFFFFFFFF, raw, len(raw)), "AddAce")
    for s, m, fl in allows:
        _check(AddAccessAllowedAceEx(acl, ACL_REVISION, fl, m, sids[s].ptr), "AddAccessAllowedAceEx")
    for raw, t, _, _ in keep:
        if t != 1:
            _check(AddAce(acl, ACL_REVISION, 0xFFFFFFFF, raw, len(raw)), "AddAce")
    si = DACL_SI | (PROTECTED_DACL_SI if protected else UNPROTECTED_DACL_SI)
    _check_err(SetNamedSecurityInfoW(path, SE_FILE_OBJECT, si, None, None, ctypes.cast(acl, PACL), None), f"SetNamedSecurityInfo {path}")


def rule_aces(action, sid, *, owner_fix=True):
    """(denies, allows) ACE lists for one rule."""
    if action == "deny":
        d, a = [(sid, FILE_ALL, OI_CI)], []
    elif action == "ro":
        d, a = [(sid, FILE_WRITE_TYPE, OI_CI)], [(sid, FILE_RX, OI_CI)]
    elif action == "rw":
        d, a = [], [(sid, FILE_MODIFY, OI_CI)]
    elif action == "read":
        d, a = [], [(sid, FILE_RX, OI_CI)]
    else:
        raise ValueError(action)
    if owner_fix and action in ("deny", "ro"):
        a.append((OWNER_RIGHTS, READ_CONTROL, OI_CI))
    return d, a


def add_rule(path, action, sid=None, *, owner_fix=True, inherit=True):
    """Add one rule's ACEs to path (merged with the path's existing explicit ACEs)."""
    sid = sid or rule_sid(action, path)
    keep, prot = _explicit_aces(path)
    d, a = rule_aces(action, sid, owner_fix=owner_fix)
    if not inherit or not os.path.isdir(path):
        d, a = [(s, m, 0) for s, m, _ in d], [(s, m, 0) for s, m, _ in a]
    existing = {(r[3], r[1]) for r in keep}
    a = [x for x in a if not (x[0] == OWNER_RIGHTS and (OWNER_RIGHTS, 0) in existing)]
    _write_dacl(path, d, a, keep, prot)
    return sid


def add_deny_delete_child(parent, sid):
    """Non-inheritable Deny FILE_DELETE_CHILD for sid on the parent: without it the parent's
    FILE_DELETE_CHILD (the user's Full Control) deletes/renames/replaces the rule's ROOT even
    though the root's own DACL denies DELETE (test A: 'refused FILE: delete')."""
    keep, prot = _explicit_aces(parent)
    _write_dacl(parent, [(sid, 0x40, 0)], [], keep, prot)


def protected_descendants(root):
    """Descendants whose DACL is protected (inheritance disabled): inheritable ACEs never
    reach them, so each needs the rule's ACEs explicitly (test A: 'protected child')."""
    out = []
    if not os.path.isdir(root) or os.path.islink(root):
        return out
    for dirpath, dirs, files in os.walk(root):
        # do not follow junctions/symlinks out of the tree
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(dirpath, d)) and not _is_junction(os.path.join(dirpath, d))]
        for n in dirs + files:
            p = os.path.join(dirpath, n)
            try:
                if _explicit_aces(p)[1]:
                    out.append(p)
            except OSError:
                out.append(p)  # unreadable SD: add_rule will raise -> refuse
    return out


def _is_junction(p):
    try:
        return os.path.isjunction(p)
    except AttributeError:  # < 3.12
        return bool(os.lstat(p).st_file_attributes & 0x400) and not os.path.islink(p)


def remove_sids(path, sids):
    """Revert: drop every explicit ACE naming one of sids (plus our OWNER RIGHTS ACE)."""
    sids = set(sids) | {OWNER_RIGHTS}
    keep, prot = _explicit_aces(path)
    _write_dacl(path, [], [], [k for k in keep if k[3] not in sids], prot)


def apply_rules(rules, *, owner_fix=True, parent_fix=True, walk_protected=True):
    """rules: [(action, path)] in _ordered_rules order. Returns [(path, sid)] applied
    (every ACL touched, for revert_rules). A path that does not exist or cannot be re-ACLed
    raises: the backend must refuse the spec."""
    applied = []
    for action, path in rules:
        sid = add_rule(path, action, owner_fix=owner_fix)
        applied.append((path, sid))
        if walk_protected:
            for p in protected_descendants(path):
                add_rule(p, action, sid, owner_fix=owner_fix)
                applied.append((p, sid))
        if parent_fix and action in ("deny", "ro"):
            parent = os.path.dirname(path)
            if parent and parent != path:
                add_deny_delete_child(parent, sid)
                applied.append((parent, sid))
    return applied


def revert_rules(applied):
    by_path = {}
    for path, sid in applied:
        by_path.setdefault(path, set()).add(sid)
    for path, sids in by_path.items():
        if os.path.lexists(path):
            remove_sids(path, sids)


# ---------------------------------------------------------------------------------------
# integrity labels (default_mode "ro")
# ---------------------------------------------------------------------------------------
def set_label(path, il_sid=LOW_IL, *, flags=OI_CI, policy=0x1):
    """Explicit mandatory label (default NO_WRITE_UP), or il_sid=None to remove it."""
    acl = ctypes.create_string_buffer(64)
    _check(InitializeAcl(acl, len(acl), ACL_REVISION), "InitializeAcl")
    if il_sid:
        s = Sid(il_sid)
        _check(AddMandatoryAce(acl, ACL_REVISION, flags, policy, s.ptr), "AddMandatoryAce")
    _check_err(SetNamedSecurityInfoW(path, SE_FILE_OBJECT, LABEL_SI, None, None, None, ctypes.cast(acl, PACL)), f"SetNamedSecurityInfo(label) {path}")


# ---------------------------------------------------------------------------------------
# AccessCheck (read-only probing of any path for any token)
# ---------------------------------------------------------------------------------------
def access_check(path, token, desired) -> int:
    """Granted mask for `desired` (0 = denied) on path's security descriptor, for token."""
    n = W.DWORD()
    si = OWNER_SI | GROUP_SI | DACL_SI | LABEL_SI
    GetFileSecurityW(path, si, None, 0, ctypes.byref(n))
    if not n.value:
        raise ctypes.WinError(ctypes.get_last_error())
    sd = ctypes.create_string_buffer(n.value)
    _check(GetFileSecurityW(path, si, sd, n, ctypes.byref(n)), f"GetFileSecurity {path}")
    imp = W.HANDLE()
    _check(DuplicateTokenEx(token, 0x8 | 0x4 | 0x2, None, 2, 2, ctypes.byref(imp)), "DuplicateTokenEx")
    ps = ctypes.create_string_buffer(256)
    psl, granted, status = W.DWORD(256), W.DWORD(), W.BOOL()
    _check(AccessCheck(sd, imp, desired, ctypes.byref(FILE_MAPPING), ps, ctypes.byref(psl), ctypes.byref(granted), ctypes.byref(status)), "AccessCheck")
    CloseHandle(imp)
    return granted.value if status.value else 0


def can_deny(path) -> str:
    """Backend pre-check for a refused row: "missing" | "already-unreadable" | "deniable" |
    "readable-not-deniable" (the user can read it but cannot WRITE_DAC it: refuse the spec)."""
    if not os.path.lexists(path):
        return "missing"
    tok = own_token()
    try:
        readable = access_check(path, tok, 0x1) != 0  # FILE_READ_DATA / LIST_DIRECTORY
        wdac = access_check(path, tok, 0x40000) != 0
    except OSError:
        return "already-unreadable"  # cannot even read its security descriptor
    finally:
        CloseHandle(tok)
    if wdac:
        return "deniable"
    return "readable-not-deniable" if readable else "already-unreadable"
