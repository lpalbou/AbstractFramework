#!/usr/bin/env bash
# =============================================================================
# Sandbox tests for the non-technical install path: install.sh preflight and
# its plain-language failures, the login-item question, uninstall.sh, the
# double-click .command files and the macOS .pkg postinstall.
# =============================================================================
# Every run uses a throwaway HOME under $TMPDIR, a PATH without the caller's
# tools, and the recorded doubles in scripts/tests/doubles (launchctl, open),
# so nothing is installed, no login item is registered and no browser or
# Terminal window opens. No step needs the network except the one that checks
# the offline message, which points curl at a dead proxy (127.0.0.1:9).
#
# Proves:
#   - every script parses (sh -n; zsh -n where zsh exists)
#   - offline (dead proxy, or curl failing) -> exit 1, "What to do", nothing written
#   - Rosetta: a piped run explains how to fix Terminal; a file run re-executes
#     itself with `arch -arm64`
#   - a root-owned ~/.local/bin -> exit 1 with the exact chown fix
#   - the start-at-login question: default yes, a previous "no" stays the default
#   - uninstall.sh removes a login item left without its tool (launchctl bootout
#     through the double, plist deleted), keeps data unless --purge
#   - Install AbstractFramework.command passes --interactive and user args, and
#     says what to do when the installer fails
#   - build_macos_installer.sh builds the zip (executable bits kept) and a
#     payload-free .pkg whose postinstall copies the installer and opens it in
#     Terminal as the user
#
# Run: bash scripts/tests/test_install_user_path.sh   (KEEP_WORK=1 keeps the sandbox)
# =============================================================================

