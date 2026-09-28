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
#      (isolated, user-scoped; commands land in ~/.local/bin, AbstractCore's
#      and its voice/vision/music commands too; prebuilt wheels only, so no
#      C compiler / Xcode tools are needed)
#   4. the terminal console (abstractgateway-console) and AbstractCode's terminal
#      client (abstractcode), built with cargo into the same folder (Rust comes
#      from rustup, user-scoped, when missing), then the optional parts: Node.js
#      for the browser apps, Ollama, LM Studio
#   5. start at login: asked when a person is at a terminal (Enter = yes); then
#      registers the gateway as a user service (`abstractgateway service install`)
#      or starts it in the background; waits for /api/health
#   6. writes the local gateway pointer (~/.abstractframework/gateway.json: the
#      address only, never a token), opens the web console (one-time claim URL when
#      supported) and prints how to reach both consoles, the web one (`/console`)
#      and the terminal one, and the apps (`/apps/<app>/` on the gateway)
#
# Upgrade: run the same line again. It finds the existing install (its bootstrap.env,
# the uv tool), says "AbstractFramework <old> found: upgrading to <new>" (or "already up
# to date"), keeps the profile, port, start at login, data dir and the choices marked
# [kept] below, moves every library to the release's exact versions, restarts the gateway
# when anything changed, and lists what changed (old -> new). The gateway's Update action
# (web console, terminal console, tray) runs this same script with --no-start.
#
# Options (environment twins in brackets; [kept] = a re-run keeps the previous choice):
#   --profile auto|light|apple|gpu  install profile (default auto)          [AF_PROFILE]
#   --port N                 gateway port (default 8080, next free if busy)  [AF_PORT]
#   --pin VERSION|latest     abstractgateway version (default: install manifest) [AF_PIN]
#   --from PATH|REQUIREMENT  install the gateway from a checkout, wheel or
#                            requirement instead of the pinned release      [AF_FROM]
#   --manifest PATH          read the pin from this install-manifest.json
#   --data-dir DIR           gateway data dir (default: per-OS user data dir) [AF_DATA_DIR] [kept]
#   --with-apps              make sure Node.js >= 18 exists for the npx apps
#                            (uv tool install nodejs-wheel; no admin)
#   --no-console             skip the terminal console (by default it is built with [kept]
#                            cargo: about 600 MB of Rust from rustup when cargo is
#                            missing, and a C compiler); AbstractCode's terminal
#                            client is then built only with a cargo already there
#   --no-code-cli            skip AbstractCode's terminal client (abstractcode; by [kept]
#                            default built with the console's cargo, into the same folder)
#   --no-core-cli            do not put AbstractCore's commands (abstractcore, its [kept]
#                            apps) and abstractvoice, abstractvision, abstractmusic on PATH
#   --with-console, --with-code-cli, --with-core-cli, --with-tray, --no-full
#                            turn back on (off, for --no-full) what a previous run's
#                            option left out (or in)
#   --with-ollama            run Ollama's official installer (may ask for sudo)
#   --with-lmstudio          run LM Studio's headless installer (llmster)
#   --full                   also build the compiled extras (stable-diffusion.cpp, [kept]
#                            echo cancellation) and llama.cpp from source; needs a C compiler
#   --no-tray                skip the tray extra [kept]
#   --no-service             do not start at login (asks nothing); start in background
#   --no-start               install only; do not start (or restart) the gateway
#   --no-open                do not open the browser (on a remote or headless session:
#                            do not offer the terminal console at the end)
#   --ask-wait SECONDS       how long a timed question waits for an answer: start at login,
#                            and the terminal console offer at the end of a remote or
#                            headless install (default 25, at most 25; alias --console-wait)
#   --no-modify-path         do not run `uv tool update-shell`
#   --print, --dry-run       show the plan and commands; change nothing
#   --print-versions         print the pinned versions and exit
#   Start at login is asked whenever a person is at a terminal (/dev/tty, so it
#   also works through curl | sh): Enter = yes, no answer within --ask-wait = the
#   previous install's choice, or no on a first install. Without a terminal
#   (automation) it stays as it was (off on a first install) and the summary says
#   how to turn it on.
#   --interactive            also ask the other choices (building the terminal console;
#                            on --uninstall: delete the data too) and wait for every
#                            answer without a time limit. The double-click installers
#                            pass it.                                  [AF_INTERACTIVE=1]
#   --uninstall [--purge] [--remove-uv]
#                            stop the whole gateway process tree, remove the service
#                            and the uv tools (--purge also deletes your data: the
#                            gateway data dir, its logs and cache, the Assistant's
#                            sessions, AbstractCode's settings; model weights stay;
#                            --remove-uv also removes uv, its Pythons and its
#                            download cache when this installer put uv there)
#   -y, --yes                ask nothing, not even start at login (it stays as it was)
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
AF_GATEWAY_PIN_DEFAULT="0.7.2"
# The AbstractFramework release these pins are (install-manifest.json `framework.version`), and
# the release's other Python packages in the gateway's environment (its `python_packages`,
# minus the gateway itself and the Assistant, a separate app). They go to `uv tool install` as
# constraints, so an install or an upgrade lands on exactly the tested matrix, never on
# whatever newer library satisfies the gateway's floors. test_inventory.sh fails on drift.
AF_FRAMEWORK_VERSION="0.6.2"
AF_PY_MATRIX="abstractcore==2.18.1 AbstractRuntime==0.7.1 abstractagent==0.3.17 abstractskill==0.3.0 AbstractMemory==0.3.0 abstractsemantics==0.0.5 abstractvoice==0.13.0 abstractvision==0.3.30 abstractmusic==0.1.15"
AF_PYTHON="3.12"
AF_NPM_APPS="@abstractframework/flow@0.4.0 @abstractframework/code@0.6.1 @abstractframework/observer@0.2.1 @abstractframework/continuum@0.4.0 @abstractframework/entity@0.3.0"
AF_CRATE_CONSOLE="abstractgateway-console@0.11.1"
AF_CRATE_CODE_CLI="abstractcode@0.7.1"
# The user commands of the gateway's own environment exposed next to `abstractgateway` and
# `abstractgateway-config` (uv tool install --with-executables-from; --no-core-cli leaves them
# out): AbstractCore and its voice, vision and music packages. Not abstractruntime (its one
# entry point is a worker the runtime starts) nor abstractagent (a deprecated stub). uv exposes
# all of a package's executables or none, and refuses the WHOLE install when one of them
# already exists, so af_cli_names lists every name each package declares (tests compare it
# with the packages' pyproject.toml) and a package whose name another program has is left out.
AF_CLI_PACKAGES="abstractcore abstractvoice abstractvision abstractmusic"
af_cli_names() {
    case "$1" in
        abstractcore) echo "abstractcore abstractcore-config abstractcore-chat abstractcore-endpoint summarizer abstractcore-summarizer extractor abstractcore-extractor judge abstractcore-judge intent abstractcore-intent deepsearch abstractcore-deepsearch" ;;
        abstractvoice) echo "abstractvoice abstractvoice-prefetch" ;;
        abstractvision) echo "abstractvision" ;;
        abstractmusic) echo "abstractmusic" ;;
    esac
}
af_cli_about() {  # one line for the summary's command list
    case "$1" in
        abstractcore) echo "AbstractCore: --config, --status, models, engines, serve; also abstractcore-chat (a chat REPL), abstractcore-endpoint and its apps summarizer, extractor, judge, intent, deepsearch" ;;
        abstractvoice) echo "voice in the terminal: a spoken chat, web, tts; abstractvoice-prefetch downloads voice models" ;;
        abstractvision) echo "images in the terminal: cli (generate), download, provider-models" ;;
        abstractmusic) echo "music in the terminal: t2m (text to music)" ;;
    esac
}
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
# Local voice on every profile: Supertonic text-to-speech (ONNX Runtime) and Whisper
# speech-to-text (faster-whisper: CTranslate2, PyAV). Both run on CPU and ship prebuilt wheels
# for Linux (glibc) x86_64/aarch64, macOS 13+ and Windows x64; the apple and gpu profiles already
# carry them. No wheels exist for musl Linux (Alpine) or macOS before 13: skipped there, said so.
AF_WITH_VOICE="abstractvoice[supertonic,stt]"
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
# af_uv_constraints GGUF: the release matrix (when this run installs the release) and the
# llama.cpp wheel pin (GGUF=1), one requirement per line; empty when neither applies.
af_uv_constraints() {
    if [ "$IS_RELEASE" = 1 ]; then for _c in $AF_PY_MATRIX; do echo "$_c"; done; fi
    [ "$1" = 1 ] && echo "llama-cpp-python==$GGUF_PIN"
    return 0
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
# The choices that change what is installed are remembered (bootstrap.env) and kept by a plain
# re-run: empty = not given on this command line (the previous install's choice, else the default).
WITH_APPS=0; OPT_CONSOLE=""; OPT_CODE_CLI=""; OPT_CORE_CLI=""; OPT_TRAY=""; OPT_FULL=""
WITH_OLLAMA=0; WITH_LMSTUDIO=0
NO_SERVICE=0; NO_START=0; NO_OPEN=0; NO_MODIFY_PATH=0
PRINT=0; UNINSTALL=0; PURGE=0; VERBOSE=0; REMOVE_UV=0; ASK_WAIT=25; ASK_NOTHING=0
INTERACTIVE="${AF_INTERACTIVE:-0}"

usage() {
    if [ -f "$0" ] && head -n 3 "$0" 2>/dev/null | grep -q "AbstractFramework bootstrap"; then
        sed -n '2,93p' "$0" | sed 's/^# \{0,1\}//'
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
        --with-console) OPT_CONSOLE=1 ;;   # the default; turns back on what a previous --no-console left out
        --no-console) OPT_CONSOLE=0 ;;
        --with-code-cli) OPT_CODE_CLI=1 ;;
        --no-code-cli) OPT_CODE_CLI=0 ;;
        --with-core-cli) OPT_CORE_CLI=1 ;;
        --no-core-cli) OPT_CORE_CLI=0 ;;
        --with-ollama) WITH_OLLAMA=1 ;;
        --with-lmstudio) WITH_LMSTUDIO=1 ;;
        --full) OPT_FULL=1 ;;
        --no-full) OPT_FULL=0 ;;
        --no-tray) OPT_TRAY=0 ;;
        --with-tray) OPT_TRAY=1 ;;
        --no-service) NO_SERVICE=1 ;;
        --no-start) NO_START=1 ;;
        --no-open) NO_OPEN=1 ;;
        --ask-wait|--console-wait) need_arg "$@"; ASK_WAIT="$2"; shift ;;
        --ask-wait=*|--console-wait=*) ASK_WAIT="${1#*=}" ;;
        --no-modify-path) NO_MODIFY_PATH=1 ;;
        --print|--dry-run|-n) PRINT=1 ;;
        --print-versions)
            echo "framework abstractframework $AF_FRAMEWORK_VERSION"
            echo "pypi abstractgateway $AF_GATEWAY_PIN_DEFAULT"
            for spec in $AF_PY_MATRIX; do echo "pypi ${spec%%==*} ${spec##*==}"; done
            for spec in $AF_NPM_APPS; do echo "npm ${spec%@*} ${spec##*@}"; done
            for spec in $AF_CRATE_CONSOLE $AF_CRATE_CODE_CLI; do echo "crates ${spec%@*} ${spec##*@}"; done
            exit 0 ;;
        --uninstall) UNINSTALL=1 ;;
        --purge) PURGE=1 ;;
        --remove-uv) REMOVE_UV=1 ;;
        --interactive) INTERACTIVE=1 ;;
        -y|--yes) INTERACTIVE=0; ASK_NOTHING=1 ;;
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

