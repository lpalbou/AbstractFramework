"""Windows command sandbox launcher (prototype, stdlib + ctypes only, one file).

    python -I win_sandbox_proto.py <policy-json | @policy-file> -- <argv...>

policy = {"rules": [[path, action], ...]}   # action: rw | ro | deny | read
  experiment-only keys: "mode" ("restricted" | "appcontainer"), "integrity" ("low" |
  "medium"), "base" (restricting SIDs; "logon" = the logon SID), "desktop" ("private" |
  "inherit"), "ui_limits", "token_flags", "ensure", "appcontainer_name", "capabilities".

Default (recommended) mechanism, measured on Windows 10 19045:
- every rule (action, real path) has a deterministic SID S-1-9-1094866498-<4 hash words>;
  the rule's folder gets explicit inheritable ACEs for it (rw: allow Modify; ro: deny
  writes + allow RX; deny: deny all; read: allow RX), written once, checked in ~0.3 ms;
- the command runs with a restricted primary token (CreateRestrictedToken,
  DISABLE_MAX_PRIVILEGE) whose restricting SIDs are Users + Everyone + RESTRICTED (the
  smallest base that starts cmd/PowerShell/python/git/node), the run's rule SIDs, a
  constant SANDBOX_SID and a per-launch SID (default DACL, desktop); the kernel's second
  access-check pass grants only what those SIDs are granted, and Windows' canonical ACE
  order gives "most specific row wins, refusal wins a tie, ro beats rw on a tie";
- at Low integrity (rw rows get a Low label): closes the Users/Everyone-writable system
  folders and registry keys a medium restricted token can still write;
- on a per-launch desktop of the session's non-interactive window station; in a
  kill-on-close job with UI limits; only the three std handles are inherited.

Any failure before the command starts exits 126 without running it (fail closed).
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import sys
from ctypes import wintypes as W

EXIT_REFUSED = 126

# ---------------------------------------------------------------------------- constants
# Restricted-token mode only (S-1-15-* cannot be a restricting SID): Users (system files),
# Everyone (process start), RESTRICTED (HKCU reads at DLL init).
RESTRICTED_BASE_SIDS = ("S-1-5-32-545", "S-1-1-0", "S-1-5-12")
RULE_AUTHORITY = "S-1-9-1094866498"  # resource-manager authority + a fixed tag word
LAUNCH_AUTHORITY = "S-1-9-1094866499"
SANDBOX_SID = "S-1-9-1094866500"  # constant, in every token: opens the shared window station
CAPABILITY_AUTHORITY = "S-1-15-3-1024"  # custom capability SIDs (AppContainer mode)
# internetClient, internetClientServer, privateNetworkClientServer: network as on macOS/Linux
NETWORK_CAPABILITIES = ("S-1-15-3-1", "S-1-15-3-2", "S-1-15-3-3")
SE_GROUP_ENABLED = 0x4
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x20009

FILE_READ_DATA = 0x1
FILE_WRITE_DATA = 0x2
FILE_APPEND_DATA = 0x4
FILE_WRITE_EA = 0x10
FILE_DELETE_CHILD = 0x40
FILE_WRITE_ATTRIBUTES = 0x100
DELETE = 0x10000
READ_CONTROL = 0x20000
WRITE_DAC = 0x40000
WRITE_OWNER = 0x80000
GENERIC_ALL = 0x10000000
FILE_ALL_ACCESS = 0x1F01FF
MASK_RX = 0x1200A9
MASK_MODIFY = 0x1301BF
MASK_WRITES = (FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_WRITE_EA | FILE_WRITE_ATTRIBUTES
               | DELETE | FILE_DELETE_CHILD | WRITE_DAC | WRITE_OWNER)

ACCESS_ALLOWED_ACE_TYPE, ACCESS_DENIED_ACE_TYPE = 0, 1
OI_CI = 0x1 | 0x2
INHERITED_ACE = 0x10
GRANT_ACCESS, DENY_ACCESS = 1, 3
SE_FILE_OBJECT = 1
DACL_SECURITY_INFORMATION = 0x4

# action -> [(ace type, mask)] ; deny entries first (canonical order is enforced anyway)
RULE_ACES = {
    "rw": [(ACCESS_ALLOWED_ACE_TYPE, MASK_MODIFY)],
    "ro": [(ACCESS_DENIED_ACE_TYPE, MASK_WRITES), (ACCESS_ALLOWED_ACE_TYPE, MASK_RX)],
    "deny": [(ACCESS_DENIED_ACE_TYPE, FILE_ALL_ACCESS)],
    "read": [(ACCESS_ALLOWED_ACE_TYPE, MASK_RX)],
}

TOKEN_QUERY, TOKEN_DUPLICATE, TOKEN_ASSIGN_PRIMARY, TOKEN_ADJUST_DEFAULT = 0x8, 0x2, 0x1, 0x80
DISABLE_MAX_PRIVILEGE = 0x1
TokenUser, TokenGroups, TokenDefaultDacl = 1, 2, 6
SE_GROUP_LOGON_ID = 0xC0000000
ERROR_INSUFFICIENT_BUFFER = 122

CREATE_SUSPENDED = 0x4
CREATE_UNICODE_ENVIRONMENT = 0x400
CREATE_NO_WINDOW = 0x08000000
EXTENDED_STARTUPINFO_PRESENT = 0x80000
STARTF_USESTDHANDLES = 0x100
PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x20002
HANDLE_FLAG_INHERIT = 0x1
INFINITE = 0xFFFFFFFF
STD_HANDLES = (-10, -11, -12)

JobObjectBasicUIRestrictions, JobObjectExtendedLimitInformation = 4, 9
JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x400
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JOB_UI_ALL = 0xFF  # handles, clipboard r/w, sysparams, display, global atoms, desktop, exitwindows

OPEN_EXISTING = 3
FILE_SHARE_ALL = 0x7
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE = W.HANDLE(-1).value

# ---------------------------------------------------------------------------- ctypes
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_adv = ctypes.WinDLL("advapi32", use_last_error=True)
_u32 = ctypes.WinDLL("user32", use_last_error=True)
PSID = ctypes.c_void_p
PACL = ctypes.c_void_p


class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", PSID), ("Attributes", W.DWORD)]


class TOKEN_DEFAULT_DACL(ctypes.Structure):
    _fields_ = [("DefaultDacl", PACL)]


class ACE_HEADER(ctypes.Structure):
    _fields_ = [("AceType", W.BYTE), ("AceFlags", W.BYTE), ("AceSize", W.WORD)]


class ACCESS_ACE(ctypes.Structure):  # ACCESS_ALLOWED_ACE / ACCESS_DENIED_ACE
    _fields_ = [("Header", ACE_HEADER), ("Mask", W.DWORD), ("SidStart", W.DWORD)]


class ACL_SIZE_INFORMATION(ctypes.Structure):
    _fields_ = [("AceCount", W.DWORD), ("AclBytesInUse", W.DWORD), ("AclBytesFree", W.DWORD)]


class TRUSTEE_W(ctypes.Structure):
    _fields_ = [("pMultipleTrustee", ctypes.c_void_p), ("MultipleTrusteeOperation", ctypes.c_int),
                ("TrusteeForm", ctypes.c_int), ("TrusteeType", ctypes.c_int), ("ptstrName", ctypes.c_void_p)]


class EXPLICIT_ACCESS_W(ctypes.Structure):
    _fields_ = [("grfAccessPermissions", W.DWORD), ("grfAccessMode", ctypes.c_int),
                ("grfInheritance", W.DWORD), ("Trustee", TRUSTEE_W)]


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", W.DWORD), ("lpSecurityDescriptor", ctypes.c_void_p), ("bInheritHandle", W.BOOL)]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR), ("lpTitle", W.LPWSTR),
                ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
                ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", W.HANDLE), ("hStdOutput", W.HANDLE),
                ("hStdError", W.HANDLE)]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [("AppContainerSid", PSID), ("Capabilities", ctypes.POINTER(SID_AND_ATTRIBUTES)),
                ("CapabilityCount", W.DWORD), ("Reserved", W.DWORD)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", W.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


def _proto(dll, name, restype, *argtypes):
    fn = getattr(dll, name)
    fn.restype, fn.argtypes = restype, list(argtypes)
    return fn


P = ctypes.POINTER
GetCurrentProcess = _proto(_k32, "GetCurrentProcess", W.HANDLE)
CloseHandle = _proto(_k32, "CloseHandle", W.BOOL, W.HANDLE)
LocalFree = _proto(_k32, "LocalFree", ctypes.c_void_p, ctypes.c_void_p)
GetStdHandle = _proto(_k32, "GetStdHandle", W.HANDLE, W.DWORD)
SetHandleInformation = _proto(_k32, "SetHandleInformation", W.BOOL, W.HANDLE, W.DWORD, W.DWORD)
GetConsoleCP = _proto(_k32, "GetConsoleCP", W.UINT)
CreateFileW = _proto(_k32, "CreateFileW", W.HANDLE, W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE)
InitializeProcThreadAttributeList = _proto(_k32, "InitializeProcThreadAttributeList", W.BOOL, ctypes.c_void_p, W.DWORD, W.DWORD, P(ctypes.c_size_t))
UpdateProcThreadAttribute = _proto(_k32, "UpdateProcThreadAttribute", W.BOOL, ctypes.c_void_p, W.DWORD, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p)
DeleteProcThreadAttributeList = _proto(_k32, "DeleteProcThreadAttributeList", None, ctypes.c_void_p)
CreateJobObjectW = _proto(_k32, "CreateJobObjectW", W.HANDLE, ctypes.c_void_p, W.LPCWSTR)
SetInformationJobObject = _proto(_k32, "SetInformationJobObject", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD)
AssignProcessToJobObject = _proto(_k32, "AssignProcessToJobObject", W.BOOL, W.HANDLE, W.HANDLE)
ResumeThread = _proto(_k32, "ResumeThread", W.DWORD, W.HANDLE)
TerminateProcess = _proto(_k32, "TerminateProcess", W.BOOL, W.HANDLE, W.UINT)
WaitForSingleObject = _proto(_k32, "WaitForSingleObject", W.DWORD, W.HANDLE, W.DWORD)
GetExitCodeProcess = _proto(_k32, "GetExitCodeProcess", W.BOOL, W.HANDLE, P(W.DWORD))
OpenProcessToken = _proto(_adv, "OpenProcessToken", W.BOOL, W.HANDLE, W.DWORD, P(W.HANDLE))
GetTokenInformation = _proto(_adv, "GetTokenInformation", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, P(W.DWORD))
SetTokenInformation = _proto(_adv, "SetTokenInformation", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD)
CreateRestrictedToken = _proto(_adv, "CreateRestrictedToken", W.BOOL, W.HANDLE, W.DWORD, W.DWORD, P(SID_AND_ATTRIBUTES), W.DWORD, ctypes.c_void_p, W.DWORD, P(SID_AND_ATTRIBUTES), P(W.HANDLE))
ConvertStringSidToSidW = _proto(_adv, "ConvertStringSidToSidW", W.BOOL, W.LPCWSTR, P(PSID))
ConvertSidToStringSidW = _proto(_adv, "ConvertSidToStringSidW", W.BOOL, PSID, P(W.LPWSTR))
GetLengthSid = _proto(_adv, "GetLengthSid", W.DWORD, PSID)
EqualSid = _proto(_adv, "EqualSid", W.BOOL, PSID, PSID)
InitializeAcl = _proto(_adv, "InitializeAcl", W.BOOL, ctypes.c_void_p, W.DWORD, W.DWORD)
AddAccessAllowedAce = _proto(_adv, "AddAccessAllowedAce", W.BOOL, ctypes.c_void_p, W.DWORD, W.DWORD, PSID)
GetAclInformation = _proto(_adv, "GetAclInformation", W.BOOL, PACL, ctypes.c_void_p, W.DWORD, ctypes.c_int)
GetAce = _proto(_adv, "GetAce", W.BOOL, PACL, W.DWORD, P(ctypes.c_void_p))
GetNamedSecurityInfoW = _proto(_adv, "GetNamedSecurityInfoW", W.DWORD, W.LPCWSTR, ctypes.c_int, W.DWORD, P(PSID), P(PSID), P(PACL), P(PACL), P(ctypes.c_void_p))
SetNamedSecurityInfoW = _proto(_adv, "SetNamedSecurityInfoW", W.DWORD, W.LPWSTR, ctypes.c_int, W.DWORD, PSID, PSID, PACL, PACL)
FN_PROGRESS = ctypes.WINFUNCTYPE(None, W.LPWSTR, W.DWORD, P(ctypes.c_int), ctypes.c_void_p, P(W.BOOL))
TreeSetNamedSecurityInfoW = _proto(_adv, "TreeSetNamedSecurityInfoW", W.DWORD, W.LPWSTR, ctypes.c_int, W.DWORD, PSID, PSID, PACL, PACL, W.DWORD, FN_PROGRESS, ctypes.c_int, ctypes.c_void_p)
SetEntriesInAclW = _proto(_adv, "SetEntriesInAclW", W.DWORD, W.ULONG, P(EXPLICIT_ACCESS_W), PACL, P(PACL))
ConvertStringSecurityDescriptorToSecurityDescriptorW = _proto(_adv, "ConvertStringSecurityDescriptorToSecurityDescriptorW", W.BOOL, W.LPCWSTR, W.DWORD, P(ctypes.c_void_p), P(W.ULONG))
CreateProcessAsUserW = _proto(_adv, "CreateProcessAsUserW", W.BOOL, W.HANDLE, W.LPCWSTR, W.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, W.BOOL, W.DWORD, ctypes.c_void_p, W.LPCWSTR, P(STARTUPINFOEXW), P(PROCESS_INFORMATION))
CreateWindowStationW = _proto(_u32, "CreateWindowStationW", W.HANDLE, W.LPCWSTR, W.DWORD, W.DWORD, P(SECURITY_ATTRIBUTES))
CloseWindowStation = _proto(_u32, "CloseWindowStation", W.BOOL, W.HANDLE)
GetProcessWindowStation = _proto(_u32, "GetProcessWindowStation", W.HANDLE)
SetProcessWindowStation = _proto(_u32, "SetProcessWindowStation", W.BOOL, W.HANDLE)
CreateDesktopW = _proto(_u32, "CreateDesktopW", W.HANDLE, W.LPCWSTR, W.LPCWSTR, ctypes.c_void_p, W.DWORD, W.DWORD, P(SECURITY_ATTRIBUTES))
CloseDesktop = _proto(_u32, "CloseDesktop", W.BOOL, W.HANDLE)
CreateProcessW = _proto(_k32, "CreateProcessW", W.BOOL, W.LPCWSTR, W.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, W.BOOL, W.DWORD, ctypes.c_void_p, W.LPCWSTR, P(STARTUPINFOEXW), P(PROCESS_INFORMATION))
_uenv = ctypes.WinDLL("userenv", use_last_error=True)
DeriveAppContainerSidFromAppContainerName = _proto(_uenv, "DeriveAppContainerSidFromAppContainerName", ctypes.c_long, W.LPCWSTR, P(PSID))
FreeSid = _proto(_adv, "FreeSid", ctypes.c_void_p, PSID)
SE_WINDOW_OBJECT = 7
GetSecurityInfo = _proto(_adv, "GetSecurityInfo", W.DWORD, W.HANDLE, ctypes.c_int, W.DWORD, P(PSID), P(PSID), P(PACL), P(PACL), P(ctypes.c_void_p))
SetSecurityInfo = _proto(_adv, "SetSecurityInfo", W.DWORD, W.HANDLE, ctypes.c_int, W.DWORD, PSID, PSID, PACL, PACL)
GetUserObjectInformationW = _proto(_u32, "GetUserObjectInformationW", W.BOOL, W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, P(W.DWORD))


class SandboxLaunchError(RuntimeError):
    """The sandbox could not be set up; the command must not run."""


def _fail(what: str, err: int | None = None) -> SandboxLaunchError:
    err = ctypes.get_last_error() if err is None else err
    return SandboxLaunchError(f"{what} failed ({err}: {ctypes.FormatError(err).strip()})")


# ---------------------------------------------------------------------------- SIDs
class Sid:
    """An owned binary SID (LocalFree'd on close)."""

    def __init__(self, text: str):
        self.text = text
        self._p = PSID()
        if not ConvertStringSidToSidW(text, ctypes.byref(self._p)):
            raise _fail(f"ConvertStringSidToSid({text})")

    @property
    def ptr(self) -> int:
        return self._p.value

    def close(self) -> None:
        if self._p:
            LocalFree(self._p)
            self._p = PSID()


def _sid_string(p: int) -> str:
    out = W.LPWSTR()
    if not ConvertSidToStringSidW(p, ctypes.byref(out)):
        raise _fail("ConvertSidToStringSid")
    try:
        return out.value
    finally:
        LocalFree(ctypes.cast(out, ctypes.c_void_p))


def normalize_rule_path(path: str) -> str:
    """The identity of a rule path: realpath (resolves junctions/symlinks, 8.3 names of
    EXISTING components, `\\\\?\\`), then normcase (case-insensitive, backslashes)."""
    real = os.path.realpath(path)
    if real.startswith("\\\\?\\UNC\\"):
        real = "\\\\" + real[8:]
    elif real.startswith("\\\\?\\"):
        real = real[4:]
    real = real.rstrip("\\/") or real
    if len(real) == 2 and real[1] == ":":
        real += "\\"
    return os.path.normcase(real)


def rule_sid(action: str, path: str, mode: str = "restricted") -> str:
    """Deterministic SID for (action, normalized real path): same folder+action = same SID
    for every run, so a folder's ACEs are written once and reused. AppContainer: a custom
    capability SID (S-1-15-3-1024-<8 words>, the DeriveCapabilitySidsFromName shape);
    restricted token: S-1-15-* is rejected there, so a resource-manager-authority SID."""
    digest = hashlib.sha256(f"{action}\0{normalize_rule_path(path)}".encode("utf-8")).digest()
    if mode == "appcontainer":
        words = [int.from_bytes(digest[i:i + 4], "little") for i in range(0, 32, 4)]
        return CAPABILITY_AUTHORITY + "".join(f"-{w}" for w in words)
    words = [int.from_bytes(digest[i:i + 4], "little") for i in range(0, 16, 4)]
    return RULE_AUTHORITY + "".join(f"-{w}" for w in words)


def launch_sid() -> str:
    words = [int.from_bytes(os.urandom(4), "little") for _ in range(4)]
    return LAUNCH_AUTHORITY + "".join(f"-{w}" for w in words)


# ---------------------------------------------------------------------------- rule ACEs
def _explicit_aces(dacl: int):
    info = ACL_SIZE_INFORMATION()
    if not GetAclInformation(dacl, ctypes.byref(info), ctypes.sizeof(info), 2):
        raise _fail("GetAclInformation")
    for i in range(info.AceCount):
        p = ctypes.c_void_p()
        if not GetAce(dacl, i, ctypes.byref(p)):
            raise _fail("GetAce")
        ace = ACCESS_ACE.from_address(p.value)
        if ace.Header.AceType in (0, 1) and not ace.Header.AceFlags & INHERITED_ACE:
            yield ace.Header.AceType, ace.Header.AceFlags, ace.Mask, p.value + ACCESS_ACE.SidStart.offset


def _has_aces(dacl: int, sid: Sid, wanted, flags: int) -> bool:
    have = list(_explicit_aces(dacl)) if dacl else []
    for typ, mask in wanted:
        if not any(t == typ and f & 0x0F == flags and m == mask and EqualSid(s, sid.ptr) for t, f, m, s in have):
            return False
    return True


def ensure_rule_aces(path: str, action: str, mode: str = "restricted") -> bool:
    """Make sure ``path`` carries the explicit ACEs of rule (action, path). Returns True when
    it wrote them, False when they were already there (one DACL read: ~0.1 ms). Raises
    SandboxLaunchError when the DACL cannot be read or written (not the owner / no WRITE_DAC)."""
    if action not in RULE_ACES:
        raise SandboxLaunchError(f"unknown rule action {action!r}")
    sid = Sid(rule_sid(action, path, mode))
    # The ACE must land on the real folder: Get/SetNamedSecurityInfo do NOT follow a
    # junction or symlink at the end of the path (they act on the reparse point itself).
    path = os.path.realpath(path)
    flags = OI_CI if os.path.isdir(path) else 0
    sd = ctypes.c_void_p()
    dacl = PACL()
    new = PACL()
    try:
        rc = GetNamedSecurityInfoW(path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None, ctypes.byref(dacl), None, ctypes.byref(sd))
        if rc:
            raise _fail(f"reading the permissions of {path}", rc)
        if _has_aces(dacl.value, sid, RULE_ACES[action], flags):
            return False
        entries = (EXPLICIT_ACCESS_W * len(RULE_ACES[action]))()
        for e, (typ, mask) in zip(entries, RULE_ACES[action]):
            e.grfAccessPermissions = mask
            e.grfAccessMode = DENY_ACCESS if typ == ACCESS_DENIED_ACE_TYPE else GRANT_ACCESS
            e.grfInheritance = flags
            e.Trustee.TrusteeForm = 0  # TRUSTEE_IS_SID
            e.Trustee.ptstrName = sid.ptr
        rc = SetEntriesInAclW(len(entries), entries, dacl, ctypes.byref(new))
        if rc:
            raise _fail("SetEntriesInAcl", rc)
        # TreeSetNamedSecurityInfo (TREE_SEC_INFO_SET) = SetNamedSecurityInfo's propagation,
        # but it REPORTS objects it could not update (SetNamedSecurityInfo returns success
        # and silently skips a child that denies WRITE_DAC: measured).
        failed: list = []

        def _progress(name, status, invoke, _args, _set):
            if status:
                failed.append((name, status))
            invoke[0] = 3  # ProgressInvokeOnError: keep going, report every failure

        cb = FN_PROGRESS(_progress)
        rc = TreeSetNamedSecurityInfoW(path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None, new, None, 1, cb, 3, None)
        if rc:
            raise _fail(f"granting the sandbox access to {path} (you must own it or be allowed to change its permissions)", rc)
        if failed:
            # Roll back: with the root ACE left in place the cheap "already applied" check
            # would pass on the next launch and the unpropagated part would go unnoticed.
            TreeSetNamedSecurityInfoW(path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None, dacl, None, 1, cb, 3, None)
            name, status = failed[0]
            raise SandboxLaunchError(
                f"could not apply the {action} rule to {len(failed)} object(s) under {path}, e.g. {name} "
                f"({status}: {ctypes.FormatError(status).strip()})")
        return True
    finally:
        if new:
            LocalFree(new)
        if sd:
            LocalFree(sd)
        sid.close()


LABEL_SECURITY_INFORMATION = 0x10
SYSTEM_MANDATORY_LABEL_ACE_TYPE = 0x11
GetSecurityDescriptorSacl = _proto(_adv, "GetSecurityDescriptorSacl", W.BOOL, ctypes.c_void_p, P(W.BOOL), P(PACL), P(W.BOOL))


def ensure_low_label(path: str) -> bool:
    """Low-integrity mode only: an rw row must carry an inheritable Low mandatory label,
    or a Low-IL process cannot write there (NO_WRITE_UP). Returns True when it wrote it."""
    sd = ctypes.c_void_p()
    sacl = PACL()
    rc = GetNamedSecurityInfoW(path, SE_FILE_OBJECT, LABEL_SECURITY_INFORMATION, None, None, None, ctypes.byref(sacl), ctypes.byref(sd))
    if rc:
        raise _fail(f"reading the integrity label of {path}", rc)
    try:
        if sacl.value:
            info = ACL_SIZE_INFORMATION()
            GetAclInformation(sacl, ctypes.byref(info), ctypes.sizeof(info), 2)
            for i in range(info.AceCount):
                pa = ctypes.c_void_p()
                GetAce(sacl, i, ctypes.byref(pa))
                ace = ACCESS_ACE.from_address(pa.value)
                if ace.Header.AceType == SYSTEM_MANDATORY_LABEL_ACE_TYPE and not ace.Header.AceFlags & INHERITED_ACE                         and _sid_string(pa.value + ACCESS_ACE.SidStart.offset) == "S-1-16-4096":
                    return False
    finally:
        LocalFree(sd)
    flags = "OICI" if os.path.isdir(path) else ""
    psd = ctypes.c_void_p()
    if not ConvertStringSecurityDescriptorToSecurityDescriptorW(f"S:(ML;{flags};NW;;;LW)", 1, ctypes.byref(psd), None):
        raise _fail("ConvertStringSecurityDescriptorToSecurityDescriptor")
    try:
        present, defaulted, new = W.BOOL(), W.BOOL(), PACL()
        if not GetSecurityDescriptorSacl(psd, ctypes.byref(present), ctypes.byref(new), ctypes.byref(defaulted)):
            raise _fail("GetSecurityDescriptorSacl")
        rc = SetNamedSecurityInfoW(path, SE_FILE_OBJECT, LABEL_SECURITY_INFORMATION, None, None, None, new)
        if rc:
            raise _fail(f"labelling {path} low integrity", rc)
        return True
    finally:
        LocalFree(psd)


# ---------------------------------------------------------------------------- token
def _token_info(token: int, cls: int) -> ctypes.Array:
    need = W.DWORD()
    GetTokenInformation(token, cls, None, 0, ctypes.byref(need))
    buf = ctypes.create_string_buffer(need.value)
    if not GetTokenInformation(token, cls, buf, need, ctypes.byref(need)):
        raise _fail("GetTokenInformation")
    return buf


def _token_user_and_logon(token: int):
    user = _sid_string(ctypes.c_void_p.from_buffer(_token_info(token, TokenUser)).value)
    buf = _token_info(token, TokenGroups)
    count = W.DWORD.from_buffer(buf).value
    groups = (SID_AND_ATTRIBUTES * count).from_buffer(buf, ctypes.sizeof(ctypes.c_void_p))
    logon = next((_sid_string(g.Sid) for g in groups if g.Attributes & SE_GROUP_LOGON_ID == SE_GROUP_LOGON_ID), None)
    return user, logon


def build_restricted_token(restricting: list[str], dacl_sids: list[str], integrity: str | None = None, flags: int = DISABLE_MAX_PRIVILEGE) -> int:
    """A restricted primary token from this process's token: every privilege but
    SeChangeNotify removed, restricting SIDs = ``restricting``, default DACL = GENERIC_ALL to
    each of ``dacl_sids`` (objects the sandboxed processes create stay usable to them)."""
    own = W.HANDLE()
    if not OpenProcessToken(GetCurrentProcess(), TOKEN_DUPLICATE | TOKEN_QUERY | TOKEN_ASSIGN_PRIMARY | TOKEN_ADJUST_DEFAULT, ctypes.byref(own)):
        raise _fail("OpenProcessToken")
    sids = [Sid(s) for s in dict.fromkeys(restricting)]
    dsids = [Sid(s) for s in dict.fromkeys(dacl_sids)]
    new = W.HANDLE()
    try:
        arr = (SID_AND_ATTRIBUTES * len(sids))(*[SID_AND_ATTRIBUTES(s.ptr, 0) for s in sids])
        if not CreateRestrictedToken(own, flags, 0, None, 0, None, len(sids), arr, ctypes.byref(new)):
            raise _fail("CreateRestrictedToken")
        size = 8 + sum(8 + GetLengthSid(s.ptr) for s in dsids)
        acl = ctypes.create_string_buffer(size)
        if not InitializeAcl(acl, size, 2):
            raise _fail("InitializeAcl")
        for s in dsids:
            if not AddAccessAllowedAce(acl, 2, GENERIC_ALL, s.ptr):
                raise _fail("AddAccessAllowedAce")
        dd = TOKEN_DEFAULT_DACL(ctypes.addressof(acl))
        if not SetTokenInformation(new, TokenDefaultDacl, ctypes.byref(dd), ctypes.sizeof(dd)):
            raise _fail("SetTokenInformation(TokenDefaultDacl)")
        if integrity == "low":
            low = Sid("S-1-16-4096")
            try:
                tml = SID_AND_ATTRIBUTES(low.ptr, 0x20)  # TOKEN_MANDATORY_LABEL, SE_GROUP_INTEGRITY
                if not SetTokenInformation(new, 25, ctypes.byref(tml), ctypes.sizeof(tml) + GetLengthSid(low.ptr)):
                    raise _fail("SetTokenInformation(TokenIntegrityLevel)")
            finally:
                low.close()
        return new.value
    except BaseException:
        if new:
            CloseHandle(new)
        raise
    finally:
        CloseHandle(own)
        for s in sids + dsids:
            s.close()


# ---------------------------------------------------------------------------- launch
def _quote(arg: str) -> str:
    """One argv element for CommandLineToArgvW / the MSVC CRT (subprocess.list2cmdline rules)."""
    if arg and not any(c in arg for c in " \t\n\v\""):
        return arg
    out, bs = ['"'], 0
    for c in arg:
        if c == "\\":
            bs += 1
        elif c == '"':
            out.append("\\" * (bs * 2 + 1) + '"')
            bs = 0
        else:
            out.append("\\" * bs + c)
            bs = 0
    out.append("\\" * (bs * 2) + '"')
    return "".join(out)


def _sd(sddl: str) -> ctypes.c_void_p:
    psd = ctypes.c_void_p()
    if not ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, ctypes.byref(psd), None):
        raise _fail("ConvertStringSecurityDescriptorToSecurityDescriptor")
    return psd


