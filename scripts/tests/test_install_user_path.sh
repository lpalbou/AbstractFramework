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
# These cases skip the terminal console (--no-console) unless BG_ARGS says otherwise;
# BG_TOOLBIN overrides the uv tool bin dir, BG_CARGO=1 adds a fake cargo (log: CARGOLOG).
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
    CARGOLOG="$WORK/$name/cargo.log"
    if [[ "${BG_CARGO:-0}" == 1 ]]; then
        # `install ... --root R NAME --version V` writes R/bin/NAME answering `--version`.
        cat >"$bin/cargo" <<CARGO
#!/bin/sh
echo "cargo \$*" >>"$CARGOLOG"
[ "\$1" = --version ] && { echo "cargo ${BG_CARGO_VERSION:-1.90.0} (fake)"; exit 0; }
root=""; ver=""; prev=""; name=""
for a in "\$@"; do
  case "\$prev" in --root) root="\$a" ;; --version) ver="\$a" ;; esac
  case "\$a" in abstractgateway-console) name="\$a" ;; esac
  prev="\$a"
done
mkdir -p "\$root/bin"
printf '#!/bin/sh\\necho "\$*" >>"\$0.args"\\necho "%s %s"\\n' "\$name" "\$ver" >"\$root/bin/\$name"
chmod +x "\$root/bin/\$name"
exit 0
CARGO
        chmod +x "$bin/cargo"
    fi
    DATA_T="$WORK/$name/home/$DATA_REL"; NETF="$DATA_T/fake-network"
    if [[ -n "$stored" ]]; then mkdir -p "$DATA_T"; echo "$stored" >"$NETF"; fi
    # BG_TOKEN: the admin token a real gateway writes into its data dir at first start.
    if [[ -n "${BG_TOKEN:-}" ]]; then mkdir -p "$DATA_T/auth"; printf '%s\n' "$BG_TOKEN" >"$DATA_T/auth/bootstrap-admin-token"; fi
    # BG_ENV: extra environment (e.g. SSH_CONNECTION); BG_PTY=1 runs the installer on a pseudo-terminal.
    # BG_OPEN=1 leaves --no-open out (the remote-session console launch is under test).
    local wrap=() open_flag=(--no-open)
    # A minimal pty runner: pty.spawn() spins forever on macOS when stdin is /dev/null.
    [[ "${BG_PTY:-0}" == 1 ]] && wrap=(/usr/bin/python3 -c 'import os, pty, sys
pid, fd = pty.fork()
if pid == 0:
    os.execvp(sys.argv[1], sys.argv[1:])
while True:
    try:
        chunk = os.read(fd, 4096)
    except OSError:
        break
    if not chunk:
        break
    os.write(1, chunk)
sys.exit(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]))')
    [[ "${BG_OPEN:-0}" == 1 ]] && open_flag=()
    run_in "$name" ${BG_ENV:-} -- ${wrap[@]+"${wrap[@]}"} sh "$SCRIPTS_DIR/install.sh" --profile light --port "$BG_PORT" --no-service ${open_flag[@]+"${open_flag[@]}"} --no-modify-path ${BG_ARGS:---no-console}
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