# tty_ok: a person can be asked: output goes to a terminal and /dev/tty opens (so it also
# works through `curl | sh`). `true`, not `:`, probes /dev/tty: a failed redirection on the
# special built-in `:` exits dash (Debian/Ubuntu /bin/sh).
tty_ok() { [ -t 1 ] && { true </dev/tty; } 2>/dev/null; }

# ask_timed QUESTION DEFAULT(y|n) WHAT-NO-ANSWER-MEANS: asks on /dev/tty and sets ANSWER to
# y or n, or to "" when nobody answered: no terminal, --print, --yes, or nothing typed within
# --ask-wait seconds (a pseudo-terminal with nobody at it, as in CI or `ssh -t` in a script,
# must never hang the install). Enter = DEFAULT. --interactive waits without a time limit.
ask_timed() {
    ANSWER=""
    [ "$PRINT" = 0 ] && [ "$ASK_NOTHING" = 0 ] && tty_ok || return 0
    _at_old="$(stty -g </dev/tty 2>/dev/null)" || return 0
    trap 'stty "$_at_old" </dev/tty 2>/dev/null; exit 130' INT TERM
    # Keys typed before the question are still buffered: drop them, so only an answer counts.
    stty -icanon -echo min 0 time 0 </dev/tty 2>/dev/null
    dd bs=4096 count=1 </dev/tty >/dev/null 2>&1
    if [ "$INTERACTIVE" = 1 ]; then
        _at_hint="Enter = $([ "$2" = y ] && echo yes || echo no)"
        stty min 1 time 0 </dev/tty 2>/dev/null
    else
        _at_hint="Enter = $([ "$2" = y ] && echo yes || echo no); no answer within $ASK_WAIT s = $3"
        # stty counts tenths of a second, at most 255.
        stty min 0 time "$((ASK_WAIT * 10))" </dev/tty 2>/dev/null
    fi
    printf '  %s?%s %s %s (%s) ' "$C_Y" "$C_0" "$1" "$([ "$2" = y ] && echo '[Y/n]' || echo '[y/N]')" "$_at_hint" >/dev/tty
    while :; do
        _at_k="$(dd bs=1 count=1 </dev/tty 2>/dev/null | od -An -tu1 | tr -d ' ')"
        case "$_at_k" in
            "") break ;;
            10|13) ANSWER="$2"; break ;;
            89|121) ANSWER=y; break ;;
            78|110) ANSWER=n; break ;;
        esac
    done
    stty "$_at_old" </dev/tty 2>/dev/null
    trap - INT TERM
    case "$ANSWER" in y) _at_said=yes ;; n) _at_said=no ;; *) _at_said="(no answer)" ;; esac
    printf '%s\n' "$_at_said" >/dev/tty
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

# The local gateway pointer (described with write_pointer below) names the data dir of the
# install that last wrote it. A re-run without --data-dir keeps a custom data dir that way: the
# pointer's folder is used when it holds this installer's state (bootstrap.env).
POINTER_FILE="$HOME/.abstractframework/gateway.json"
# pointer_data_dir: the data_dir the pointer names (any JSON layout); empty when the file is
# absent or names none this shell can read.
pointer_data_dir() {
    [ -f "$POINTER_FILE" ] && [ -r "$POINTER_FILE" ] || return 0
    tr '\n\r' '  ' <"$POINTER_FILE" 2>/dev/null \
        | sed -nE 's/.*"data_dir"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' | head -n 1 \
        | sed 's/\\"/"/g; s/\\\\/\\/g'
}
DATA_DIR_CUSTOM=0; [ -n "$DATA_DIR" ] && DATA_DIR_CUSTOM=1
DATA_DIR_KEPT=0
if [ -z "$DATA_DIR" ]; then
    if [ "$OS_ID" = macos ]; then DATA_DIR="$HOME/Library/Application Support/AbstractGateway"
    else DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/abstractgateway"; fi
    _pd="$(pointer_data_dir)"
    _def_real="$(CDPATH='' cd -- "$DATA_DIR" 2>/dev/null && pwd -P || echo "$DATA_DIR")"
    if [ -n "$_pd" ] && [ "$_pd" != "$DATA_DIR" ] && [ "$_pd" != "$_def_real" ] && [ -f "$_pd/bootstrap.env" ]; then
        DATA_DIR="$_pd"; DATA_DIR_CUSTOM=1; DATA_DIR_KEPT=1
    fi
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