def _ensure_object_ace(handle: int, sid_text: str, mask: int) -> None:
    """Add an allow ACE for ``sid_text`` to a window station's DACL (and a Low label) when
    missing: the per-session window station may pre-exist (created by an earlier launch or
    by anything else of this logon session asking for an unnamed one)."""
    sd = ctypes.c_void_p()
    dacl = PACL()
    rc = GetSecurityInfo(handle, SE_WINDOW_OBJECT, DACL_SECURITY_INFORMATION, None, None, ctypes.byref(dacl), None, ctypes.byref(sd))
    if rc:
        raise _fail("GetSecurityInfo(window station)", rc)
    sid = Sid(sid_text)
    new = PACL()
    try:
        if dacl.value and any(t == ACCESS_ALLOWED_ACE_TYPE and m & mask == mask and EqualSid(x, sid.ptr) for t, _, m, x in _explicit_aces(dacl.value)):
            return
        e = EXPLICIT_ACCESS_W()
        e.grfAccessPermissions, e.grfAccessMode, e.grfInheritance = mask, GRANT_ACCESS, 0
        e.Trustee.TrusteeForm, e.Trustee.ptstrName = 0, sid.ptr
        rc = SetEntriesInAclW(1, ctypes.byref(e), dacl, ctypes.byref(new))
        if rc:
            raise _fail("SetEntriesInAcl(window station)", rc)
        rc = SetSecurityInfo(handle, SE_WINDOW_OBJECT, DACL_SECURITY_INFORMATION, None, None, new, None)
        if rc:
            raise _fail("SetSecurityInfo(window station)", rc)
        lsd = _sd("S:(ML;;NW;;;LW)")
        try:
            present, defaulted, sacl = W.BOOL(), W.BOOL(), PACL()
            GetSecurityDescriptorSacl(lsd, ctypes.byref(present), ctypes.byref(sacl), ctypes.byref(defaulted))
            SetSecurityInfo(handle, SE_WINDOW_OBJECT, LABEL_SECURITY_INFORMATION, None, None, None, sacl)
        finally:
            LocalFree(lsd)
    finally:
        sid.close()
        if new:
            LocalFree(new)
        LocalFree(sd)


