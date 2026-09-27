#!/bin/sh
# =============================================================================
# AbstractFramework bootstrap installer (macOS / Linux)
# =============================================================================
# One line, no admin rights, no system Python needed:
#
#   curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
#   curl -LsSf .../install.sh | sh -s -- --with-apps --with-ollama
#
# What it does (every step prints its command; `--print` shows them all and
# changes nothing):
#   1. preflight: OS/arch, macOS >= 14 (apple profile), NVIDIA/ROCm (gpu
#      profile), free disk, a free port, systemd user bus (Linux)
#   2. uv (https://docs.astral.sh/uv) if missing, then Python 3.12 through uv
#   3. `uv tool install --python 3.12 "abstractgateway[<profile>,tray]==<pin>"`
#      (isolated, user-scoped; commands land in ~/.local/bin; prebuilt wheels
#      only, so no C compiler / Xcode tools are needed)
#   4. the terminal console (abstractgateway-console, built with cargo; Rust
#      comes from rustup, user-scoped, when missing), then the optional parts:
#      Node.js for the browser apps, AbstractCode's terminal client, Ollama, LM Studio
#   5. registers the gateway as a user service when the installed gateway
#      supports `abstractgateway service install`, otherwise starts it in the
#      background; waits for /api/health
#   6. opens the web console (one-time claim URL when supported) and prints how to
#      reach both consoles: the web one (`/console`) and the terminal one
#
# Options (environment twins in brackets):
#   --profile auto|light|apple|gpu  install profile (default auto)          [AF_PROFILE]
#   --port N                 gateway port (default 8080, next free if busy)  [AF_PORT]
#   --pin VERSION|latest     abstractgateway version (default: install manifest) [AF_PIN]
#   --from PATH|REQUIREMENT  install the gateway from a checkout, wheel or
#                            requirement instead of the pinned release      [AF_FROM]
#   --manifest PATH          read the pin from this install-manifest.json
#   --data-dir DIR           gateway data dir (default: per-OS user data dir) [AF_DATA_DIR]
#   --with-apps              make sure Node.js >= 18 exists for the npx apps
#                            (uv tool install nodejs-wheel; no admin)
#   --no-console             skip the terminal console (by default it is built with
#                            cargo: about 600 MB of Rust from rustup when cargo is
#                            missing, and a C compiler)
#   --with-code-cli          cargo install the AbstractCode terminal client
#   --with-core-cli          also expose the `abstractcore` command
#   --with-ollama            run Ollama's official installer (may ask for sudo)
#   --with-lmstudio          run LM Studio's headless installer (llmster)
#   --full                   also build the compiled extras (stable-diffusion.cpp,
#                            echo cancellation) and llama.cpp from source; needs a C compiler
#   --no-tray                skip the tray extra
#   --no-service             do not register a login service; start in background
#   --no-start               install only; do not start the gateway
#   --no-open                do not open the browser
#   --no-modify-path         do not run `uv tool update-shell`
#   --print, --dry-run       show the plan and commands; change nothing
#   --print-versions         print the pinned versions and exit
#   --interactive            ask before the choices that matter (start at login;
#                            on --uninstall: delete the data too). Questions go
#                            to the terminal, so this works through curl | sh.
#                            The double-click installers pass it.     [AF_INTERACTIVE=1]
#   --uninstall [--purge] [--remove-uv]
#                            stop the whole gateway process tree, remove the service
#                            and the uv tools (--purge also deletes your data: the
#                            gateway data dir, its logs and cache, the Assistant's
#                            sessions, AbstractCode's settings; model weights stay;
#                            --remove-uv also removes uv, its Pythons and its
#                            download cache when this installer put uv there)
#   -y, --yes                ask nothing (the default unless --interactive)
#   -v, --verbose            show the full output of every command
#   -h, --help               this help
# =============================================================================

if [ -n "${ZSH_VERSION:-}" ]; then emulate sh; fi
set -eu

# ---------------------------------------------------------------------------
# Apple Silicon under Rosetta: a Terminal set to "Open using Rosetta" reports
# x86_64, so uv would fetch an Intel Python and the Mac would get the light
# profile with no MLX. Re-run natively when this script is a file; when it is
# piped (curl | sh) there is nothing to re-run, so say how to fix Terminal.
# ---------------------------------------------------------------------------
if [ "$(uname -s)" = Darwin ] && [ "$(sysctl -n sysctl.proc_translated 2>/dev/null || echo 0)" = 1 ]; then
    if [ -z "${AF_REEXEC_NATIVE:-}" ] && [ -f "$0" ] && head -n 3 "$0" 2>/dev/null | grep -q "AbstractFramework bootstrap" \
        && arch -arm64 /usr/bin/true 2>/dev/null; then
        echo "This Terminal runs in Intel (Rosetta) mode on an Apple Silicon Mac: restarting the installer natively."
        echo "  \$ arch -arm64 /bin/sh $0 $*"
        AF_REEXEC_NATIVE=1 exec arch -arm64 /bin/sh "$0" "$@"
    fi
    printf '\nERROR: this Terminal runs in Intel (Rosetta) mode on an Apple Silicon Mac, so the installer\n' >&2
    printf 'would set up the slow Intel version without the Apple Silicon engines.\n' >&2
    printf 'What to do: quit Terminal; in Finder open Applications > Utilities, select Terminal, choose\n' >&2
    printf 'File > Get Info, untick "Open using Rosetta", open Terminal again and run the installer again.\n' >&2
    printf '(Or paste: curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | arch -arm64 sh)\n' >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Release pins. The gateway pin mirrors `bootstrap.gateway_version` in
# docs/installers/install-manifest.json (scripts/tests/test_inventory.sh fails
# on drift); a manifest next to this script wins at runtime.
# ---------------------------------------------------------------------------
AF_GATEWAY_PIN_DEFAULT="0.6.0"
AF_PYTHON="3.12"
AF_NPM_APPS="@abstractframework/flow@0.3.22 @abstractframework/code@0.5.0 @abstractframework/observer@0.1.14 @abstractframework/continuum@0.3.2 @abstractframework/entity@0.2.2"
AF_CRATE_CONSOLE="abstractgateway-console@0.10.0"
# Browser apps whose CLI takes the gateway address as a launch flag (--gateway-url);
# the others start on http://127.0.0.1:8080 and take another address on their sign-in screen.
AF_NPM_GATEWAY_FLAG_APPS="@abstractframework/flow @abstractframework/continuum"
AF_CRATE_CODE_CLI="abstractcode@0.6.0"
AF_DOCS="https://github.com/lpalbou/AbstractFramework/blob/main/docs/install.md"
AF_SCRIPT_URL="https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh"

# ---------------------------------------------------------------------------
# Prebuilt wheels only: by default no C compiler (Xcode CLT, gcc) is needed.
# A few packages in the gateway tree publish no usable wheel on PyPI, so a plain
# install compiles them (and on a fresh Mac pops the Xcode tools dialog).
# `uv tool install` gets an overrides file (an override whose marker is never
# true drops the package) and --no-build-package for the same packages, so a gap
# fails fast with a resolver error instead of starting a compiler:
#   webrtcvad    always dropped; `webrtcvad-wheels` (same module) via --with
#   vllm         Linux only (no Windows build exists)
#   the compiled extras, dropped unless --full: stable-diffusion-cpp-python
#   (stable-diffusion.cpp) and aec-audio-processing (echo cancellation). Both
#   are optional and imported lazily. --full keeps them and builds them from
#   source, so it requires a compiler.
#   llama-cpp-python (llama.cpp GGUF, every profile): PyPI has only the sdist, so
#   it comes from upstream's prebuilt wheels: --find-links on the package page of
#   abetlen's wheel index (one flat page, not a second index for every package),
#   pinned through --constraints uv-constraints.txt, with --no-build-package so
#   the sdist is never built. Metal 0.3.28 on Apple Silicon (the 0.3.32-0.3.35
#   Metal wheels fail zip CRC checks and uv refuses them), CPU 0.3.35 on glibc
#   Linux x86_64/aarch64. No wheel for Intel Macs (newest is 0.3.2, below
#   abstractcore's floor) or musl Linux: there, and whenever the wheel install
#   fails, llama-cpp-python is dropped like the other extras and the summary
#   says so. --full builds it from source instead.
# Pure-Python sdists (langdetect, antlr4-python3-runtime, encodec,
# transformers-stream-generator) still build: they need no compiler, which is
# why there is no global --no-build. install.ps1 carries the same lists
# (tests/test_install_profiles.py keeps them in sync).
# ---------------------------------------------------------------------------
AF_WITH_WHEELS="webrtcvad-wheels>=2.0.14"
AF_COMPILED_EXTRAS="stable-diffusion-cpp-python aec-audio-processing"
AF_SKIPPED_LINE="Skipped compiled extras (stable-diffusion.cpp, echo cancellation): re-run with --full after installing a C compiler."
AF_LLAMA_INDEX="https://abetlen.github.io/llama-cpp-python/whl"
AF_LLAMA_METAL_PIN="0.3.28"
AF_LLAMA_CPU_PIN="0.3.35"
AF_GGUF_SKIPPED="GGUF (llama.cpp) skipped: no prebuilt wheel for this machine; re-run with --full after installing a C compiler"
af_uv_overrides() {  # $1 = 1 when llama-cpp-python comes from the prebuilt wheel
    echo "webrtcvad; sys_platform == 'never'"
    echo "vllm>=0.6.0,<1.0.0; sys_platform == 'linux'"
    if [ "$FULL" = 0 ]; then
        for _p in $AF_COMPILED_EXTRAS; do echo "$_p; sys_platform == 'never'"; done
        [ "$1" = 1 ] || echo "llama-cpp-python; sys_platform == 'never'"
    fi
}
af_no_build_packages() {
    echo "webrtcvad vllm"
    [ "$FULL" = 1 ] || echo "$AF_COMPILED_EXTRAS llama-cpp-python"
}

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
PROFILE="${AF_PROFILE:-auto}"
PORT="${AF_PORT:-}"
PIN="${AF_PIN:-}"
FROM="${AF_FROM:-}"
MANIFEST=""
DATA_DIR="${AF_DATA_DIR:-${ABSTRACTGATEWAY_DATA_DIR:-}}"
WITH_APPS=0; WITH_CONSOLE=1; WITH_CODE_CLI=0; WITH_CORE_CLI=0
WITH_OLLAMA=0; WITH_LMSTUDIO=0
FULL=0; NO_TRAY=0; NO_SERVICE=0; NO_START=0; NO_OPEN=0; NO_MODIFY_PATH=0
PRINT=0; UNINSTALL=0; PURGE=0; VERBOSE=0; REMOVE_UV=0
INTERACTIVE="${AF_INTERACTIVE:-0}"

usage() {
    if [ -f "$0" ] && head -n 3 "$0" 2>/dev/null | grep -q "AbstractFramework bootstrap"; then
        sed -n '2,67p' "$0" | sed 's/^# \{0,1\}//'
    else
        echo "Usage: install.sh [--profile auto|light|apple|gpu] [--port N] [--pin X] [--with-apps]"
        echo "                  [--with-ollama] [--with-lmstudio] [--no-service] [--no-open] [--print] [--uninstall]"
        echo "Full help: $AF_DOCS"
    fi
}

need_arg() { [ $# -ge 2 ] && [ -n "$2" ] || { echo "ERROR: $1 needs a value" >&2; exit 2; }; }

while [ $# -gt 0 ]; do
    case "$1" in
        --profile) need_arg "$@"; PROFILE="$2"; shift ;;
        --profile=*) PROFILE="${1#*=}" ;;
        --light|--apple|--gpu) PROFILE="${1#--}" ;;
        --port) need_arg "$@"; PORT="$2"; shift ;;
        --port=*) PORT="${1#*=}" ;;
        --pin) need_arg "$@"; PIN="$2"; shift ;;
        --pin=*) PIN="${1#*=}" ;;
        --from) need_arg "$@"; FROM="$2"; shift ;;
        --from=*) FROM="${1#*=}" ;;
        --manifest) need_arg "$@"; MANIFEST="$2"; shift ;;
        --manifest=*) MANIFEST="${1#*=}" ;;
        --data-dir) need_arg "$@"; DATA_DIR="$2"; shift ;;
        --data-dir=*) DATA_DIR="${1#*=}" ;;
        --with-apps) WITH_APPS=1 ;;
        --with-console) WITH_CONSOLE=1 ;;   # the default; kept for older command lines
        --no-console) WITH_CONSOLE=0 ;;
        --with-code-cli) WITH_CODE_CLI=1 ;;
        --with-core-cli) WITH_CORE_CLI=1 ;;
        --with-ollama) WITH_OLLAMA=1 ;;
        --with-lmstudio) WITH_LMSTUDIO=1 ;;
        --full) FULL=1 ;;
        --no-tray) NO_TRAY=1 ;;
        --no-service) NO_SERVICE=1 ;;
        --no-start) NO_START=1 ;;
        --no-open) NO_OPEN=1 ;;
        --no-modify-path) NO_MODIFY_PATH=1 ;;
        --print|--dry-run|-n) PRINT=1 ;;
        --print-versions)
            echo "pypi abstractgateway $AF_GATEWAY_PIN_DEFAULT"
            for spec in $AF_NPM_APPS; do echo "npm ${spec%@*} ${spec##*@}"; done
            for spec in $AF_CRATE_CONSOLE $AF_CRATE_CODE_CLI; do echo "crates ${spec%@*} ${spec##*@}"; done
            exit 0 ;;
        --uninstall) UNINSTALL=1 ;;
        --purge) PURGE=1 ;;
        --remove-uv) REMOVE_UV=1 ;;
        --interactive) INTERACTIVE=1 ;;
        -y|--yes) INTERACTIVE=0 ;;
        -v|--verbose) VERBOSE=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != "dumb" ]; then
    C_B="$(printf '\033[1m')"; C_D="$(printf '\033[2m')"; C_R="$(printf '\033[31m')"
    C_G="$(printf '\033[32m')"; C_Y="$(printf '\033[33m')"; C_C="$(printf '\033[36m')"; C_0="$(printf '\033[0m')"