# ---------------------------------------------------------------------------
# The local gateway pointer, ~/.abstractframework/gateway.json (root backlog 0943):
# where this computer's gateway listens, for the clients that cannot ask Python (the
# terminal consoles, the browser apps, the Assistant .app). The address only: never a
# token, a pid or liveness. The installer owns the install it just made and is the one
# writer that always knows a custom --data-dir, so it writes the pointer for this install
# unconditionally after the health check (replacing one that names another data dir: the
# user just installed or re-ran this one), atomically, mode 0600. `abstractgateway serve`
# rewrites it once bound, but only under its ownership rule (abstractgateway/
# gateway_pointer.py: absent + default data dir, or naming its own data dir), so a test
# gateway never takes it over. --uninstall deletes it only when it names this install's
# data dir (paths compared resolved).
# ---------------------------------------------------------------------------
real_dir() { (CDPATH='' cd -- "$1" 2>/dev/null && pwd -P) || abs_path "$1"; }
json_str() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
# write_pointer: after the health check (the port is the one that answered), always.
write_pointer() {
    _pd="$(pointer_data_dir)"
    if [ -n "$_pd" ] && [ "$(real_dir "$_pd")" != "$(real_dir "$DATA_DIR")" ]; then
        info "the gateway pointer named the gateway with data directory $_pd; it now names this install"
    fi
    _ptmp="$POINTER_FILE.$$.tmp"
    if mkdir -p "$(dirname "$POINTER_FILE")" 2>/dev/null \
        && ( umask 077; printf '{\n  "data_dir": "%s",\n  "port": %s,\n  "schema": 1,\n  "updated_at": "%s",\n  "url": "%s",\n  "written_by": "installer"\n}\n' \
               "$(json_str "$(real_dir "$DATA_DIR")")" "$PORT" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$BASE_URL" >"$_ptmp" ) 2>/dev/null \
        && chmod 600 "$_ptmp" && mv -f "$_ptmp" "$POINTER_FILE"; then
        ok "gateway pointer: $POINTER_FILE -> $BASE_URL (the consoles and apps on this computer find the gateway there)"
    else
        rm -f "$_ptmp" 2>/dev/null
        warn "could not write the gateway pointer $POINTER_FILE; clients take --gateway-url $BASE_URL"
    fi
    return 0
}
# remove_pointer (--uninstall): only a pointer that names this install's data dir.
remove_pointer() {
    _pd="$(pointer_data_dir)"
    if [ -z "$_pd" ]; then
        [ -e "$POINTER_FILE" ] && info "kept $POINTER_FILE: it names no data directory"
        return 0
    fi
    if [ "$(real_dir "$_pd")" = "$(real_dir "$DATA_DIR")" ]; then
        run "remove the gateway pointer" rm -f "$POINTER_FILE"
    else
        info "kept the gateway pointer $POINTER_FILE: it belongs to the gateway with data directory $_pd"
    fi
}

# Previous run state (port, service mode, whether we installed Node, the release, the choices).
ST_PORT=""; ST_MODE=""; ST_NODE_WHEEL=""; ST_PROFILE=""; ST_UV_BY_US=""; ST_RUST_BY_US=""; ST_VOICE=""
ST_FRAMEWORK=""; ST_CONSOLE=""; ST_CODE_CLI=""; ST_CORE_CLI=""; ST_TRAY=""; ST_FULL=""
st_get() { sed -n "s/^$1=//p" "$STATE_FILE" | tail -n 1; }
if [ -f "$STATE_FILE" ]; then
    ST_FRAMEWORK="$(st_get FRAMEWORK_VERSION)"
    ST_CONSOLE="$(st_get CONSOLE)"; ST_CODE_CLI="$(st_get CODE_CLI)"; ST_CORE_CLI="$(st_get CORE_CLI)"
    ST_TRAY="$(st_get TRAY)"; ST_FULL="$(st_get FULL)"
    ST_RUST_BY_US="$(sed -n 's/^RUST_BY_INSTALLER=//p' "$STATE_FILE" | tail -n 1)"
    ST_VOICE="$(sed -n 's/^VOICE_SPEC=//p' "$STATE_FILE" | tail -n 1)"
    ST_UV_BY_US="$(sed -n 's/^UV_BY_INSTALLER=//p' "$STATE_FILE" | tail -n 1)"
    ST_PORT="$(sed -n 's/^PORT=//p' "$STATE_FILE" | tail -n 1)"
    ST_MODE="$(sed -n 's/^MODE=//p' "$STATE_FILE" | tail -n 1)"
    ST_NODE_WHEEL="$(sed -n 's/^NODE_WHEEL=//p' "$STATE_FILE" | tail -n 1)"
    ST_PROFILE="$(sed -n 's/^PROFILE=//p' "$STATE_FILE" | tail -n 1)"
fi
# The choices a re-run keeps: this command line's, else the previous install's, else the default.
# KEPT lists the ones taken from the previous install that differ from the default.
KEPT=""
[ "$DATA_DIR_KEPT" = 1 ] && KEPT="--data-dir $DATA_DIR"
opt_choice() {  # opt_choice GIVEN RECORDED DEFAULT FLAG-WHEN-OFF FLAG-WHEN-ON: sets CHOICE (0|1)
    case "$1" in 0|1) CHOICE="$1"; return 0 ;; esac
    case "$2" in 0|1) CHOICE="$2" ;; *) CHOICE="$3"; return 0 ;; esac
    [ "$2" = "$3" ] && return 0
    if [ "$2" = 0 ]; then KEPT="${KEPT:+$KEPT, }$4"; else KEPT="${KEPT:+$KEPT, }$5"; fi
}
# resolve_choices: runs once the previous install is known (below, after its detection).
resolve_choices() {
    opt_choice "$OPT_CONSOLE" "$ST_CONSOLE" 1 --no-console --with-console; WITH_CONSOLE="$CHOICE"
    opt_choice "$OPT_CODE_CLI" "$ST_CODE_CLI" 1 --no-code-cli --with-code-cli; WITH_CODE_CLI="$CHOICE"
    opt_choice "$OPT_CORE_CLI" "$ST_CORE_CLI" 1 --no-core-cli --with-core-cli; WITH_CORE_CLI="$CHOICE"
    opt_choice "$OPT_TRAY" "$ST_TRAY" 1 --no-tray --with-tray; WITH_TRAY="$CHOICE"
    opt_choice "$OPT_FULL" "$ST_FULL" 0 --no-full --full; FULL="$CHOICE"
    NO_TRAY=$((1 - WITH_TRAY))
}
WITH_CONSOLE=1; WITH_CODE_CLI=1; WITH_CORE_CLI=1; WITH_TRAY=1; FULL=0; NO_TRAY=0

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
# console_bin: where the terminal console and AbstractCode's terminal client go. cargo builds
# both with --root <parent of the uv tool bin dir>, so they land next to `abstractgateway`; a
# bin dir not named .../bin falls back to cargo's own ~/.cargo/bin.
CONSOLE_NAME="${AF_CRATE_CONSOLE%@*}"; CONSOLE_PIN="${AF_CRATE_CONSOLE##*@}"
CODE_NAME="${AF_CRATE_CODE_CLI%@*}"; CODE_PIN="${AF_CRATE_CODE_CLI##*@}"
CRATE_ROOT=""; CONSOLE_BIN=""; CODE_ROOT=""; CODE_BIN=""
console_bin() {
    case "$TOOL_BIN" in
        */bin) CRATE_ROOT="${TOOL_BIN%/bin}" ;;
        *) CRATE_ROOT="" ;;
    esac
    CONSOLE_BIN="${CRATE_ROOT:-${CARGO_HOME:-$HOME/.cargo}}/bin/$CONSOLE_NAME"
    # AbstractCode's terminal client: CODE_ROOT (cargo --root; "" = cargo's own ~/.cargo) is the
    # ONE place that decides where it goes; build, summary and uninstall all follow it.
    CODE_ROOT="$CRATE_ROOT"
    CODE_BIN="${CODE_ROOT:-${CARGO_HOME:-$HOME/.cargo}}/bin/$CODE_NAME"
}
# crate_installed BIN NAME PIN: BIN answers --version with that crate at that pin.
crate_installed() { [ "$("$1" --version 2>/dev/null)" = "$2 $3" ]; }
console_installed() { crate_installed "$CONSOLE_BIN" "$CONSOLE_NAME" "$CONSOLE_PIN"; }
# version_at_least A B: dotted numeric version A >= B (X.Y.Z; a missing part counts as 0).
version_at_least() {
    awk -v a="$1" -v b="$2" 'BEGIN {
        if (a !~ /^[0-9]+(\.[0-9]+)*$/) exit 1
        na = split(a, x, "."); nb = split(b, y, "."); n = na > nb ? na : nb
        for (i = 1; i <= n; i++) { if (x[i] + 0 > y[i] + 0) exit 0; if (x[i] + 0 < y[i] + 0) exit 1 }
        exit 0 }'
}
# code_installed: abstractcode at the pin OR LATER. The gateway's Apps page updates it in place in
# the same folder, so a re-run must never downgrade it to the pin. Sets CODE_HAVE_V.
CODE_HAVE_V=""
code_installed() {
    _cv="$("$CODE_BIN" --version 2>/dev/null)" || return 1
    case "$_cv" in "$CODE_NAME "*) CODE_HAVE_V="${_cv#"$CODE_NAME "}" ;; *) return 1 ;; esac
    version_at_least "$CODE_HAVE_V" "$CODE_PIN"
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
    # The terminal console and AbstractCode's terminal client this installer built (see
    # console_bin). The uv tool's exposed commands went with `uv tool uninstall` above.
    console_bin
    uninstall_crate() {  # uninstall_crate NAME BIN ROOT "what it is" "step title"
        _uc_name="$1"; _uc_bin="$2"; _uc_root="$3"; _uc_what="$4"
        [ -e "$_uc_bin" ] || return 0
        step "$5"
        if find_cargo && grep -qs "^\"$_uc_name " "${_uc_root:-${CARGO_HOME:-$HOME/.cargo}}/.crates.toml"; then
            set -- "$CARGO" uninstall
            [ -n "$_uc_root" ] && set -- "$@" --root "$_uc_root"
            RUN_SOFT=1 run "uninstall $_uc_what" "$@" "$_uc_name"
        fi
        [ "$PRINT" = 0 ] && [ ! -e "$_uc_bin" ] || run "remove $_uc_what" rm -f "$_uc_bin"
    }
    uninstall_crate "$CONSOLE_NAME" "$CONSOLE_BIN" "$CRATE_ROOT" "the terminal console" "Terminal console"
    uninstall_crate "$CODE_NAME" "$CODE_BIN" "$CODE_ROOT" "AbstractCode's terminal client" "AbstractCode terminal client"
    # Gateways before 0.7.1 installed their terminal app into <data>/apps/bin (not on PATH). The
    # data dir stays without --purge, so remove what the gateway put there: its installable terminal
    # apps (apps_manager TUI_BY_APP: abstractcode; it never installs the console), and the folder
    # only when that leaves it empty.
    _stale="$DATA_DIR/apps/bin"
    for _t in abstractcode; do
        [ -e "$_stale/$_t" ] || continue
        run "remove the terminal app an older gateway installed ($_t)" rm -f "$_stale/$_t"
    done
    [ "$PRINT" = 1 ] || rmdir "$_stale" 2>/dev/null || true
    [ "$ST_RUST_BY_US" = 1 ] && info "kept: Rust, which the installer added for the terminal console and AbstractCode's terminal client (remove it with: ${CARGO_HOME:-$HOME/.cargo}/bin/rustup self uninstall)"
    step "Data"
    # Before the data dir goes (--purge): the pointer is matched against its resolved path.
    remove_pointer
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
        info "kept: model weights and shared caches (~/.cache/huggingface, ~/.abstractcore, ~/.abstractframework apart from its gateway.json, ~/.cache/abstractvoice, LM Studio and Ollama models)"
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

