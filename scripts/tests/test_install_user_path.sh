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
#   - the start-at-login question: asked only on a terminal (Enter = yes, 'n' = no, no
#     answer in --ask-wait = off on a first install); without a terminal a first install
#     leaves it off and the summary says how to turn it on; a re-run keeps the previous
#     choice; --yes and --no-service ask nothing; dash without a controlling terminal
#   - the local gateway pointer (~/.abstractframework/gateway.json): written after the
#     health check with written_by "installer", 0600, no token, for the install just made
#     (a custom --data-dir included; a pointer naming another data dir or unreadable is
#     replaced); --uninstall deletes it only when it names this install's data dir
#   - uninstall.sh removes a login item left without its tool (launchctl bootout
#     through the double, plist deleted), keeps data unless --purge
#   - uninstall with a live gateway tree (a writer every 50 ms and a detached,
#     SIGTERM-proof worker): the tree is listed and stopped, the data dir (with a
#     space) is gone and stays gone, --purge also deletes the Assistant's sessions,
#     AbstractCode's settings, the gateway logs/cache and the installer copy and
#     keeps model weights; a second run says "nothing to do"; --print changes
#     nothing; answering no keeps everything; a folder that cannot be deleted
#     (uchg on macOS, read-only on Linux) exits 1 naming it, with uninstall advice
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
    pkill -9 -f "$WORK/" 2>/dev/null
    [[ "$(uname -s)" == Darwin ]] && chflags -R nouchg "$WORK" 2>/dev/null
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
         lib/build_macos_installer.sh tests/doubles/launchctl tests/doubles/open tests/doubles/defaults; do
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