else
    C_B=""; C_D=""; C_R=""; C_G=""; C_Y=""; C_C=""; C_0=""
fi
STEP=0
step() { STEP=$((STEP + 1)); printf '\n%s[%s] %s%s\n' "$C_B" "$STEP" "$1" "$C_0"; }
ok()   { printf '  %s✓%s %s\n' "$C_G" "$C_0" "$1"; }
info() { printf '  %s·%s %s\n' "$C_C" "$C_0" "$1"; }
warn() { printf '  %s!%s %s\n' "$C_Y" "$C_0" "$1"; }
die()  { printf '\n%sERROR:%s %s\n' "$C_R" "$C_0" "$1" >&2; exit 1; }

# ask_yes QUESTION DEFAULT(y|n): 0 for yes. Only with --interactive and a
# terminal to ask on (/dev/tty, so it also works through `curl | sh`); otherwise
# it answers DEFAULT and says so, so every choice is on the record.
ask_yes() {
    _def="$2"; _ans=""
    if [ "$INTERACTIVE" = 1 ] && [ "$PRINT" = 0 ] && { : </dev/tty; } 2>/dev/null; then
        printf '  %s?%s %s %s ' "$C_Y" "$C_0" "$1" "$([ "$_def" = y ] && echo '[Y/n]' || echo '[y/N]')" >/dev/tty
        IFS= read -r _ans </dev/tty || _ans=""
    else
        info "$1 -> $([ "$_def" = y ] && echo yes || echo no) (default$([ "$INTERACTIVE" = 1 ] || echo '; --interactive asks'))"
    fi
    case "${_ans:-$_def}" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

# Shell-quote one word for display.
q() {
    case "$1" in
        ''|*[!A-Za-z0-9_./:=@,+%-]*) printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")" ;;
        *) printf '%s' "$1" ;;
    esac
}
show_cmd() {
    _line=""
    for _w in "$@"; do _line="$_line $(q "$_w")"; done
    printf '%s' "${_line# }"
}

TWINS=""
twin() { TWINS="${TWINS}    $1
"; }

LOG_FILE=""
# run DESCRIPTION CMD... : print the command, run it quietly (log) or verbosely.
run() {
    _desc="$1"; shift
    _shown="${RUN_SHOW:-$(show_cmd "$@")}"; RUN_SHOW=""
    printf '  %s$ %s%s\n' "$C_D" "$_shown" "$C_0"
    twin "$_shown"
    _soft="$RUN_SOFT"; RUN_SOFT=0
    RUN_RC=0
    [ "$PRINT" = 1 ] && return 0
    _rc=0
    if [ "$VERBOSE" = 1 ] || [ -z "$LOG_FILE" ]; then
        "$@" || _rc=$?
    else
        printf '\n$ %s\n' "$_shown" >>"$LOG_FILE"
        "$@" >>"$LOG_FILE" 2>&1 || _rc=$?
    fi
    RUN_RC="$_rc"
    [ "$_rc" = 0 ] && return 0
    if [ "$_soft" = 1 ]; then
        warn "$_desc did not succeed (exit $_rc; details in ${LOG_FILE:-the output above}); continuing"
        return 0
    fi
    if [ -n "$LOG_FILE" ] && [ "$VERBOSE" = 0 ]; then
        printf '%s--- last lines of %s ---%s\n' "$C_D" "$LOG_FILE" "$C_0" >&2
        tail -n 25 "$LOG_FILE" >&2 || true
    fi
    # An uninstall needs no network, and "run the installer again" would reinstall:
    # say how to finish the removal instead.
    if [ "$UNINSTALL" = 1 ]; then
        die "$_desc failed (command: $_shown).
What to do: $UNINSTALL_AGAIN"
    fi
    # Most failures on a clean machine are a dropped connection: say that in
    # plain words instead of leaving the user with a resolver traceback.
    if ! net_ok; then
        die "$_desc failed because the internet connection dropped (command: $_shown).
What to do: reconnect, then run the installer again; it continues where it stopped."
    fi
    die "$_desc failed (command: $_shown).
What to do: run the installer again (it repairs a half-finished install). If it stops at the
same step, report it with the log file: ${LOG_FILE:-the output above} ($AF_DOCS#if-something-goes-wrong)"
}
RUN_SOFT=0
# run_sh DESCRIPTION 'shell pipeline' : for the vendor `curl ... | sh` one-liners.
RUN_SHOW=""
run_sh() { RUN_SHOW="$2"; run "$1" sh -c "$2"; }

have() { command -v "$1" >/dev/null 2>&1; }

http_get() {  # URL -> body on stdout; non-zero when unreachable
    if have curl; then curl -fsS --connect-timeout 2 --max-time 5 "$1" 2>/dev/null
    elif have wget; then wget -qO- --timeout=5 "$1" 2>/dev/null
    else return 1; fi
}
# net_ok: 0 when PyPI answers, through whatever proxy the environment sets.
AF_NET_PROBE="https://pypi.org/simple/pip/"
net_ok() {
    if have curl; then curl -sS -o /dev/null --connect-timeout 5 --max-time 15 "$AF_NET_PROBE" 2>/dev/null
    elif have wget; then wget -q -O /dev/null --timeout=10 "$AF_NET_PROBE" 2>/dev/null
    else return 1; fi
}
offline_msg() {
    _proxy="${HTTPS_PROXY:-${https_proxy:-${ALL_PROXY:-${all_proxy:-}}}}"
    if [ -n "$_proxy" ]; then
        echo "this computer cannot reach pypi.org through the proxy set in your environment ($_proxy).
What to do: check that proxy (or remove the HTTPS_PROXY setting), then run the installer again."
    else
        echo "no internet connection: the installer could not reach pypi.org, where it downloads AbstractFramework.
What to do: connect to the internet (Wi-Fi or cable), then run the installer again. Nothing was changed."
    fi
}
fetch_cmd() {  # the downloader as a shell fragment, for `... | sh`
    if have curl; then echo "curl -LsSf"; elif have wget; then echo "wget -qO-"; else echo ""; fi
}

# ---------------------------------------------------------------------------
# Platform facts
# ---------------------------------------------------------------------------
OS="$(uname -s)"; ARCH="$(uname -m)"
case "$OS" in
    Darwin) OS_ID=macos ;;
    Linux)  OS_ID=linux ;;
    MINGW*|MSYS*|CYGWIN*) die "Windows: use install.ps1 (powershell -ExecutionPolicy ByPass -c \"irm .../install.ps1 | iex\")." ;;
    *) die "unsupported OS: $OS (supported: macOS, Linux; Windows uses install.ps1)" ;;
esac
MACOS_VERSION=""; MACOS_MAJOR=0
if [ "$OS_ID" = macos ]; then
    MACOS_VERSION="$(sw_vers -productVersion 2>/dev/null || echo 0)"
    MACOS_MAJOR="${MACOS_VERSION%%.*}"
fi

DATA_DIR_CUSTOM=0; [ -n "$DATA_DIR" ] && DATA_DIR_CUSTOM=1
if [ -z "$DATA_DIR" ]; then
    if [ "$OS_ID" = macos ]; then DATA_DIR="$HOME/Library/Application Support/AbstractGateway"
    else DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/abstractgateway"; fi
fi
# abs_path PATH: absolute, its parent folder resolved (pwd -P: /tmp -> /private/tmp, a
# linked HOME); the last component is kept as given, so a data dir that is itself a link
# stays a link. A relative --data-dir would otherwise be used (and deleted) from
# whatever folder the command runs in.
abs_path() {
    _ap="$1"
    case "$_ap" in /*) ;; *) _ap="$PWD/$_ap" ;; esac
    while [ "$_ap" != / ] && [ "${_ap%/}" != "$_ap" ]; do _ap="${_ap%/}"; done
    [ "$_ap" = / ] && { echo /; return 0; }
    _dn="$(dirname "$_ap")"; _bn="$(basename "$_ap")"
    if _dr="$(CDPATH='' cd -- "$_dn" 2>/dev/null && pwd -P)"; then
        case "$_bn" in
            .) _ap="$_dr" ;;
            ..) _ap="$(dirname "$_dr")" ;;
            *) _ap="${_dr%/}/$_bn" ;;
        esac
    fi
    printf '%s\n' "$_ap"
}
DATA_DIR_GIVEN="$DATA_DIR"
case "$DATA_DIR" in /*) DATA_DIR_ABS_GIVEN="${DATA_DIR%/}" ;; *) DATA_DIR_ABS_GIVEN="$PWD/${DATA_DIR%/}" ;; esac
DATA_DIR="$(abs_path "$DATA_DIR")"
# Never the root, the home folder or a folder that contains it (an uninstall --purge
# deletes the data dir). Exit 2: a usage error, nothing was changed.
_home_p="$(CDPATH='' cd -- "$HOME" 2>/dev/null && pwd -P || echo "$HOME")"
_home_l="${HOME%/}"
case "$DATA_DIR" in
    ""|/|"$_home_l"|"$_home_p") _refuse="it is the root folder or your home folder" ;;
    *) case "$_home_p/" in "$DATA_DIR"/*) _refuse="it contains your home folder" ;; *)
       case "$_home_l/" in "$DATA_DIR"/*) _refuse="it contains your home folder" ;; *) _refuse="" ;; esac ;; esac ;;
esac
if [ -n "$_refuse" ]; then
    printf '\nERROR: refusing the data dir %s (resolved: %s): %s.\nWhat to do: pass --data-dir with the gateway'"'"'s own folder (default: the per-OS user data dir). Nothing was changed.\n' \
        "'$DATA_DIR_GIVEN'" "'${DATA_DIR:-nothing}'" "$_refuse" >&2
    exit 2
fi
STATE_FILE="$DATA_DIR/bootstrap.env"
PID_FILE="$DATA_DIR/gateway.pid"
LOG_DIR="$DATA_DIR/logs"
GATEWAY_LOG="$LOG_DIR/gateway.log"

# Previous run state (port, service mode, whether we installed Node).
ST_PORT=""; ST_MODE=""; ST_NODE_WHEEL=""; ST_PROFILE=""; ST_UV_BY_US=""; ST_RUST_BY_US=""
if [ -f "$STATE_FILE" ]; then
    ST_RUST_BY_US="$(sed -n 's/^RUST_BY_INSTALLER=//p' "$STATE_FILE" | tail -n 1)"
    ST_UV_BY_US="$(sed -n 's/^UV_BY_INSTALLER=//p' "$STATE_FILE" | tail -n 1)"
    ST_PORT="$(sed -n 's/^PORT=//p' "$STATE_FILE" | tail -n 1)"
    ST_MODE="$(sed -n 's/^MODE=//p' "$STATE_FILE" | tail -n 1)"
    ST_NODE_WHEEL="$(sed -n 's/^NODE_WHEEL=//p' "$STATE_FILE" | tail -n 1)"
    ST_PROFILE="$(sed -n 's/^PROFILE=//p' "$STATE_FILE" | tail -n 1)"
fi

# ---------------------------------------------------------------------------
# uv discovery
# ---------------------------------------------------------------------------
UV=""
find_uv() {
    if have uv; then UV="$(command -v uv)"; return 0; fi
    for _c in "${UV_INSTALL_DIR:-}/uv" "${XDG_BIN_HOME:-}/uv" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$_c" ]; then UV="$_c"; return 0; fi
    done
    return 1
}
# cargo: on PATH, or where rustup puts it (an earlier run of this installer).
CARGO=""
find_cargo() {
    if have cargo; then CARGO="$(command -v cargo)"; return 0; fi
    if [ -x "${CARGO_HOME:-$HOME/.cargo}/bin/cargo" ]; then CARGO="${CARGO_HOME:-$HOME/.cargo}/bin/cargo"; return 0; fi
    return 1
}
# console_bin: where the terminal console goes. cargo builds it with --root <parent of the
# uv tool bin dir>, so it lands next to `abstractgateway`; a bin dir not named .../bin falls
# back to cargo's own ~/.cargo/bin.
CONSOLE_NAME="${AF_CRATE_CONSOLE%@*}"; CONSOLE_PIN="${AF_CRATE_CONSOLE##*@}"
CRATE_ROOT=""; CONSOLE_BIN=""
console_bin() {
    case "$TOOL_BIN" in
        */bin) CRATE_ROOT="${TOOL_BIN%/bin}"; CONSOLE_BIN="$TOOL_BIN/$CONSOLE_NAME" ;;
        *) CRATE_ROOT=""; CONSOLE_BIN="${CARGO_HOME:-$HOME/.cargo}/bin/$CONSOLE_NAME" ;;
    esac
}
console_installed() { [ "$("$CONSOLE_BIN" --version 2>/dev/null)" = "$CONSOLE_NAME $CONSOLE_PIN" ]; }
TOOL_BIN=""
tool_bin() {
    if [ -n "$UV" ] && [ -x "$UV" ]; then TOOL_BIN="$("$UV" tool dir --bin 2>/dev/null || true)"; fi
    [ -n "$TOOL_BIN" ] || TOOL_BIN="${UV_TOOL_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
}