# ---------------------------------------------------------------------------
# An existing install: say what is there and what this run brings. The same line
# installs, upgrades (keeping the profile, port, start at login, data dir and the
# choices above) and repairs; the summary lists what changed.
# ---------------------------------------------------------------------------
# IS_RELEASE: this run installs the release these pins are (not --pin, --from or --manifest
# with another gateway), so the release matrix applies and bootstrap.env records its version.
IS_RELEASE=0; { [ -z "$FROM" ] && [ "$PIN" = "$AF_GATEWAY_PIN_DEFAULT" ]; } && IS_RELEASE=1
find_uv >/dev/null 2>&1 || true; tool_bin; tool_venv; console_bin
PREV_GW=""
[ -n "$UV" ] && PREV_GW="$("$UV" tool list 2>/dev/null | sed -n 's/^abstractgateway v\([^ ]*\).*/\1/p' | head -n 1)"
if [ "$IS_RELEASE" = 1 ]; then TARGET="AbstractFramework $AF_FRAMEWORK_VERSION"
elif [ -n "$FROM" ]; then TARGET="abstractgateway from $FROM (--from)"
elif [ "$PIN" = latest ]; then TARGET="the newest abstractgateway (--pin latest)"
else TARGET="abstractgateway $PIN ($PIN_SOURCE)"; fi
if [ ! -f "$STATE_FILE" ] && [ -z "$PREV_GW" ]; then
    ACTION=install; FOUND_LINE="No AbstractFramework install found: installing $TARGET"
elif [ "$IS_RELEASE" = 1 ] && [ "$ST_FRAMEWORK" = "$AF_FRAMEWORK_VERSION" ]; then
    ACTION=check; FOUND_LINE="AbstractFramework $ST_FRAMEWORK found: already up to date (every part is checked, and repaired if needed)"
elif [ -n "$ST_FRAMEWORK" ]; then
    ACTION=upgrade; FOUND_LINE="AbstractFramework $ST_FRAMEWORK found: upgrading to $TARGET"
elif [ -f "$STATE_FILE" ]; then
    ACTION=upgrade; FOUND_LINE="AbstractFramework found (abstractgateway ${PREV_GW:-not installed}; its release was not recorded): upgrading to $TARGET"
else
    ACTION=upgrade; FOUND_LINE="abstractgateway $PREV_GW found (a uv tool this installer has no record of): upgrading to $TARGET"
fi
# env_snapshot: "name==version" lines (names lower-cased, _ as -) of the gateway's uv tool
# environment, plus the two crates this installer builds; the summary diffs two of them.
env_snapshot() {
    [ -n "$UV" ] && [ -x "$UV" ] && "$UV" pip freeze --python "$TOOL_VENV" 2>/dev/null \
        | tr 'A-Z_' 'a-z-' | sed -n 's/^\([a-z0-9.-]*\)==\([^ ;]*\).*$/\1==\2/p' | sort
    return 0
}
crate_snapshot() {
    for _cs in "$CONSOLE_BIN" "$CODE_BIN"; do
        _cv="$("$_cs" --version 2>/dev/null | head -n 1)" || continue
        case "$_cv" in "$CONSOLE_NAME "*|"$CODE_NAME "*) echo "${_cv%% *}==${_cv#* }" ;; esac
    done
    return 0
}
ENV_BEFORE=""; CRATES_BEFORE=""
if [ "$PRINT" = 0 ] && [ "$ACTION" != install ]; then ENV_BEFORE="$(env_snapshot)"; CRATES_BEFORE="$(crate_snapshot)"; fi

# An install made before AbstractFramework 0.6.2 recorded none of the choices a re-run keeps
# (bootstrap.env has no CONSOLE, CODE_CLI, CORE_CLI, TRAY or FULL). Each missing one is read from
# what that install left on disk, so its first upgrade keeps them too; the new bootstrap.env then
# records them, only while that install's gateway is still there (the uv tool). (A custom
# --data-dir is found through the gateway pointer, above.)
# The terminal console and abstractcode: present where this installer builds them (next to the
# gateway's commands), or in cargo's own bin folder (installers before 0.6.1).
# The library commands: the uv receipt's entrypoints `from = "abstractcore"` (--with-executables-from).
# The tray: the tray extra in the receipt's gateway requirement (else the recorded GATEWAY_SPEC);
# without it, off only where the installer would have added it (macOS, or a display).
# --full: uv-overrides.txt without the compiled extras' "never" lines (else the tool environment
# holds one of them).
INFERRED=""
if [ -f "$STATE_FILE" ] && [ -n "$PREV_GW" ]; then
    _cargo_bin="${CARGO_HOME:-$HOME/.cargo}/bin"
    _rcpt="$TOOL_VENV/uv-receipt.toml"; [ -f "$_rcpt" ] || _rcpt="$TOOL_VENV2/uv-receipt.toml"
    [ -f "$_rcpt" ] || _rcpt=""
    if [ -z "$ST_CONSOLE" ]; then
        if [ -x "$CONSOLE_BIN" ] || [ -x "$_cargo_bin/$CONSOLE_NAME" ]; then ST_CONSOLE=1; else ST_CONSOLE=0; fi
        INFERRED="${INFERRED:+$INFERRED, }terminal console $([ "$ST_CONSOLE" = 1 ] && echo present || echo absent)"
    fi
    if [ -z "$ST_CODE_CLI" ]; then
        if [ -x "$CODE_BIN" ] || [ -x "$_cargo_bin/$CODE_NAME" ]; then ST_CODE_CLI=1; else ST_CODE_CLI=0; fi
        INFERRED="${INFERRED:+$INFERRED, }abstractcode $([ "$ST_CODE_CLI" = 1 ] && echo present || echo absent)"
    fi
    if [ -z "$ST_CORE_CLI" ] && [ -n "$_rcpt" ]; then
        if grep -q 'from = "abstractcore"' "$_rcpt"; then ST_CORE_CLI=1; else ST_CORE_CLI=0; fi
        INFERRED="${INFERRED:+$INFERRED, }library commands $([ "$ST_CORE_CLI" = 1 ] && echo exposed || echo not exposed)"
    fi
    if [ -z "$ST_TRAY" ]; then
        _gw_req=""
        [ -n "$_rcpt" ] && _gw_req="$(grep -o '{ *name = "abstractgateway"[^}]*}' "$_rcpt" | head -n 1)"
        [ -n "$_gw_req" ] || _gw_req="$([ -f "$STATE_FILE" ] && st_get GATEWAY_SPEC)"
        if [ -n "$_gw_req" ]; then
            if printf '%s' "$_gw_req" | grep -q 'tray'; then ST_TRAY=1
            elif [ "$OS_ID" = macos ] || [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then ST_TRAY=0; fi
            [ -n "$ST_TRAY" ] && INFERRED="${INFERRED:+$INFERRED, }tray extra $([ "$ST_TRAY" = 1 ] && echo installed || echo not installed)"
        fi
    fi
    if [ -z "$ST_FULL" ]; then
        _first_extra="${AF_COMPILED_EXTRAS%% *}"
        if [ -f "$DATA_DIR/uv-overrides.txt" ]; then
            if grep -q "^$_first_extra; sys_platform == 'never'" "$DATA_DIR/uv-overrides.txt"; then ST_FULL=0; else ST_FULL=1; fi
        else
            ST_FULL=0
            for _p in $AF_COMPILED_EXTRAS; do env_snapshot | grep -q "^$_p==" && ST_FULL=1; done
        fi
        INFERRED="${INFERRED:+$INFERRED, }compiled extras $([ "$ST_FULL" = 1 ] && echo "built (--full)" || echo "not built")"
    fi
fi
resolve_choices

printf '%s%s%s\n' "$C_B" "$FOUND_LINE" "$C_0"
[ -n "$INFERRED" ] && info "the previous install recorded no options (before AbstractFramework 0.6.2): read from disk: $INFERRED"
[ -n "$KEPT" ] && info "kept from the previous install: $KEPT (give the opposite option to change it)"

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

# Local voice (Supertonic + Whisper): see AF_WITH_VOICE at the top.
VOICE_SPEC="$AF_WITH_VOICE"; VOICE_RESULT="Supertonic (text-to-speech) and Whisper (speech-to-text), local on CPU"
if [ "$OS_ID" = linux ] && ldd --version 2>&1 | grep -qi musl; then
    VOICE_SPEC=""; VOICE_RESULT="skipped: ONNX Runtime and CTranslate2 publish no wheels for musl Linux (Alpine)"
elif [ "$OS_ID" = macos ] && [ "$MACOS_MAJOR" -lt 13 ] 2>/dev/null; then
    VOICE_SPEC=""; VOICE_RESULT="skipped: ONNX Runtime publishes no wheels for macOS $MACOS_VERSION (13 or later needed)"
fi
[ -n "$VOICE_SPEC" ] || warn "local voice $VOICE_RESULT"
VOICE_WANTED="$VOICE_SPEC"

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
# Start at login as the previous install left it (y, n, or empty on a first install): the
# login item's own state when the installed gateway reports it (the consoles and the tray
# have a switch for it), else the installer's state file.
LOGIN_WAS=""
case "$ST_MODE" in service) LOGIN_WAS=y ;; background) LOGIN_WAS=n ;; esac
if [ -n "$ST_MODE" ]; then
    find_uv >/dev/null 2>&1 || true; tool_bin
    if gateway_supports service; then
        _svc="$("$TOOL_BIN/abstractgateway" service status --json --data-dir "$DATA_DIR" 2>/dev/null | sed -n 's/^  "state": "\([a-z]*\)".*/\1/p' | head -n 1)" || _svc=""
        case "$_svc" in on) LOGIN_WAS=y ;; off) LOGIN_WAS=n ;; esac
    fi