echo "[6] start at login without a terminal: the defaults (the terminal cases are in [13])"
run_in login_default -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
if [[ "$IS_MAC" == 1 ]]; then
    check "--print, no terminal, first install: off, said why" "$(has "$OUT" "start at login: no (no terminal to ask on" && has "$OUT" "Start in the background" && ! has "$OUT" "service install"; echo $?)" "$OUT"
    mkdir -p "$WORK/login_prev_yes/home/$DATA_REL"
    printf 'PORT=18829\nMODE=service\nPROFILE=light\n' >"$WORK/login_prev_yes/home/$DATA_REL/bootstrap.env"
    run_in login_prev_yes -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
    check "a previous 'yes' is kept without a terminal" "$(has "$OUT" "start at login: yes (kept from the previous install" && has "$OUT" "ai.abstractframework.gateway.plist"; echo $?)" "$OUT"
    # The login item must not pin --host: the gateway's Network setting binds it (mission T).
    check "--print: service install passes --port only, never --host" "$(has "$OUT" "service install --port 18829" && ! has "$OUT" "service install --host"; echo $?)" "$OUT"
    mkdir -p "$WORK/login_prev_no/home/$DATA_REL"
    printf 'PORT=18829\nMODE=background\nPROFILE=light\n' >"$WORK/login_prev_no/home/$DATA_REL/bootstrap.env"
    run_in login_prev_no -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829
    check "a previous 'no' is kept without a terminal" "$(has "$OUT" "start at login: no (kept from the previous install" && has "$OUT" "Start in the background"; echo $?)" "$OUT"
    run_in login_yes -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829 --yes
    check "--yes asks nothing: a first install leaves it off" "$(has "$OUT" "start at login: no (--yes: nothing is asked" && has "$OUT" "Start in the background"; echo $?)" "$OUT"
    run_in login_flag -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829 --no-service
    check "--no-service asks nothing and starts in the background" "$(! has "$OUT" "start at login:" && has "$OUT" "Start in the background"; echo $?)" "$OUT"
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

echo "[7b] uninstall: a live gateway tree, --purge of every user-data location"
# A fake installed gateway in the sandbox HOME: `service uninstall` returns at once
# (as `launchctl bootout` does) while `serve` keeps a tree alive that writes into the
# data dir every 50 ms: a writer child, and a detached worker (its own session, parent
# gone, ignores SIGTERM) like the entity loop / download jobs. The data dir has a space.
# Only processes whose command line holds the sandbox paths are ever signalled.
mk_live_gateway() {  # mk_live_gateway HOME DATA_DIR
    local h="$1" d="$2" v="$1/.local/share/uv/tools/abstractgateway"
    mkdir -p "$v/bin" "$h/.local/bin" "$h/Library/LaunchAgents" "$d/runtime/artifacts" "$d/logs"
    local i j
    for i in $(seq 1 60); do mkdir -p "$d/runtime/artifacts/r$i"; for j in $(seq 1 25); do echo x >"$d/runtime/artifacts/r$i/a$j.json"; done; done
    printf 'PORT=18829\nMODE=service\nPROFILE=light\n' >"$d/bootstrap.env"
    cat >"$v/bin/worker-loop" <<'W'
#!/bin/sh
trap '' TERM
while :; do mkdir -p "$1/entities/e1" 2>/dev/null; date >>"$1/entities/e1/own_time.log" 2>/dev/null; sleep 0.05; done
W
    cat >"$v/bin/abstractgateway" <<GW
#!/bin/sh
case "\$1 \${2:-}" in
  "service --help") exit 0 ;;
  "service uninstall") rm -f "$h/Library/LaunchAgents/ai.abstractframework.gateway.plist"; echo "Your data is kept: $d"; exit 0 ;;
  serve*)
    ( sh "$v/bin/worker-loop" "$d" </dev/null >/dev/null 2>&1 & )
    while :; do mkdir -p "$d/runtime/artifacts/r\$((\$\$ % 60 + 1))" "$d/logs" 2>/dev/null
      n=\$((\${n:-0} + 1)); echo \$n >"$d/runtime/artifacts/r\$((n % 60 + 1))/w\$n.json" 2>/dev/null; echo \$n >>"$d/logs/gateway.log" 2>/dev/null; sleep 0.05; done ;;
esac
exit 0
GW
    chmod +x "$v/bin/abstractgateway" "$v/bin/worker-loop"
    ln -sf "$v/bin/abstractgateway" "$h/.local/bin/abstractgateway"
    touch "$h/Library/LaunchAgents/ai.abstractframework.gateway.plist"
}
populate_user_data() {  # the other locations --purge covers, and two it must keep
    local h="$1"
    mkdir -p "$h/.abstractassistant/sessions/s1" "$h/.abstractcode" "$h/.cache/huggingface/hub" "$h/.abstractcore/config"
    echo '{}' >"$h/.abstractassistant/sessions.json"; echo '{}' >"$h/.abstractassistant/sessions/s1/session.json"
    echo '{}' >"$h/.abstractcode/prefs.json"; echo w >"$h/.cache/huggingface/hub/weights"; echo '{}' >"$h/.abstractcore/config/abstractcore.json"
    if [[ "$IS_MAC" == 1 ]]; then
        mkdir -p "$h/Library/Logs/AbstractGateway" "$h/Library/Caches/AbstractGateway/engines" "$h/Library/Logs/Assistant" \
                 "$h/Library/Application Support/AbstractFramework/Installer"
        echo l >"$h/Library/Logs/AbstractGateway/gateway.err.log"; echo l >"$h/Library/Logs/Assistant/abstractassistant-launcher.log"
        echo i >"$h/Library/Application Support/AbstractFramework/Installer/install.sh"
        mkdir -p "$h/Library/Preferences"; echo p >"$h/Library/Preferences/ai.abstractcore.abstractassistant.plist"
        echo p >"$h/Library/Preferences/com.example.other.plist"
    else
        mkdir -p "$h/.cache/abstractgateway/engines"
    fi
}
sandbox_procs() { pgrep -f "$WORK/$1/" 2>/dev/null | tr '\n' ' '; }
LH="$WORK/live/home"; LD="$WORK/live/my data"
mk_live_gateway "$LH" "$LD"; populate_user_data "$LH"
( cd "$WORK" && env -i HOME="$LH" PATH=/usr/bin:/bin sh -c "exec '$LH/.local/share/uv/tools/abstractgateway/bin/abstractgateway' serve" </dev/null >/dev/null 2>&1 & ) 2>/dev/null
sleep 1
check "the fake gateway tree runs (serve + detached worker)" "$([[ $(sandbox_procs live | wc -w) -ge 2 ]]; echo $?)"
run_in live AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$LD"
check "exits 0" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
check "lists the running tree, then stops it (the SIGTERM-proof worker with SIGKILL)" "$(has "$OUT" "gateway processes still running" && has "$OUT" "kill -TERM" && has "$OUT" "kill -KILL" && has "$OUT" "stopped the gateway processes"; echo $?)" "$OUT"
check "no sandbox gateway process is left" "$([[ -z "$(sandbox_procs live)" ]]; echo $?)" "$OUT"
check "the data dir (path with a space) is gone and stays gone" "$(sleep 0.5; [[ ! -e "$LD" ]]; echo $?)" "$OUT"
check "--purge deleted the Assistant's sessions and AbstractCode's settings" "$([[ ! -e "$LH/.abstractassistant" && ! -e "$LH/.abstractcode" ]]; echo $?)" "$OUT"
if [[ "$IS_MAC" == 1 ]]; then
    check "--purge deleted the gateway logs, its cache, the Assistant's log and the installer copy" "$([[ ! -e "$LH/Library/Logs/AbstractGateway" && ! -e "$LH/Library/Caches/AbstractGateway" && ! -e "$LH/Library/Logs/Assistant" && ! -e "$LH/Library/Application Support/AbstractFramework" ]]; echo $?)" "$OUT"
    check "D5: --purge deleted the Assistant's preferences plist, kept another app's" "$([[ ! -e "$LH/Library/Preferences/ai.abstractcore.abstractassistant.plist" && -f "$LH/Library/Preferences/com.example.other.plist" ]]; echo $?)" "$OUT"
    check "D5: and dropped the cached domain (defaults delete, recorded by the double, printed)" "$(grep -q "defaults delete ai.abstractcore.abstractassistant" "$WORK/live/launchd/calls.log" && has "$OUT" '\$ defaults delete ai.abstractcore.abstractassistant'; echo $?)" "$OUT"
else
    check "--purge deleted the gateway cache" "$([[ ! -e "$LH/.cache/abstractgateway" ]]; echo $?)" "$OUT"
fi
check "model weights and abstractcore's config are kept" "$([[ -f "$LH/.cache/huggingface/hub/weights" && -f "$LH/.abstractcore/config/abstractcore.json" ]] && has "$OUT" "kept: model weights"; echo $?)" "$OUT"
run_in live AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$LD"
check "second run: exit 0, nothing to do, no error" "$([[ $RC == 0 ]] && has "$OUT" "nothing to do" && has "$OUT" "no gateway process is running" && ! has "$OUT" "ERROR"; echo $?)" "$OUT"
pkill -9 -f "$WORK/live/" 2>/dev/null

echo "[7c] uninstall --print and the 'keep my data' answer change nothing"
PH="$WORK/printcase/home"; mkdir -p "$PH/$DATA_REL"; printf 'MODE=background\n' >"$PH/$DATA_REL/bootstrap.env"; populate_user_data "$PH"
snap() { (cd "$1" && find . -exec ls -ld {} + | awk '{print $1, $5, $NF}' | sort); }
before="$(snap "$PH")"
run_in printcase -- sh "$SCRIPTS_DIR/uninstall.sh" --purge --print
check "--print: exit 0, shows each rm -rf, changes nothing" "$([[ $RC == 0 ]] && has "$OUT" "rm -rf .*abstractassistant" && has "$OUT" "rm -rf .*$DATA_REL" && [[ "$(snap "$PH")" == "$before" ]]; echo $?)" "$OUT"
run_in printcase -- sh "$SCRIPTS_DIR/uninstall.sh" --yes
check "no --purge (answer N): exit 0, the data and the Assistant's sessions are kept" "$([[ $RC == 0 && -f "$PH/$DATA_REL/bootstrap.env" && -f "$PH/.abstractassistant/sessions.json" && -f "$PH/.abstractcode/prefs.json" ]] && has "$OUT" "kept the gateway data dir" && has "$OUT" "Also delete your AbstractFramework data" && has "$OUT" "-> no (default"; echo $?)" "$OUT"

echo "[7d] uninstall --purge: a folder that cannot be deleted is named, with what is left"
BH="$WORK/blocked/home"; BD="$WORK/blocked/data dir"; mkdir -p "$BD/runtime/locked" "$BH"
printf 'MODE=background\n' >"$BD/bootstrap.env"; echo x >"$BD/runtime/locked/ledger.jsonl"
if [[ "$IS_MAC" == 1 ]]; then chflags uchg "$BD/runtime/locked/ledger.jsonl"; else chmod 555 "$BD/runtime/locked"; fi
run_in blocked AF_RM_TRIES=2 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$BD"
check "exit 1 with the explicit listing and uninstall advice (never 'run the installer again')" "$([[ $RC == 1 ]] && has "$OUT" "could not delete" && has "$OUT" "ledger.jsonl" && has "$OUT" "the uninstaller could not delete" && has "$OUT" "run the uninstaller again" && ! has "$OUT" "run the installer again"; echo $?)" "$OUT"
[[ "$IS_MAC" == 1 ]] && check "the listing shows the uchg flag" "$(has "$OUT" "uchg"; echo $?)" "$OUT"
if [[ "$IS_MAC" == 1 ]]; then chflags -R nouchg "$BD"; else chmod 755 "$BD/runtime/locked"; fi
run_in blocked AF_RM_TRIES=2 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$BD"
check "once unlocked, a second run finishes (exit 0, dir gone; the failed run left its marker)" "$([[ $RC == 0 && ! -e "$BD" ]]; echo $?)" "$OUT"

echo "[7e] uninstall: recorded pids, app watchers, mounts, relative and unsafe data dirs, re-created data"
# D1: a stale pid file naming an unrelated process that happens to mention "abstract".
SH="$WORK/stale/home"; SD="$WORK/stale/data"; mkdir -p "$SH" "$SD/run"; printf 'MODE=background\n' >"$SD/bootstrap.env"
/usr/bin/python3 -c 'import time; time.sleep(60)  # abstract' </dev/null >/dev/null 2>&1 &
STALE_PID=$!
printf '{"pid": %s}\n' "$STALE_PID" >"$SD/run/gateway-serve.json"; echo "$STALE_PID" >"$SD/gateway.pid"
run_in stale AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --data-dir "$SD"
check "D1: a stale pid file's unrelated process is left alone, and said so" "$([[ $RC == 0 ]] && kill -0 "$STALE_PID" 2>/dev/null && has "$OUT" "stale pid file: pid $STALE_PID" && ! has "$OUT" "kill -TERM"; echo $?)" "$OUT"
kill -9 "$STALE_PID" 2>/dev/null
# ... even when it names the data dir: `tail -f <data>/logs/x` is not the gateway.
mkdir -p "$SD/logs"; echo x >"$SD/logs/x"
tail -f "$SD/logs/x" </dev/null >/dev/null 2>&1 &
TAIL_PID=$!
printf '{"pid": %s}\n' "$TAIL_PID" >"$SD/run/gateway-serve.json"; rm -f "$SD/gateway.pid"
run_in stale AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --data-dir "$SD"
check "D1: a stale pid naming a process that only mentions the data dir (tail -f) is left alone" "$([[ $RC == 0 ]] && kill -0 "$TAIL_PID" 2>/dev/null && has "$OUT" "stale pid file: pid $TAIL_PID" && ! has "$OUT" "kill -TERM"; echo $?)" "$OUT"
kill -9 "$TAIL_PID" 2>/dev/null

# D3: only `<node> -r <this data dir>/apps/_support/parent_watch.cjs` is an app of this gateway.
AH="$WORK/appw/home"; AD="$WORK/appw/data"; mkdir -p "$AH" "$AD/apps/_support"
printf 'MODE=background\n' >"$AD/bootstrap.env"; echo "//" >"$AD/apps/_support/parent_watch.cjs"
# a viewer whose command line names the file (not node): `less <data>/apps/_support/parent_watch.cjs`
bash -c 'exec -a "less $0/apps/_support/parent_watch.cjs" sleep 60' "$AD" </dev/null >/dev/null 2>&1 &
VIEWER_PID=$!
# argv as the gateway starts an app: node -r <data>/apps/_support/parent_watch.cjs <bin.js>
bash -c 'exec -a "node -r $0/apps/_support/parent_watch.cjs $0/app.js" sleep 60' "$AD" </dev/null >/dev/null 2>&1 &
NODE_PID=$!
sleep 0.3
run_in appw AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --data-dir "$AD"
check "D3: the app (node -r <data>/apps/_support/parent_watch.cjs) is stopped" "$(! kill -0 "$NODE_PID" 2>/dev/null; echo $?)" "$OUT"
check "D3: another program naming parent_watch.cjs is left alone" "$(kill -0 "$VIEWER_PID" 2>/dev/null; echo $?)" "$OUT"
kill -9 "$VIEWER_PID" "$NODE_PID" 2>/dev/null

# D2: a volume mounted inside the data dir, listed by `mount` under a linked path.
MH="$WORK/mnt/home"; MD="$WORK/mnt/data"; mkdir -p "$MH" "$MD/vol" "$WORK/mnt/bin"; ln -s "$WORK/mnt" "$WORK/mntlink"
printf 'MODE=background\n' >"$MD/bootstrap.env"; echo keep >"$MD/vol/on-the-volume"
if [[ "$IS_MAC" == 1 ]]; then MLINE="/dev/disk9s1 on $WORK/mntlink/data/vol (apfs, local, nodev)"
else MLINE="/dev/sdz1 on $WORK/mntlink/data/vol type ext4 (rw,relatime)"; fi
printf '#!/bin/sh\n/sbin/mount 2>/dev/null || /bin/mount 2>/dev/null\necho "%s"\n' "$MLINE" >"$WORK/mnt/bin/mount"; chmod +x "$WORK/mnt/bin/mount"
run_in mnt AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$MD"
check "D2: a mount inside the data dir (listed via a linked path) is refused, nothing deleted" "$([[ $RC == 1 && -f "$MD/vol/on-the-volume" ]] && has "$OUT" "a volume is mounted inside"; echo $?)" "$OUT"

# D6: a relative --data-dir is resolved once; the root and the home folder are refused.
RH="$WORK/rel/home"; mkdir -p "$RH" "$WORK/rel/cwd" "$WORK/rel/rel-data"; printf 'MODE=background\n' >"$WORK/rel/rel-data/bootstrap.env"
run_in rel AF_STOP_TIMEOUT=1 -- sh -c "cd '$WORK/rel/cwd' && sh '$SCRIPTS_DIR/uninstall.sh' --yes --purge --data-dir ../rel-data"
check "D6: a relative data dir is shown and deleted as an absolute path" "$([[ $RC == 0 && ! -e "$WORK/rel/rel-data" && -d "$WORK/rel/cwd" ]] && has "$OUT" "rm -rf $WORK/rel/rel-data" && ! has "$OUT" "rm -rf ../"; echo $?)" "$OUT"
run_in refuse_home -- sh -c 'sh "$0" --purge --print --data-dir "$HOME"' "$SCRIPTS_DIR/uninstall.sh"
check "D6: --data-dir \$HOME is refused" "$([[ $RC == 2 && -d "$HOME_T" ]] && has "$OUT" "refusing the data dir" && ! has "$OUT" "rm -rf"; echo $?)" "$OUT"
run_in refuse_root -- sh "$SCRIPTS_DIR/uninstall.sh" --purge --print --data-dir /
check "D6: --data-dir / is refused" "$([[ $RC == 2 ]] && has "$OUT" "refusing the data dir" && ! has "$OUT" "rm -rf"; echo $?)" "$OUT"

# D4: a writer the uninstaller does not recognise re-creates the data dir after its deletion.
WH="$WORK/back/home"; WD="$WORK/back/data"; mkdir -p "$WH" "$WD"; printf 'MODE=background\n' >"$WD/bootstrap.env"
printf '#!/bin/sh\nwhile :; do sleep 0.3; mkdir -p "$AF_T_DIR" && date >>"$AF_T_DIR/again.log"; done\n' >"$WORK/back/writer"
AF_T_DIR="$WD" sh "$WORK/back/writer" </dev/null >/dev/null 2>&1 &
BACK_PID=$!
run_in back AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$WD"
check "D4: a data dir re-created after its deletion fails the run (exit 1) and is named" "$([[ $RC == 1 ]] && has "$OUT" "is back: a program is still writing there" && has "$OUT" "re-created after it was deleted"; echo $?)" "$OUT"
kill -9 "$BACK_PID" 2>/dev/null

echo "[7f] uninstall --purge refuses a folder that is not a gateway data dir (D9)"
# ~/Library of the sandbox home: files, no gateway marker.
run_in d9lib -- sh -c 'mkdir -p "$HOME/Library/Keep" && echo k >"$HOME/Library/Keep/file" && sh "$0" --yes --purge --data-dir "$HOME/Library"' "$SCRIPTS_DIR/uninstall.sh"
check "D9: --data-dir ~/Library is refused (exit 2), nothing deleted" "$([[ $RC == 2 && -f "$HOME_T/Library/Keep/file" ]] && has "$OUT" "refusing to purge" && ! has "$OUT" "rm -rf"; echo $?)" "$OUT"
# The parent of the home folder, with a sibling user folder in it.
mkdir -p "$WORK/d9parent/other"; echo s >"$WORK/d9parent/other/file"
run_in d9parent -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$WORK/d9parent"
check "D9: the parent of the home folder is refused (exit 2), home and sibling kept" "$([[ $RC == 2 && -d "$HOME_T" && -f "$WORK/d9parent/other/file" ]] && has "$OUT" "contains your home folder"; echo $?)" "$OUT"
run_in d9parent -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$WORK"
check "D9: a folder further up (the sandbox root) is refused too" "$([[ $RC == 2 && -f "$WORK/d9parent/other/file" ]]; echo $?)" "$OUT"
# A random folder with files, and an empty folder.
mkdir -p "$WORK/d9rand/data/notes"; echo n >"$WORK/d9rand/data/notes/todo.txt"; echo r >"$WORK/d9rand/data/README"
run_in d9rand -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$WORK/d9rand/data"
check "D9: a folder with files but no gateway marker is refused (exit 2), nothing deleted" "$([[ $RC == 2 && -f "$WORK/d9rand/data/notes/todo.txt" && -f "$WORK/d9rand/data/README" ]] && has "$OUT" "refusing to purge"; echo $?)" "$OUT"
mkdir -p "$WORK/d9empty/data"
run_in d9empty -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$WORK/d9empty/data"
check "D9: an empty folder is 'nothing to do' (exit 0)" "$([[ $RC == 0 ]] && has "$OUT" "nothing to do (empty folder"; echo $?)" "$OUT"
# A real-shaped gateway data dir without the installer's bootstrap.env.
mkdir -p "$WORK/d9real/data/auth" "$WORK/d9real/data/run" "$WORK/d9real/data/artifacts"
echo '{}' >"$WORK/d9real/data/auth/users.json"; : >"$WORK/d9real/data/gateway.sqlite3"; echo a >"$WORK/d9real/data/artifacts/a"
run_in d9real -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge --data-dir "$WORK/d9real/data"
check "D9: a real-shaped gateway data dir (sqlite, auth/users.json) is deleted" "$([[ $RC == 0 && ! -e "$WORK/d9real/data" ]]; echo $?)" "$OUT"

echo "[8] Install AbstractFramework.command"
C="$WORK/cmd"; mkdir -p "$C"
cp "$SCRIPTS_DIR/Install AbstractFramework.command" "$C/"
printf '#!/bin/sh\necho "STUB install.sh $*"\nexit "${STUB_RC:-0}"\n' >"$C/install.sh"
# curl doubles: one serves "the latest install.sh" for the one-liner's URL, one cannot reach GitHub.
for n in cmd_ok cmd_fail cmd_offline cmd_portal; do mkdir -p "$WORK/$n/bin"; done
for n in cmd_ok cmd_fail; do
    cat >"$WORK/$n/bin/curl" <<'CURL'
#!/bin/sh
out=""; url=""; prev=""
for a in "$@"; do [ "$prev" = -o ] && out="$a"; case "$a" in https://*) url="$a" ;; esac; prev="$a"; done
[ "$url" = "https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh" ] || exit 22
printf '#!/bin/sh\necho "LATEST install.sh $*"\nexit "${STUB_RC:-0}"\n' >"$out"
CURL
    chmod +x "$WORK/$n/bin/curl"
done
printf '#!/bin/sh\nexit 6\n' >"$WORK/cmd_offline/bin/curl"; chmod +x "$WORK/cmd_offline/bin/curl"
# A captive portal: curl succeeds, but the "script" is an HTML sign-in page.
printf '#!/bin/sh\nout=""; prev=""\nfor a in "$@"; do [ "$prev" = -o ] && out="$a"; prev="$a"; done\nprintf "<html><body>Sign in to the network</body></html>\\n" >"$out"\n' >"$WORK/cmd_portal/bin/curl"; chmod +x "$WORK/cmd_portal/bin/curl"
run_in cmd_ok -- sh "$C/Install AbstractFramework.command" --port 18829
check "runs the LATEST install.sh (the one-liner's) with --interactive and the user's args, not its own copy" "$(has "$OUT" "LATEST install.sh --interactive --port 18829" && ! has "$OUT" "STUB install.sh" && has "$OUT" "All done"; echo $?)" "$OUT"
run_in cmd_offline -- sh "$C/Install AbstractFramework.command" --port 18829
check "GitHub unreachable: runs the copy next to it, and says so" "$(has "$OUT" "STUB install.sh --interactive --port 18829" && has "$OUT" "GitHub could not be reached"; echo $?)" "$OUT"
run_in cmd_portal -- sh "$C/Install AbstractFramework.command" --port 18829
check "a download that is not the installer (captive portal HTML): not run; the copy next to it runs, and it says so" "$(has "$OUT" "STUB install.sh --interactive --port 18829" && has "$OUT" "The download was not the installer" && ! has "$OUT" "Sign in to the network"; echo $?)" "$OUT"
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
# These cases skip the terminal console (--no-console) unless BG_ARGS says otherwise;
# BG_TOOLBIN overrides the uv tool bin dir, BG_CARGO=1 adds a fake cargo (log: CARGOLOG;
# BG_CARGO_FAIL=CRATE makes that crate's build fail), BG_UV_LIST is what `uv tool list` prints.
# BG_TOOLDIR: what `uv tool dir` prints (the tool environments; default: the bin dir, as before).
# BG_SERVICE=1: the fake gateway has `abstractgateway service` (install starts the fake
# server, as a login item would; its pid in SVCPID) and --no-service is not passed, so the
# start-at-login question is under test (a fake `systemctl --user` on Linux).
bg_case() {
    local name="$1" network="$2" stored="${3:-}"
    local bin="$WORK/$name/bin" toolbin="${BG_TOOLBIN:-$WORK/$name/toolbin}"
    mkdir -p "$bin" "$toolbin" "$WORK/$name/home"
    GWLOG="$WORK/$name/gw.log"
    cat >"$bin/curl" <<CURL
#!/bin/sh
for a in "\$@"; do [ "\$a" = "https://pypi.org/simple/pip/" ] && exit 0; done
# Never download Rust from a test: rustup's installer is refused like a dead network.
for a in "\$@"; do [ "\$a" = "https://sh.rustup.rs" ] && exit 7; done
exec /usr/bin/curl "\$@"
CURL
    # The fake uv: every call is logged (UVLOG); `pip freeze` prints the environment's packages
    # (BG_FREEZE_BEFORE until an install, then BG_FREEZE_AFTER, when given).
    UVLOG="$WORK/$name/uv.log"; : >"$UVLOG"
    rm -f "$WORK/$name/freeze.now" "$WORK/$name/freeze.after"
    [[ -n "${BG_FREEZE_BEFORE:-}" ]] && printf '%b' "$BG_FREEZE_BEFORE" >"$WORK/$name/freeze.now"
    [[ -n "${BG_FREEZE_AFTER:-}" ]] && printf '%b' "$BG_FREEZE_AFTER" >"$WORK/$name/freeze.after"
    cat >"$bin/uv" <<UV
#!/bin/sh
echo "uv \$*" >>"$UVLOG"
case "\$1 \${2:-}" in
  "--version "*) echo "uv 0.0.0" ;;
  "tool dir") if [ "\${3:-}" != --bin ] && [ -n "${BG_TOOLDIR:-}" ]; then echo "${BG_TOOLDIR:-}"; else echo "$toolbin"; fi ;;
  "tool list") printf '%b\n' "${BG_UV_LIST:-abstractgateway v9.9.9}" ;;
  "tool install") [ -f "$WORK/$name/freeze.after" ] && cp "$WORK/$name/freeze.after" "$WORK/$name/freeze.now" ;;
  "pip freeze") [ -f "$WORK/$name/freeze.now" ] && cat "$WORK/$name/freeze.now" ;;