gateway_supports() {  # gateway_supports service|claim-url
    case "$1" in
        service) [ -x "$TOOL_BIN/abstractgateway" ] && "$TOOL_BIN/abstractgateway" service --help >/dev/null 2>&1 ;;
        claim-url) [ -x "$TOOL_BIN/abstractgateway-config" ] && "$TOOL_BIN/abstractgateway-config" claim-url --help >/dev/null 2>&1 ;;
        network) [ -x "$TOOL_BIN/abstractgateway" ] && "$TOOL_BIN/abstractgateway" network --help >/dev/null 2>&1 ;;
    esac
}

# seed_network_setting: before a background `serve` without --host/--port, make the
# gateway's Network setting hold this install's port. Nothing stored yet -> `localhost`
# (127.0.0.1, the bind the installer always used). A stored mode (e.g. `lan` chosen in
# the tray) is KEPT; only its port is aligned to $PORT when it differs. Returns 1 when the
# setting cannot be read: the caller then starts the old pinned command line, and says so.
seed_network_setting() {
    _net="$("$GW" network status --json 2>/dev/null | awk '
        /^  "configured": \{/ { inb = 1; next }
        inb && /^  \}/ { inb = 0 }
        inb && /"mode":/ { v = $2; gsub(/[",]/, "", v); m = v }
        inb && /"port":/ { v = $2; gsub(/[",]/, "", v); p = v }
        inb && /"source":/ { v = $2; gsub(/[",]/, "", v); s = v }
        inb && /"port_source":/ { v = $2; gsub(/[",]/, "", v); ps = v }
        END { if (m != "") print m, p, s, ps }')" || _net=""
    if [ -z "$_net" ]; then
        warn "could not read the gateway's Network setting ('abstractgateway network status' failed); starting it pinned to 127.0.0.1:$PORT, so a Network choice will not apply until the next run"
        return 1
    fi
    # shellcheck disable=SC2086
    set -- $_net
    if [ "$3" != stored ]; then
        run "store the Network setting: this machine only (localhost), port $PORT" "$GW" network set localhost --port "$PORT"
    elif [ "$4" != stored ] || [ "$2" != "$PORT" ]; then
        # `internet` was acknowledged when it was chosen; only the port changes here.
        if [ "$1" = internet ]; then
            run "keep the Network setting '$1', port $PORT" "$GW" network set "$1" --port "$PORT" --acknowledge-internet
        else
            run "keep the Network setting '$1', port $PORT" "$GW" network set "$1" --port "$PORT"
        fi
    else
        ok "Network setting kept: '$1' on port $PORT"
    fi
    return 0
}

pid_alive() { [ -f "$PID_FILE" ] && _p="$(cat "$PID_FILE" 2>/dev/null)" && [ -n "$_p" ] && kill -0 "$_p" 2>/dev/null; }

stop_background_gateway() {
    if pid_alive; then
        _p="$(cat "$PID_FILE")"
        run "stop the background gateway" kill "$_p"
        if [ "$PRINT" = 0 ]; then
            _i=0; while kill -0 "$_p" 2>/dev/null && [ "$_i" -lt 20 ]; do sleep 0.5; _i=$((_i + 1)); done
            kill -0 "$_p" 2>/dev/null && kill -9 "$_p" 2>/dev/null || true
            rm -f "$PID_FILE"
        fi
    fi
}

# ---------------------------------------------------------------------------
# Uninstall helpers
# ---------------------------------------------------------------------------
# The gateway process tree. `launchctl bootout` signals the login item and returns;
# the serve process then shuts down for a while, and several of its children run in
# their own session (start_new_session), so launchd never stops them: an entity's
# own-time loop (-m abstractruntime.identity.life, writes into <data>/entities),
# model download jobs (-m abstractcore.config.host_jobs), managed processes and apps
# (node -r <data>/apps/_support/parent_watch.cjs), the tray (-m abstractgateway.tray).
# Each keeps writing into the data dir, which is what made `rm -rf` fail with
# "Directory not empty". Matched here: every process of this user whose command line
# runs from this install's uv tool environment (all of the Python children use its
# python), the `abstractgateway` command, or the data dir's app watcher; the pids the
# gateway and the installer recorded; and all their descendants. A gateway run from
# somewhere else (a source checkout) is not matched: step [3] lists what still holds
# files instead of stopping it.
AF_STOP_TIMEOUT="${AF_STOP_TIMEOUT:-20}"   # seconds to wait for a clean exit (tests lower it)
AF_RM_TRIES="${AF_RM_TRIES:-5}"            # rm -rf attempts, 1 s apart
TOOL_VENV=""; TOOL_VENV2=""
tool_venv() {
    _td=""
    if [ -n "$UV" ] && [ -x "$UV" ]; then _td="$("$UV" tool dir 2>/dev/null || true)"; fi
    [ -n "$_td" ] || _td="${UV_TOOL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/uv/tools}"
    TOOL_VENV="$_td/abstractgateway"
    # The command in the bin dir is a link into the tool environment: follow it too.
    if [ -L "$TOOL_BIN/abstractgateway" ]; then
        _t="$(readlink "$TOOL_BIN/abstractgateway" 2>/dev/null || true)"
        case "$_t" in /*/bin/abstractgateway) TOOL_VENV2="${_t%/bin/abstractgateway}" ;; esac
    fi
}
# Pids the gateway (run/gateway-serve.json, run/apps/*.json) and a background start
# by this installer (gateway.pid) recorded.
gw_record_pids() {
    for _f in "$DATA_DIR/run/gateway-serve.json" "$DATA_DIR"/run/apps/*.json; do
        [ -f "$_f" ] && sed -n 's/.*"pid": *\([0-9][0-9]*\).*/\1/p' "$_f" 2>/dev/null | head -n 1
    done
    [ -f "$PID_FILE" ] && sed -n '1s/[^0-9]//gp' "$PID_FILE" 2>/dev/null
    return 0
}
# gw_scan: one "PID<TAB>COMMAND" line per live process of the gateway tree.
gw_scan() {
    have ps || return 0
    ps -A -o pid= -o ppid= -o uid= -o args= 2>/dev/null | \
    AF_P1="${TOOL_VENV:+$TOOL_VENV/}" AF_P2="${TOOL_VENV2:+$TOOL_VENV2/}" AF_P3="$TOOL_BIN/abstractgateway " \
    AF_P4="-r $DATA_DIR/apps/_support/parent_watch.cjs " AF_P5="-r $DATA_DIR_ABS_GIVEN/apps/_support/parent_watch.cjs " \
    AF_UID="$(id -u)" AF_SELF="$$" awk '
        {
            pid = $1; ppid = $2; uid = $3; a = $0
            sub(/^[ \t]*[0-9]+[ \t]+[0-9]+[ \t]+[0-9]+[ \t]*/, "", a)
            if (uid != ENVIRON["AF_UID"] || pid == ENVIRON["AF_SELF"]) next
            args[pid] = a; parent[pid] = ppid; n++; order[n] = pid
            hit = 0
            if (ENVIRON["AF_P1"] != "" && index(a, ENVIRON["AF_P1"])) hit = 1
            if (ENVIRON["AF_P2"] != "" && index(a, ENVIRON["AF_P2"])) hit = 1
            if (index(a " ", ENVIRON["AF_P3"])) hit = 1
            # an app the gateway started: `<node> -r <this data dir>/apps/_support/parent_watch.cjs ...`
            split(a, w, " "); exe = w[1]; sub(/.*\//, "", exe)
            if (exe ~ /^node(js)?$/ && (index(a " ", ENVIRON["AF_P4"]) || index(a " ", ENVIRON["AF_P5"]))) hit = 1
            # A recorded pid (run/*.json, gateway.pid) earns nothing by itself: it is
            # stopped only when it matches one of the rules above, since a stale pid file
            # may name an unrelated process that reused the pid (stop_gateway_tree says so).
            if (hit) inset[pid] = 1
        }
        END {
            # never this uninstaller or its own pipeline (ps, awk, subshells)
            mine[ENVIRON["AF_SELF"]] = 1
            do { grew = 0
                for (i = 1; i <= n; i++) { p = order[i]
                    if (!(p in mine) && (parent[p] in mine)) { mine[p] = 1; grew = 1 } }
            } while (grew)
            for (p in mine) delete inset[p]
            do { grew = 0
                for (i = 1; i <= n; i++) { p = order[i]
                    if (!(p in inset) && !(p in mine) && (parent[p] in inset)) { inset[p] = 1; grew = 1 } }
            } while (grew)
            for (i = 1; i <= n; i++) { p = order[i]; if (p in inset) printf "%s\t%s\n", p, substr(args[p], 1, 160) }
        }'
}
# alive_of "PIDS": those still running.
alive_of() { _al=""; for _x in $1; do kill -0 "$_x" 2>/dev/null && _al="$_al $_x"; done; echo "${_al# }"; }
# stop_gateway_tree: wait for the tree to exit (up to AF_STOP_TIMEOUT s), then
# SIGTERM, then SIGKILL; say what was running and how it ended.
stop_gateway_tree() {
    _list="$(gw_scan)"
    if ! have ps; then  # no ps (a minimal container): a recorded pid cannot be checked
        for _x in $(gw_record_pids); do
            kill -0 "$_x" 2>/dev/null && warn "pid $_x is recorded in the data dir, but without 'ps' it cannot be checked to be the gateway; left alone"
        done
    fi
    _pids="$(printf '%s\n' "$_list" | cut -f1 | tr '\n' ' ')"
    # shellcheck disable=SC2086  # word splitting of a pid list
    _pids="$(echo $_pids)"
    if have ps; then
        for _x in $(gw_record_pids | sort -un); do
            case " $_pids " in *" $_x "*) continue ;; esac
            kill -0 "$_x" 2>/dev/null || continue
            info "stale pid file: pid $_x now belongs to another program ($(ps -o args= -p "$_x" 2>/dev/null | cut -c1-80)); left alone"
        done
    fi
    if [ -z "$_pids" ]; then ok "no gateway process is running"; return 0; fi
    info "gateway processes still running:"
    printf '%s\n' "$_list" | sed '/^$/d; s/^/      /'
    if [ "$PRINT" = 1 ]; then
        printf '  %s$ kill -TERM %s   (only if still running after %s s; then kill -KILL)%s\n' "$C_D" "$_pids" "$AF_STOP_TIMEOUT" "$C_0"
        twin "kill -TERM $_pids"
        return 0
    fi
    _n=0; _max=$((AF_STOP_TIMEOUT * 2))
    while :; do
        # Re-scan: children re-parented to launchd/init lose their ppid link.
        _pids="$(alive_of "$_pids $(gw_scan | cut -f1 | tr '\n' ' ')")"
        _pids="$(printf '%s\n' $_pids | sort -un | tr '\n' ' ')"; _pids="$(echo $_pids)"
        [ -z "$_pids" ] && break
        [ "$_n" -ge "$_max" ] && break
        [ "$_n" = 0 ] && info "waiting up to $AF_STOP_TIMEOUT s for them to exit"
        sleep 0.5; _n=$((_n + 1))
    done
    if [ -z "$_pids" ]; then ok "the gateway process tree has exited"; return 0; fi
    printf '  %s$ kill -TERM %s%s\n' "$C_D" "$_pids" "$C_0"; twin "kill -TERM $_pids"
    kill -TERM $_pids 2>/dev/null || true
    _signalled="$_pids"
    _n=0; while [ -n "$(alive_of "$_pids")" ] && [ "$_n" -lt 10 ]; do sleep 0.5; _n=$((_n + 1)); done
    _left="$(alive_of "$(printf '%s\n' $_pids $(gw_scan | cut -f1) | sort -un | tr '\n' ' ')")"
    if [ -n "$_left" ]; then
        _signalled="$(printf '%s\n' $_signalled $_left | sort -un | tr '\n' ' ')"; _signalled="$(echo $_signalled)"
        printf '  %s$ kill -KILL %s%s\n' "$C_D" "$_left" "$C_0"; twin "kill -KILL $_left"
        kill -KILL $_left 2>/dev/null || true
        _n=0; while [ -n "$(alive_of "$_left")" ] && [ "$_n" -lt 6 ]; do sleep 0.5; _n=$((_n + 1)); done
        _left="$(alive_of "$_left")"
        if [ -n "$_left" ]; then
            ps -o pid= -o user= -o args= -p "$(echo $_left | tr ' ' ',')" 2>/dev/null | sed 's/^/      /' >&2 || true
            die "these gateway processes could not be stopped: $_left.
What to do: quit them in Activity Monitor (or log out and back in), then $UNINSTALL_AGAIN"
        fi
    fi
    ok "stopped the gateway processes: $_signalled"
}
# mounts_under PATH: mount points inside PATH (rm -rf would delete into them).
# Both sides are resolved (pwd -P), so /tmp vs /private/tmp or a linked HOME cannot hide
# a mount; automounter maps (autofs) are skipped, never entered.
mounts_under() {
    have mount || return 0
    _root="$(CDPATH='' cd -- "$1" 2>/dev/null && pwd -P || echo "$1")"
    if [ "$OS_ID" = linux ]; then mount 2>/dev/null | grep -v autofs | sed -n 's/^.* on \(.*\) type .*$/\1/p'
    else mount 2>/dev/null | grep -v autofs | sed -n 's/^.* on \(.*\) (.*)$/\1/p'; fi | while IFS= read -r _m; do
        case "$_m" in "$1"/*|"$_root"/*) echo "$_m"; continue ;; esac
        _mp="$(CDPATH='' cd -- "$_m" 2>/dev/null && pwd -P || true)"
        case "$_mp" in "$_root"/*) echo "$_m" ;; esac
    done
}
PURGE_FAILED=""; PURGE_DONE=""
# Files only a gateway data dir holds: the installer's state, the gateway's database,
# serve record, auth store and settings, and the note a failed purge leaves behind so
# the next run can finish it.
AF_DATA_MARKERS="bootstrap.env gateway.sqlite3 run/gateway-serve.json auth/users.json config/runtime_config.json service.json first_run.json gateway.pid .abstractgateway-purge-incomplete"
is_gateway_data_dir() {
    for _m in $AF_DATA_MARKERS; do [ -e "$1/$_m" ] && return 0; done
    return 1
}
mark_incomplete() {  # mark_incomplete PATH: only for the data dir, best effort
    [ "$1" = "$DATA_DIR" ] && [ -d "$1" ] && : >"$1/.abstractgateway-purge-incomplete" 2>/dev/null
    return 0
}
# holders PATH: the programs holding files under PATH (lsof +D), when lsof exists.
holders() {
    have lsof || return 0
    _h="$(lsof -n +D "$1" 2>/dev/null | head -n 20)"
    if [ -n "$_h" ]; then info "programs holding files there (lsof +D):"; printf '%s\n' "$_h" | sed 's/^/      /'
    else info "no program holds a file there (lsof +D)"; fi
}
# recheck_purged: a second after the last deletion, nothing deleted may be back: a
# program this uninstaller did not recognise as the gateway is still writing there.
recheck_purged() {
    [ "$PRINT" = 1 ] && return 0
    [ -n "$PURGE_DONE" ] || return 0
    sleep 1
    _oifs2="$IFS"; IFS='
'; set -f
    for _p in $PURGE_DONE; do
        IFS="$_oifs2"; set +f
        if [ -e "$_p" ]; then
            warn "$_p was deleted and is back: a program is still writing there. What it holds now:"
            find "$_p" 2>/dev/null | head -n 20 | sed 's/^/      /'
            holders "$_p"
            mark_incomplete "$_p"
            PURGE_FAILED="$PURGE_FAILED
  $_p   (re-created after it was deleted: quit the program writing there)"
        fi
        IFS='
'; set -f
    done
    IFS="$_oifs2"; set +f
}
# purge_path DESCRIPTION PATH: delete PATH (retrying while something re-creates it),
# then check it is gone; if not, list what is left and who holds it, and remember it.
purge_path() {
    _d="$1"; _p="$2"
    if [ ! -e "$_p" ] && [ ! -L "$_p" ]; then info "$_d: nothing to do (not there: $_p)"; return 0; fi
    if [ "$_p" = "$DATA_DIR" ] && [ "$DATA_DIR_CUSTOM" = 1 ] && [ -d "$_p" ] && [ ! -L "$_p" ] && [ -z "$(ls -A "$_p" 2>/dev/null)" ]; then
        info "$_d: nothing to do (empty folder, left in place: $_p)"; return 0
    fi
    if [ -L "$_p" ]; then
        _t="$(readlink "$_p" 2>/dev/null || echo '?')"
        run "remove the link $_p" rm -f "$_p"
        warn "$_p was a link to $_t: removed the link, kept what it points to (delete that by hand if it is yours)"
        return 0
    fi
    _mn="$(mounts_under "$_p")"
    if [ -n "$_mn" ]; then
        warn "$_d: not deleted: a volume is mounted inside $_p:"
        printf '%s\n' "$_mn" | sed 's/^/      /'
        PURGE_FAILED="$PURGE_FAILED
  $_p   (a volume is mounted inside: eject it first)"
        return 0
    fi
    printf '  %s$ %s%s\n' "$C_D" "$(show_cmd rm -rf "$_p")" "$C_0"; twin "$(show_cmd rm -rf "$_p")"
    [ "$PRINT" = 1 ] && return 0
    _i=1; _err=""
    while :; do
        _err="$(rm -rf "$_p" 2>&1 >/dev/null)" || true
        if [ ! -e "$_p" ] && [ ! -L "$_p" ]; then
            ok "$_d: deleted$([ "$_i" -gt 1 ] && echo " (attempt $_i)")"
            PURGE_DONE="$PURGE_DONE$_p
"
            return 0
        fi
        [ "$_i" -ge "$AF_RM_TRIES" ] && break
        sleep 1; _i=$((_i + 1))
    done
    warn "$_d: could not delete $_p after $_i attempts:"
    printf '%s\n' "$_err" | head -n 8 | sed 's/^/      /'
    info "what is left there$([ "$OS_ID" = macos ] && echo ' (ls -lO shows file flags such as uchg)'):"
    if [ "$OS_ID" = macos ]; then find "$_p" -exec ls -ldO {} + 2>/dev/null | head -n 40 | sed 's/^/      /'
    else find "$_p" -exec ls -ld {} + 2>/dev/null | head -n 40 | sed 's/^/      /'; fi
    holders "$_p"
    mark_incomplete "$_p"
    PURGE_FAILED="$PURGE_FAILED
  $_p"
}
# Everything --purge deletes: "DESCRIPTION|PATH" lines. Model weights and shared
# caches (~/.cache/huggingface, ~/.abstractcore, ~/.abstractframework, the libraries'
# own dirs) are not in it.
purge_targets() {
    echo "the gateway data (settings, users, chats, run history, artifacts, memory)|$DATA_DIR"
    if [ "$OS_ID" = macos ]; then
        echo "the login item's logs|$HOME/Library/Logs/AbstractGateway"
        echo "the gateway's download cache (engine installers)|$HOME/Library/Caches/AbstractGateway"
    else
        echo "the gateway's download cache (engine installers)|${XDG_CACHE_HOME:-$HOME/.cache}/abstractgateway"
    fi
    echo "the Assistant's sessions, snapshots and preferences|$HOME/.abstractassistant"
    if [ "$OS_ID" = macos ]; then
        # The .app's bundle id (abstractassistant/packaging/macos/AbstractAssistant.spec).
        echo "the Assistant's macOS preferences|$HOME/Library/Preferences/ai.abstractcore.abstractassistant.plist"
        for _f in "$HOME/Library/Logs/Assistant"/abstractassistant-*; do
            [ -e "$_f" ] && echo "the Assistant's launcher log|$_f"
        done
    fi
    echo "AbstractCode's login and preferences|$HOME/.abstractcode"
    echo "AbstractCode's older preferences|$HOME/.abstractcode-tui"
}
UNINSTALL_AGAIN="run the uninstaller again (sh uninstall.sh --yes, or double-click Uninstall AbstractFramework.command); it skips what is already gone."

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
if [ "$UNINSTALL" = 1 ]; then
    printf '%sAbstractFramework uninstall%s%s\n' "$C_B" "$C_0" "$([ "$PRINT" = 1 ] && echo ' (--print: nothing is changed)')"
    find_uv || true; tool_bin; tool_venv
    # Asked first, so the user answers once and every step below runs unattended.
    if [ "$PURGE" = 0 ]; then
        _there=0; _kb=0
        _targets="$(purge_targets)"
        _oifs="$IFS"; IFS='
'; set -f
        for _t in $_targets; do
            if [ -e "${_t#*|}" ]; then
                _there=1; _kb=$((_kb + $(du -sk "${_t#*|}" 2>/dev/null | awk '{print $1 + 0}' | tail -n 1)))
            fi
        done
        IFS="$_oifs"; set +f
        if [ "$_there" = 1 ]; then
            _size="$(echo "$_kb" | awk '{ if ($1 >= 1048576) printf "%.1fG", $1/1048576; else if ($1 >= 1024) printf "%.0fM", $1/1024; else printf "%dK", $1 }')"
            if ask_yes "Also delete your AbstractFramework data (${_size:-?}): the gateway's settings, users, chats, run history and artifacts ($DATA_DIR), its logs and download cache, the Assistant's sessions and preferences (~/.abstractassistant) and AbstractCode's login and preferences (~/.abstractcode)? Model weights are kept. This cannot be undone." n; then
                PURGE=1
            fi
        fi
    fi
    if [ "$ST_UV_BY_US" = 1 ] && [ "$REMOVE_UV" = 0 ] && [ -n "$UV" ]; then
        _uvsize="$(du -sch "$("$UV" cache dir 2>/dev/null)" "$("$UV" python dir 2>/dev/null)" 2>/dev/null | tail -n 1 | awk '{print $1}')"
        if ask_yes "Also remove uv, its Python and its download cache (${_uvsize:-?})? The installer added uv; anything else you installed with uv would stop working." n; then
            REMOVE_UV=1
        fi
    fi
    # A --data-dir given by hand must look like a gateway data dir before --purge deletes
    # it (a typo such as ~/Documents must not be wiped). The per-OS default is the
    # gateway's own folder, so it needs no marker (a half-deleted one may have none).
    if [ "$PURGE" = 1 ] && [ "$DATA_DIR_CUSTOM" = 1 ] && [ -d "$DATA_DIR" ] && [ ! -L "$DATA_DIR" ] \
        && [ -n "$(ls -A "$DATA_DIR" 2>/dev/null)" ] && ! is_gateway_data_dir "$DATA_DIR"; then
        printf '\nERROR: refusing to purge %s: it holds none of the files a gateway data dir has\n(%s).\n' "$(q "$DATA_DIR")" "$AF_DATA_MARKERS" >&2
        printf 'What to do: check --data-dir (it must be the gateway'"'"'s own folder). Nothing was changed.\n' >&2
        exit 2
    fi
    [ "$PURGE" = 1 ] && UNINSTALL_AGAIN="run the uninstaller again with --purge (sh uninstall.sh --yes --purge); it skips what is already gone."
    step "Gateway service and processes"
    # Only touch the login service when this install registered it (or when no state says
    # otherwise): a --no-service install must not unregister a service set up separately.
    UNIT_MAC="$HOME/Library/LaunchAgents/ai.abstractframework.gateway.plist"
    UNIT_LINUX="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/abstractgateway.service"
    if [ "$ST_MODE" = background ] || [ "$ST_MODE" = none ]; then
        info "no login service was registered by this install (mode: $ST_MODE)"
    elif gateway_supports service; then
        run "remove the gateway service" "$TOOL_BIN/abstractgateway" service uninstall
    elif [ "$OS_ID" = macos ] && [ -f "$UNIT_MAC" ]; then
        # A half-removed install (the tool is gone, the login item is not): the
        # same two steps `abstractgateway service uninstall` runs.
        RUN_SOFT=1 run "stop the login item" launchctl bootout "gui/$(id -u)/ai.abstractframework.gateway"
        run "remove the login item" rm -f "$UNIT_MAC"
    elif [ "$OS_ID" = linux ] && [ -f "$UNIT_LINUX" ]; then
        RUN_SOFT=1 run "stop the login service" systemctl --user disable --now abstractgateway.service
        run "remove the login service" rm -f "$UNIT_LINUX"
    elif [ "$ST_MODE" = service ]; then
        info "the state file says a service was registered, but none is installed now; nothing to remove"
    else
        info "no login service found"
    fi
    # Removing the login item does not wait for the gateway to exit (launchd), and
    # children in their own session outlive it: wait for the whole tree, then stop it.
    stop_gateway_tree
    [ "$PRINT" = 1 ] || rm -f "$PID_FILE"
    step "uv tools"
    if [ -n "$UV" ]; then
        if "$UV" tool list 2>/dev/null | grep -q '^abstractgateway '; then
            run "uninstall abstractgateway" "$UV" tool uninstall abstractgateway
        else info "abstractgateway is not installed as a uv tool"; fi
        if [ "$ST_NODE_WHEEL" = 1 ] && "$UV" tool list 2>/dev/null | grep -q '^nodejs-wheel '; then
            run "uninstall nodejs-wheel" "$UV" tool uninstall nodejs-wheel
        fi
    else
        info "uv not found; nothing to uninstall there"
    fi
    # The terminal console this installer built (see console_bin).
    console_bin
    if [ -e "$CONSOLE_BIN" ]; then
        step "Terminal console"
        if find_cargo && grep -qs "^\"$CONSOLE_NAME " "${CRATE_ROOT:-${CARGO_HOME:-$HOME/.cargo}}/.crates.toml"; then
            set -- "$CARGO" uninstall
            [ -n "$CRATE_ROOT" ] && set -- "$@" --root "$CRATE_ROOT"
            RUN_SOFT=1 run "uninstall the terminal console" "$@" "$CONSOLE_NAME"
        fi
        [ "$PRINT" = 0 ] && [ ! -e "$CONSOLE_BIN" ] || run "remove the terminal console" rm -f "$CONSOLE_BIN"
    fi
    [ "$ST_RUST_BY_US" = 1 ] && info "kept: Rust, which the installer added for the terminal console (remove it with: ${CARGO_HOME:-$HOME/.cargo}/bin/rustup self uninstall)"
    step "Data"
    _inst="$HOME/Library/Application Support/AbstractFramework/Installer"
    if [ "$OS_ID" = macos ] && [ -e "$_inst" ]; then
        purge_path "the copy of the installer left by the .pkg" "$_inst"
        [ "$PRINT" = 1 ] || rmdir "$HOME/Library/Application Support/AbstractFramework" 2>/dev/null || true
    fi
    if [ "$PURGE" = 1 ]; then
        _had_prefs=0
        [ -e "$HOME/Library/Preferences/ai.abstractcore.abstractassistant.plist" ] && _had_prefs=1
        _targets="$(purge_targets)"
        _oifs="$IFS"; IFS='
'; set -f
        for _t in $_targets; do
            IFS="$_oifs"; set +f
            purge_path "${_t%%|*}" "${_t#*|}"
            IFS='
'; set -f
        done
        IFS="$_oifs"; set +f
        # cfprefsd caches preferences and can write a deleted plist back: drop the domain
        # too (soft: after the file is gone there may be nothing cached).
        if [ "$OS_ID" = macos ] && [ "$_had_prefs" = 1 ]; then
            printf '  %s$ defaults delete ai.abstractcore.abstractassistant%s\n' "$C_D" "$C_0"
            twin "defaults delete ai.abstractcore.abstractassistant"
            if [ "$PRINT" = 0 ]; then
                if defaults delete ai.abstractcore.abstractassistant >/dev/null 2>&1; then ok "the Assistant's cached preferences: dropped"
                else info "the Assistant's cached preferences: nothing cached"; fi
            fi
        fi
        recheck_purged
        if [ "$OS_ID" = macos ] && [ "$PRINT" = 0 ]; then rmdir "$HOME/Library/Logs/Assistant" 2>/dev/null || true; fi
        info "kept: model weights and shared caches (~/.cache/huggingface, ~/.abstractcore, ~/.abstractframework, ~/.cache/abstractvoice, LM Studio and Ollama models)"
        if [ -n "$PURGE_FAILED" ]; then
            die "the uninstaller could not delete:$PURGE_FAILED
The entries still there, and any program holding them, are listed above.
What to do: quit the programs listed (or log out and back in);$([ "$OS_ID" = macos ] && printf '%s' " if 'ls -lO' shows 'uchg',
clear it with: chflags -R nouchg <folder>;") if a file belongs to another user (root), fix it with:
sudo chown -R $(id -un) <folder>. Then $UNINSTALL_AGAIN"
        fi
    else
        info "kept the gateway data dir: $DATA_DIR (delete it with --uninstall --purge)"
        info "kept: the Assistant's sessions (~/.abstractassistant) and AbstractCode's settings (~/.abstractcode); --purge deletes them"
    fi
    if [ "$REMOVE_UV" = 1 ] && [ -n "$UV" ]; then
        step "uv, its Python and its download cache"
        if [ "$ST_UV_BY_US" != 1 ]; then
            warn "uv was not installed by this installer (or the record of it is gone): removing it because --remove-uv was given"
        fi
        _uvdir="$(dirname "$UV")"
        run "delete uv's download cache" "$UV" cache clean
        run "remove the Pythons uv installed" "$UV" python uninstall --all
        run "remove uv" rm -f "$UV" "$_uvdir/uvx" "${XDG_CONFIG_HOME:-$HOME/.config}/uv/uv-receipt.json"
        info "kept: the PATH line uv added to your shell profile (harmless; delete it by hand if you like)"
        info "kept: Ollama, LM Studio, and any other cargo tools"
    else
        info "kept: uv ($([ -n "$UV" ] && echo "$UV" || echo 'not found'); --remove-uv removes it), Ollama, LM Studio, and any other cargo tools"
    fi
    printf '\n%sDone.%s\n' "$C_G" "$C_0"
    exit 0
fi

# ---------------------------------------------------------------------------
# Pin resolution
# ---------------------------------------------------------------------------
manifest_pin() {
    sed -n 's/.*"gateway_version": *"\([^"]*\)".*/\1/p' "$1" 2>/dev/null | head -n 1
}
PIN_SOURCE=""
if [ -n "$PIN" ]; then PIN_SOURCE="--pin"
elif [ -n "$FROM" ]; then PIN_SOURCE="--from"
else
    if [ -z "$MANIFEST" ] && [ -f "$0" ]; then
        _m="$(dirname "$0")/../docs/installers/install-manifest.json"
        [ -f "$_m" ] && MANIFEST="$_m"
    fi
    if [ -n "$MANIFEST" ]; then
        [ -f "$MANIFEST" ] || die "--manifest: no such file: $MANIFEST"
        PIN="$(manifest_pin "$MANIFEST")"
        [ -n "$PIN" ] || die "no bootstrap.gateway_version in $MANIFEST"
        PIN_SOURCE="$MANIFEST"
    else
        PIN="$AF_GATEWAY_PIN_DEFAULT"; PIN_SOURCE="built into install.sh"
    fi
fi

# ---------------------------------------------------------------------------
# 1. Preflight
# ---------------------------------------------------------------------------
printf '%sAbstractFramework bootstrap%s  %s%s%s\n' "$C_B" "$C_0" "$C_D" \
    "$([ "$PRINT" = 1 ] && echo '(--print: preflight only, nothing is installed)' || echo "$AF_SCRIPT_URL")" "$C_0"

step "Preflight"
ok "system: $OS_ID $ARCH$([ -n "$MACOS_VERSION" ] && echo " (macOS $MACOS_VERSION)")"
if [ "$OS_ID" = macos ] && [ "$MACOS_MAJOR" -lt 13 ] 2>/dev/null; then
    warn "macOS $MACOS_VERSION is older than the versions AbstractFramework is tested on (13 and later). If the install fails, update macOS (System Settings > General > Software Update) and run the installer again."
fi

# Every path the install writes must be writable by this user: a folder left
# owned by root (an earlier `sudo pip`/`sudo uv`) otherwise fails deep inside uv.
check_writable() {  # DIR: its nearest existing ancestor must be writable
    _d="$1"
    while [ ! -e "$_d" ] && [ "$_d" != / ]; do _d="$(dirname "$_d")"; done
    [ -w "$_d" ] && return 0
    _owner="$(ls -ld "$_d" 2>/dev/null | awk '{print $3}')"
    die "the folder $_d belongs to '$_owner', so the installer (running as '$(id -un)') cannot write there. This usually happens after a command was run with sudo.
What to do: in Terminal run   sudo chown -R $(id -un) $(q "$_d")   (it asks for your password once), then run the installer again."
}
for _w in "$HOME" "${UV_TOOL_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}" "${UV_TOOL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/uv/tools}" "$DATA_DIR"; do
    check_writable "$_w"
done
[ "$OS_ID" = macos ] && [ "$NO_SERVICE" = 0 ] && check_writable "$HOME/Library/LaunchAgents"
ok "folders: everything installs under $HOME (no admin password needed)"
HAS_CC=1
if [ "$OS_ID" = macos ]; then xcode-select -p >/dev/null 2>&1 || HAS_CC=0
elif ! have cc && ! have gcc; then HAS_CC=0; fi
if [ "$HAS_CC" = 0 ]; then
    if [ "$FULL" = 1 ]; then
        if [ "$OS_ID" = macos ]; then die "--full builds llama.cpp, stable-diffusion.cpp and echo cancellation from source and needs a C compiler: run 'xcode-select --install', then re-run with --full"
        else die "--full builds llama.cpp, stable-diffusion.cpp and echo cancellation from source and needs a C compiler: install one (Debian/Ubuntu: sudo apt-get install -y build-essential), then re-run with --full"; fi
    fi
    info "no C compiler ($([ "$OS_ID" = macos ] && echo 'Xcode CLT' || echo 'cc/gcc')) – fine, all packages install as prebuilt wheels"
elif [ "$FULL" = 1 ]; then
    ok "C compiler found: --full builds the compiled extras from source (several minutes)"
fi
DL="$(fetch_cmd)"
[ -n "$DL" ] || die "this computer has neither curl nor wget, so the installer cannot download anything.
What to do: install curl with your system's package manager (Debian/Ubuntu: sudo apt-get install -y curl), then run the installer again."
if net_ok; then ok "internet: pypi.org reachable"
elif [ "$PRINT" = 1 ]; then warn "$(offline_msg | head -n 1)"
else die "$(offline_msg)"; fi

HAS_NVIDIA=0; HAS_ROCM=0
if have nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then HAS_NVIDIA=1; fi
if have rocminfo && rocminfo >/dev/null 2>&1; then HAS_ROCM=1; fi
APPLE_OK=0
if [ "$OS_ID" = macos ] && [ "$ARCH" = arm64 ] && [ "$MACOS_MAJOR" -ge 14 ] 2>/dev/null; then APPLE_OK=1; fi

case "$PROFILE" in
    auto|"")
        if [ -n "$ST_PROFILE" ]; then PROFILE="$ST_PROFILE"; _why="kept from the previous install"
        elif [ "$APPLE_OK" = 1 ]; then PROFILE=apple; _why="Apple Silicon, macOS $MACOS_VERSION"
        elif [ "$OS_ID" = macos ] && [ "$ARCH" = arm64 ]; then PROFILE=light
            _why="macOS $MACOS_VERSION: the Apple Silicon engines (MLX) need macOS 14 or later; update macOS and run the installer again to add them"
        elif [ "$HAS_NVIDIA" = 1 ]; then PROFILE=gpu; _why="nvidia-smi found a GPU"
        elif [ "$HAS_ROCM" = 1 ]; then PROFILE=gpu; _why="rocminfo found a GPU"
        else PROFILE=light; _why="no local accelerator stack detected"; fi
        ok "profile: $PROFILE ($_why; override with --profile)" ;;
    light) ok "profile: light (remote/endpoint engines only)" ;;
    apple)
        [ "$OS_ID" = macos ] && [ "$ARCH" = arm64 ] || die "the apple profile needs an Apple Silicon Mac (this is $OS_ID $ARCH); use --profile light"
        [ "$MACOS_MAJOR" -ge 14 ] 2>/dev/null || die "the apple profile needs macOS 14 or later (this is $MACOS_VERSION); use --profile light"
        ok "profile: apple (local MLX/Metal engines)" ;;
    gpu)
        [ "$OS_ID" = linux ] || die "the gpu profile targets Linux (Windows: install.ps1); on a Mac use --profile apple"
        if [ "$HAS_NVIDIA" = 0 ] && [ "$HAS_ROCM" = 0 ]; then
            warn "gpu profile requested but neither nvidia-smi nor rocminfo works; local GPU engines will fall back to CPU"
        fi
        ok "profile: gpu (local CUDA/ROCm engines)" ;;
    *) die "unknown profile '$PROFILE' (expected auto, light, apple or gpu)" ;;
esac

EXTRAS=""
case "$PROFILE" in apple) EXTRAS="apple" ;; gpu) EXTRAS="gpu" ;; esac
if [ "$NO_TRAY" = 0 ]; then
    if [ "$OS_ID" = macos ] || [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
        EXTRAS="${EXTRAS:+$EXTRAS,}tray"
    else
        info "no display: the tray extra is skipped"
    fi
fi

# llama.cpp GGUF: the prebuilt wheel for this machine (see the top of this script).
GGUF_PIN=""; GGUF_KIND=""; GGUF_LINKS=""
if [ "$FULL" = 0 ]; then
    case "$OS_ID/$ARCH" in
        macos/arm64) GGUF_PIN="$AF_LLAMA_METAL_PIN"; GGUF_KIND=metal ;;
        linux/x86_64|linux/aarch64|linux/arm64)
            if ldd --version 2>&1 | grep -qi musl; then :; else GGUF_PIN="$AF_LLAMA_CPU_PIN"; GGUF_KIND=cpu; fi ;;
    esac
    [ -n "$GGUF_KIND" ] && GGUF_LINKS="$AF_LLAMA_INDEX/$GGUF_KIND/llama-cpp-python/"
fi

# Gateway requirement.
if [ -n "$FROM" ]; then
    if [ -e "$FROM" ]; then
        _abs="$(cd "$(dirname "$FROM")" && pwd)/$(basename "$FROM")"
        GW_SPEC="abstractgateway${EXTRAS:+[$EXTRAS]} @ file://$_abs"
    else
        GW_SPEC="$FROM"
    fi
elif [ "$PIN" = latest ]; then
    GW_SPEC="abstractgateway${EXTRAS:+[$EXTRAS]}"
else
    GW_SPEC="abstractgateway${EXTRAS:+[$EXTRAS]}==$PIN"
fi
ok "gateway: $GW_SPEC  ${C_D}(pin from $PIN_SOURCE)${C_0}"

# Disk.
case "$PROFILE" in apple) NEED_MB=8000 ;; gpu) NEED_MB=12000 ;; *) NEED_MB=1500 ;; esac
[ "$WITH_APPS" = 1 ] && NEED_MB=$((NEED_MB + 300))
# The terminal console: Rust from rustup (minimal profile) and cargo's build cache.
[ "$WITH_CONSOLE" = 1 ] && [ "$HAS_CC" = 1 ] && ! find_cargo && NEED_MB=$((NEED_MB + 700))
FREE_MB="$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2 {print int($4/1024)}')"
if [ -n "$FREE_MB" ]; then
    if [ "$FREE_MB" -lt 1000 ]; then die "only ${FREE_MB} MB free under $HOME (about ${NEED_MB} MB needed)"
    elif [ "$FREE_MB" -lt "$NEED_MB" ]; then warn "only ${FREE_MB} MB free under $HOME; the $PROFILE profile needs about ${NEED_MB} MB (models need more)"
    else ok "disk: ${FREE_MB} MB free (about ${NEED_MB} MB needed, models extra)"; fi
fi

# Port.
port_busy() {
    if have lsof; then lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1 && return 0
    fi
    if have ss; then ss -ltnH 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]$1\$" && return 0
    fi
    if have curl; then
        curl -s -o /dev/null --connect-timeout 1 --max-time 2 "http://127.0.0.1:$1/" 2>/dev/null
        [ $? -ne 7 ] && return 0
    fi
    return 1
}
is_our_gateway() {  # port -> 0 when an abstractgateway answers there
    http_get "http://127.0.0.1:$1/api/health" | grep -q '"abstractgateway"'
}
REUSE_RUNNING=0
if [ -z "$PORT" ]; then PORT="${ST_PORT:-8080}"; PORT_EXPLICIT=0; else PORT_EXPLICIT=1; fi
case "$PORT" in ''|*[!0-9]*) die "--port must be a number (got '$PORT')" ;; esac
if port_busy "$PORT"; then
    if [ "$PORT" = "$ST_PORT" ] && { pid_alive || { [ "$ST_MODE" = service ] && is_our_gateway "$PORT"; }; }; then
        REUSE_RUNNING=1
        ok "port $PORT: this install's gateway is already running (it will be restarted if the package changes)"
    elif [ "$PORT_EXPLICIT" = 1 ]; then
        die "port $PORT is already in use by another process; pick another one with --port"
    else
        _p=$((PORT + 1))
        while [ "$_p" -le $((PORT + 20)) ] && port_busy "$_p"; do _p=$((_p + 1)); done
        [ "$_p" -le $((PORT + 20)) ] || die "ports $PORT-$((PORT + 20)) are all busy; pick one with --port"
        warn "port $PORT is in use by another process; using $_p (kept for future runs)"
        PORT="$_p"
    fi