fi
REUSE_RUNNING=0
# PORT_HELD=1: --no-start, and this install's recorded port is taken by a process this installer
# does not recognise as its own (a gateway started by hand, or another program). Nothing starts,
# so the recorded port is kept: moving it would point the next start at a different port.
PORT_HELD=0
if [ -z "$PORT" ]; then PORT="${ST_PORT:-8080}"; PORT_EXPLICIT=0; else PORT_EXPLICIT=1; fi
case "$PORT" in ''|*[!0-9]*) die "--port must be a number (got '$PORT')" ;; esac
case "$ASK_WAIT" in ''|*[!0-9]*) die "--ask-wait must be a number of seconds (got '$ASK_WAIT')" ;; esac
[ "$ASK_WAIT" -le 25 ] || ASK_WAIT=25
if port_busy "$PORT"; then
    if [ "$PORT" = "$ST_PORT" ] && { pid_alive || { [ "$LOGIN_WAS" = y ] && is_our_gateway "$PORT"; }; }; then
        REUSE_RUNNING=1
        ok "port $PORT: this install's gateway is already running (it will be restarted if the package changes)"
    elif [ "$NO_START" = 1 ] && [ -n "$ST_PORT" ] && [ "$PORT" = "$ST_PORT" ]; then
        PORT_HELD=1
        info "port $PORT (this install's) is in use by a process this installer did not start; kept (--no-start starts nothing)"
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

# Start at login: asked here, before anything is downloaded, so the user answers once and
# can walk away. Asked whenever a person is at a terminal; Enter = yes on a first install,
# the previous choice on a re-run. Nobody to ask (automation, --yes, no answer in time):
# a re-run keeps the previous choice, a first install leaves it off and the summary says
# how to turn it on.
SERVICE_POSSIBLE=0
{ [ "$OS_ID" = macos ] || [ "$SYSTEMD_USER" = 1 ]; } && SERVICE_POSSIBLE=1
if [ "$NO_START" = 0 ] && [ "$NO_SERVICE" = 0 ] && [ "$SERVICE_POSSIBLE" = 1 ]; then
    if [ -n "$LOGIN_WAS" ]; then _lnone="$([ "$LOGIN_WAS" = y ] && echo 'yes, as now' || echo 'no, as now')"; else _lnone=no; fi
    ask_timed "Start AbstractFramework automatically when you log in? (a per-user login item, no admin; the uninstaller removes it)" "${LOGIN_WAS:-y}" "$_lnone"
    _lans="$ANSWER"
    if [ -n "$_lans" ]; then _lwhy="your answer"
    elif [ -n "$LOGIN_WAS" ]; then _lans="$LOGIN_WAS"; _lwhy="kept from the previous install"
    elif [ "$ASK_NOTHING" = 1 ]; then _lans=n; _lwhy="--yes: nothing is asked, a first install leaves it off"
    elif ! tty_ok; then _lans=n; _lwhy="no terminal to ask on, so a first install leaves it off"
    elif [ "$PRINT" = 1 ]; then _lans=y; _lwhy="--print: the install asks on this terminal, Enter = yes"
    else _lans=n; _lwhy="no answer within $ASK_WAIT s, so a first install leaves it off"; fi
    if [ "$_lans" = y ]; then
        ok "start at login: yes ($_lwhy; $([ "$OS_ID" = macos ] && echo "LaunchAgent ~/Library/LaunchAgents/ai.abstractframework.gateway.plist" || echo "systemd --user unit abstractgateway.service"); turn it off with the Start at login switch in either console, or re-run with --no-service)"
    else
        NO_SERVICE=1
        ok "start at login: no ($_lwhy; the gateway starts now in the background; the summary says how to turn it on)"
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
        if [ -n "$(af_uv_constraints "$_gguf")" ]; then
            info "$DATA_DIR/uv-constraints.txt:$([ "$IS_RELEASE" = 1 ] && echo " the AbstractFramework $AF_FRAMEWORK_VERSION release matrix (exact versions)")"
            af_uv_constraints "$_gguf" | sed 's/^/      /'
        fi
    else
        af_uv_overrides "$_gguf" >"$DATA_DIR/uv-overrides.txt"
        af_uv_constraints "$_gguf" >"$DATA_DIR/uv-constraints.txt"
    fi
    set -- "$UV" tool install --python "$AF_PYTHON" --with "$AF_WITH_WHEELS"
    [ -n "$VOICE_SPEC" ] && set -- "$@" --with "$VOICE_SPEC"
    if [ "$_gguf" = 1 ]; then set -- "$@" --with "llama-cpp-python==$GGUF_PIN"
    elif [ "$FULL" = 1 ]; then set -- "$@" --with llama-cpp-python; fi
    [ -n "$(af_uv_constraints "$_gguf")" ] && set -- "$@" --constraints uv-constraints.txt
    [ "$_gguf" = 1 ] && set -- "$@" --find-links "$GGUF_LINKS"
    set -- "$@" --overrides uv-overrides.txt
    for _p in $(af_no_build_packages); do set -- "$@" --no-build-package "$_p"; done
    for _p in $CLI_FROM; do set -- "$@" --with-executables-from "$_p"; done
    { [ -n "$FROM" ] || [ "$REINSTALL" = 1 ]; } && set -- "$@" --reinstall
    # --pin latest: re-resolve to the newest releases. Without --upgrade, uv keeps every
    # package already installed that still satisfies the requirement, so a re-run over a
    # pinned install would change nothing. (`uv tool upgrade` cannot do it either: it keeps
    # the `==<pin>` the first install recorded and answers "Nothing to upgrade".)
    [ "$PIN" = latest ] && [ -z "$FROM" ] && set -- "$@" --upgrade
    _cwd="$(pwd)"
    RUN_SHOW="cd $(q "$DATA_DIR") && $(show_cmd "$@" "$GW_SPEC")"
    [ "$PRINT" = 1 ] || cd "$DATA_DIR"
    RUN_SOFT="$_gsoft" run "install abstractgateway$([ "$_gguf" = 1 ] && echo " with the llama.cpp $GGUF_KIND wheel")" "$@" "$GW_SPEC"
    [ "$PRINT" = 1 ] || cd "$_cwd" 2>/dev/null || cd "$HOME"
    return "$RUN_RC"
}
# install_gateway_voice GGUF SOFT: install_gateway with local voice when it is wanted. Voice
# is never what fails an install: where its wheels are missing (e.g. glibc older than 2.28) the
# same install is retried without it and the summary says so.
install_gateway_voice() {
    if [ -n "$VOICE_WANTED" ]; then
        VOICE_SPEC="$VOICE_WANTED"
        if install_gateway "$1" 1; then
            VOICE_RESULT="Supertonic (text-to-speech) and Whisper (speech-to-text), local on CPU"
            return 0
        fi
        warn "local voice (Supertonic, Whisper) did not install on this system: retrying without it"
        VOICE_SPEC=""; VOICE_RESULT="skipped: its packages did not install on this system (see $LOG_FILE)"
    fi
    install_gateway "$1" "$2"
}
# The packages whose commands this install exposes (AF_CLI_PACKAGES): each one whose names are
# all free in the tool bin dir, or already the gateway tool's own (a re-run). A name that another
# program has (a file, or another uv tool's command) would make uv refuse the whole install, so
# that package is left out and the summary says which file is in the way.
CLI_FROM=""; CLI_TAKEN=""
if [ "$WITH_CORE_CLI" = 1 ]; then
    _ours=""
    [ -n "$UV" ] && [ -x "$UV" ] && _ours="$("$UV" tool list 2>/dev/null | awk '/^[^ -]/ { t = $1 } t == "abstractgateway" && $1 == "-" { print $2 }')"
    for _p in $AF_CLI_PACKAGES; do
        _taken=""
        for _n in $(af_cli_names "$_p"); do
            if [ -e "$TOOL_BIN/$_n" ] || [ -L "$TOOL_BIN/$_n" ]; then
                printf '%s\n' "$_ours" | grep -qx "$_n" || { _taken="$TOOL_BIN/$_n"; break; }
            fi
        done
        if [ -z "$_taken" ]; then CLI_FROM="${CLI_FROM:+$CLI_FROM }$_p"
        else
            CLI_TAKEN="${CLI_TAKEN:+$CLI_TAKEN }$_p"
            warn "$_p commands not exposed: $_taken already exists (another program's); remove it and run the installer again to add them"
        fi
    done
fi
GGUF_RESULT=""
REINSTALL=0
if [ "$FULL" = 1 ]; then
    install_gateway_voice 0 0
    GGUF_RESULT="llama-cpp-python built from source (--full)"
elif [ -n "$GGUF_PIN" ]; then
    [ "$PRINT" = 1 ] && info "llama.cpp GGUF: llama-cpp-python $GGUF_PIN, $GGUF_KIND wheel from $GGUF_LINKS (if this install fails, it is retried without it)"
    if install_gateway_voice 1 1; then
        GGUF_RESULT="llama-cpp-python $GGUF_PIN ($GGUF_KIND wheel from $GGUF_LINKS)"
    else
        warn "$AF_GGUF_SKIPPED"
        install_gateway_voice 0 0
        GGUF_RESULT="skipped (the prebuilt $GGUF_KIND wheel did not install; see $LOG_FILE)"
    fi