class _Desktop:
    """A desktop only this launch may open, on a non-interactive window station: no access
    to the user's windows, input, clipboard or other launches' UI.

    A non-admin cannot NAME a window station (ERROR_ACCESS_DENIED), and every unnamed one
    of a logon session is the same object ("Service-0x0-<luid>$"): it is shared by all
    launches and grants the constant SANDBOX_SID; the desktop is unique per launch and
    grants only the launch SID (plus the user and SYSTEM)."""

    def __init__(self, user: str, launch: str):
        self.winsta = self.desk = None
        wsd = _sd(f"D:(A;;GA;;;{user})(A;;GA;;;SY)(A;;GA;;;{SANDBOX_SID})S:(ML;;NW;;;LW)")
        dsd = _sd(f"D:(A;;GA;;;{user})(A;;GA;;;SY)(A;;GA;;;{launch})S:(ML;;NW;;;LW)")
        try:
            self.winsta = CreateWindowStationW(None, 0, 0x37F | 0xF0000, ctypes.byref(SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), wsd, False)))
            if not self.winsta:
                raise _fail("CreateWindowStation")
            _ensure_object_ace(self.winsta, SANDBOX_SID, 0x37F)
            buf = ctypes.create_unicode_buffer(256)
            if not GetUserObjectInformationW(self.winsta, 2, buf, ctypes.sizeof(buf), None):  # UOI_NAME
                raise _fail("GetUserObjectInformation")
            desk_name = "afsbx-" + os.urandom(8).hex()
            old = GetProcessWindowStation()
            if not SetProcessWindowStation(self.winsta):
                raise _fail("SetProcessWindowStation")
            try:
                self.desk = CreateDesktopW(desk_name, None, None, 0, 0x1FF | 0xF0000, ctypes.byref(SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), dsd, False)))
                if not self.desk:
                    raise _fail("CreateDesktop")
            finally:
                SetProcessWindowStation(old)
            self.name = buf.value + "\\" + desk_name
        except BaseException:
            self.close()
            raise
        finally:
            LocalFree(wsd)
            LocalFree(dsd)

    def close(self) -> None:
        if self.desk:
            CloseDesktop(self.desk)
        if self.winsta:
            CloseWindowStation(self.winsta)
        self.winsta = self.desk = None