set -u

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(dirname "$TEST_DIR")"
DOUBLES="$TEST_DIR/doubles"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/af_install_user_path.XXXXXX")"
WORK="$(cd "$WORK" && pwd -P)"
cleanup() {
    chmod -R u+w "$WORK" 2>/dev/null
    if [[ "${KEEP_WORK:-0}" == "1" ]]; then echo "sandbox kept: $WORK"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT

PASS=0; FAIL=0
check() {  # check NAME CONDITION-EXIT-CODE [detail file]
    if [[ "$2" == 0 ]]; then PASS=$((PASS + 1)); echo "  PASS $1"
    else FAIL=$((FAIL + 1)); echo "  FAIL $1"; [[ -n "${3:-}" && -f "$3" ]] && sed 's/^/       | /' "$3" | tail -n 25; fi
}
has() { grep -q -- "$2" "$1"; }

# run_in NAME [ENV=VAL...] -- CMD... : fresh HOME per case, doubles first on PATH.
run_in() {
    local name="$1"; shift
    local envs=()
    while [[ $# -gt 0 && "$1" != "--" ]]; do envs+=("$1"); shift; done
    shift
    local home="$WORK/$name/home"
    mkdir -p "$home" "$WORK/$name/bin"
    RC=0
    env -u ABSTRACTGATEWAY_AUTH_TOKEN -i HOME="$home" USER="$(id -un)" LOGNAME="$(id -un)" LANG=C TERM=dumb \
        PATH="$WORK/$name/bin:$DOUBLES:/usr/bin:/bin:/usr/sbin:/sbin" TMPDIR="$WORK/$name/" \
        AF_LAUNCHD_DOUBLE_STATE="$WORK/$name/launchd" AF_OPEN_DOUBLE_LOG="$WORK/$name/open.log" \
        ${envs[@]+"${envs[@]}"} "$@" </dev/null >"$WORK/$name/out.txt" 2>&1 || RC=$?
    OUT="$WORK/$name/out.txt"; HOME_T="$home"
}
IS_MAC=0; [[ "$(uname -s)" == Darwin ]] && IS_MAC=1
if [[ "$IS_MAC" == 1 ]]; then DATA_REL="Library/Application Support/AbstractGateway"; else DATA_REL=".local/share/abstractgateway"; fi

echo "[1] syntax"
for f in install.sh uninstall.sh "Install AbstractFramework.command" "Uninstall AbstractFramework.command" \
         lib/build_macos_installer.sh tests/doubles/launchctl tests/doubles/open; do
    sh -n "$SCRIPTS_DIR/$f"; check "sh -n $f" "$?"
    if command -v zsh >/dev/null 2>&1; then zsh -n "$SCRIPTS_DIR/$f"; check "zsh -n $f" "$?"; fi
done

echo "[2] offline: a dead proxy"
run_in offline_proxy HTTPS_PROXY=http://127.0.0.1:9 -- sh "$SCRIPTS_DIR/install.sh" --port 18829 --no-open
check "exits 1" "$([[ $RC == 1 ]]; echo $?)" "$OUT"
check "names the proxy and says what to do" "$(has "$OUT" "through the proxy" && has "$OUT" "What to do"; echo $?)" "$OUT"
check "installed nothing (no uv, no data dir)" "$([[ ! -e "$HOME_T/.local/bin/uv" && ! -e "$HOME_T/$DATA_REL" ]]; echo $?)"

echo "[3] offline: no connection at all (curl fails like a missing network)"
mkdir -p "$WORK/offline_curl/bin"
printf '#!/bin/sh\necho "curl: (6) Could not resolve host" >&2\nexit 6\n' >"$WORK/offline_curl/bin/curl"
chmod +x "$WORK/offline_curl/bin/curl"
run_in offline_curl -- sh "$SCRIPTS_DIR/install.sh" --port 18829 --no-open
check "exits 1" "$([[ $RC == 1 ]]; echo $?)" "$OUT"
check "plain message: connect and run again" "$(has "$OUT" "no internet connection" && has "$OUT" "run the installer again"; echo $?)" "$OUT"

if [[ "$IS_MAC" == 1 ]]; then
    echo "[4] Rosetta"
    mkdir -p "$WORK/rosetta_pipe/bin"
    printf '#!/bin/sh\n[ "$2" = sysctl.proc_translated ] && { echo 1; exit 0; }\nexec /usr/sbin/sysctl "$@"\n' >"$WORK/rosetta_pipe/bin/sysctl"
    chmod +x "$WORK/rosetta_pipe/bin/sysctl"
    run_in rosetta_pipe -- sh -c "cat '$SCRIPTS_DIR/install.sh' | sh -s -- --print"
    check "piped: exits 1 and explains 'Open using Rosetta'" "$([[ $RC == 1 ]] && has "$OUT" "Open using Rosetta"; echo $?)" "$OUT"
    mkdir -p "$WORK/rosetta_file/bin"
    cp "$WORK/rosetta_pipe/bin/sysctl" "$WORK/rosetta_file/bin/sysctl"
    printf '#!/bin/sh\necho "arch $*" >>"$HOME/arch.log"\nshift\nexec "$@"\n' >"$WORK/rosetta_file/bin/arch"
    chmod +x "$WORK/rosetta_file/bin/arch"
    run_in rosetta_file -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
    check "file: re-executes itself with arch -arm64" "$(grep -q "arch -arm64 /bin/sh $SCRIPTS_DIR/install.sh --print --port 18829" "$HOME_T/arch.log"; echo $?)" "$OUT"
    check "file: re-executes once, then stops with the fix (the double stays 'translated')" "$([[ $RC == 1 ]] && has "$OUT" "restarting the installer natively" && has "$OUT" "Open using Rosetta"; echo $?)" "$OUT"
fi

echo "[5] a root-owned folder in the way (simulated: not writable)"
mkdir -p "$WORK/readonly/home/.local/bin"; chmod 555 "$WORK/readonly/home/.local/bin"
run_in readonly -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
check "exits 1 with the chown fix" "$([[ $RC == 1 ]] && has "$OUT" "sudo chown -R $(id -un)" && has "$OUT" ".local/bin"; echo $?)" "$OUT"
chmod 755 "$WORK/readonly/home/.local/bin"

echo "[6] start at login: the question and its defaults"
run_in login_default -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
if [[ "$IS_MAC" == 1 ]]; then
    check "--print: default yes, stated" "$(has "$OUT" "when you log in?.*-> yes (default" && has "$OUT" "ai.abstractframework.gateway.plist"; echo $?)" "$OUT"
    # The login item must not pin --host: the gateway's Network setting binds it (mission T).
    check "--print: service install passes --port only, never --host" "$(has "$OUT" "service install --port 18829" && ! has "$OUT" "service install --host"; echo $?)" "$OUT"
    mkdir -p "$WORK/login_prev_no/home/$DATA_REL"
    printf 'PORT=18829\nMODE=background\nPROFILE=light\n' >"$WORK/login_prev_no/home/$DATA_REL/bootstrap.env"
    run_in login_prev_no -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
    check "a previous 'no' is the default" "$(has "$OUT" "when you log in?.*-> no (default" && has "$OUT" "Start in the background"; echo $?)" "$OUT"
    run_in login_flag -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829 --no-service
    check "--no-service asks nothing and starts in the background" "$(! has "$OUT" "when you log in?" && has "$OUT" "Start in the background"; echo $?)" "$OUT"
fi

if [[ "$IS_MAC" == 1 ]]; then
    echo "[7] uninstall.sh: a login item left behind without its tool"
    H="$WORK/uninst/home"; mkdir -p "$H/Library/LaunchAgents" "$H/$DATA_REL/logs" "$WORK/uninst/launchd"
    cat >"$H/Library/LaunchAgents/ai.abstractframework.gateway.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>Label</key><string>ai.abstractframework.gateway</string>
<key>ProgramArguments</key><array><string>/bin/sleep</string><string>300</string></array></dict></plist>
PLIST
    printf 'PORT=18829\nMODE=service\nPROFILE=light\n' >"$H/$DATA_REL/bootstrap.env"
    # "Load" it through the double, as launchd would at login.
    env HOME="$H" AF_LAUNCHD_DOUBLE_STATE="$WORK/uninst/launchd" "$DOUBLES/launchctl" bootstrap "gui/$(id -u)" "$H/Library/LaunchAgents/ai.abstractframework.gateway.plist"
    SLEEP_PID="$(cat "$WORK/uninst/launchd/ai.abstractframework.gateway.pid")"
    run_in uninst -- sh "$SCRIPTS_DIR/uninstall.sh" --yes
    check "exits 0" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "boots the label out (recorded by the double)" "$(grep -q "launchctl bootout gui/$(id -u)/ai.abstractframework.gateway" "$WORK/uninst/launchd/calls.log"; echo $?)" "$OUT"
    check "the loaded process is stopped" "$(! kill -0 "$SLEEP_PID" 2>/dev/null; echo $?)"
    check "the plist is gone" "$([[ ! -e "$H/Library/LaunchAgents/ai.abstractframework.gateway.plist" ]]; echo $?)" "$OUT"
    check "data kept without --purge" "$([[ -d "$H/$DATA_REL" ]] && has "$OUT" "kept the gateway data dir"; echo $?)" "$OUT"
    run_in uninst -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge
    check "--purge deletes the data dir" "$([[ $RC == 0 && ! -e "$H/$DATA_REL" ]]; echo $?)" "$OUT"
    run_in uninst_noconfirm -- sh "$SCRIPTS_DIR/uninstall.sh"
    check "without a terminal or --yes it removes nothing" "$([[ $RC == 2 ]] && has "$OUT" "re-run with --yes"; echo $?)" "$OUT"
fi

echo "[8] Install AbstractFramework.command"
C="$WORK/cmd"; mkdir -p "$C"
cp "$SCRIPTS_DIR/Install AbstractFramework.command" "$C/"
printf '#!/bin/sh\necho "STUB install.sh $*"\nexit "${STUB_RC:-0}"\n' >"$C/install.sh"
run_in cmd_ok -- sh "$C/Install AbstractFramework.command" --port 18829
check "runs the adjacent install.sh with --interactive and the user's args" "$(has "$OUT" "STUB install.sh --interactive --port 18829" && has "$OUT" "All done"; echo $?)" "$OUT"
run_in cmd_fail STUB_RC=1 -- sh "$C/Install AbstractFramework.command"
check "on failure: exit 1 and 'double-click this file again'" "$([[ $RC == 1 ]] && has "$OUT" "double-click this file again"; echo $?)" "$OUT"

if [[ "$IS_MAC" == 1 ]] && command -v pkgbuild >/dev/null 2>&1; then
    echo "[9] macOS installers (zip + payload-free pkg)"
    sh "$SCRIPTS_DIR/lib/build_macos_installer.sh" --out "$WORK/dist" >"$WORK/build.txt" 2>&1
    check "build succeeds and says it is UNSIGNED" "$([[ $? == 0 ]] && has "$WORK/build.txt" "UNSIGNED"; echo $?)" "$WORK/build.txt"
    zipinfo "$WORK/dist/AbstractFramework-Installer-macOS.zip" >"$WORK/zip.txt" 2>&1
    check "zip keeps the executable bit on the .command" "$(grep -E '^-rwxr-xr-x.*Install AbstractFramework.command' "$WORK/zip.txt" >/dev/null; echo $?)" "$WORK/zip.txt"
    pkgutil --expand "$WORK/dist/AbstractFramework-Installer.pkg" "$WORK/pkgx" >/dev/null 2>&1
    check "pkg is payload-free and user-domain only" "$([[ ! -e "$WORK/pkgx/component.pkg/Payload" ]] && grep -q 'enable_localSystem="false"' "$WORK/pkgx/Distribution"; echo $?)"
    run_in postinstall -- sh "$WORK/dist/stage/scripts/postinstall"
    DEST="$HOME_T/Library/Application Support/AbstractFramework/Installer"
    check "postinstall copies the installer folder" "$([[ -x "$DEST/Install AbstractFramework.command" && -f "$DEST/install.sh" && -f "$DEST/uninstall.sh" ]]; echo $?)" "$OUT"
    check "postinstall opens it in Terminal (recorded by the open double)" "$(grep -q "open -a Terminal $DEST/Install AbstractFramework.command" "$WORK/postinstall/open.log"; echo $?)" "$OUT"
fi

echo "[10] background start (--no-service): the Network setting binds it (mission T)"
# A real (not --print) run against a fake uv, a curl that answers only the PyPI probe
# offline, and a fake `abstractgateway` whose `serve` binds the port it is GIVEN or, with
# no --port, the port of its (fake) Network setting, and answers /api/health. Port 18870.
BG_PORT=18870
# bg_case NAME NETWORK(1|0) [STORED "mode port"]: run the installer, leave OUT/GWLOG/NETF/DATA_T.
bg_case() {
    local name="$1" network="$2" stored="${3:-}"
    local bin="$WORK/$name/bin" toolbin="$WORK/$name/toolbin"
    mkdir -p "$bin" "$toolbin" "$WORK/$name/home"
    GWLOG="$WORK/$name/gw.log"
    cat >"$bin/curl" <<CURL
#!/bin/sh
for a in "\$@"; do [ "\$a" = "https://pypi.org/simple/pip/" ] && exit 0; done
exec /usr/bin/curl "\$@"
CURL
    cat >"$bin/uv" <<UV
#!/bin/sh
case "\$1 \${2:-}" in
  "--version "*) echo "uv 0.0.0" ;;
  "tool dir") echo "$toolbin" ;;
  "tool list") echo "abstractgateway v9.9.9" ;;
esac
exit 0
UV
    cat >"$toolbin/abstractgateway" <<GW
#!/bin/sh
D="\${ABSTRACTGATEWAY_DATA_DIR:-$WORK/$name/no-data-dir}"
echo "abstractgateway \$*" >>"$GWLOG"
# An old gateway has no \`network\` subcommand at all (argparse: invalid choice, exit 2).
[ "\$1" = network ] && [ "$network" != 1 ] && { echo "invalid choice: 'network'" >&2; exit 2; }
case "\$1 \${2:-}" in
  "network --help") exit 0 ;;
  "service --help") exit 2 ;;
  "network status")
    if [ -f "\$D/fake-network" ]; then read -r m p <"\$D/fake-network"; s=stored; else m=localhost; p=8080; s=default; fi
    printf '{\n  "configured": {\n    "mode": "%s",\n    "port": %s,\n    "source": "%s",\n    "port_source": "%s"\n  },\n  "effective": {\n    "mode": "decoy",\n    "port": 1,\n    "source": "decoy"\n  }\n}\n' "\$m" "\$p" "\$s" "\$s"
    exit 0 ;;
  "network set")
    port=""; prev=""; for a in "\$@"; do [ "\$prev" = --port ] && port="\$a"; prev="\$a"; done
    mkdir -p "\$D"; echo "\$3 \$port" >"\$D/fake-network"; exit 0 ;;
  serve*)
    port=""; prev=""; for a in "\$@"; do [ "\$prev" = --port ] && port="\$a"; prev="\$a"; done
    [ -n "\$port" ] || { [ -f "\$D/fake-network" ] && read -r _m port <"\$D/fake-network"; }
    exec /usr/bin/python3 -c 'import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"{\"service\": \"abstractgateway\"}")
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()' "\${port:-8080}" ;;
esac
exit 0
GW
    chmod +x "$bin/curl" "$bin/uv" "$toolbin/abstractgateway"
    DATA_T="$WORK/$name/home/$DATA_REL"; NETF="$DATA_T/fake-network"
    if [[ -n "$stored" ]]; then mkdir -p "$DATA_T"; echo "$stored" >"$NETF"; fi
    run_in "$name" -- sh "$SCRIPTS_DIR/install.sh" --profile light --port "$BG_PORT" --no-service --no-open --no-modify-path
    local pid; pid="$(cat "$DATA_T/gateway.pid" 2>/dev/null)"
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1 || break; sleep 0.5; done
}
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the background-start cases" 1
else
    bg_case bg_new 1
    check "new gateway: installer succeeds" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "new gateway: seeds localhost on the install port (nothing stored)" "$(grep -qx "abstractgateway network set localhost --port $BG_PORT" "$GWLOG" && [[ "$(cat "$NETF")" == "localhost $BG_PORT" ]]; echo $?)" "$GWLOG"
    check "new gateway: starts plain serve (no --host/--port)" "$(grep -qx "abstractgateway serve" "$GWLOG" && ! grep -q "serve --host" "$GWLOG"; echo $?)" "$GWLOG"
    check "new gateway: the Start hint is plain serve" "$(has "$OUT" "Start: .*abstractgateway serve$"; echo $?)" "$OUT"

    bg_case bg_lan 1 "lan $BG_PORT"
    check "stored lan: installer succeeds" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "stored lan survives a re-run (no network set)" "$(! grep -q "network set" "$GWLOG" && [[ "$(cat "$NETF")" == "lan $BG_PORT" ]] && grep -qx "abstractgateway serve" "$GWLOG"; echo $?)" "$GWLOG"

    bg_case bg_lan_port 1 "lan 18999"
    check "stored lan on another port: mode kept, port aligned" "$([[ $RC == 0 ]] && grep -qx "abstractgateway network set lan --port $BG_PORT" "$GWLOG" && [[ "$(cat "$NETF")" == "lan $BG_PORT" ]]; echo $?)" "$GWLOG"

    bg_case bg_old 0
    check "old gateway: installer succeeds" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "old gateway: keeps the pinned argv, seeds nothing" "$(grep -qx "abstractgateway serve --host 127.0.0.1 --port $BG_PORT" "$GWLOG" && ! grep -q "network set\|network status" "$GWLOG" && [[ ! -e "$NETF" ]]; echo $?)" "$GWLOG"
    check "old gateway: the Start hint keeps --host/--port" "$(has "$OUT" "abstractgateway serve --host 127.0.0.1 --port $BG_PORT"; echo $?)" "$OUT"
fi

echo ""
echo "passed: $PASS  failed: $FAIL"
[[ "$FAIL" == 0 ]]