else
    warn "$AF_GGUF_SKIPPED"
    install_gateway_voice 0 0
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
# CHANGED: the running gateway must be restarted. Any package of its environment that moved
# counts (a library-only release keeps the gateway's version).
ENV_AFTER=""
[ "$PRINT" = 0 ] && ENV_AFTER="$(env_snapshot)"
CHANGED=0
if [ "$BEFORE" != "$AFTER" ] || [ -n "$FROM" ] || [ "$REINSTALL" = 1 ] || { [ -n "$ST_SPEC" ] && [ "$ST_SPEC" != "$GW_SPEC" ]; } \
    || { [ -n "$BEFORE" ] && [ "$ST_VOICE" != "$VOICE_SPEC" ]; } || [ "$ENV_BEFORE" != "$ENV_AFTER" ]; then CHANGED=1; fi
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
    info "the browser apps open through the gateway: in the console's Apps page, Install, then Open (each at $BASE_URL/apps/<app>/)"
    info "advanced: run one on its own, outside the gateway (first launch downloads it):"
    for spec in $AF_NPM_APPS; do
        printf '      npx -y %s --gateway-url %s\n' "$spec" "$BASE_URL"
    done
fi

# Terminal console and AbstractCode's terminal client: crates.io publishes no prebuilt binary,
# so cargo builds both, into the same folder (see console_bin). When there is no cargo, or only
# one older than the crates' Rust 1.87 (the distro packages are), Rust comes from rustup:
# user-scoped (~/.rustup, ~/.cargo), shell profiles untouched, its cargo used by absolute path;
# only for the terminal console (--no-console adds no Rust: AbstractCode's client is then built
# only with a cargo already there). The TLS stack (ring) compiles C, so it needs a C compiler.
# A failure here never fails the install: the web console does everything the terminal one
# does, and the gateway serves AbstractCode's browser client at /apps/code/.
CONSOLE_OK=0; CONSOLE_WHY="skipped with --no-console"
CODE_OK=0; CODE_WHY="skipped with --no-code-cli"
RUST_BY_US="${ST_RUST_BY_US:-0}"
RUSTUP_CARGO="${CARGO_HOME:-$HOME/.cargo}/bin/cargo"
console_bin
cargo_minor() { "$1" --version 2>/dev/null | awk '{ split($2, v, "."); print v[1] * 1000 + v[2] }'; }
CONSOLE_HAVE=0; CODE_HAVE=0
if [ "$PRINT" = 0 ]; then
    console_installed && CONSOLE_HAVE=1
    code_installed && CODE_HAVE=1
fi
# What still needs building, for the messages below.
RUST_FOR=""
[ "$WITH_CONSOLE" = 1 ] && [ "$CONSOLE_HAVE" = 0 ] && RUST_FOR="the terminal console"
[ "$WITH_CODE_CLI" = 1 ] && [ "$CODE_HAVE" = 0 ] && RUST_FOR="${RUST_FOR:+$RUST_FOR and }AbstractCode's terminal client"
# rust_cargo: CARGO = a cargo of Rust 1.87 or later, or RUST_WHY = why there is none. Decided
# once for both crates, so each problem is reported once.
RUST_DONE=0; RUST_WHY=""
rust_cargo() {
    if [ "$RUST_DONE" = 1 ]; then [ -n "$CARGO" ]; return; fi
    RUST_DONE=1; CARGO=""
    if [ "$HAS_CC" = 0 ]; then
        RUST_WHY="building it needs a C compiler: $([ "$OS_ID" = macos ] && echo 'xcode-select --install' || echo 'sudo apt-get install -y build-essential (Debian/Ubuntu)')"
        warn "$RUST_FOR skipped: $RUST_WHY; then run the installer again"
        return 1
    fi
    find_cargo || true
    if [ -n "$CARGO" ] && [ "$PRINT" = 0 ] && [ "$(cargo_minor "$CARGO")" -lt 1087 ] 2>/dev/null; then
        _rust_old="$("$CARGO" --version 2>/dev/null | awk '{print $2}')"
        if [ "$WITH_CONSOLE" = 0 ]; then
            RUST_WHY="skipped with --no-console: it adds no Rust, and $CARGO is $_rust_old (1.87 or later needed)"
            CARGO=""
        elif [ -x "$(dirname "$CARGO")/rustup" ]; then
            RUST_WHY="it needs Rust 1.87 or later and $CARGO is $_rust_old; update it (rustup update stable)"
            warn "$RUST_FOR skipped: $RUST_WHY, then run the installer again"
            CARGO=""
        else
            info "cargo $_rust_old ($CARGO) is older than the Rust 1.87 $RUST_FOR needs: adding a current Rust with rustup"
            CARGO=""; [ -x "$RUSTUP_CARGO" ] && [ "$(cargo_minor "$RUSTUP_CARGO")" -ge 1087 ] 2>/dev/null && CARGO="$RUSTUP_CARGO"
        fi
    fi
    if [ -z "$CARGO" ] && [ -z "$RUST_WHY" ]; then
        if [ "$WITH_CONSOLE" = 0 ]; then
            RUST_WHY="skipped with --no-console: it adds no Rust, and no cargo was found"
        elif ask_yes "Build $RUST_FOR? It needs Rust: about 600 MB in ~/.rustup and ~/.cargo, no admin, a few minutes" y; then
            info "installing Rust with rustup into ~/.rustup and ~/.cargo (no admin, shell profile untouched)"
            RUN_SOFT=1 run_sh "install Rust (rustup)" "$DL https://sh.rustup.rs | sh -s -- -y --profile minimal --no-modify-path"
            if [ "$PRINT" = 1 ]; then CARGO="$RUSTUP_CARGO"
            elif [ -x "$RUSTUP_CARGO" ]; then CARGO="$RUSTUP_CARGO"; RUST_BY_US=1
            else RUST_WHY="Rust could not be installed (see $LOG_FILE)"; warn "$RUST_FOR skipped: $RUST_WHY"; fi
        else
            RUST_WHY="you chose not to install Rust; re-run the installer to add it"
        fi
    fi
    [ -n "$CARGO" ]
}
# build_crate "what it is" NAME PIN BIN ROOT: cargo install it with --root ROOT ("" = cargo's
# own). Soft: a failure is one warning plus the command to run by hand; returns 1.
build_crate() {
    _bc_what="$1"; _bc_name="$2"; _bc_pin="$3"; _bc_bin="$4"; _bc_root="$5"
    info "compiling it from crates.io (a few minutes the first time)"
    set -- "$CARGO" install --locked --force
    [ -n "$_bc_root" ] && set -- "$@" --root "$_bc_root"
    set -- "$@" "$_bc_name" --version "$_bc_pin"
    RUN_SOFT=1 run "build $_bc_what" "$@"
    [ "$PRINT" = 1 ] && return 0
    if [ "$RUN_RC" = 0 ] && crate_installed "$_bc_bin" "$_bc_name" "$_bc_pin"; then
        ok "installed $_bc_name $_bc_pin: $_bc_bin"; return 0
    fi
    [ "$RUN_RC" = 0 ] && warn "cargo reported success but $_bc_bin does not answer --version"
    info "build it by hand: $(show_cmd "$@")"
    return 1
}
if [ "$WITH_CONSOLE" = 0 ]; then
    CONSOLE_OK="$CONSOLE_HAVE"
else
    step "Terminal console ($CONSOLE_NAME $CONSOLE_PIN)"
    if [ "$CONSOLE_HAVE" = 1 ]; then
        ok "$CONSOLE_NAME $CONSOLE_PIN already installed: $CONSOLE_BIN"; CONSOLE_OK=1
    elif ! rust_cargo; then CONSOLE_WHY="$RUST_WHY"
    elif build_crate "the terminal console" "$CONSOLE_NAME" "$CONSOLE_PIN" "$CONSOLE_BIN" "$CRATE_ROOT"; then CONSOLE_OK=1
    else CONSOLE_WHY="the build failed (see $LOG_FILE)"; fi
fi
if [ "$WITH_CODE_CLI" = 0 ]; then
    CODE_OK="$CODE_HAVE"
else
    step "AbstractCode terminal client ($CODE_NAME $CODE_PIN)"
    if [ "$CODE_HAVE" = 1 ]; then
        ok "$CODE_NAME $CODE_HAVE_V already installed ($CODE_PIN or later): $CODE_BIN"; CODE_OK=1
    elif ! rust_cargo; then
        CODE_WHY="$RUST_WHY"
        # Under --no-console nothing above said it (the console step warns for both).
        [ "$WITH_CONSOLE" = 0 ] && info "AbstractCode's terminal client skipped: $CODE_WHY"
    elif build_crate "AbstractCode's terminal client" "$CODE_NAME" "$CODE_PIN" "$CODE_BIN" "$CODE_ROOT"; then CODE_OK=1
    else CODE_WHY="the build failed (see $LOG_FILE)"; fi
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
        echo "UV_BY_INSTALLER=$UV_BY_US"; echo "RUST_BY_INSTALLER=$RUST_BY_US"; echo "VOICE_SPEC=$VOICE_SPEC"
        # The release this install is (empty after --pin/--from), and the choices a re-run keeps.
        echo "FRAMEWORK_VERSION=$([ "$IS_RELEASE" = 1 ] && echo "$AF_FRAMEWORK_VERSION")"
        echo "CONSOLE=$WITH_CONSOLE"; echo "CODE_CLI=$WITH_CODE_CLI"; echo "CORE_CLI=$WITH_CORE_CLI"
        echo "TRAY=$WITH_TRAY"; echo "FULL=$FULL"
    } >"$STATE_FILE"
}