echo "[11] terminal console: built by default, both consoles in the summary"
# The same fake gateway, a fake cargo, and a uv tool bin dir named .../bin, so the console
# must be built with --root <its parent> and land next to `abstractgateway`.
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the terminal console cases" 1
else
    TB="$WORK/con/tools/bin"
    CON_PIN="$(sed -n 's/^AF_CRATE_CONSOLE="abstractgateway-console@\(.*\)"$/\1/p' "$SCRIPTS_DIR/install.sh")"
    check "console: install.sh pins the terminal console" "$([[ -n "$CON_PIN" ]]; echo $?)"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_sandbox_123" bg_case con 1
    check "console: installer succeeds" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "console: cargo builds the pinned crate into the tool bin dir" "$(grep -qx "cargo install --locked --force --root $WORK/con/tools abstractgateway-console --version $CON_PIN" "$CARGOLOG" && [[ -x "$TB/abstractgateway-console" ]]; echo $?)" "$CARGOLOG"
    check "console: summary gives the web console and its tunnel hint" "$(has "$OUT" "Web:  *http://127.0.0.1:$BG_PORT/console" && has "$OUT" "ssh -L $BG_PORT:127.0.0.1:$BG_PORT"; echo $?)" "$OUT"
    check "console: summary gives the terminal console command with the admin token (--token)" "$(has "$OUT" "Terminal:  abstractgateway-console --url http://127.0.0.1:$BG_PORT --token tok_sandbox_123$"; echo $?)" "$OUT"
    check "console: no 'browser now shows' claim when no browser was opened" "$(! has "$OUT" "browser now shows"; echo $?)" "$OUT"
    # A re-run finds the pinned binary and does not build again.
    : >"$CARGOLOG"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " bg_case con 1
    check "console: a re-run keeps the installed console (no cargo install)" "$([[ $RC == 0 ]] && ! grep -q "cargo install" "$CARGOLOG" && has "$OUT" "abstractgateway-console $CON_PIN already installed"; echo $?)" "$OUT"
    # A distro cargo older than 1.87 and no rustup: rustup is tried (refused here), soft.
    BG_TOOLBIN="$WORK/con3/tools/bin" BG_CARGO=1 BG_CARGO_VERSION=1.75.0 BG_ARGS=" " bg_case con3 1
    check "console: an old cargo without rustup falls back to rustup, and its failure is soft" "$([[ $RC == 0 ]] && has "$OUT" "cargo 1.75.0 .* is older than the Rust 1.87" && has "$OUT" "sh.rustup.rs" && has "$OUT" "Terminal:  not installed: Rust could not be installed" && ! grep -q "cargo install" "$CARGOLOG"; echo $?)" "$OUT"
    BG_TOOLBIN="$WORK/con2/tools/bin" BG_CARGO=1 BG_ARGS="--no-console" bg_case con2 1
    check "console: --no-console builds nothing and says so" "$([[ $RC == 0 ]] && [[ ! -s "$CARGOLOG" ]] && has "$OUT" "Terminal:  not installed: skipped with --no-console"; echo $?)" "$OUT"
fi

echo "[12] remote or headless session: the terminal console opens at the end, signed in"
if lsof -nP -iTCP:"$BG_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    check "port $BG_PORT is free for the remote-session cases" 1
else
    TB="$WORK/rem/tools/bin"
    BG_TOOLBIN="$TB" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_PTY=1 BG_OPEN=1 bg_case rem 1
    check "remote: installer succeeds on a terminal" "$([[ $RC == 0 ]]; echo $?)" "$OUT"
    check "remote: the console is started with the gateway URL and the admin token" "$(grep -qx -- "--url http://127.0.0.1:$BG_PORT --token tok_remote_9" "$TB/abstractgateway-console.args"; echo $?)" "$OUT"
    check "remote: no browser is opened over SSH" "$([[ ! -s "$WORK/rem/open.log" ]] && has "$OUT" "tunnel it first: ssh -L $BG_PORT:127.0.0.1:$BG_PORT"; echo $?)" "$OUT"
    TB2="$WORK/rem2/tools/bin"
    BG_TOOLBIN="$TB2" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_PTY=1 bg_case rem2 1
    check "remote: --no-open does not start the console" "$([[ $RC == 0 ]] && ! grep -q -- "--url" "$TB2/abstractgateway-console.args"; echo $?)" "$OUT"
    TB3="$WORK/rem3/tools/bin"
    BG_TOOLBIN="$TB3" BG_CARGO=1 BG_ARGS=" " BG_TOKEN="tok_remote_9" BG_ENV="SSH_CONNECTION=10.0.0.2_5000_10.0.0.1_22" BG_OPEN=1 bg_case rem3 1
    check "remote: without a terminal (piped output) the console is not started" "$([[ $RC == 0 ]] && ! grep -q -- "--url" "$TB3/abstractgateway-console.args"; echo $?)" "$OUT"
fi

echo ""
echo "passed: $PASS  failed: $FAIL"
[[ "$FAIL" == 0 ]]