else
    ok "port $PORT is free"
fi
BASE_URL="http://127.0.0.1:$PORT"

# Linux ARM64: gateways before 0.3 pull abstractcore 2.13, which caps psutil below 6;
# psutil 5.x ships no aarch64 Linux wheel, so uv builds it from source and needs a C
# compiler. abstractcore 2.14 (gateway 0.3) allows psutil 6/7, which ship the wheel.
_old_pin=0
case "$PIN" in 0.1.*|0.2.*) _old_pin=1 ;; esac
if [ "$_old_pin" = 1 ] && [ "$OS_ID" = linux ] && { [ "$ARCH" = aarch64 ] || [ "$ARCH" = arm64 ]; } && ! have cc && ! have gcc; then
    warn "Linux ARM64 without a C compiler: psutil must be built from source; install one first (Debian/Ubuntu: sudo apt-get install -y gcc)"
fi

# Linux service manager.
SYSTEMD_USER=0
if [ "$OS_ID" = linux ]; then
    if have systemctl && systemctl --user show-environment >/dev/null 2>&1; then
        SYSTEMD_USER=1; ok "systemd user session available"
    elif [ "$NO_SERVICE" = 0 ]; then
        warn "no systemd user session (container or minimal SSH host): the gateway will run in the background, not as a service"
    fi