export ABSTRACTGATEWAY_DATA_DIR="$DATA_DIR"
# Gateways before 0.3 (reachable with --pin) refuse to start without an auth mode; from
# 0.3 on, user auth with a bootstrapped admin is the loopback default, so this is a no-op.
export ABSTRACTGATEWAY_USER_AUTH=1

MODE=none
NET_SETTING=0   # 1 = the background gateway starts plain `serve` (the Network setting binds it)
SERVICE_FALLBACK=0   # 1 = the login item failed to register, so the gateway runs in the background
AF_SYSTEMD_UNIT="abstractgateway.service"
# start_background: (re)start the gateway as a background process of this user, pid in gateway.pid.
start_background() {
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
}
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
    SERVICE_FAILED=0
    if [ "$LOGIN_WAS" = y ] && [ "$REUSE_RUNNING" = 1 ] && [ "$CHANGED" = 0 ]; then
        ok "login item already registered and the gateway is running, unchanged"
    else
        # A running systemd user unit: `systemctl --user enable --now` (what `service install`
        # runs) leaves it on the code it started with, so it is restarted below when anything
        # changed. launchd's bootout + bootstrap restarts the LaunchAgent by itself.
        _was_active=0
        if [ "$OS_ID" = linux ] && [ "$PRINT" = 0 ] && systemctl --user is-active --quiet "$AF_SYSTEMD_UNIT" 2>/dev/null; then _was_active=1; fi
        # The installer waits for health and mints the sign-in link itself (below), so the
        # service verb does neither when it supports skipping them (gateway 0.3.0+).
        # No --host: the login item runs plain `serve` and the gateway's Network setting
        # (localhost unless the user chose otherwise) binds it; passing 127.0.0.1 here would
        # reset a "Local network" choice on every re-run. Older gateways default to 127.0.0.1.
        set -- --port "$PORT"
        if [ "$PRINT" = 0 ] && "$GW" service install --help 2>/dev/null | grep -q -- '--no-claim'; then
            set -- "$@" --no-wait --no-claim
        fi
        RUN_SOFT=1 run "register the gateway service" "$GW" service install "$@"
        if [ "$RUN_RC" != 0 ]; then
            SERVICE_FAILED=1
        elif [ "$_was_active" = 1 ] && [ "$CHANGED" = 1 ]; then
            run "restart the gateway service (it was running the previous version)" systemctl --user restart "$AF_SYSTEMD_UNIT"
        fi
        [ "$PRINT" = 1 ] && [ "$OS_ID" = linux ] && info "$(show_cmd systemctl --user restart "$AF_SYSTEMD_UNIT")   (when the unit was running and anything changed)"
    fi
    if [ "$SERVICE_FAILED" = 1 ]; then
        # Never leave the gateway stopped: it runs now, in the background, and the summary
        # says how to turn start at login on once the cause is fixed.
        warn "the login item could not be registered (details above and in $LOG_FILE): start at login is off; starting the gateway in the background instead, so it runs now"
        step "Start in the background"
        start_background
        MODE=background; SERVICE_FALLBACK=1
    else
        MODE=service
    fi
else
    step "Start in the background"
    if [ "$LOGIN_WAS" = y ] && [ "$SERVICE_OK" = 1 ]; then
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
        start_background
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
# A remote or headless session: SSH, or Linux with no graphical display. The installer then
# opens the terminal console at the end instead of a browser.
REMOTE_SESSION=0
if [ -n "${SSH_CONNECTION:-}${SSH_TTY:-}" ]; then REMOTE_SESSION=1
elif [ "$OS_ID" = linux ] && [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then REMOTE_SESSION=1; fi
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
        write_pointer
    fi
    [ "$PRINT" = 1 ] && info "then write the gateway pointer $POINTER_FILE -> $BASE_URL (this install's address and data dir; no token)"

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
    elif [ "$REMOTE_SESSION" = 1 ]; then
        # Over SSH a browser would open on the remote machine's own screen, if it has one.
        info "open: $CONSOLE_URL"
        info "remote host? tunnel it first: ssh -L $PORT:127.0.0.1:$PORT <this-host>"
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
# What this run changed: the release, the gateway, the release's libraries and the two crates
# (old -> new), then how many other packages of the environment moved.
CHANGE_LINES=""; CHANGE_OTHERS=0; UPGRADE_LINE=""
if [ "$PRINT" = 0 ] && [ "$ACTION" != install ]; then
    _names="abstractgateway"
    for _c in $AF_PY_MATRIX; do _names="$_names $(printf '%s' "${_c%%==*}" | tr 'A-Z_' 'a-z-')"; done
    _names="$_names $CONSOLE_NAME $CODE_NAME"
    CHANGE_LINES="$(printf '%s\n%s\n' "$ENV_BEFORE" "$CRATES_BEFORE" | sed '/^$/d' | sed 's/^/B /'; \
        printf '%s\n%s\n' "$ENV_AFTER" "$(crate_snapshot)" | sed '/^$/d' | sed 's/^/A /')"
    CHANGE_LINES="$(printf '%s\n' "$CHANGE_LINES" | awk -v names="$_names" '
        { split($2, kv, "=="); if ($1 == "B") b[kv[1]] = kv[2]; else a[kv[1]] = kv[2]; seen[kv[1]] = 1 }
        END {
            n = split(names, order, " "); for (i = 1; i <= n; i++) named[order[i]] = 1
            for (i = 1; i <= n; i++) { k = order[i]
                if (!(k in seen) || b[k] == a[k]) continue
                printf "%s %s -> %s\n", k, (k in b ? b[k] : "(none)"), (k in a ? a[k] : "(removed)") }
            o = 0; for (k in seen) if (!(k in named) && b[k] != a[k]) o++
            printf "#others %d\n", o
        }')"
    CHANGE_OTHERS="$(printf '%s\n' "$CHANGE_LINES" | sed -n 's/^#others //p')"
    CHANGE_LINES="$(printf '%s\n' "$CHANGE_LINES" | sed '/^#others /d')"
    if [ "$IS_RELEASE" = 1 ] && [ "$ST_FRAMEWORK" != "$AF_FRAMEWORK_VERSION" ]; then
        CHANGE_LINES="AbstractFramework ${ST_FRAMEWORK:-(not recorded)} -> $AF_FRAMEWORK_VERSION${CHANGE_LINES:+
$CHANGE_LINES}"
    fi
    if [ -z "$CHANGE_LINES" ] && [ "${CHANGE_OTHERS:-0}" = 0 ]; then
        UPGRADE_LINE="Already up to date: $([ "$IS_RELEASE" = 1 ] && echo "AbstractFramework $AF_FRAMEWORK_VERSION" || echo "abstractgateway $AFTER"); nothing changed."
    elif [ "$IS_RELEASE" = 1 ]; then
        UPGRADE_LINE="Upgraded: AbstractFramework ${ST_FRAMEWORK:-(not recorded)} -> $AF_FRAMEWORK_VERSION (what changed is listed under Details)."
    else
        UPGRADE_LINE="Upgraded: $TARGET (what changed is listed under Details)."
    fi
fi
# The terminal console signs in with the admin token (`--token`), printed ready to paste; the
# gateway keeps it in its data dir. Before the gateway has written it, the command names that file.
_tui_exe="$CONSOLE_NAME"; [ "$CONSOLE_BIN" = "$TOOL_BIN/$CONSOLE_NAME" ] || _tui_exe="$(q "$CONSOLE_BIN")"
_tui_tok=""; [ "$PRINT" = 0 ] && [ -r "$TOKEN_FILE" ] && _tui_tok="$(tr -d '[:space:]' <"$TOKEN_FILE")"
_code_exe="$CODE_NAME"; [ "$CODE_BIN" = "$TOOL_BIN/$CODE_NAME" ] || _code_exe="$(q "$CODE_BIN")"
if [ -n "$_tui_tok" ]; then _tok_arg="--token $_tui_tok"
else _tok_arg="--token <admin token: cat $(q "$TOKEN_FILE")>"; fi
TUI_CMD="$_tui_exe --gateway-url $BASE_URL $_tok_arg"
# AbstractCode's terminal client signs in once with the admin token given directly (the installer
# never saves it for you) and then follows the gateway pointer, so no --gateway-url. On this
# machine `abstractgateway apps tui-command code` opens it signed in without handling a token (it
# finds the gateway through its data dir: a custom one is passed on).
CODE_LOGIN="$_code_exe login $_tok_arg"
TUI_COMMAND="abstractgateway apps tui-command code"; [ "$DATA_DIR_CUSTOM" = 1 ] && TUI_COMMAND="$TUI_COMMAND --data-dir $(q "$DATA_DIR")"
if [ "$PRINT" = 0 ] && [ "$NO_START" = 0 ]; then
    # The plain-language part first: what a non-technical user needs to know.
    printf '\n%s%sAbstractFramework is ready.%s\n' "$C_B" "$C_G" "$C_0"
    [ -n "$UPGRADE_LINE" ] && echo "  $UPGRADE_LINE"
    [ "$SERVICE_FALLBACK" = 1 ] && echo "  Start at login is off: the login item could not be registered (see the warning above). Once its cause is fixed, turn it on as below."
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
    if [ "$CODE_OK" = 1 ]; then
        echo "  AbstractCode, the coding client, in the terminal:"
        echo "  Sign in (terminal, once): $CODE_LOGIN"
        echo "    then run: $_code_exe"
        echo "    or, on this machine, without a token: $TUI_COMMAND"
    else
        echo "  AbstractCode (terminal): not installed: $CODE_WHY"
    fi
    if [ "$MODE" = service ]; then
        echo "  It starts by itself when you log in; nothing to launch."
    else
        echo "  It runs until you restart the computer."
        if [ "$SERVICE_POSSIBLE" = 1 ] && [ "$SERVICE_OK" = 1 ]; then
            echo "  Start at login is off. To turn it on: the Start at login switch in either console (web: the Gateway"
            echo "    section; terminal: F3), or run: abstractgateway service enable"
        else
            echo "  Run the installer again to start it."
        fi
    fi
    case ",$EXTRAS," in *,tray,*) echo "  Its icon in the $([ "$OS_ID" = macos ] && echo 'menu bar' || echo 'system tray') opens the console and shows its status." ;; esac
    echo "  First steps in the console: pick an engine and a model; it shows what fits this computer."
    echo "  To remove it: run the uninstaller (Uninstall AbstractFramework.command), or: sh install.sh --uninstall"