esac
exit 0
UV
    SVCPID="$WORK/$name/svc.pid"
    cat >"$toolbin/abstractgateway" <<GW
#!/bin/sh
D="\${ABSTRACTGATEWAY_DATA_DIR:-$WORK/$name/no-data-dir}"
echo "abstractgateway \$*" >>"$GWLOG"
# An old gateway has no \`network\` subcommand at all (argparse: invalid choice, exit 2).
[ "\$1" = network ] && [ "$network" != 1 ] && { echo "invalid choice: 'network'" >&2; exit 2; }
for a in "\$@"; do [ "\$a" = --help ] && { [ "\$1" = service ] && [ "${BG_SERVICE:-0}" != 1 ] && exit 2; exit 0; }; done
case "\$1 \${2:-}" in
  "service install")
    [ "${BG_SERVICE_FAIL:-0}" = 1 ] && { echo "Bootstrap failed: 5: Input/output error" >&2; exit 1; }
    port=""; prev=""; for a in "\$@"; do [ "\$prev" = --port ] && port="\$a"; prev="\$a"; done
    nohup /usr/bin/python3 -c 'import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"{\"service\": \"abstractgateway\"}")
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()' "\$port" </dev/null >/dev/null 2>&1 &
    echo \$! >"$SVCPID"; exit 0 ;;
  "service uninstall") [ -f "$SVCPID" ] && kill "\$(cat "$SVCPID")" 2>/dev/null; exit 0 ;;
  "service status") exit 0 ;;
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
    # BG_LINUX=1: the installer believes it runs on Linux (a fake uname), with a systemd user
    # session whose calls are logged (SYSTEMCTL_LOG); BG_UNIT_ACTIVE=1: the unit is running.
    SYSTEMCTL_LOG="$WORK/$name/systemctl.log"; : >"$SYSTEMCTL_LOG"
    if [[ "${BG_LINUX:-0}" == 1 ]]; then
        printf '#!/bin/sh\ncase "$1" in -s) echo Linux ;; -m) echo x86_64 ;; *) /usr/bin/uname "$@" ;; esac\n' >"$bin/uname"; chmod +x "$bin/uname"
    fi
    if [[ "${BG_SERVICE:-0}" == 1 && ( "$IS_MAC" == 0 || "${BG_LINUX:-0}" == 1 ) ]]; then
        cat >"$bin/systemctl" <<SCTL
#!/bin/sh
echo "systemctl \$*" >>"$SYSTEMCTL_LOG"
[ "\$2" = is-active ] && exit \$([ "${BG_UNIT_ACTIVE:-0}" = 1 ] && echo 0 || echo 3)
exit 0
SCTL
        chmod +x "$bin/systemctl"
    fi
    CARGOLOG="$WORK/$name/cargo.log"
    if [[ "${BG_CARGO:-0}" == 1 ]]; then
        # `install ... --root R NAME --version V` writes R/bin/NAME answering `--version` and
        # records it in R/.crates.toml, as cargo does; `uninstall --root R NAME` removes both.
        cat >"$bin/cargo" <<CARGO
#!/bin/sh
echo "cargo \$*" >>"$CARGOLOG"
[ "\$1" = --version ] && { echo "cargo ${BG_CARGO_VERSION:-1.90.0} (fake)"; exit 0; }
root=""; ver=""; prev=""; name=""
for a in "\$@"; do
  case "\$prev" in --root) root="\$a" ;; --version) ver="\$a" ;; esac
  case "\$a" in abstractgateway-console|abstractcode) name="\$a" ;; esac
  prev="\$a"
done
if [ "\$1" = uninstall ]; then
  rm -f "\$root/bin/\$name"; grep -v "^\\"\$name " "\$root/.crates.toml" >"\$root/.crates.new"; mv "\$root/.crates.new" "\$root/.crates.toml"; exit 0