fi

# Start at login: asked here, before anything is downloaded, so an interactive
# user answers once and can walk away. Default yes (the gateway is the app's
# presence on the machine); a previous "no" is remembered as the default.
if [ "$NO_START" = 0 ] && [ "$NO_SERVICE" = 0 ] && { [ "$OS_ID" = macos ] || [ "$SYSTEMD_USER" = 1 ]; }; then
    _login_def=y; [ "$ST_MODE" = background ] && _login_def=n
    if ask_yes "Start AbstractFramework automatically when you log in? (a per-user login item, no admin; the uninstaller removes it)" "$_login_def"; then
        ok "start at login: yes ($([ "$OS_ID" = macos ] && echo "LaunchAgent ~/Library/LaunchAgents/ai.abstractframework.gateway.plist" || echo "systemd --user unit abstractgateway.service"); turn off: re-run with --no-service)"
    else
        NO_SERVICE=1
        ok "start at login: no (the gateway starts now in the background; re-run the installer to change this)"
    fi
fi

# ---------------------------------------------------------------------------
# 2. uv + Python
# ---------------------------------------------------------------------------
if [ "$PRINT" = 0 ]; then
    mkdir -p "$LOG_DIR"
    LOG_FILE="$LOG_DIR/install-$(date +%Y%m%d-%H%M%S).log"
    ( umask 077; : >"$LOG_FILE" )