fi
if [ "$PRINT" = 0 ] && [ "$NO_START" = 1 ]; then
    printf '\n%sAbstractFramework is installed (--no-start).%s\n' "$C_B" "$C_0"
    [ -n "$UPGRADE_LINE" ] && echo "  $UPGRADE_LINE"
    if [ "$CHANGED" = 1 ] && [ "$ACTION" != install ]; then
        echo "  A gateway that is running still runs the previous version until it restarts: the console's"
        echo "  Restart (web: the Gateway section), the tray's Restart, or re-run this installer without --no-start."
    fi
    if [ "$PORT_HELD" = 1 ]; then
        echo "  Port $PORT, this install's port, is in use by a program this installer did not start (for example a"
        echo "  gateway started by hand). The install keeps port $PORT: restart that gateway to run this version, or stop"
        echo "  the program before the gateway starts again."
    fi
fi
printf '\n%s%s%s\n' "$C_B" "$([ "$PRINT" = 1 ] && echo 'Plan printed (--print): nothing was changed.' || echo 'Details')" "$C_0"
if [ -n "$CHANGE_LINES" ] || [ "${CHANGE_OTHERS:-0}" != 0 ]; then
    echo "  Changes:"
    printf '%s\n' "$CHANGE_LINES" | sed '/^$/d' | awk '{ printf "      %-24s %s %s %s\n", $1, $2, $3, $4 }'
    [ "${CHANGE_OTHERS:-0}" != 0 ] && echo "      (and $CHANGE_OTHERS other packages of the gateway's environment)"
elif [ -n "$UPGRADE_LINE" ]; then
    echo "  Changes:    none"
fi
printf '  %-11s %s\n' "Console:" "$BASE_URL/console" \
    "Release:" "$([ "$IS_RELEASE" = 1 ] && echo "AbstractFramework $AF_FRAMEWORK_VERSION" || echo "$TARGET (not a recorded AbstractFramework release)")" \
    "Gateway:" "$GW_SPEC ($PROFILE profile)" \
    "Terminal:" "$([ "$CONSOLE_OK" = 1 ] && echo "$TUI_CMD" || echo "not installed ($CONSOLE_WHY)")" \
    "Code:" "$([ "$CODE_OK" = 1 ] && echo "$_code_exe   (sign in once: $CODE_LOGIN; or on this machine: $TUI_COMMAND)" || echo "not installed ($CODE_WHY)")" \
    "Data dir:" "$DATA_DIR" "Logs:" "$LOG_DIR" "Mode:" "$MODE"
echo ""
# What each command on PATH is, so a new user knows what abstractgateway-config and the others do.
# The crates are listed by full path when they are not in the tool bin dir.
cmd_line() { printf '      %-24s %s\n' "$1" "$2"; }
echo "  Commands (in $TOOL_BIN):"
cmd_line abstractgateway "the gateway: serve, service, network, models, engines, apps"
cmd_line abstractgateway-config "the gateway's admin command: status, claim-url (a new console sign-in link), defaults and set-default (model routing), get/set runtime settings, bootstrap-admin"
[ "$CONSOLE_OK" = 1 ] && cmd_line "$_tui_exe" "the terminal console (Terminal: above)"
[ "$CODE_OK" = 1 ] && cmd_line "$_code_exe" "AbstractCode, the coding client, in the terminal (Code: above)"
for _p in $CLI_FROM; do cmd_line "$_p" "$(af_cli_about "$_p")"; done
[ -z "$CLI_TAKEN" ] || echo "  Not exposed (a command name is taken, see the warning above): $CLI_TAKEN"
echo ""
echo "  Status:     $([ "$MODE" = service ] && echo "abstractgateway service status" || echo "curl $BASE_URL/api/health")"
echo "  Stop:       $([ "$MODE" = service ] && echo "abstractgateway service uninstall   (stops it and removes the login entry; data is kept)" || echo "kill \$(cat $(q "$PID_FILE"))")"
echo "  Start:      $([ "$MODE" = service ] && echo "abstractgateway service install --port $PORT" || echo "re-run this installer, or: ABSTRACTGATEWAY_USER_AUTH=1 ABSTRACTGATEWAY_DATA_DIR=$(q "$DATA_DIR") abstractgateway serve$([ "$NET_SETTING" = 1 ] || echo " --host 127.0.0.1 --port $PORT")")"
echo "  Upgrade:    curl -LsSf $AF_SCRIPT_URL | sh   (the latest AbstractFramework release; keeps your settings and data)"
echo "              curl -LsSf $AF_SCRIPT_URL | sh -s -- --pin latest   (the newest abstractgateway on PyPI; see $AF_DOCS#upgrade)"
echo "  Uninstall:  sh install.sh --uninstall   (or: $([ "$MODE" = service ] && echo 'abstractgateway service uninstall && ')uv tool uninstall abstractgateway)"
echo "  Check:      uvx abstractframework doctor"
echo "  GGUF:       $GGUF_RESULT"
echo "  Voice:      $VOICE_RESULT"
if [ "$FULL" = 0 ] && { [ "$PROFILE" = apple ] || [ "$PROFILE" = gpu ]; }; then
    echo "  $AF_SKIPPED_LINE"
fi
echo "  Apps:       $BASE_URL/apps/<app>/   (console > Apps > Open; <app>: observer, code, flow, continuum, entity)"
echo "  Standalone: npx -y @abstractframework/flow --gateway-url $BASE_URL   (advanced; also code, observer, continuum, entity)"
echo "  Docs:       $AF_DOCS"
if [ -n "$TWINS" ]; then
    echo ""
    echo "  The same steps by hand:"
    printf '%s' "$TWINS"
fi
[ -n "$LOG_FILE" ] && printf '\n  %sFull log: %s%s\n' "$C_D" "$LOG_FILE" "$C_0"

# Remote or headless: offer the terminal console, signed in, the way a Mac opens the web console.
# It is ASKED (Enter within --ask-wait s), never assumed: a pseudo-terminal with nobody at it
# (CI, Terraform, `ssh -t` in a script) must not hang (tty_ok is the dash-safe probe). --no-open
# and --yes skip the offer; --ask-wait sets how long it waits.
offer_console() {
    _old_tty="$(stty -g </dev/tty 2>/dev/null)" || return 1
    # Keys typed during the install are still buffered: drop them, so only an answer counts.
    stty -icanon -echo min 0 time 0 </dev/tty 2>/dev/null
    dd bs=4096 count=1 </dev/tty >/dev/null 2>&1
    printf '\n%sPress Enter within %s s to open the terminal console%s (any other key, or waiting, skips it) ' \
        "$C_B" "$ASK_WAIT" "$C_0" >/dev/tty
    # stty counts tenths of a second, at most 255.
    stty time "$((ASK_WAIT * 10))" </dev/tty 2>/dev/null
    _key="$(dd bs=1 count=1 </dev/tty 2>/dev/null | od -An -tu1 | tr -d ' ')"
    stty "$_old_tty" </dev/tty 2>/dev/null
    printf '\n' >/dev/tty
    [ "$_key" = 10 ] || [ "$_key" = 13 ]
}
if [ "$PRINT" = 0 ] && [ "$NO_START" = 0 ] && [ "$NO_OPEN" = 0 ] && [ "$REMOTE_SESSION" = 1 ] \
    && [ "$ASK_NOTHING" = 0 ] && [ "$CONSOLE_OK" = 1 ] && [ -n "$_tui_tok" ] && tty_ok; then
    # Everything is installed: Ctrl+C here must not turn a finished install into exit 130.
    trap : INT
    if offer_console; then
        "$CONSOLE_BIN" --gateway-url "$BASE_URL" --token "$_tui_tok" </dev/tty >/dev/tty 2>&1 || \
            warn "the terminal console exited with an error; start it again with the Terminal command above"
        stty sane </dev/tty 2>/dev/null || true
    else
        info "not opened; start it any time with the Terminal command above"
    fi
    trap - INT
fi
exit 0