fi
[ "\$name" = "${BG_CARGO_FAIL:-none}" ] && { echo "error: could not compile \$name" >&2; exit 101; }
mkdir -p "\$root/bin"
printf '#!/bin/sh\\necho "\$*" >>"\$0.args"\\necho "%s %s"\\n' "\$name" "\$ver" >"\$root/bin/\$name"
chmod +x "\$root/bin/\$name"
echo "\\"\$name \$ver (registry+https://github.com/rust-lang/crates.io-index)\\" = [\\"\$name\\"]" >>"\$root/.crates.toml"
exit 0
CARGO
        chmod +x "$bin/cargo"
    fi
    local data_rel="$DATA_REL"; [[ "${BG_LINUX:-0}" == 1 ]] && data_rel=".local/share/abstractgateway"
    DATA_T="${BG_DATA_T:-$WORK/$name/home/$data_rel}"; NETF="$DATA_T/fake-network"
    if [[ -n "$stored" ]]; then mkdir -p "$DATA_T"; echo "$stored" >"$NETF"; fi
    # BG_STATE: a previous install's bootstrap.env (printf %b); BG_POINTER: a gateway.json already there.
    if [[ -n "${BG_STATE:-}" ]]; then mkdir -p "$DATA_T"; printf '%b' "$BG_STATE" >"$DATA_T/bootstrap.env"; fi
    # BG_PRERUN=1: the previous install's background gateway is running (pid in gateway.pid: PRE_PID).
    # BG_FOREIGN=1: a gateway answers on the port but this installer did not start it (no gateway.pid,
    # no login item: a hand-started `serve`); its pid is PRE_PID too.
    PRE_PID=""
    if [[ "${BG_PRERUN:-0}" == 1 || "${BG_FOREIGN:-0}" == 1 ]]; then
        mkdir -p "$DATA_T"
        /usr/bin/python3 -c 'import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"{\"service\": \"abstractgateway\"}")
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()' "$BG_PORT" </dev/null >/dev/null 2>&1 &
        PRE_PID=$!; [[ "${BG_FOREIGN:-0}" == 1 ]] || echo "$PRE_PID" >"$DATA_T/gateway.pid"
        for _ in 1 2 3 4 5 6 7 8 9 10; do lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1 && break; sleep 0.3; done
    fi
    PTR="$WORK/$name/home/.abstractframework/gateway.json"
    if [[ -n "${BG_POINTER:-}" ]]; then mkdir -p "$(dirname "$PTR")"; printf '%s\n' "$BG_POINTER" >"$PTR"; fi
    # BG_TOKEN: the admin token a real gateway writes into its data dir at first start.
    if [[ -n "${BG_TOKEN:-}" ]]; then mkdir -p "$DATA_T/auth"; printf '%s\n' "$BG_TOKEN" >"$DATA_T/auth/bootstrap-admin-token"; fi
    # BG_ENV: extra environment (e.g. SSH_CONNECTION); BG_PTY=1 runs the installer on a pseudo-terminal.
    # BG_OPEN=1 leaves --no-open out (the remote-session console launch is under test).
    local wrap=() open_flag=(--no-open)
    # BG_PTY=1: the installer runs on a pseudo-terminal that is its controlling terminal; with
    # BG_PTY_ENTER=1 the runner presses Enter when the console offer appears; BG_PTY_ANSWER="TEXT KEY"
    # (repeatable, separated by '|') types KEY ("enter" or one character) when TEXT appears.
    # BG_PTY=2: stdout is a pseudo-terminal but the process has NO controlling terminal
    # (/dev/tty cannot be opened).
    # (pty.spawn() spins forever on macOS when stdin is /dev/null, hence these small runners.)
    local answers="${BG_PTY_ANSWER:-}"
    [[ "${BG_PTY_ENTER:-0}" == 1 ]] && answers="${answers:+$answers|}Press Enter within enter"
    [[ "${BG_PTY:-0}" == 1 ]] && wrap=(/usr/bin/python3 -c 'import os, pty, sys
todo = []
for item in filter(None, sys.argv[1].split("|")):
    text, key = item.rsplit(" ", 1)
    todo.append((text.encode(), b"\r" if key == "enter" else key.encode()))
pid, fd = pty.fork()
if pid == 0:
    os.execvp(sys.argv[2], sys.argv[2:])
seen = b""
while True:
    try:
        chunk = os.read(fd, 4096)
    except OSError:
        break
    if not chunk:
        break
    os.write(1, chunk)
    seen = (seen + chunk)[-4096:]
    if todo and todo[0][0] in seen:
        os.write(fd, todo.pop(0)[1])
        seen = b""
sys.exit(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]))' "$answers")
    [[ "${BG_PTY:-0}" == 2 ]] && wrap=(/usr/bin/python3 -c 'import os, subprocess, sys
master, slave = os.openpty()
proc = subprocess.Popen(sys.argv[1:], stdin=subprocess.DEVNULL, stdout=slave, stderr=slave, start_new_session=True)
os.close(slave)
while True:
    try:
        chunk = os.read(master, 4096)
    except OSError:
        break
    if not chunk:
        break
    os.write(1, chunk)
sys.exit(proc.wait())')
    [[ "${BG_OPEN:-0}" == 1 ]] && open_flag=()
    local svc_flag=(--no-service)
    [[ "${BG_SERVICE:-0}" == 1 ]] && svc_flag=()
    # BG_NO_PORT=1: no --port (the port comes from bootstrap.env, as for the gateway's Update run).
    local port_flag=(--port "$BG_PORT")
    [[ "${BG_NO_PORT:-0}" == 1 ]] && port_flag=()
    run_in "$name" ${BG_ENV:-} -- ${wrap[@]+"${wrap[@]}"} "${BG_SHELL:-sh}" "$SCRIPTS_DIR/install.sh" --profile light ${port_flag[@]+"${port_flag[@]}"} ${svc_flag[@]+"${svc_flag[@]}"} ${open_flag[@]+"${open_flag[@]}"} --no-modify-path ${BG_ARGS:---no-console}
    local pid f
    # the background gateway (any data dir: BG_ARGS may pass --data-dir) and the login item's
    while IFS= read -r f; do
        pid="$(cat "$f" 2>/dev/null)"
        [[ -n "$pid" ]] && kill "$pid" 2>/dev/null
    done < <(find "$WORK/$name" -name gateway.pid 2>/dev/null; echo "$SVCPID")
    [[ -n "$PRE_PID" ]] && kill "$PRE_PID" 2>/dev/null
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
    # 0943: the pointer, written by the installer once the gateway answered (default data dir).
    PTR_DD="$(cd "$DATA_T" && pwd -P)"
    check "pointer: written after the health check, the contract's keys, written_by installer" "$(/usr/bin/python3 -c 'import json, sys
d = json.load(open(sys.argv[1]))
assert set(d) == {"schema", "url", "port", "data_dir", "updated_at", "written_by"}, d
assert d["schema"] == 1 and d["url"] == "http://127.0.0.1:" + sys.argv[2] and d["port"] == int(sys.argv[2]), d
assert d["data_dir"] == sys.argv[3] and d["written_by"] == "installer" and d["updated_at"].endswith("Z"), d' "$PTR" "$BG_PORT" "$PTR_DD" 2>&1; echo $?)" "$OUT"
    check "pointer: mode 0600, no token, no temp file left" "$([[ "$(stat -f %Lp "$PTR" 2>/dev/null || stat -c %a "$PTR")" == 600 ]] && ! grep -qi token "$PTR" && [[ "$(ls -A "$(dirname "$PTR")")" == gateway.json ]]; echo $?)" "$OUT"
    check "pointer: the installer says where it wrote it" "$(has "$OUT" "gateway pointer: $PTR -> http://127.0.0.1:$BG_PORT"; echo $?)" "$OUT"
    # The installer owns the install it just made: a pointer naming another data dir is replaced, and said so.
    BG_POINTER='{"data_dir": "/elsewhere/other-gateway", "port": 9999, "schema": 1, "updated_at": "2026-01-01T00:00:00Z", "url": "http://127.0.0.1:9999", "written_by": "serve"}' bg_case bg_ptr_other 1
    check "pointer: one naming another gateway's data dir is replaced by this install, and said so" "$([[ $RC == 0 ]] && grep -q "\"port\": $BG_PORT" "$PTR" && grep -q "\"data_dir\": \"$(cd "$DATA_T" && pwd -P)\"" "$PTR" && grep -q '"written_by": "installer"' "$PTR" && has "$OUT" "the gateway pointer named the gateway with data directory /elsewhere/other-gateway; it now names this install"; echo $?)" "$OUT"
    BG_POINTER='not json' bg_case bg_ptr_bad 1
    check "pointer: an unreadable one is replaced" "$([[ $RC == 0 ]] && grep -q '"written_by": "installer"' "$PTR"; echo $?)" "$OUT"
    # ... and one naming this data dir (through a linked path) is taken over.
    mkdir -p "$WORK/bg_ptr_mine/home/$DATA_REL"; ln -s "$WORK/bg_ptr_mine/home" "$WORK/bg_ptr_mine/homelink"
    BG_POINTER="{\"data_dir\": \"$WORK/bg_ptr_mine/homelink/$DATA_REL\", \"port\": 9999, \"schema\": 1, \"updated_at\": \"x\", \"url\": \"http://127.0.0.1:9999\", \"written_by\": \"serve\"}" bg_case bg_ptr_mine 1
    check "pointer: one naming this data dir (via a link) is rewritten with the install's port" "$([[ $RC == 0 ]] && grep -q "\"port\": $BG_PORT" "$PTR" && grep -q '"written_by": "installer"' "$PTR"; echo $?)" "$OUT"
    # A custom --data-dir, first install: the installer is the one writer that knows it.
    BG_ARGS="--no-console --data-dir $WORK/bg_ptr_custom/data" bg_case bg_ptr_custom 1
    check "pointer: a custom --data-dir first install writes the pointer naming that data dir" "$([[ $RC == 0 ]] && grep -q "\"data_dir\": \"$WORK/bg_ptr_custom/data\"" "$PTR" && grep -q "\"port\": $BG_PORT" "$PTR"; echo $?)" "$OUT"

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

