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
#   4. optional: Node.js for the browser apps, terminal tools, Ollama, LM Studio
#   5. registers the gateway as a user service when the installed gateway
#      supports `abstractgateway service install`, otherwise starts it in the
#      background; waits for /api/health
#   6. opens the gateway console (one-time claim URL when supported)
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
#   --with-console           cargo install the terminal console (needs Rust)
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
#                            remove the service and the uv tools (--purge also
#                            deletes the gateway data dir; --remove-uv also removes
#                            uv, its Pythons and its download cache when this
#                            installer is what put uv there)
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
AF_GATEWAY_PIN_DEFAULT="0.4.3"
AF_PYTHON="3.12"
AF_NPM_APPS="@abstractframework/flow@0.3.20 @abstractframework/code@0.4.2 @abstractframework/observer@0.1.12 @abstractframework/continuum@0.3.1 @abstractframework/entity@0.2.1"
AF_CRATE_CONSOLE="abstractgateway-console@0.8.0"
AF_CRATE_CODE_CLI="abstractcode@0.5.1"
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
WITH_APPS=0; WITH_CONSOLE=0; WITH_CODE_CLI=0; WITH_CORE_CLI=0
WITH_OLLAMA=0; WITH_LMSTUDIO=0
FULL=0; NO_TRAY=0; NO_SERVICE=0; NO_START=0; NO_OPEN=0; NO_MODIFY_PATH=0
PRINT=0; UNINSTALL=0; PURGE=0; VERBOSE=0; REMOVE_UV=0
INTERACTIVE="${AF_INTERACTIVE:-0}"

usage() {
    if [ -f "$0" ] && head -n 3 "$0" 2>/dev/null | grep -q "AbstractFramework bootstrap"; then
        sed -n '2,59p' "$0" | sed 's/^# \{0,1\}//'
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
        --with-console) WITH_CONSOLE=1 ;;
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

if [ -z "$DATA_DIR" ]; then
    if [ "$OS_ID" = macos ]; then DATA_DIR="$HOME/Library/Application Support/AbstractGateway"
    else DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/abstractgateway"; fi
fi
STATE_FILE="$DATA_DIR/bootstrap.env"
PID_FILE="$DATA_DIR/gateway.pid"
LOG_DIR="$DATA_DIR/logs"
GATEWAY_LOG="$LOG_DIR/gateway.log"

# Previous run state (port, service mode, whether we installed Node).
ST_PORT=""; ST_MODE=""; ST_NODE_WHEEL=""; ST_PROFILE=""; ST_UV_BY_US=""
if [ -f "$STATE_FILE" ]; then
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
# Uninstall
# ---------------------------------------------------------------------------
if [ "$UNINSTALL" = 1 ]; then
    printf '%sAbstractFramework uninstall%s%s\n' "$C_B" "$C_0" "$([ "$PRINT" = 1 ] && echo ' (--print: nothing is changed)')"
    find_uv || true; tool_bin
    # Asked first, so the user answers once and every step below runs unattended.
    if [ "$PURGE" = 0 ] && [ -d "$DATA_DIR" ]; then
        _size="$(du -sh "$DATA_DIR" 2>/dev/null | awk '{print $1}')"
        if ask_yes "Also delete your AbstractFramework data (settings, users, chats, run history: ${_size:-?} in $DATA_DIR)? This cannot be undone." n; then
            PURGE=1
        fi
    fi
    if [ "$ST_UV_BY_US" = 1 ] && [ "$REMOVE_UV" = 0 ] && [ -n "$UV" ]; then
        _uvsize="$(du -sch "$("$UV" cache dir 2>/dev/null)" "$("$UV" python dir 2>/dev/null)" 2>/dev/null | tail -n 1 | awk '{print $1}')"
        if ask_yes "Also remove uv, its Python and its download cache (${_uvsize:-?})? The installer added uv; anything else you installed with uv would stop working." n; then
            REMOVE_UV=1
        fi
    fi
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
    stop_background_gateway
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
    step "Data"
    _inst="$HOME/Library/Application Support/AbstractFramework/Installer"
    if [ "$OS_ID" = macos ] && [ -d "$_inst" ]; then
        run "remove the copy of the installer left by the .pkg" rm -rf "$_inst"
    fi
    if [ "$PURGE" = 1 ]; then
        run "delete the gateway data dir" rm -rf "$DATA_DIR"
        # The LaunchAgent's stdout/stderr files (os_service.log_dir on macOS).
        if [ "$OS_ID" = macos ] && [ -d "$HOME/Library/Logs/AbstractGateway" ]; then
            run "delete the login item's logs" rm -rf "$HOME/Library/Logs/AbstractGateway"
        fi
    else
        info "kept the gateway data dir: $DATA_DIR (delete it with --uninstall --purge)"
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
        info "kept: Ollama, LM Studio, and any cargo tools"
    else
        info "kept: uv ($([ -n "$UV" ] && echo "$UV" || echo 'not found'); --remove-uv removes it), Ollama, LM Studio, and any cargo tools"
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
    for spec in $AF_NPM_APPS; do
        printf '      npx -y %s   %s# ABSTRACTGATEWAY_URL=%s%s\n' "$spec" "$C_D" "$BASE_URL" "$C_0"
    done