def launch(argv: list[str], *, token: int | None = None, caps: SECURITY_CAPABILITIES | None = None,
           desktop: str | None, ui_limits: bool = True) -> int:
    """Run ``argv`` with ``token`` in a kill-on-close job, std handles inherited (and only
    them); return its exit code. Killing this process kills the whole tree."""
    cmdline = ctypes.create_unicode_buffer(" ".join(_quote(a) for a in argv))
    handles = []
    for n in STD_HANDLES:
        h = GetStdHandle(n)
        if h and h != INVALID_HANDLE and h not in handles and SetHandleInformation(h, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT):
            handles.append(h)
    si = STARTUPINFOEXW()
    si.StartupInfo.cb = ctypes.sizeof(si)
    si.StartupInfo.dwFlags = STARTF_USESTDHANDLES
    si.StartupInfo.hStdInput, si.StartupInfo.hStdOutput, si.StartupInfo.hStdError = (GetStdHandle(n) for n in STD_HANDLES)
    si.StartupInfo.lpDesktop = desktop
    size = ctypes.c_size_t()
    nattr = 2 if caps is not None else 1
    InitializeProcThreadAttributeList(None, nattr, 0, ctypes.byref(size))
    attrs = ctypes.create_string_buffer(size.value)
    if not InitializeProcThreadAttributeList(attrs, nattr, 0, ctypes.byref(size)):
        raise _fail("InitializeProcThreadAttributeList")
    harr = (W.HANDLE * max(1, len(handles)))(*handles)
    job = pi = None
    try:
        if handles and not UpdateProcThreadAttribute(attrs, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST, harr, ctypes.sizeof(W.HANDLE) * len(handles), None, None):
            raise _fail("UpdateProcThreadAttribute")
        if caps is not None and not UpdateProcThreadAttribute(attrs, 0, PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES, ctypes.byref(caps), ctypes.sizeof(caps), None, None):
            raise _fail("UpdateProcThreadAttribute(security capabilities)")
        si.lpAttributeList = ctypes.addressof(attrs)
        job = CreateJobObjectW(None, None)
        if not job:
            raise _fail("CreateJobObject")
        lim = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        lim.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION
        if not SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(lim), ctypes.sizeof(lim)):
            raise _fail("SetInformationJobObject(limits)")
        if ui_limits:
            ui = W.DWORD(JOB_UI_ALL)
            if not SetInformationJobObject(job, JobObjectBasicUIRestrictions, ctypes.byref(ui), 4):
                raise _fail("SetInformationJobObject(UI)")
        flags = CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | EXTENDED_STARTUPINFO_PRESENT
        if not GetConsoleCP():  # no console here: never let a console child open a window
            flags |= CREATE_NO_WINDOW
        pi = PROCESS_INFORMATION()
        ok = (CreateProcessW(None, cmdline, None, None, bool(handles), flags, None, None, ctypes.byref(si), ctypes.byref(pi))
              if token is None else
              CreateProcessAsUserW(token, None, cmdline, None, None, bool(handles), flags, None, None, ctypes.byref(si), ctypes.byref(pi)))
        if not ok:
            err = ctypes.get_last_error()
            pi = None
            raise _fail(f"starting {argv[0]!r}", err)
        if not AssignProcessToJobObject(job, pi.hProcess):
            err = ctypes.get_last_error()
            TerminateProcess(pi.hProcess, EXIT_REFUSED)
            raise _fail("AssignProcessToJobObject", err)
        ResumeThread(pi.hThread)
        WaitForSingleObject(pi.hProcess, INFINITE)
        code = W.DWORD()
        GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
        return ctypes.c_int32(code.value).value  # NTSTATUS codes (0xC0000142) fit sys.exit
    finally:
        DeleteProcThreadAttributeList(attrs)
        if pi:
            CloseHandle(pi.hThread)
            CloseHandle(pi.hProcess)
        if job:
            CloseHandle(job)  # KILL_ON_JOB_CLOSE: grandchildren still running die here