echo "[11] terminal console and AbstractCode's terminal client: built by default, both in the summary"
# The same fake gateway, a fake cargo, and a uv tool bin dir named .../bin, so the console
# must be built with --root <its parent> and land next to `abstractgateway`.
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the terminal console cases" 1
else
    TB="$WORK/con/tools/bin"
    CON_PIN="$(sed -n 's/^AF_CRATE_CONSOLE="abstractgateway-console@\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    check "console: install.sh pins the terminal console" "$([[ -n "$CON_PIN" ]]; echo $?)"
    CODE_PIN="$(sed -n 's/^AF_CRATE_CODE_CLI="abstractcode@\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    check "code CLI: install.sh pins AbstractCode's terminal client" "$([[ -n "$CODE_PIN" ]]; echo $?)"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_sandbox_123" bg_case con 1
    check "console: installer succeeds" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "console: cargo builds the pinned crate into the tool bin dir" "$(grep -qx "cargo install --locked --force --root $WORK/con/tools abstractgateway-console --version $CON_PIN" "$CARGOLOG" && [[ -x "$TB/abstractgateway-console" ]]; echo $?)" "$CARGOLOG"
    check "console: summary gives the web console and its tunnel hint" "$(has "$OUT" "Web:  *http://127.0.0.1:$BG_PORT/console" && has "$OUT" "ssh -L $BG_PORT:127.0.0.1:$BG_PORT"; echo $?)" "$OUT"
    check "console: summary gives the terminal console command with the admin token (--token)" "$(has "$OUT" "Terminal:  abstractgateway-console --gateway-url http://127.0.0.1:$BG_PORT --token tok_sandbox_123$"; echo $?)" "$OUT"
    check "console: no 'browser now shows' claim when no browser was opened" "$(! has "$OUT" "browser now shows"; echo $?)" "$OUT"
    check "code CLI: built by default with the same cargo and --root, next to the console" "$(grep -qx "cargo install --locked --force --root $WORK/con/tools abstractcode --version $CODE_PIN" "$CARGOLOG" && [[ -x "$TB/abstractcode" ]]; echo $?)" "$CARGOLOG"
    # Sign-in: the token given directly, ready to paste, once; never saved by the installer; no
    # --gateway-url (abstractcode follows the gateway pointer); the no-token way on this machine.
    check "code CLI: summary says how to sign it in (login --token, then abstractcode; or tui-command)" "$(has "$OUT" "^  Sign in (terminal, once): abstractcode login --token tok_sandbox_123$" && has "$OUT" "^    then run: abstractcode$" && has "$OUT" "^    or, on this machine, without a token: abstractgateway apps tui-command code$" && has "$OUT" "Code:  *abstractcode   (sign in once: abstractcode login --token tok_sandbox_123; or on this machine: abstractgateway apps tui-command code)$" && ! has "$OUT" "abstractcode --gateway-url" && [[ ! -e "$WORK/con/home/.abstractcode" ]] && ! grep -qs login "$TB/abstractcode.args"; echo $?)" "$OUT"
    check "summary: lists the commands and says what abstractgateway-config is" "$(has "$OUT" "Commands (in $TB" && has "$OUT" "^      abstractgateway-config   the gateway's admin command: status" && has "$OUT" "^      abstractcode  " && has "$OUT" "^      abstractcore  "; echo $?)" "$OUT"
    check "core CLI: the library commands are exposed by default" "$(has "$OUT" "tool install .*--with-executables-from abstractcore --with-executables-from abstractvoice --with-executables-from abstractvision --with-executables-from abstractmusic "; echo $?)" "$OUT"
    # --uninstall removes both binaries it built (cargo uninstall --root, as it built them).
    run_in con AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/install.sh" --uninstall --yes
    check "uninstall: removes the console and AbstractCode's terminal client from the tool bin dir" "$([[ $RC == 0 && ! -e "$TB/abstractgateway-console" && ! -e "$TB/abstractcode" ]] && grep -qx "cargo uninstall --root $WORK/con/tools abstractcode" "$CARGOLOG" && grep -qx "cargo uninstall --root $WORK/con/tools abstractgateway-console" "$CARGOLOG"; echo $?)" "$OUT"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_sandbox_123" bg_case con 1
    # A re-run finds the pinned binary and does not build again.
    : >"$CARGOLOG"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " bg_case con 1
    check "console: a re-run keeps the installed console (no cargo install)" "$([[ $RC == 0 ]] && ! grep -q "cargo install" "$CARGOLOG" && has "$OUT" "abstractgateway-console $CON_PIN already installed"; echo $?)" "$OUT"
    check "code CLI: a re-run keeps it too" "$(has "$OUT" "abstractcode $CODE_PIN already installed"; echo $?)" "$OUT"
    # The gateway updates abstractcode in place in the same folder: a newer one is kept (never
    # downgraded to the pin); an older one is rebuilt at the pin.
    : >"$CARGOLOG"; printf '#!/bin/sh\necho "abstractcode 9.10.0"\n' >"$TB/abstractcode"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " bg_case con 1
    check "code CLI: a newer abstractcode (the gateway's update) is kept, never downgraded" "$([[ $RC == 0 ]] && ! grep -q "install.* abstractcode " "$CARGOLOG" && has "$OUT" "abstractcode 9.10.0 already installed ($CODE_PIN or later)"; echo $?)" "$OUT"
    : >"$CARGOLOG"; printf '#!/bin/sh\necho "abstractcode 0.6.9"\n' >"$TB/abstractcode"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " bg_case con 1
    check "code CLI: an older abstractcode is rebuilt at the pin" "$([[ $RC == 0 ]] && grep -qx "cargo install --locked --force --root $WORK/con/tools abstractcode --version $CODE_PIN" "$CARGOLOG"; echo $?)" "$OUT"
    # A distro cargo older than 1.87 and no rustup: rustup is tried (refused here), soft.
    BG_TOOLBIN="$WORK/con3/tools/bin" BG_CARGO=1 BG_CARGO_VERSION=1.75.0 BG_ARGS=" " bg_case con3 1
    check "console: an old cargo without rustup falls back to rustup, and its failure is soft" "$([[ $RC == 0 ]] && has "$OUT" "cargo 1.75.0 .* is older than the Rust 1.87" && has "$OUT" "sh.rustup.rs" && has "$OUT" "Terminal:  not installed: Rust could not be installed" && ! grep -q "cargo install" "$CARGOLOG"; echo $?)" "$OUT"
    check "code CLI: the same Rust, the same reason" "$(has "$OUT" "AbstractCode (terminal): not installed: Rust could not be installed" && [[ "$(grep -c "skipped: Rust could not be installed" "$OUT")" == 1 ]]; echo $?)" "$OUT"
    BG_TOOLBIN="$WORK/con2/tools/bin" BG_CARGO=1 BG_ARGS="--no-console" bg_case con2 1
    check "console: --no-console skips the console; an existing cargo still builds AbstractCode's client" "$([[ $RC == 0 ]] && ! grep -q "abstractgateway-console" "$CARGOLOG" && grep -qx "cargo install --locked --force --root $WORK/con2/tools abstractcode --version $CODE_PIN" "$CARGOLOG" && has "$OUT" "Terminal:  not installed: skipped with --no-console"; echo $?)" "$OUT"
    BG_TOOLBIN="$WORK/con4/tools/bin" BG_CARGO=1 BG_ARGS="--no-console --no-code-cli" bg_case con4 1
    check "--no-console --no-code-cli: cargo is not even asked" "$([[ $RC == 0 ]] && [[ ! -s "$CARGOLOG" ]] && has "$OUT" "AbstractCode (terminal): not installed: skipped with --no-code-cli"; echo $?)" "$OUT"
    BG_TOOLBIN="$WORK/con5/tools/bin" BG_CARGO=1 BG_ARGS="--no-code-cli" bg_case con5 1
    check "--no-code-cli: the console is built, AbstractCode's client is not" "$([[ $RC == 0 && -x "$WORK/con5/tools/bin/abstractgateway-console" && ! -e "$WORK/con5/tools/bin/abstractcode" ]] && ! grep -q "abstractcode" "$CARGOLOG"; echo $?)" "$OUT"
    BG_TOOLBIN="$WORK/con7/tools/bin" BG_CARGO=1 BG_ARGS="--with-code-cli" bg_case con7 1
    check "--with-code-cli: kept as an alias of the default" "$([[ $RC == 0 && -x "$WORK/con7/tools/bin/abstractcode" ]] && grep -qx "cargo install --locked --force --root $WORK/con7/tools abstractcode --version $CODE_PIN" "$CARGOLOG"; echo $?)" "$OUT"
    # A failed build never fails the install: one warning, the command to run by hand, the summary says why.
    BG_TOOLBIN="$WORK/con6/tools/bin" BG_CARGO=1 BG_CARGO_FAIL=abstractcode BG_ARGS=" " bg_case con6 1
    check "code CLI: a failed build is soft: exit 0, one warning, the manual command, the summary says why" "$([[ $RC == 0 && -x "$WORK/con6/tools/bin/abstractgateway-console" ]] && [[ "$(grep -c "^  ! " "$OUT")" == "$(( $(grep -c "^  ! " "$WORK/con5/out.txt") + 1 ))" ]] && [[ "$(grep -c "AbstractCode's terminal client did not succeed" "$OUT")" == 1 ]] && has "$OUT" "build it by hand: .*cargo install --locked --force --root $WORK/con6/tools abstractcode --version $CODE_PIN" && has "$OUT" "AbstractCode (terminal): not installed: the build failed"; echo $?)" "$OUT"
    # A command name that another program already has in the tool bin dir: that package is left
    # out (uv would refuse the whole install); names the gateway's own tool has are fine.
    mkdir -p "$WORK/cli/tools/bin"; printf '#!/bin/sh\n' >"$WORK/cli/tools/bin/judge"; printf '#!/bin/sh\n' >"$WORK/cli/tools/bin/abstractvoice"
    BG_TOOLBIN="$WORK/cli/tools/bin" BG_UV_LIST='abstractgateway v9.9.9\n- abstractgateway\n- abstractgateway-config\n- judge\nother-tool v1.0\n- abstractvision' bg_case cli 1
    check "core CLI: a name owned by the gateway tool is not a conflict; another program's is, and is said" "$([[ $RC == 0 ]] && has "$OUT" "tool install .*--with-executables-from abstractcore --with-executables-from abstractvision --with-executables-from abstractmusic " && ! has "$OUT" "executables-from abstractvoice" && has "$OUT" "abstractvoice commands not exposed: $WORK/cli/tools/bin/abstractvoice already exists (another program's)"; echo $?)" "$OUT"
    printf '#!/bin/sh\n' >"$WORK/cli/tools/bin/abstractvision"
    BG_TOOLBIN="$WORK/cli/tools/bin" BG_UV_LIST='abstractgateway v9.9.9\n- abstractgateway\n- judge\nother-tool v1.0\n- abstractvision' bg_case cli 1
    check "core CLI: a name another uv tool owns is a conflict too" "$([[ $RC == 0 ]] && has "$OUT" "abstractvision commands not exposed: $WORK/cli/tools/bin/abstractvision already exists (another program's)"; echo $?)" "$OUT"
    BG_TOOLBIN="$WORK/cli2/tools/bin" BG_ARGS="--no-console --no-core-cli" bg_case cli2 1
    check "--no-core-cli: only the gateway's own commands" "$([[ $RC == 0 ]] && ! has "$OUT" "executables-from" && ! has "$OUT" "^      abstractcore "; echo $?)" "$OUT"
fi

echo "[12] remote or headless session: the terminal console opens at the end, signed in"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the remote-session cases" 1
else
    TB="$WORK/rem/tools/bin"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_PTY=1 BG_PTY_ENTER=1 BG_OPEN=1 bg_case rem 1
    check "remote: installer succeeds on a terminal" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "remote: the console is started with the gateway URL and the admin token" "$(grep -qx -- "--gateway-url http://127.0.0.1:$BG_PORT --token tok_remote_9" "$TB/abstractgateway-console.args"; echo $?)" "$OUT"
    check "remote: the console is offered, not assumed" "$(has "$OUT" "Press Enter within 25 s to open the terminal console"; echo $?)" "$OUT"
    check "remote: no browser is opened over SSH" "$([[ ! -s "$WORK/rem/open.log" ]] && has "$OUT" "tunnel it first: ssh -L $BG_PORT:127.0.0.1:$BG_PORT"; echo $?)" "$OUT"
    TB2="$WORK/rem2/tools/bin"
    BG_TOOLBIN="$TB2" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_PTY=1 bg_case rem2 1
    check "remote: --no-open does not start the console" "$([[ $RC == 0 ]] && ! grep -q -- "--gateway-url" "$TB2/abstractgateway-console.args"; echo $?)" "$OUT"
    # Nobody at the pseudo-terminal (CI, Terraform, ssh -t in a script): the offer times out.
    TB4="$WORK/rem4/tools/bin"
    BG_TOOLBIN="$TB4" BG_CARGO=1 BG_ARGS="--console-wait 1" BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_PTY=1 BG_OPEN=1 bg_case rem4 1
    check "remote: nobody answers the offer, the install still finishes and opens nothing" "$([[ $RC == 0 ]] && ! grep -q -- "--gateway-url" "$TB4/abstractgateway-console.args" && has "$OUT" "not opened; start it any time"; echo $?)" "$OUT"
    # Debian/Ubuntu /bin/sh is dash: a terminal on stdout but no controlling terminal must not
    # abort the finished install (a failed redirection on the special built-in ':' exits dash).
    if command -v dash >/dev/null 2>&1; then
        TB5="$WORK/rem5/tools/bin"
        BG_TOOLBIN="$TB5" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_PTY=2 BG_SHELL=dash BG_OPEN=1 bg_case rem5 1
        check "remote: dash without a controlling terminal exits 0 and opens nothing" "$([[ $RC == 0 ]] && ! grep -q -- "--gateway-url" "$TB5/abstractgateway-console.args"; echo $?)" "$OUT"
    fi
    TB3="$WORK/rem3/tools/bin"
    BG_TOOLBIN="$TB3" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_OPEN=1 bg_case rem3 1
    check "remote: without a terminal (piped output) the console is not started" "$([[ $RC == 0 ]] && ! grep -q -- "--gateway-url" "$TB3/abstractgateway-console.args"; echo $?)" "$OUT"
fi

echo "[13] start at login on a terminal (the fake gateway has 'abstractgateway service')"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the start-at-login cases" 1
else
    BG_SERVICE=1 BG_PTY=1 BG_PTY_ANSWER="when you log in? enter" bg_case login_tty_enter 1
    check "terminal + Enter: installer succeeds" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "terminal + Enter: asked with the time limit, answered yes" "$(has "$OUT" "when you log in?.*\[Y/n\] (Enter = yes; no answer within 25 s = no)" && has "$OUT" "start at login: yes (your answer"; echo $?)" "$OUT"
    check "terminal + Enter: the login service is registered (--port only), mode service" "$(grep -qx "abstractgateway service install --port $BG_PORT" "$GWLOG" && grep -qx "MODE=service" "$DATA_T/bootstrap.env" && ! has "$OUT" "Start at login is off"; echo $?)" "$GWLOG"
    BG_SERVICE=1 BG_PTY=1 BG_PTY_ANSWER="when you log in? n" bg_case login_tty_no 1
    check "terminal + 'n': no service, background start, the summary says how to turn it on" "$([[ $RC == 0 ]] && ! grep -q "service install" "$GWLOG" && grep -qx "MODE=background" "$DATA_T/bootstrap.env" && has "$OUT" "start at login: no (your answer" && has "$OUT" "Start at login is off"; echo $?)" "$OUT"
    BG_SERVICE=1 BG_PTY=1 BG_ARGS="--no-console --ask-wait 1" bg_case login_tty_silent 1
    check "terminal, nobody answers: the install finishes, a first install leaves it off" "$([[ $RC == 0 ]] && ! grep -q "service install" "$GWLOG" && has "$OUT" "no answer within 1 s, so a first install leaves it off"; echo $?)" "$OUT"
    BG_SERVICE=1 bg_case login_notty 1
    check "no terminal (automation): not enabled, never asked" "$([[ $RC == 0 ]] && ! grep -q "service install" "$GWLOG" && ! has "$OUT" "\[Y/n\]" && has "$OUT" "start at login: no (no terminal to ask on"; echo $?)" "$OUT"
    check "no terminal: the summary says how to turn it on (either console's switch, or the command)" "$(has "$OUT" "Start at login is off. To turn it on: the Start at login switch in either console" && has "$OUT" "or run: abstractgateway service enable"; echo $?)" "$OUT"
    BG_SERVICE=1 BG_STATE='PORT=18870\nMODE=service\nPROFILE=light\n' bg_case login_rerun 1
    check "re-run without a terminal keeps the recorded 'yes'" "$([[ $RC == 0 ]] && grep -qx "abstractgateway service install --port $BG_PORT" "$GWLOG" && has "$OUT" "start at login: yes (kept from the previous install"; echo $?)" "$OUT"
    BG_SERVICE=1 BG_STATE='PORT=18870\nMODE=service\nPROFILE=light\n' BG_PTY=1 BG_PTY_ANSWER="when you log in? n" bg_case login_rerun_no 1
    check "re-run, answered 'n' on a terminal: the recorded 'yes' is the default, the answer wins" "$([[ $RC == 0 ]] && has "$OUT" "when you log in?.*\[Y/n\] (Enter = yes; no answer within 25 s = yes, as now)" && ! grep -q "service install" "$GWLOG" && grep -qx "abstractgateway service uninstall" "$GWLOG" && grep -qx "MODE=background" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"
    if command -v dash >/dev/null 2>&1; then
        BG_SERVICE=1 BG_PTY=2 BG_SHELL=dash bg_case login_dash 1
        check "dash, terminal output but no controlling terminal: exit 0, not enabled" "$([[ $RC == 0 ]] && ! grep -q "service install" "$GWLOG" && has "$OUT" "start at login: no (no terminal to ask on"; echo $?)" "$OUT"
    fi
fi

echo "[14] uninstall removes the gateway pointer only when it names this install's data dir"
UH="$WORK/ptr_uninst/home"; UD="$UH/$DATA_REL"; mkdir -p "$UD" "$UH/.abstractframework"; printf 'MODE=background\n' >"$UD/bootstrap.env"
printf '{\n  "data_dir": "%s",\n  "port": 8080,\n  "schema": 1,\n  "updated_at": "x",\n  "url": "http://127.0.0.1:8080",\n  "written_by": "installer"\n}\n' "$(cd "$UD" && pwd -P)" >"$UH/.abstractframework/gateway.json"
run_in ptr_uninst -- sh "$SCRIPTS_DIR/uninstall.sh" --purge --print
check "--print: shows the rm of the pointer, deletes nothing" "$([[ $RC == 0 && -f "$UH/.abstractframework/gateway.json" ]] && has "$OUT" "rm -f $UH/.abstractframework/gateway.json"; echo $?)" "$OUT"
run_in ptr_uninst AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes --purge
check "--uninstall --purge: the pointer naming this data dir is gone, the folder's other files stay" "$([[ $RC == 0 && ! -e "$UH/.abstractframework/gateway.json" && -d "$UH/.abstractframework" ]]; echo $?)" "$OUT"
OH="$WORK/ptr_keep/home"; mkdir -p "$OH/$DATA_REL" "$OH/.abstractframework"; printf 'MODE=background\n' >"$OH/$DATA_REL/bootstrap.env"
printf '{\n  "data_dir": "/elsewhere/other-gateway",\n  "port": 9999,\n  "schema": 1,\n  "url": "http://127.0.0.1:9999"\n}\n' >"$OH/.abstractframework/gateway.json"
run_in ptr_keep AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes
check "--uninstall: another gateway's pointer is kept, and said so" "$([[ $RC == 0 && -f "$OH/.abstractframework/gateway.json" ]] && has "$OUT" "kept the gateway pointer"; echo $?)" "$OUT"

echo "[15] uninstall removes the terminal app gateways before 0.7.1 put in <data>/apps/bin (data kept)"
# The gateway's Apps page installed abstractcode into <data>/apps/bin (not on PATH) before 0.7.1.
# A non-purge uninstall removes it (only the binaries the gateway installs there: TUI_BY_APP ->
# abstractcode), and the folder only when it is then empty.
AH="$WORK/appsbin/home"; AD="$AH/$DATA_REL"; mkdir -p "$AD/apps/bin"; printf 'MODE=background\n' >"$AD/bootstrap.env"
printf '#!/bin/sh\n' >"$AD/apps/bin/abstractcode"; chmod +x "$AD/apps/bin/abstractcode"
run_in appsbin -- sh "$SCRIPTS_DIR/uninstall.sh" --print
check "--print: shows the removal of <data>/apps/bin/abstractcode, deletes nothing" "$([[ $RC == 0 && -f "$AD/apps/bin/abstractcode" ]] && has "$OUT" "rm -f '$AD/apps/bin/abstractcode'"; echo $?)" "$OUT"
run_in appsbin AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes
check "--uninstall: the gateway-installed abstractcode and the emptied folder are gone, the data is kept" "$([[ $RC == 0 && ! -e "$AD/apps/bin" && -d "$AD/apps" && -f "$AD/bootstrap.env" ]] && has "$OUT" "rm -f '$AD/apps/bin/abstractcode'"; echo $?)" "$OUT"
BH="$WORK/appsbin2/home"; BD="$BH/$DATA_REL"; mkdir -p "$BD/apps/bin"; printf 'MODE=background\n' >"$BD/bootstrap.env"
printf '#!/bin/sh\n' >"$BD/apps/bin/abstractcode"; printf 'mine\n' >"$BD/apps/bin/abstractgateway-console"
run_in appsbin2 AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes
check "--uninstall: a file the gateway never installs there is kept, and so is the folder" "$([[ $RC == 0 && ! -e "$BD/apps/bin/abstractcode" && -f "$BD/apps/bin/abstractgateway-console" ]]; echo $?)" "$OUT"
CH="$WORK/appsbin3/home"; CD="$CH/$DATA_REL"; mkdir -p "$CD"; printf 'MODE=background\n' >"$CD/bootstrap.env"
run_in appsbin3 AF_STOP_TIMEOUT=1 -- sh "$SCRIPTS_DIR/uninstall.sh" --yes
check "--uninstall: no <data>/apps/bin, nothing said about it" "$([[ $RC == 0 ]] && ! has "$OUT" "apps/bin"; echo $?)" "$OUT"

echo "[16] upgrade: --pin latest re-resolves a pinned install; the summary gives working upgrade commands"
# A first install records `abstractgateway[...]==<pin>` in uv's receipt, so `uv tool upgrade`
# answers "Nothing to upgrade" and a plain `uv tool install` keeps what is there. --pin latest
# must therefore run `uv tool install --upgrade` with an unpinned spec, never `uv tool upgrade`.
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the upgrade cases" 1
else
    UP_STATE="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nGATEWAY_SPEC=abstractgateway[tray]==0.7.0\n"
    BG_UV_LIST='abstractgateway v0.7.0\n- abstractgateway' BG_STATE="$UP_STATE" BG_ARGS="--no-console --pin latest" bg_case up_latest 1
    check "--pin latest over a pinned install: uv tool install --upgrade, unpinned spec" "$([[ $RC == 0 ]] && grep "tool install " "$OUT" | grep -q -- " --upgrade " && grep "tool install " "$OUT" | grep -q "abstractgateway\[[a-z,]*\]'\?$" && ! grep "tool install " "$OUT" | grep -q "abstractgateway\[[a-z,]*\]=="; echo $?)" "$OUT"
    check "--pin latest over a pinned install: never uv tool upgrade (a no-op on a pinned install)" "$(! has "$OUT" "tool upgrade"; echo $?)" "$OUT"
    GW_PIN="$(sed -n 's/^AF_GATEWAY_PIN_DEFAULT="\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    BG_UV_LIST='abstractgateway v0.7.0\n- abstractgateway' BG_STATE="$UP_STATE" bg_case up_default 1
    check "a plain re-run installs the release pin, without --upgrade" "$([[ $RC == 0 ]] && grep "tool install " "$OUT" | grep -q "abstractgateway\[[a-z,]*\]==$GW_PIN" && ! grep "tool install " "$OUT" | grep -q -- " --upgrade "; echo $?)" "$OUT"
    check "summary: the upgrade lines are the one-liner and --pin latest, not uv tool upgrade" "$(has "$OUT" "Upgrade:    curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh " && has "$OUT" "install.sh | sh -s -- --pin latest " && ! has "$OUT" "uv tool upgrade"; echo $?)" "$OUT"
fi

echo "[17] re-running the line upgrades in place: detection, remembered choices, release matrix, restart, changes"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the re-run cases" 1
else
    GW_PIN="$(sed -n 's/^AF_GATEWAY_PIN_DEFAULT="\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    FW="$(sed -n 's/^AF_FRAMEWORK_VERSION="\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    MATRIX="$(sed -n 's/^AF_PY_MATRIX="\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    check "install.sh names its release and matrix" "$([[ -n "$FW" && "$MATRIX" == *abstractcore==* ]]; echo $?)"
    BG_UV_LIST='other-tool v1.0' bg_case up_first 1
    check "first install: says there is nothing to upgrade" "$([[ $RC == 0 ]] && has "$OUT" "^No AbstractFramework install found: installing AbstractFramework $FW$"; echo $?)" "$OUT"
    check "first install: records the release and the choices a re-run keeps" "$(grep -qx "FRAMEWORK_VERSION=$FW" "$DATA_T/bootstrap.env" && grep -qx "CONSOLE=0" "$DATA_T/bootstrap.env" && grep -qx "CORE_CLI=1" "$DATA_T/bootstrap.env" && grep -qx "TRAY=1" "$DATA_T/bootstrap.env" && grep -qx "FULL=0" "$DATA_T/bootstrap.env"; echo $?)" "$DATA_T/bootstrap.env"
    check "first install: the release matrix goes to uv as constraints" "$([[ -n "$MATRIX" ]] || exit 1; for c in $MATRIX; do grep -qx "$c" "$DATA_T/uv-constraints.txt" || exit 1; done; grep "tool install " "$UVLOG" | grep -q -- "--constraints uv-constraints.txt"; echo $?)" "$DATA_T/uv-constraints.txt"

    # A previous release, the console left out: a plain re-run (no options) upgrades, keeps the choice.
    UP_OLD="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nFRAMEWORK_VERSION=0.6.0\nCONSOLE=0\nGATEWAY_SPEC=abstractgateway[tray]==0.7.0\n"
    BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$UP_OLD" BG_CARGO=1 BG_ARGS=" " \
        BG_FREEZE_BEFORE='abstractgateway==0.7.0\nabstractcore==2.17.0\nAbstractRuntime==0.7.0\nnumpy==1.26.0\n' \
        BG_FREEZE_AFTER="abstractgateway==$GW_PIN\nabstractcore==2.18.0\nabstractruntime==0.7.1\nnumpy==2.0.0\n" bg_case up_old 1
    check "re-run over a previous release: 'found: upgrading to'" "$([[ $RC == 0 ]] && has "$OUT" "^AbstractFramework 0.6.0 found: upgrading to AbstractFramework $FW$"; echo $?)" "$OUT"
    check "re-run: the remembered --no-console is kept (said, and no console build)" "$(has "$OUT" "kept from the previous install: --no-console" && ! grep -q "abstractgateway-console" "$CARGOLOG" && grep -qx "CONSOLE=0" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"
    check "re-run: the libraries go to the release matrix (constraints), not only the gateway's floors" "$(grep -qx "abstractcore==$(printf '%s\n' $MATRIX | sed -n 's/^abstractcore==//p')" "$DATA_T/uv-constraints.txt" && grep "tool install " "$UVLOG" | grep -q -- "--constraints uv-constraints.txt"; echo $?)" "$UVLOG"
    check "re-run: the summary lists what changed, old -> new" "$(has "$OUT" "^  Changes:$" && has "$OUT" "^      AbstractFramework  *0.6.0 -> $FW$" && has "$OUT" "^      abstractgateway  *0.7.0 -> $GW_PIN$" && has "$OUT" "^      abstractcore  *2.17.0 -> 2.18.0$" && has "$OUT" "^      abstractruntime  *0.7.0 -> 0.7.1$" && has "$OUT" "(and 1 other packages of the gateway's environment)"; echo $?)" "$OUT"
    check "re-run: the plain block says it was upgraded" "$(has "$OUT" "^  Upgraded: AbstractFramework 0.6.0 -> $FW " && grep -qx "FRAMEWORK_VERSION=$FW" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"

    UP_SAME="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nFRAMEWORK_VERSION=$FW\nCONSOLE=0\nGATEWAY_SPEC=abstractgateway[tray]==$GW_PIN\nVOICE_SPEC=abstractvoice[supertonic,stt]\n"
    BG_UV_LIST="abstractgateway v$GW_PIN" BG_STATE="$UP_SAME" BG_FREEZE_BEFORE="abstractgateway==$GW_PIN\nabstractcore==2.18.0\n" bg_case up_same 1
    check "re-run at the release: 'already up to date', nothing changed" "$([[ $RC == 0 ]] && has "$OUT" "^AbstractFramework $FW found: already up to date" && has "$OUT" "^  Already up to date: AbstractFramework $FW; nothing changed.$" && has "$OUT" "^  Changes:    none$"; echo $?)" "$OUT"

    # A library-only release (the gateway's version is the same): the running gateway still restarts.
    BG_UV_LIST="abstractgateway v$GW_PIN" BG_STATE="$UP_SAME" BG_PRERUN=1 \
        BG_FREEZE_BEFORE="abstractgateway==$GW_PIN\nabstractcore==2.17.9\n" BG_FREEZE_AFTER="abstractgateway==$GW_PIN\nabstractcore==2.18.0\n" bg_case up_libs 1
    check "a library-only change restarts the running background gateway" "$([[ $RC == 0 ]] && grep -qx "abstractgateway serve" "$GWLOG" && ! has "$OUT" "unchanged" && has "$OUT" "abstractcore  *2.17.9 -> 2.18.0"; echo $?)" "$OUT"
    BG_UV_LIST="abstractgateway v$GW_PIN" BG_STATE="$UP_SAME" BG_PRERUN=1 BG_FREEZE_BEFORE="abstractgateway==$GW_PIN\nabstractcore==2.18.0\n" bg_case up_nochange 1
    check "nothing changed: the running gateway is left alone" "$([[ $RC == 0 ]] && ! grep -q "serve" "$GWLOG" && has "$OUT" "already running (pid $PRE_PID), unchanged"; echo $?)" "$OUT"

    # Remembered choices: every option that changes what is installed, and the flag that turns one back on.
    UP_OPTS="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nFRAMEWORK_VERSION=$FW\nCONSOLE=0\nCODE_CLI=0\nCORE_CLI=0\nTRAY=0\nFULL=0\n"
    BG_STATE="$UP_OPTS" BG_CARGO=1 BG_ARGS=" " bg_case up_opts 1
    check "remembered: --no-console --no-code-cli --no-core-cli --no-tray kept by a plain re-run" "$([[ $RC == 0 ]] && has "$OUT" "kept from the previous install: --no-console, --no-code-cli, --no-core-cli, --no-tray" && [[ ! -s "$CARGOLOG" ]] && ! grep "tool install " "$UVLOG" | grep -q -- "--with-executables-from" && grep "tool install " "$UVLOG" | grep -q "abstractgateway==$GW_PIN$"; echo $?)" "$OUT"
    BG_STATE="$UP_OPTS" BG_ARGS="--no-console --with-core-cli --with-tray" bg_case up_opts2 1
    check "remembered: --with-core-cli and --with-tray turn them back on, and are recorded" "$([[ $RC == 0 ]] && grep "tool install " "$UVLOG" | grep -q -- "--with-executables-from abstractcore" && grep -qx "CORE_CLI=1" "$DATA_T/bootstrap.env" && grep -qx "TRAY=1" "$DATA_T/bootstrap.env" && grep -qx "CODE_CLI=0" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"
    if [[ "$IS_MAC" == 1 ]]; then
        check "remembered: --with-tray puts the tray extra back (macOS)" "$(grep "tool install " "$UVLOG" | grep -q "abstractgateway\[tray\]==$GW_PIN$"; echo $?)" "$UVLOG"
    fi
    mkdir -p "$WORK/up_full/home/$DATA_REL"; printf 'PORT=18829\nMODE=background\nPROFILE=light\nFULL=1\n' >"$WORK/up_full/home/$DATA_REL/bootstrap.env"
    run_in up_full -- sh "$SCRIPTS_DIR/install.sh" --print --port 18829 --profile light
    check "remembered: --full is kept by a re-run (--print: no llama.cpp wheel, the compiled extras kept)" "$(has "$OUT" "kept from the previous install: .*--full" && { has "$OUT" "tool install .*--with llama-cpp-python --constraints" || has "$OUT" "needs a C compiler"; }; echo $?)" "$OUT"

    # A custom data dir is kept through the gateway pointer (it names the data dir that holds this installer's state).
    BG_ARGS="--no-console --data-dir $WORK/up_dd/data" bg_case up_dd 1
    BG_ARGS="--no-console" bg_case up_dd 1
    check "a plain re-run keeps the custom --data-dir (found through the gateway pointer)" "$([[ $RC == 0 ]] && has "$OUT" "kept from the previous install: --data-dir $WORK/up_dd/data" && has "$OUT" "^AbstractFramework $FW found: already up to date" && [[ ! -e "$WORK/up_dd/home/$DATA_REL/bootstrap.env" ]]; echo $?)" "$OUT"

    # --pin latest (the newest gateway): no release matrix, no release recorded.
    BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$UP_OLD" BG_ARGS="--no-console --pin latest" bg_case up_latest2 1
    check "--pin latest: says what it installs, no release matrix, no release recorded" "$([[ $RC == 0 ]] && has "$OUT" "found: upgrading to the newest abstractgateway (--pin latest)" && ! grep -qs "abstractcore==" "$DATA_T/uv-constraints.txt" && grep -qx "FRAMEWORK_VERSION=" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"

    # The Update button's run: --no-start installs, never touches the running gateway, and says a restart is due.
    BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$UP_OLD" BG_ARGS="--no-console --no-start --yes" \
        BG_FREEZE_BEFORE='abstractgateway==0.7.0\n' BG_FREEZE_AFTER="abstractgateway==$GW_PIN\n" bg_case up_nostart 1
    check "--no-start: upgraded, the gateway not started or restarted, a restart is said to be due" "$([[ $RC == 0 ]] && has "$OUT" "AbstractFramework is installed (--no-start)" && has "$OUT" "^  Upgraded: AbstractFramework 0.6.0 -> $FW" && has "$OUT" "still runs the previous version until it restarts" && ! grep -q "serve\|service install" "$GWLOG" && grep -qx "MODE=background" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"

    # The login item cannot be registered (launchd's "Bootstrap failed: 5"): never leave the gateway stopped.
    BG_SERVICE=1 BG_SERVICE_FAIL=1 BG_STATE="PORT=$BG_PORT\nMODE=service\nPROFILE=light\n" bg_case up_svcfail 1
    check "service install fails: the gateway starts in the background instead, and it is said" "$([[ $RC == 0 ]] && has "$OUT" "starting the gateway in the background instead" && grep -qx "abstractgateway serve" "$GWLOG" && grep -qx "MODE=background" "$DATA_T/bootstrap.env" && has "$OUT" "Start at login is off: the login item could not be registered" && has "$OUT" "or run: abstractgateway service enable"; echo $?)" "$OUT"

    # Linux, a running systemd user unit: `service install` (enable --now) leaves it on the old code.
    UP_SVC="PORT=$BG_PORT\nMODE=service\nPROFILE=light\nFRAMEWORK_VERSION=0.6.0\n"
    BG_LINUX=1 BG_SERVICE=1 BG_UNIT_ACTIVE=1 BG_STATE="$UP_SVC" BG_FREEZE_BEFORE='abstractgateway==0.7.0\n' BG_FREEZE_AFTER="abstractgateway==$GW_PIN\n" bg_case up_systemd 1
    check "systemd: a running unit is restarted after an upgrade (after service install)" "$([[ $RC == 0 ]] && grep -qx "abstractgateway service install --port $BG_PORT" "$GWLOG" && grep -qx "systemctl --user restart abstractgateway.service" "$SYSTEMCTL_LOG" && has "$OUT" "systemd user session available"; echo $?)" "$OUT"
    BG_LINUX=1 BG_SERVICE=1 BG_UNIT_ACTIVE=1 BG_STATE="PORT=$BG_PORT\nMODE=service\nPROFILE=light\nFRAMEWORK_VERSION=$FW\nGATEWAY_SPEC=abstractgateway==$GW_PIN\nVOICE_SPEC=abstractvoice[supertonic,stt]\n" BG_UV_LIST="abstractgateway v$GW_PIN" BG_FREEZE_BEFORE="abstractgateway==$GW_PIN\n" bg_case up_systemd_same 1
    check "systemd: nothing changed, no restart" "$([[ $RC == 0 ]] && ! grep -q "restart" "$SYSTEMCTL_LOG"; echo $?)" "$SYSTEMCTL_LOG"
    BG_LINUX=1 BG_SERVICE=1 BG_UNIT_ACTIVE=0 BG_STATE="$UP_SVC" BG_FREEZE_BEFORE='abstractgateway==0.7.0\n' BG_FREEZE_AFTER="abstractgateway==$GW_PIN\n" bg_case up_systemd_idle 1
    check "systemd: a unit that was not running is started by service install, not restarted" "$([[ $RC == 0 ]] && ! grep -q "restart" "$SYSTEMCTL_LOG" && grep -qx "abstractgateway service install --port $BG_PORT" "$GWLOG"; echo $?)" "$SYSTEMCTL_LOG"
fi

echo "[18] --no-start (the gateway's Update run) keeps the recorded port when a gateway it did not start holds it"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the --no-start port cases" 1
else
    GW_PIN="$(sed -n 's/^AF_GATEWAY_PIN_DEFAULT="\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    # A hand-started `serve` on the recorded port: no gateway.pid, no login item, so the installer
    # cannot recognise it as its own. No --port, as the gateway's Update runs it.
    HELD_OLD="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nFRAMEWORK_VERSION=0.6.0\nCONSOLE=0\nGATEWAY_SPEC=abstractgateway[tray]==0.7.0\n"
    BG_FOREIGN=1 BG_NO_PORT=1 BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$HELD_OLD" BG_ARGS="--no-console --no-start --yes" \
        BG_FREEZE_BEFORE='abstractgateway==0.7.0\n' BG_FREEZE_AFTER="abstractgateway==$GW_PIN\n" bg_case held_nostart 1
    check "--no-start, recorded port held by a gateway it did not start: the recorded port is kept and recorded" "$([[ $RC == 0 ]] && grep -qx "PORT=$BG_PORT" "$DATA_T/bootstrap.env" && ! has "$OUT" "using $((BG_PORT + 1))" && has "$OUT" "port $BG_PORT (this install's) is in use by a process this installer did not start; kept"; echo $?)" "$OUT"
    check "--no-start, recorded port held: the summary keeps the port and says a restart is due" "$(has "$OUT" "The install keeps port $BG_PORT" && has "$OUT" "still runs the previous version until it restarts" && ! grep -q "serve\|service install" "$GWLOG"; echo $?)" "$OUT"
    # Without --no-start the installer starts a gateway, so a busy port still moves to the next free one.
    BG_FOREIGN=1 BG_NO_PORT=1 BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$HELD_OLD" \
        BG_FREEZE_BEFORE='abstractgateway==0.7.0\n' BG_FREEZE_AFTER="abstractgateway==$GW_PIN\n" bg_case held_start 1
    check "without --no-start, a held recorded port still moves to the next free port (kept for future runs)" "$([[ $RC == 0 ]] && has "$OUT" "using $((BG_PORT + 1)) (kept for future runs)" && grep -qx "PORT=$((BG_PORT + 1))" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"
fi

echo "[19] the first upgrade of an install made before 0.6.2: the unrecorded choices are read from disk"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the pre-0.6.2 upgrade cases" 1
else
    GW_PIN="$(sed -n 's/^AF_GATEWAY_PIN_DEFAULT="\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    # A 0.6.1-era bootstrap.env: no FRAMEWORK_VERSION, CONSOLE, CODE_CLI, CORE_CLI, TRAY or FULL.
    PRE062="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nGATEWAY_SPEC=abstractgateway==0.7.0\n"
    # (a) made with --no-console --no-core-cli --no-tray, no abstractcode, no --full: nothing of
    # them on disk. A plain re-run (no options) must not add Rust/console, abstractcode, the tray
    # or the library commands.
    mkdir -p "$WORK/pre_min/tools/abstractgateway" "$WORK/pre_min/home/$DATA_REL"
    printf '[tool]\nrequirements = [{ name = "abstractgateway", specifier = "==0.7.0" }, { name = "webrtcvad-wheels", specifier = ">=2.0.14" }]\nentrypoints = [\n    { name = "abstractgateway", install-path = "/x/abstractgateway", from = "abstractgateway" },\n]\n' >"$WORK/pre_min/tools/abstractgateway/uv-receipt.toml"
    printf "webrtcvad; sys_platform == 'never'\nstable-diffusion-cpp-python; sys_platform == 'never'\naec-audio-processing; sys_platform == 'never'\n" >"$WORK/pre_min/home/$DATA_REL/uv-overrides.txt"
    BG_TOOLDIR="$WORK/pre_min/tools" BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$PRE062" BG_CARGO=1 BG_ARGS=" " bg_case pre_min 1
    check "pre-0.6.2, nothing extra on disk: says the options were read from disk" "$([[ $RC == 0 ]] && has "$OUT" "recorded no options (before AbstractFramework 0.6.2): read from disk: terminal console absent, abstractcode absent, library commands not exposed"; echo $?)" "$OUT"
    check "pre-0.6.2, nothing extra on disk: no console or abstractcode build, no library commands, recorded" "$([[ $RC == 0 ]] && [[ ! -s "$CARGOLOG" ]] && ! grep "tool install " "$UVLOG" | grep -q -- "--with-executables-from" && grep -qx "CONSOLE=0" "$DATA_T/bootstrap.env" && grep -qx "CODE_CLI=0" "$DATA_T/bootstrap.env" && grep -qx "CORE_CLI=0" "$DATA_T/bootstrap.env" && grep -qx "FULL=0" "$DATA_T/bootstrap.env"; echo $?)" "$OUT"
    if [[ "$IS_MAC" == 1 ]]; then
        check "pre-0.6.2, no tray extra in the receipt (macOS): the tray is not added, TRAY=0 recorded" "$(grep "tool install " "$UVLOG" | grep -q " abstractgateway==$GW_PIN$" && grep -qx "TRAY=0" "$DATA_T/bootstrap.env"; echo $?)" "$UVLOG"
    fi
    # (b) made with the console, abstractcode, the library commands, the tray and --full: all kept.
    mkdir -p "$WORK/pre_all/tools/abstractgateway" "$WORK/pre_all/home/$DATA_REL" "$WORK/pre_all/home/.cargo/bin"
    printf '[tool]\nrequirements = [{ name = "abstractgateway", extras = ["tray"], specifier = "==0.7.0" }, { name = "llama-cpp-python" }]\nentrypoints = [\n    { name = "abstractgateway", install-path = "/x/abstractgateway", from = "abstractgateway" },\n    { name = "abstractcore", install-path = "/x/abstractcore", from = "abstractcore" },\n]\n' >"$WORK/pre_all/tools/abstractgateway/uv-receipt.toml"
    printf "webrtcvad; sys_platform == 'never'\n" >"$WORK/pre_all/home/$DATA_REL/uv-overrides.txt"
    for c in abstractgateway-console abstractcode; do printf '#!/bin/sh\necho "%s 0.0.1"\n' "$c" >"$WORK/pre_all/home/.cargo/bin/$c"; chmod +x "$WORK/pre_all/home/.cargo/bin/$c"; done
    BG_TOOLDIR="$WORK/pre_all/tools" BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nGATEWAY_SPEC=abstractgateway[tray]==0.7.0\n" BG_CARGO=1 BG_ARGS=" " bg_case pre_all 1
    check "pre-0.6.2, everything on disk: console, abstractcode, library commands, tray and --full kept and recorded" "$([[ $RC == 0 ]] && grep -qx "CONSOLE=1" "$DATA_T/bootstrap.env" && grep -qx "CODE_CLI=1" "$DATA_T/bootstrap.env" && grep -qx "CORE_CLI=1" "$DATA_T/bootstrap.env" && grep -qx "TRAY=1" "$DATA_T/bootstrap.env" && grep -qx "FULL=1" "$DATA_T/bootstrap.env" && has "$OUT" "compiled extras built (--full)"; echo $?)" "$OUT"
    check "pre-0.6.2, everything on disk: the install keeps --full (no llama.cpp wheel pin) and the library commands" "$({ grep "tool install " "$UVLOG" | grep -q -- "--with llama-cpp-python --constraints" || has "$OUT" "needs a C compiler"; } && grep "tool install " "$UVLOG" | grep -q -- "--with-executables-from abstractcore" && grep -q "abstractgateway-console" "$CARGOLOG"; echo $?)" "$UVLOG"
fi

echo "[20] one installer at a time per data dir: a running one is refused cleanly, a stale lock is taken over"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the installer-lock cases" 1
else
    LOCK_STATE="PORT=$BG_PORT\nMODE=background\nPROFILE=light\nFRAMEWORK_VERSION=0.6.0\nCONSOLE=0\nCODE_CLI=0\nCORE_CLI=0\nTRAY=1\nFULL=0\n"
    # Another installer holds the lock (a live pid): the gateway's Update run is refused, and changes nothing.
    sleep 300 & LIVE_PID=$!
    mkdir -p "$WORK/lock_live/home/$DATA_REL/update/install.lock"; echo "$LIVE_PID" >"$WORK/lock_live/home/$DATA_REL/update/install.lock/pid"
    BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$LOCK_STATE" BG_ARGS="--no-console --no-start --yes" bg_case lock_live 1
    check "a running installer holds the lock: refused (exit 1) with the pid, the lock and what to do" "$([[ $RC == 1 ]] && has "$OUT" "another AbstractFramework installer is already running for .*(pid $LIVE_PID; lock .*install.lock)" && has "$OUT" "wait until it finishes" && has "$OUT" "Nothing was changed"; echo $?)" "$OUT"
    check "refused: nothing installed, no state written, the other run's lock left as it was" "$(! grep -q "tool install" "$UVLOG" && grep -qx "FRAMEWORK_VERSION=0.6.0" "$DATA_T/bootstrap.env" && [[ "$(cat "$DATA_T/update/install.lock/pid")" == "$LIVE_PID" ]]; echo $?)" "$OUT"
    kill "$LIVE_PID" 2>/dev/null; wait "$LIVE_PID" 2>/dev/null
    # The lock of a run that is gone (its pid is dead): taken over, said so, and released at the end.
    sleep 0 & DEAD_PID=$!; wait "$DEAD_PID" 2>/dev/null
    mkdir -p "$WORK/lock_stale/home/$DATA_REL/update/install.lock"; echo "$DEAD_PID" >"$WORK/lock_stale/home/$DATA_REL/update/install.lock/pid"
    BG_UV_LIST='abstractgateway v0.7.0' BG_STATE="$LOCK_STATE" BG_ARGS="--no-console --no-start --yes" bg_case lock_stale 1
    check "a stale lock (dead pid) is taken over, the install runs, and the lock is gone afterwards" "$([[ $RC == 0 ]] && has "$OUT" "took over a stale installer lock (pid $DEAD_PID is no longer running)" && grep -q "tool install" "$UVLOG" && [[ ! -e "$DATA_T/update/install.lock" ]]; echo $?)" "$OUT"
    # A first install takes (and releases) the lock too; --print takes none.
    BG_UV_LIST='other-tool v1.0' bg_case lock_first 1
    check "a first install leaves no lock behind" "$([[ $RC == 0 ]] && [[ -d "$DATA_T/update" && ! -e "$DATA_T/update/install.lock" ]]; echo $?)" "$OUT"
fi

echo ""
echo "passed: $PASS  failed: $FAIL"
[[ "$FAIL" == 0 ]]