fi

step "uv (Python toolchain manager)"
UV_BY_US="${ST_UV_BY_US:-0}"
if find_uv; then
    ok "uv found: $UV ($("$UV" --version 2>/dev/null | awk '{print $2}'))"
else
    info "installing uv from astral.sh into ~/.local/bin (no admin)"
    run_sh "install uv" "$DL https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh"
    UV_BY_US=1
    if [ "$PRINT" = 1 ]; then UV="uv"; else find_uv || die "uv was installed but cannot be found (looked in \$UV_INSTALL_DIR, \$XDG_BIN_HOME, ~/.local/bin)"; ok "uv installed: $UV"; fi
fi
if [ "$PRINT" = 1 ] && [ "$UV" = uv ]; then TOOL_BIN="${UV_TOOL_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"; else tool_bin; fi

step "Python $AF_PYTHON (managed by uv, isolated from any system Python)"
run "install Python $AF_PYTHON" "$UV" python install "$AF_PYTHON"

# ---------------------------------------------------------------------------
# 3. Gateway
# ---------------------------------------------------------------------------
step "AbstractGateway"
BEFORE=""
if [ "$PRINT" = 0 ]; then BEFORE="$("$UV" tool list 2>/dev/null | sed -n 's/^abstractgateway v\([^ ]*\).*/\1/p' | head -n 1)"; fi
# install_gateway GGUF SOFT: GGUF=1 adds the llama.cpp wheel. uv splits --overrides and
# --constraints values at whitespace ("Application Support"), so the install runs from
# the data dir and names both files relatively.
install_gateway() {
    _gguf="$1"; _gsoft="$2"
    if [ "$PRINT" = 1 ]; then
        info "$DATA_DIR/uv-overrides.txt (written at install time; see the top of install.sh):"
        af_uv_overrides "$_gguf" | sed 's/^/      /'
        [ "$_gguf" = 1 ] && info "$DATA_DIR/uv-constraints.txt:" && echo "      llama-cpp-python==$GGUF_PIN"
    else
        af_uv_overrides "$_gguf" >"$DATA_DIR/uv-overrides.txt"
        [ "$_gguf" = 1 ] && echo "llama-cpp-python==$GGUF_PIN" >"$DATA_DIR/uv-constraints.txt"
    fi
    set -- "$UV" tool install --python "$AF_PYTHON" --with "$AF_WITH_WHEELS"
    if [ "$_gguf" = 1 ]; then
        set -- "$@" --with "llama-cpp-python==$GGUF_PIN" --constraints uv-constraints.txt --find-links "$GGUF_LINKS"
    elif [ "$FULL" = 1 ]; then
        set -- "$@" --with llama-cpp-python
    fi
    set -- "$@" --overrides uv-overrides.txt
    for _p in $(af_no_build_packages); do set -- "$@" --no-build-package "$_p"; done
    [ "$WITH_CORE_CLI" = 1 ] && set -- "$@" --with-executables-from abstractcore
    { [ -n "$FROM" ] || [ "$REINSTALL" = 1 ]; } && set -- "$@" --reinstall
    _cwd="$(pwd)"
    RUN_SHOW="cd $(q "$DATA_DIR") && $(show_cmd "$@" "$GW_SPEC")"
    [ "$PRINT" = 1 ] || cd "$DATA_DIR"
    RUN_SOFT="$_gsoft" run "install abstractgateway$([ "$_gguf" = 1 ] && echo " with the llama.cpp $GGUF_KIND wheel")" "$@" "$GW_SPEC"
    [ "$PRINT" = 1 ] || cd "$_cwd" 2>/dev/null || cd "$HOME"
    return "$RUN_RC"
}
GGUF_RESULT=""
REINSTALL=0
if [ -n "$BEFORE" ] && [ "$PIN" = latest ] && [ -z "$FROM" ] && [ "$ST_PROFILE" = "$PROFILE" ]; then
    run "upgrade abstractgateway" "$UV" tool upgrade abstractgateway
    GGUF_RESULT="as in the previous install (uv tool upgrade keeps it)"
elif [ "$FULL" = 1 ]; then
    install_gateway 0 0
    GGUF_RESULT="llama-cpp-python built from source (--full)"
elif [ -n "$GGUF_PIN" ]; then
    [ "$PRINT" = 1 ] && info "llama.cpp GGUF: llama-cpp-python $GGUF_PIN, $GGUF_KIND wheel from $GGUF_LINKS (if this install fails, it is retried without it)"
    if install_gateway 1 1; then
        GGUF_RESULT="llama-cpp-python $GGUF_PIN ($GGUF_KIND wheel from $GGUF_LINKS)"
    else
        warn "$AF_GGUF_SKIPPED"
        install_gateway 0 0
        GGUF_RESULT="skipped (the prebuilt $GGUF_KIND wheel did not install; see $LOG_FILE)"
    fi
else
    warn "$AF_GGUF_SKIPPED"
    install_gateway 0 0
    GGUF_RESULT="skipped (no prebuilt wheel for $OS_ID $ARCH)"