def _appcontainer_sid(name: str) -> str:
    p = PSID()
    hr = DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(p))
    if hr != 0:
        raise SandboxLaunchError(f"DeriveAppContainerSidFromAppContainerName failed (0x{hr & 0xFFFFFFFF:08x})")
    try:
        return _sid_string(p.value)
    finally:
        FreeSid(p)


def run(policy: dict, argv: list[str]) -> int:
    mode = policy.get("mode", "restricted")
    if mode not in ("appcontainer", "restricted"):
        raise SandboxLaunchError(f"unknown mode {mode!r}")
    rules = [(str(p), str(a)) for p, a in policy.get("rules", [])]
    for p, a in rules:
        if a not in RULE_ACES:
            raise SandboxLaunchError(f"unknown rule action {a!r} for {p}")
        if policy.get("ensure", True) and os.path.exists(p):
            ensure_rule_aces(p, a, mode)
            if a == "rw" and policy.get("integrity", "low") == "low":
                ensure_low_label(p)
    own = W.HANDLE()
    if not OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(own)):
        raise _fail("OpenProcessToken")
    try:
        user, logon = _token_user_and_logon(own.value)
    finally:
        CloseHandle(own)
    rule_sids = [rule_sid(a, p, mode) for p, a in rules]
    token = None
    caps = None
    keep: list = []
    if mode == "restricted":
        me = launch_sid()
        base = [logon if s == "logon" else s for s in policy.get("base", RESTRICTED_BASE_SIDS) if s != "logon" or logon]
        token = build_restricted_token(base + rule_sids + [SANDBOX_SID, me], [user, "S-1-5-18", me], policy.get("integrity", "low"), int(policy.get("token_flags", DISABLE_MAX_PRIVILEGE)))
    else:
        # A fresh AppContainer identity per launch (no profile: nothing is registered).
        me = _appcontainer_sid(policy.get("appcontainer_name") or "abstractframework.sandbox." + os.urandom(8).hex())
        cap_texts = list(dict.fromkeys(rule_sids + list(policy.get("capabilities", NETWORK_CAPABILITIES))))
        keep = [Sid(me)] + [Sid(t) for t in cap_texts]
        arr = (SID_AND_ATTRIBUTES * max(1, len(cap_texts)))(*[SID_AND_ATTRIBUTES(x.ptr, SE_GROUP_ENABLED) for x in keep[1:]])
        keep.append(arr)
        caps = SECURITY_CAPABILITIES(keep[0].ptr, arr, len(cap_texts), 0)
    desk = None
    try:
        if policy.get("desktop", "private") == "private":
            desk = _Desktop(user, me)
        return launch(argv, token=token, caps=caps, desktop=desk.name if desk else None,
                      ui_limits=policy.get("ui_limits", True))
    finally:
        if token:
            CloseHandle(token)
        if desk:
            desk.close()
        for x in keep:
            if isinstance(x, Sid):
                x.close()


def main(argv: list[str]) -> int:
    try:
        sep = argv.index("--")
        raw = argv[0] if sep == 1 else None
        if raw is None or not argv[sep + 1:]:
            raise SandboxLaunchError("usage: win_sandbox_proto.py <policy-json> -- <argv...>")
        if raw.startswith("@"):  # @file: a policy too long for the command line
            with open(raw[1:], encoding="utf-8") as fh:
                raw = fh.read()
        policy = json.loads(raw)
        return run(policy, argv[sep + 1:])
    except Exception as exc:  # fail closed: the command did not run
        try:
            sys.stderr.write(f"sandbox: {exc}; the command did not run\n")
            sys.stderr.flush()
        except Exception:
            pass
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