fi

if [ "$WITH_CONSOLE" = 1 ] || [ "$WITH_CODE_CLI" = 1 ]; then
    step "Terminal tools (crates.io)"
    for _sel in console code; do
        if [ "$_sel" = console ]; then [ "$WITH_CONSOLE" = 1 ] || continue; _c="$AF_CRATE_CONSOLE"
        else [ "$WITH_CODE_CLI" = 1 ] || continue; _c="$AF_CRATE_CODE_CLI"; fi
        if have cargo; then
            run "cargo install ${_c%@*}" cargo install --locked "${_c%@*}" --version "${_c##*@}"
        else
            warn "cargo not found: install Rust from https://rustup.rs, then run: cargo install --locked ${_c%@*} --version ${_c##*@}"
        fi
    done
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
        echo "UV_BY_INSTALLER=$UV_BY_US"
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
    CLAIMED=0
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
    TOKEN_FILE="$DATA_DIR/auth/bootstrap-admin-token"
    if [ "$CLAIMED" = 0 ]; then
        info "sign in as 'admin' with the token in: $TOKEN_FILE"
        info "    cat $(q "$TOKEN_FILE")"
    fi

    if [ "$NO_OPEN" = 1 ] || [ "$PRINT" = 1 ]; then
        info "open: $CONSOLE_URL"
    elif [ "$OS_ID" = macos ] && have open; then
        if open "$CONSOLE_URL" >/dev/null 2>&1; then ok "opened the console in your browser"; else info "open: $CONSOLE_URL"; fi
    elif [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && have xdg-open; then
        if xdg-open "$CONSOLE_URL" >/dev/null 2>&1; then ok "opened the console in your browser"; else info "open: $CONSOLE_URL"; fi
    else
        info "open: $CONSOLE_URL"
        info "remote host? tunnel it first: ssh -L $PORT:127.0.0.1:$PORT <this-host>"
    fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if [ "$PRINT" = 0 ] && [ "$NO_START" = 0 ]; then
    # The plain-language part first: what a non-technical user needs to know.
    printf '\n%s%sAbstractFramework is ready.%s\n' "$C_B" "$C_G" "$C_0"
    if [ "$NO_OPEN" = 0 ]; then
        echo "  Your browser now shows it. Its address is $BASE_URL/console (bookmark it)."
    else
        echo "  Open $CONSOLE_URL in your browser."
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
echo "  Apps:       npx -y @abstractframework/flow   (also: code, observer, continuum, entity)"
echo "  Docs:       $AF_DOCS"
if [ -n "$TWINS" ]; then
    echo ""
    echo "  The same steps by hand:"
    printf '%s' "$TWINS"
fi
[ -n "$LOG_FILE" ] && printf '\n  %sFull log: %s%s\n' "$C_D" "$LOG_FILE" "$C_0"
exit 0