fi
# Repair: an interrupted or damaged earlier install can leave uv reporting the
# tool as installed while its command is missing or cannot start. uv then does
# nothing, so check the command itself and reinstall in place when it fails.
if [ "$PRINT" = 0 ] && ! "$TOOL_BIN/abstractgateway" --help >/dev/null 2>&1; then
    warn "the installed gateway does not start (an earlier install was interrupted or damaged): reinstalling it"
    REINSTALL=1
    case "$GGUF_RESULT" in
        "llama-cpp-python $GGUF_PIN ("*) install_gateway 1 0 ;;
        *) install_gateway 0 0 ;;
    esac
fi
AFTER="$BEFORE"
if [ "$PRINT" = 0 ]; then
    AFTER="$("$UV" tool list 2>/dev/null | sed -n 's/^abstractgateway v\([^ ]*\).*/\1/p' | head -n 1)"
    "$TOOL_BIN/abstractgateway" --help >/dev/null 2>&1 || die "abstractgateway is still not usable in $TOOL_BIN after reinstalling it (log: $LOG_FILE).
What to do: run the installer again; if it stops here again, report it with that log file ($AF_DOCS#if-something-goes-wrong)."
    if [ -z "$BEFORE" ]; then ok "installed abstractgateway $AFTER"
    elif [ "$REINSTALL" = 1 ]; then ok "abstractgateway $AFTER repaired (reinstalled in place)"
    elif [ "$BEFORE" = "$AFTER" ] && [ -z "$FROM" ]; then ok "abstractgateway $AFTER already installed"
    else ok "abstractgateway $BEFORE -> $AFTER"; fi
fi
ST_SPEC=""
[ -f "$STATE_FILE" ] && ST_SPEC="$(sed -n 's/^GATEWAY_SPEC=//p' "$STATE_FILE" | tail -n 1)"
CHANGED=0
if [ "$BEFORE" != "$AFTER" ] || [ -n "$FROM" ] || [ "$REINSTALL" = 1 ] || { [ -n "$ST_SPEC" ] && [ "$ST_SPEC" != "$GW_SPEC" ]; }; then CHANGED=1; fi
GW="$TOOL_BIN/abstractgateway"
GWCFG="$TOOL_BIN/abstractgateway-config"

case ":$PATH:" in
    *":$TOOL_BIN:"*) ;;
    *)
        if [ "$NO_MODIFY_PATH" = 0 ] && grep -qsF "$TOOL_BIN" "$HOME/.zshenv" "$HOME/.zshrc" "$HOME/.bashrc" \
            "$HOME/.bash_profile" "$HOME/.profile" "${XDG_CONFIG_HOME:-$HOME/.config}/fish/conf.d/uv.env.fish"; then
            # A re-run from a Terminal opened before the first install: the profile is
            # already done (uv tool update-shell would fail with "already up-to-date").
            ok "$TOOL_BIN is already on PATH in your shell profile (new Terminal windows have it)"
        elif [ "$NO_MODIFY_PATH" = 0 ]; then
            RUN_SOFT=1 run "add $TOOL_BIN to PATH in your shell profile" "$UV" tool update-shell
            info "open a new terminal for the 'abstractgateway' command to be on PATH"
        else
            warn "$TOOL_BIN is not on PATH; add it yourself or use absolute paths"
        fi ;;
esac

# ---------------------------------------------------------------------------
# 4. Optional components
# ---------------------------------------------------------------------------
NODE_WHEEL="${ST_NODE_WHEEL:-0}"
if [ "$WITH_APPS" = 1 ]; then
    step "Node.js for the browser apps"
    _nv="$(node -v 2>/dev/null | sed 's/^v//; s/\..*//')" || true
    if [ -n "$_nv" ] && [ "$_nv" -ge 18 ] 2>/dev/null; then
        ok "Node.js $(node -v) found"
    elif [ -x "$TOOL_BIN/node" ]; then
        ok "Node.js from nodejs-wheel: $TOOL_BIN/node"
    else
        info "no Node.js >= 18: installing the nodejs-wheel uv tool (node, npm, npx in $TOOL_BIN; no admin)"
        run "install nodejs-wheel" "$UV" tool install nodejs-wheel
        NODE_WHEEL=1
    fi
    info "apps are not installed globally; each runs on demand (first launch downloads it):"
    _others=""
    for spec in $AF_NPM_APPS; do
        case " $AF_NPM_GATEWAY_FLAG_APPS " in
            *" ${spec%@*} "*) printf '      npx -y %s --gateway-url %s\n' "$spec" "$BASE_URL" ;;
            *) printf '      npx -y %s\n' "$spec"; _others="$_others${_others:+, }${spec%@*}" ;;
        esac
    done
    [ "$BASE_URL" = "http://127.0.0.1:8080" ] || [ -z "$_others" ] \
        || info "$_others start on http://127.0.0.1:8080: enter $BASE_URL on their sign-in screen"
fi

# Terminal console: crates.io publishes no prebuilt binary, so cargo builds it (see
# console_bin). When there is no cargo, or only one older than the crate's Rust 1.87 (the
# distro packages are), Rust comes from rustup: user-scoped (~/.rustup, ~/.cargo), shell
# profiles untouched, its cargo used by absolute path. The TLS stack (ring) compiles C, so
# it needs a C compiler. A failure here never fails the install: the web console does
# everything the terminal one does.
CONSOLE_OK=0; CONSOLE_WHY="skipped with --no-console"
RUST_BY_US="${ST_RUST_BY_US:-0}"
RUSTUP_CARGO="${CARGO_HOME:-$HOME/.cargo}/bin/cargo"
console_bin
cargo_minor() { "$1" --version 2>/dev/null | awk '{ split($2, v, "."); print v[1] * 1000 + v[2] }'; }
if [ "$WITH_CONSOLE" = 0 ]; then
    [ "$PRINT" = 0 ] && console_installed && CONSOLE_OK=1
else
    step "Terminal console ($CONSOLE_NAME $CONSOLE_PIN)"
    _rust_old=""
    if [ "$PRINT" = 0 ] && console_installed; then
        ok "$CONSOLE_NAME $CONSOLE_PIN already installed: $CONSOLE_BIN"
        CONSOLE_OK=1
    elif [ "$HAS_CC" = 0 ]; then
        CONSOLE_WHY="building it needs a C compiler: $([ "$OS_ID" = macos ] && echo 'xcode-select --install' || echo 'sudo apt-get install -y build-essential (Debian/Ubuntu)')"
        warn "terminal console skipped: $CONSOLE_WHY; then run the installer again"
    else
        find_cargo || true
        if [ -n "$CARGO" ] && [ "$PRINT" = 0 ] && [ "$(cargo_minor "$CARGO")" -lt 1087 ] 2>/dev/null; then
            _rust_old="$("$CARGO" --version 2>/dev/null | awk '{print $2}')"
            if [ -x "$(dirname "$CARGO")/rustup" ]; then
                CONSOLE_WHY="it needs Rust 1.87 or later and $CARGO is $_rust_old; update it (rustup update stable)"
                warn "terminal console skipped: $CONSOLE_WHY, then run the installer again"
                CARGO=""
            else
                info "cargo $_rust_old ($CARGO) is older than the Rust 1.87 the console needs: adding a current Rust with rustup"
                CARGO=""; [ -x "$RUSTUP_CARGO" ] && [ "$(cargo_minor "$RUSTUP_CARGO")" -ge 1087 ] 2>/dev/null && CARGO="$RUSTUP_CARGO"
                [ -n "$CARGO" ] || _rust_old="rustup"
            fi
        fi
        if [ -z "$CARGO" ] && { [ -z "$_rust_old" ] || [ "$_rust_old" = rustup ]; }; then
            if ask_yes "Build the terminal console? It needs Rust: about 600 MB in ~/.rustup and ~/.cargo, no admin, a few minutes" y; then
                info "installing Rust with rustup into ~/.rustup and ~/.cargo (no admin, shell profile untouched)"
                RUN_SOFT=1 run_sh "install Rust (rustup)" "$DL https://sh.rustup.rs | sh -s -- -y --profile minimal --no-modify-path"
                if [ "$PRINT" = 1 ]; then CARGO="$RUSTUP_CARGO"
                elif [ -x "$RUSTUP_CARGO" ]; then CARGO="$RUSTUP_CARGO"; RUST_BY_US=1
                else CONSOLE_WHY="Rust could not be installed (see $LOG_FILE)"; warn "terminal console skipped: $CONSOLE_WHY"; fi
            else
                CONSOLE_WHY="you chose not to install Rust; re-run the installer to add it"
            fi
        fi
        if [ -n "$CARGO" ]; then
            info "compiling it from crates.io (a few minutes the first time)"
            set -- "$CARGO" install --locked --force
            [ -n "$CRATE_ROOT" ] && set -- "$@" --root "$CRATE_ROOT"
            RUN_SOFT=1 run "build the terminal console" "$@" "$CONSOLE_NAME" --version "$CONSOLE_PIN"
            if [ "$PRINT" = 1 ]; then CONSOLE_OK=1
            elif [ "$RUN_RC" = 0 ] && console_installed; then
                CONSOLE_OK=1; ok "installed $CONSOLE_NAME $CONSOLE_PIN: $CONSOLE_BIN"
            else
                CONSOLE_WHY="the build failed (see $LOG_FILE)"
                [ "$RUN_RC" = 0 ] && warn "cargo reported success but $CONSOLE_BIN does not answer --version"
            fi
        fi
    fi
fi

if [ "$WITH_CODE_CLI" = 1 ]; then
    step "AbstractCode terminal client (crates.io)"
    _c="$AF_CRATE_CODE_CLI"
    if [ -n "$CARGO" ] || find_cargo; then
        run "cargo install ${_c%@*}" "$CARGO" install --locked "${_c%@*}" --version "${_c##*@}"
        info "run it: ${_c%@*} --gateway $BASE_URL"
    else
        warn "cargo not found: install Rust from https://rustup.rs, then run: cargo install --locked ${_c%@*} --version ${_c##*@}"
    fi
fi

if [ "$WITH_OLLAMA" = 1 ]; then
    step "Ollama (vendor installer)"
    if have ollama || http_get "http://127.0.0.1:11434/api/version" >/dev/null; then
        ok "Ollama already installed or reachable; skipped"
    else
        if [ "$OS_ID" = linux ]; then
            warn "Ollama's Linux installer uses sudo: it installs to /usr/local and creates a system service. It may ask for your password."
        else
            warn "Ollama's installer moves Ollama.app to /Applications and may ask for your password for /usr/local/bin/ollama."
        fi
        run_sh "install Ollama" "$DL https://ollama.com/install.sh | sh"
    fi
fi

if [ "$WITH_LMSTUDIO" = 1 ]; then
    step "LM Studio (headless daemon, vendor installer)"
    if have lms || [ -x "$HOME/.lmstudio/bin/lms" ] || [ -d "/Applications/LM Studio.app" ] || http_get "http://127.0.0.1:1234/v1/models" >/dev/null; then
        ok "LM Studio already installed or reachable; skipped"
    else
        if [ "$OS_ID" = macos ] && [ "$ARCH" != arm64 ]; then
            warn "LM Studio supports Apple Silicon Macs only; skipped"
        else
            [ "$OS_ID" = linux ] && warn "the LM Studio installer may ask for sudo to add libatomic1."
            run_sh "install LM Studio (llmster)" "curl -fsSL https://lmstudio.ai/install.sh | bash"
            info "start its server with: ~/.lmstudio/bin/lms daemon up && ~/.lmstudio/bin/lms server start --port 1234 --bind 127.0.0.1"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# 5. Service / start
# ---------------------------------------------------------------------------
write_state() {
    [ "$PRINT" = 1 ] && return 0
    mkdir -p "$DATA_DIR"
    {
        echo "# written by AbstractFramework install.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "PORT=$PORT"; echo "MODE=$MODE"; echo "PROFILE=$PROFILE"
        echo "NODE_WHEEL=$NODE_WHEEL"; echo "GATEWAY_SPEC=$GW_SPEC"; echo "GATEWAY_VERSION=$AFTER"
        echo "UV_BY_INSTALLER=$UV_BY_US"; echo "RUST_BY_INSTALLER=$RUST_BY_US"
    } >"$STATE_FILE"
}

export ABSTRACTGATEWAY_DATA_DIR="$DATA_DIR"
# Gateways before 0.3 (reachable with --pin) refuse to start without an auth mode; from
# 0.3 on, user auth with a bootstrapped admin is the loopback default, so this is a no-op.
export ABSTRACTGATEWAY_USER_AUTH=1

