#!/usr/bin/env bash
# =============================================================================
# Tests for the installer's background-gateway restart loop (AF_GW_LOOP in
# scripts/install.sh) — real processes, fake gateways.
# =============================================================================
# 2026-10-04: a hung gateway now exits by itself (`serve`'s event-loop
# watchdog, exit code 75). A login service restarts that exit; the
# installer's background mode had no loop at all (`nohup serve &`), so a
# watchdog exit left the machine with no gateway. Proves:
#   1. exit 75 after running >= MIN_RUN_S is restarted, gateway.pid then names
#      the NEW gateway, and the log says why;
#   2. a stop by signal (kill $(cat gateway.pid): 143) is not restarted;
#   3. a clean exit (0) is not restarted;
#   4. a start failure (non-zero before MIN_RUN_S) is not restarted;
#   5. once gateway.pid is removed (installer stop/takeover), no restart.
# Run: bash scripts/tests/test_install_gateway_loop.sh
# =============================================================================

set -u

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SH="$(dirname "$TEST_DIR")/install.sh"

LOOP_SRC="$(sed -n '/^# >>> af-gateway-loop/,/^# <<< af-gateway-loop/p' "$INSTALL_SH")"
[[ -n "$LOOP_SRC" ]] || { echo "FAIL: no af-gateway-loop block in $INSTALL_SH"; exit 1; }
eval "$(printf '%s\n' "$LOOP_SRC" | sed -n '/^AF_GW_LOOP=/,/^done'"'"'$/p')"
[[ -n "${AF_GW_LOOP:-}" ]] || { echo "FAIL: AF_GW_LOOP not defined by the block"; exit 1; }
grep -q 'nohup sh -c "$AF_GW_LOOP" af-gateway-loop "$PID_FILE"' "$INSTALL_SH"
[[ "$?" == 0 ]] || { echo "FAIL: start_background does not run the gateway under AF_GW_LOOP"; exit 1; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/af_gw_loop_test.XXXXXX")"
cleanup() {
    for p in $(cat "$WORK"/*.loop 2>/dev/null); do kill "$p" 2>/dev/null; done
    for f in "$WORK"/*.pid; do [[ -f "$f" ]] && kill "$(cat "$f")" 2>/dev/null; done
    rm -rf "$WORK"
}
trap cleanup EXIT

PASS=0; FAIL=0
check() {
    if [[ "$2" == "0" ]]; then echo "  PASS: $1"; PASS=$((PASS + 1)); else echo "  FAIL: $1"; FAIL=$((FAIL + 1)); fi
}

# A fake gateway: counts its starts, then behaves per the start number.
# fake_gw NAME BEHAVIOUR... (one word per start; the last repeats):
#   hang75   run 2 s, exit 75 (the watchdog)      fast3   exit 3 at once
#   clean    run 2 s, exit 0                      forever sleep until killed
mk_fake() {
    local name="$1"; shift
    cat >"$WORK/$name.gw" <<EOF
#!/bin/sh
n=\$(( \$(cat "$WORK/$name.count" 2>/dev/null || echo 0) + 1 ))
echo "\$n" >"$WORK/$name.count"
set -- $*
i=1; b="\$1"; for x in "\$@"; do [ "\$i" -le "\$n" ] && b="\$x"; i=\$((i + 1)); done
case "\$b" in
  hang75) sleep 2; exit 75 ;;
  clean)  sleep 2; exit 0 ;;
  fast3)  exit 3 ;;
  forever) exec sleep 600 ;;
esac
EOF
    chmod +x "$WORK/$name.gw"
}

start_loop() {  # start_loop NAME MIN_RUN_S
    sh -c "$AF_GW_LOOP" af-gateway-loop "$WORK/$1.pid" "$2" 1 "$WORK/$1.gw" >>"$WORK/$1.log" 2>&1 </dev/null &
    echo $! >"$WORK/$1.loop"
}
wait_for() {  # wait_for SECONDS CONDITION...
    local end=$((SECONDS + $1)); shift
    while [[ "$SECONDS" -lt "$end" ]]; do "$@" && return 0; sleep 0.2; done
    return 1
}
count_is() { [[ "$(cat "$WORK/$1.count" 2>/dev/null)" == "$2" ]]; }
loop_gone() { ! kill -0 "$(cat "$WORK/$1.loop")" 2>/dev/null; }

echo "== installer gateway loop tests (work dir: $WORK) =="

# 1. watchdog exit after running -> restarted; gateway.pid follows the new gateway
mk_fake t1 hang75 forever
start_loop t1 1
wait_for 5 count_is t1 1; FIRST="$(cat "$WORK/t1.pid")"
wait_for 10 count_is t1 2
check "1: exit 75 after running is restarted" "$?"
sleep 0.3
SECOND="$(cat "$WORK/t1.pid")"
[[ -n "$SECOND" && "$SECOND" != "$FIRST" ]] && kill -0 "$SECOND" 2>/dev/null
check "1: gateway.pid names the new, live gateway" "$?"
grep -q "exited with code 75 after .*event-loop watchdog.*restarting it" "$WORK/t1.log"
check "1: the log says it restarts and why" "$?"

# 2. the installer's stop (TERM to the pid in gateway.pid) -> not restarted
kill "$SECOND"
wait_for 5 loop_gone t1
check "2: kill \$(cat gateway.pid) stops the loop (no restart)" "$?"
count_is t1 2
check "2: no third start" "$?"

# 3. clean exit -> not restarted
mk_fake t3 clean
start_loop t3 1
wait_for 8 loop_gone t3
check "3: a clean exit (0) ends the loop" "$?"
count_is t3 1
check "3: started once" "$?"

# 4. start failure (exit before MIN_RUN_S) -> not restarted
mk_fake t4 fast3
start_loop t4 30
wait_for 5 loop_gone t4
check "4: a start failure ends the loop" "$?"
count_is t4 1 && grep -q "a start failure): not restarted" "$WORK/t4.log"
check "4: started once, and the log says why it was not restarted" "$?"

# 5. gateway.pid removed (installer stopped/took over) -> not restarted
mk_fake t5 hang75
start_loop t5 1
wait_for 5 count_is t5 1
rm -f "$WORK/t5.pid"
wait_for 8 loop_gone t5
check "5: with gateway.pid removed, a watchdog exit is not restarted" "$?"
count_is t5 1
check "5: started once" "$?"

echo "== results: $PASS passed, $FAIL failed =="
[[ "$FAIL" == 0 ]]