MODE=none
NET_SETTING=0   # 1 = the background gateway starts plain `serve` (the Network setting binds it)
SERVICE_OK=0
if gateway_supports service; then SERVICE_OK=1; fi
USE_SERVICE=0
if [ "$NO_SERVICE" = 0 ] && { [ "$OS_ID" = macos ] || [ "$SYSTEMD_USER" = 1 ]; }; then
    # In --print mode the gateway may not be installed yet: show the service path.
    if [ "$SERVICE_OK" = 1 ] || [ "$PRINT" = 1 ]; then USE_SERVICE=1; fi
fi

if [ "$NO_START" = 1 ]; then
    step "Start"
    info "--no-start: the gateway is installed but not started"
    MODE="${ST_MODE:-none}"
elif [ "$USE_SERVICE" = 1 ]; then
    step "Login service ($([ "$OS_ID" = macos ] && echo 'LaunchAgent' || echo 'systemd --user'))"
    if [ "$PRINT" = 1 ] && [ "$SERVICE_OK" = 0 ]; then
        info "(only when the installed gateway has 'abstractgateway service'; otherwise it starts in the background)"
    fi
    stop_background_gateway
    if [ "$ST_MODE" = service ] && [ "$REUSE_RUNNING" = 1 ] && [ "$CHANGED" = 0 ]; then
        ok "login item already registered and the gateway is running, unchanged"
    else
        # The installer waits for health and mints the sign-in link itself (below), so the
        # service verb does neither when it supports skipping them (gateway 0.3.0+).
        # No --host: the login item runs plain `serve` and the gateway's Network setting
        # (localhost unless the user chose otherwise) binds it; passing 127.0.0.1 here would
        # reset a "Local network" choice on every re-run. Older gateways default to 127.0.0.1.
        set -- --port "$PORT"
        if [ "$PRINT" = 0 ] && "$GW" service install --help 2>/dev/null | grep -q -- '--no-claim'; then
            set -- "$@" --no-wait --no-claim
        fi
        run "register the gateway service" "$GW" service install "$@"
    fi
    MODE=service
else
    step "Start in the background"
    if [ "$ST_MODE" = service ] && [ "$SERVICE_OK" = 1 ]; then
        # Chosen "no" this time: the earlier login item would fight the background
        # gateway for the port, so it goes first.
        run "remove the login item registered by the previous install" "$GW" service uninstall
    fi
    if [ "$NO_SERVICE" = 0 ] && [ "$PRINT" = 0 ] && [ "$SERVICE_OK" = 0 ]; then
        warn "gateway $AFTER has no 'abstractgateway service' command: it will not start at login"
        info "re-run this installer after the gateway upgrades, or set up a login item by hand: $AF_DOCS#run-at-login"
    fi
    if [ "$REUSE_RUNNING" = 1 ] && [ "$CHANGED" = 0 ] && pid_alive; then
        ok "already running (pid $(cat "$PID_FILE")), unchanged"
    else
        stop_background_gateway
        # Plain `serve` when the gateway has the Network setting (`abstractgateway network`):
        # flags on the command line would override it forever (a restart replays them).
        # Older gateways keep the pinned command line they need.
        if [ "$PRINT" = 1 ]; then
            info "$(show_cmd abstractgateway network set localhost --port "$PORT")   (gateways with 'abstractgateway network', when no mode is stored yet; then plain 'serve')"
        elif gateway_supports network && seed_network_setting; then
            NET_SETTING=1
        fi
        if [ "$NET_SETTING" = 1 ]; then set -- serve; else set -- serve --host 127.0.0.1 --port "$PORT"; fi
        _cmd="ABSTRACTGATEWAY_DATA_DIR=$(q "$DATA_DIR") ABSTRACTGATEWAY_USER_AUTH=1 nohup $(q "$GW") $(show_cmd "$@") >>$(q "$GATEWAY_LOG") 2>&1 &"
        printf '  %s$ %s%s\n' "$C_D" "$_cmd" "$C_0"
        twin "$_cmd"
        if [ "$PRINT" = 0 ]; then
            ( umask 077; : >>"$GATEWAY_LOG" )
            nohup "$GW" "$@" >>"$GATEWAY_LOG" 2>&1 </dev/null &
            echo $! >"$PID_FILE"
            ok "started (pid $(cat "$PID_FILE")), log: $GATEWAY_LOG"
        fi
    fi
    MODE=background
fi
write_state

# ---------------------------------------------------------------------------
# 6. Health + console
# ---------------------------------------------------------------------------
CONSOLE_URL="$BASE_URL/console"
TOKEN_FILE="$DATA_DIR/auth/bootstrap-admin-token"
CLAIMED=0; OPENED=0
if [ "$NO_START" = 0 ]; then
    step "Health check"
    twin "curl $BASE_URL/api/health"
    if [ "$PRINT" = 1 ]; then
        info "would wait up to 180 s for $BASE_URL/api/health"
    else
        # The first start loads the local engine stacks (MLX, torch) from a cold disk
        # cache: allow 3 minutes and say that it is still going.
        _i=0; _wait=180
        _svc_log="$HOME/Library/Logs/AbstractGateway"
        [ "$OS_ID" = macos ] || _svc_log="journalctl --user -u abstractgateway"
        _glog="$([ "$MODE" = service ] && echo "$_svc_log" || echo "$GATEWAY_LOG")"
        until http_get "$BASE_URL/api/health" | grep -q '"abstractgateway"'; do
            _i=$((_i + 1))
            if [ "$MODE" = background ] && ! pid_alive; then
                tail -n 30 "$GATEWAY_LOG" >&2 || true
                die "the gateway stopped while starting (log: $GATEWAY_LOG).
What to do: run the installer again; if it stops here again, report it with that log file ($AF_DOCS#if-something-goes-wrong)."
            fi
            if [ "$_i" -ge "$_wait" ]; then
                [ "$MODE" = background ] && { tail -n 30 "$GATEWAY_LOG" >&2 2>/dev/null || true; }
                die "the gateway did not answer at $BASE_URL within $_wait s (logs: $_glog).
What to do: restart the computer (the login item starts it again) or run the installer again, then open $BASE_URL/console."
            fi
            [ $((_i % 15)) = 0 ] && info "still starting (${_i}s; the first start loads the engines and takes longer)"
            sleep 1
        done
        ok "gateway healthy at $BASE_URL (${_i}s)"
    fi

    step "Console sign-in"
    if [ "$PRINT" = 0 ] && gateway_supports claim-url; then
        _claim="$("$GWCFG" claim-url --base-url "$BASE_URL" 2>>"$LOG_FILE" | grep -Eo 'https?://[^[:space:]]+' | tail -n 1)" || true
        if [ -n "$_claim" ]; then
            CONSOLE_URL="$_claim"; CLAIMED=1
            twin "$(show_cmd "$GWCFG" claim-url --base-url "$BASE_URL")"
            ok "one-time sign-in link created (valid 10 minutes, this machine only)"
        else
            warn "'abstractgateway-config claim-url' is present but returned no URL (see $LOG_FILE); falling back to the admin token"
        fi
    elif [ "$PRINT" = 1 ]; then
        info "$(show_cmd abstractgateway-config claim-url --base-url "$BASE_URL")   (when supported)"
    fi
    if [ "$CLAIMED" = 0 ]; then
        info "sign in as 'admin' with the token in: $TOKEN_FILE"
        info "    cat $(q "$TOKEN_FILE")"
    fi

    if [ "$NO_OPEN" = 1 ] || [ "$PRINT" = 1 ]; then
        info "open: $CONSOLE_URL"
    elif [ "$OS_ID" = macos ] && have open; then
        if open "$CONSOLE_URL" >/dev/null 2>&1; then OPENED=1; ok "opened the console in your browser"; else info "open: $CONSOLE_URL"; fi
    elif [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && have xdg-open; then
        if xdg-open "$CONSOLE_URL" >/dev/null 2>&1; then OPENED=1; ok "opened the console in your browser"; else info "open: $CONSOLE_URL"; fi
    else
        info "open: $CONSOLE_URL"
        info "remote host? tunnel it first: ssh -L $PORT:127.0.0.1:$PORT <this-host>"
    fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
# The terminal console signs in with the admin token the gateway keeps in its data dir:
# --token-file names the file, so the token never lands in argv, the environment or this output.
_tui_exe="$CONSOLE_NAME"; [ "$CONSOLE_BIN" = "$TOOL_BIN/$CONSOLE_NAME" ] || _tui_exe="$(q "$CONSOLE_BIN")"
TUI_CMD="$_tui_exe --url $BASE_URL --token-file $(q "$TOKEN_FILE")"
if [ "$PRINT" = 0 ] && [ "$NO_START" = 0 ]; then
    # The plain-language part first: what a non-technical user needs to know.
    printf '\n%s%sAbstractFramework is ready.%s\n' "$C_B" "$C_G" "$C_0"
    [ "$OPENED" = 1 ] && echo "  Your browser now shows its web console. Its address is $BASE_URL/console (bookmark it)."
    echo "  Configure it from either console (the same settings, both need this machine):"
    # An opened claim link is spent (the browser redeemed it): show the plain address then.
    echo "    Web:       $([ "$OPENED" = 1 ] && echo "$BASE_URL/console" || echo "$CONSOLE_URL")"
    if [ "$CLAIMED" = 1 ] && [ "$OPENED" = 1 ]; then
        echo "               signed in already in this browser; another browser needs a new link: abstractgateway-config claim-url --base-url $BASE_URL"
    elif [ "$CLAIMED" = 1 ]; then
        echo "               one-time sign-in link (10 minutes); a new one: abstractgateway-config claim-url --base-url $BASE_URL"
    else
        echo "               sign in as 'admin' with the token in $TOKEN_FILE"
    fi
    [ "$OPENED" = 1 ] || echo "               from another computer, tunnel it first: ssh -L $PORT:127.0.0.1:$PORT <this-host>"
    if [ "$CONSOLE_OK" = 1 ]; then
        echo "    Terminal:  $TUI_CMD"
    else
        echo "    Terminal:  not installed: $CONSOLE_WHY"
    fi
    if [ "$MODE" = service ]; then
        echo "  It starts by itself when you log in; nothing to launch."
    else
        echo "  It runs until you restart the computer; run the installer again to start it."
    fi
    case ",$EXTRAS," in *,tray,*) echo "  Its icon in the $([ "$OS_ID" = macos ] && echo 'menu bar' || echo 'system tray') opens the console and shows its status." ;; esac
    echo "  First steps in the console: pick an engine and a model; it shows what fits this computer."
    echo "  To remove it: run the uninstaller (Uninstall AbstractFramework.command), or: sh install.sh --uninstall"
fi
printf '\n%s%s%s\n' "$C_B" "$([ "$PRINT" = 1 ] && echo 'Plan printed (--print): nothing was changed.' || echo 'Details')" "$C_0"
printf '  %-11s %s\n' "Console:" "$BASE_URL/console" "Gateway:" "$GW_SPEC ($PROFILE profile)" \
    "Terminal:" "$([ "$CONSOLE_OK" = 1 ] && echo "$TUI_CMD" || echo "not installed ($CONSOLE_WHY)")" \
    "Data dir:" "$DATA_DIR" "Logs:" "$LOG_DIR" "Mode:" "$MODE"
echo ""
echo "  Status:     $([ "$MODE" = service ] && echo "abstractgateway service status" || echo "curl $BASE_URL/api/health")"
echo "  Stop:       $([ "$MODE" = service ] && echo "abstractgateway service uninstall   (stops it and removes the login entry; data is kept)" || echo "kill \$(cat $(q "$PID_FILE"))")"
echo "  Start:      $([ "$MODE" = service ] && echo "abstractgateway service install --port $PORT" || echo "re-run this installer, or: ABSTRACTGATEWAY_USER_AUTH=1 ABSTRACTGATEWAY_DATA_DIR=$(q "$DATA_DIR") abstractgateway serve$([ "$NET_SETTING" = 1 ] || echo " --host 127.0.0.1 --port $PORT")")"
echo "  Upgrade:    re-run this installer (or: uv tool upgrade abstractgateway)"
echo "  Uninstall:  sh install.sh --uninstall   (or: $([ "$MODE" = service ] && echo 'abstractgateway service uninstall && ')uv tool uninstall abstractgateway)"
echo "  Check:      uvx abstractframework doctor"
echo "  GGUF:       $GGUF_RESULT"
if [ "$FULL" = 0 ] && { [ "$PROFILE" = apple ] || [ "$PROFILE" = gpu ]; }; then
    echo "  $AF_SKIPPED_LINE"
fi
echo "  Apps:       npx -y @abstractframework/flow --gateway-url $BASE_URL   (also: code, observer, continuum, entity)"
echo "  Docs:       $AF_DOCS"
if [ -n "$TWINS" ]; then
    echo ""
    echo "  The same steps by hand:"
    printf '%s' "$TWINS"
fi
[ -n "$LOG_FILE" ] && printf '\n  %sFull log: %s%s\n' "$C_D" "$LOG_FILE" "$C_0"
exit 0
