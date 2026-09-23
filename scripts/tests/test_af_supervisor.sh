#!/usr/bin/env bash
# =============================================================================
# Tests for scripts/lib/af_supervisor.sh — stub services, real processes.
# =============================================================================
# Proves the separated-failure-domain semantics (maintainer ruling 2026-07-21):
#   1. an app crash is restarted; the critical service is untouched
#   2. a crash-looping app converges to FAILED; the stack stays up
#   3. a critical death is respawned (unlimited, backoff); apps untouched
#   4. an app dying while the critical service is down is PARKED (no budget
#      charge) and returns after critical recovery
#   5. a hung critical service (alive, health probes failing) is killed and
#      respawned
#   6. shutdown stops everything, apps first, critical last
#   7. singleton guard: with SUP_SINGLETON_TAKEOVER=0 a second acquire on a
#      live pidfile is refused; a stale pidfile (dead pid) is reclaimed; by
#      default a live previous holder is stopped and replaced
#   8. a FAILED app is revived with a fresh budget after the cooldown
#
# Stubs are real processes: python http.server for probeable services, plain
# bash for crashers. Run: bash scripts/tests/test_af_supervisor.sh
# =============================================================================

set -u

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(dirname "$TEST_DIR")/lib"

# Fast policies for tests (set BEFORE sourcing: the library reads them then).
SUP_POLL_S=1
SUP_READY_TIMEOUT_S=15
SUP_APP_RESTART_MAX=2
SUP_APP_RESTART_WINDOW_S=300
SUP_APP_RESTART_DELAY_S=1
SUP_CRIT_BACKOFF_CAP_S=4
SUP_CRIT_STABLE_RESET_S=5
SUP_HEALTH_EVERY_S=1
SUP_HEALTH_FAILS_MAX=2
SUP_PROBE_TIMEOUT_S=2
SUP_KILL_GRACE_S=2
SUP_FAILED_RETRY_S=5

source "$LIB_DIR/af_supervisor.sh"

PY="$(command -v python3 || true)"
[[ -n "$PY" ]] || { echo "SKIP: python3 not found"; exit 0; }

WORK="$(mktemp -d /tmp/af_supervisor_test.XXXXXX)"
mkdir -p "$WORK/www"   # tiny served dir: probe responses stay small + fast
CRIT_PORT=19381
APP_PORT=19382
DEAD_PORT=19383   # nothing ever listens here (hung-health simulation)

# A probeable stub service command on a given port.
stub_server() {
    echo "exec $PY -m http.server $1 --bind 127.0.0.1 --directory $WORK/www"
}

PASS=0
FAIL=0
check() {
    local label="$1" ok="$2"
    if [[ "$ok" == "0" ]]; then
        echo "  PASS: $label"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $label"
        FAIL=$((FAIL + 1))
    fi
}

# Drive the state machine for N seconds.
run_ticks() {
    local secs="$1" end
    end=$(( $(sup_now) + secs ))
    while [[ "$(sup_now)" -lt "$end" ]]; do
        sup_tick
        sleep 1
    done
}

cleanup() {
    sup_shutdown >/dev/null 2>&1 || true
    if [[ "${KEEP_WORK:-0}" == "1" ]]; then
        echo "work dir kept for inspection: $WORK"
    else
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT

echo "== af_supervisor tests (work dir: $WORK) =="

# --- registry ----------------------------------------------------------------
# critical "gateway" stub: http server; health probed on a DEAD port only in
# test 5 (separate service), so here health == ready URL.
sup_register "crit" 1 \
    "$(stub_server "$CRIT_PORT")" \
    "$WORK/crit.log" \
    "http://127.0.0.1:$CRIT_PORT/" "http://127.0.0.1:$CRIT_PORT/" ""
CRIT=$SUP_LAST_INDEX

sup_register "app" 0 \
    "$(stub_server "$APP_PORT")" \
    "$WORK/app.log" \
    "http://127.0.0.1:$APP_PORT/" "http://127.0.0.1:$APP_PORT/" ""
APP=$SUP_LAST_INDEX

sup_register "crasher" 0 \
    "exit 7" \
    "$WORK/crasher.log" \
    "http://127.0.0.1:1/" "" ""
CRASHER=$SUP_LAST_INDEX

# --- launch ------------------------------------------------------------------
sup_start_service "$CRIT"
sup_await_state "$CRIT" "running" 15
check "critical becomes running" "$?"

sup_start_service "$APP"
sup_await_state "$APP" "running" 15
check "app becomes running" "$?"

# --- test 1: app crash -> restarted, critical untouched ------------------------
CRIT_PID_BEFORE="${SUP_PID[$CRIT]}"
APP_PID_BEFORE="${SUP_PID[$APP]}"
kill -9 "$APP_PID_BEFORE" 2>/dev/null
run_ticks 5
[[ "${SUP_STATE[$APP]}" == "running" && "${SUP_PID[$APP]}" != "$APP_PID_BEFORE" ]]
check "test1: killed app was restarted (new pid, running)" "$?"
[[ "${SUP_PID[$CRIT]}" == "$CRIT_PID_BEFORE" && "${SUP_STATE[$CRIT]}" == "running" ]]
check "test1: critical pid untouched by app crash" "$?"

# --- test 2: crash-looping app -> FAILED, stack stays up -----------------------
# Poll for the FAILED transition (a snapshot can miss it: with the short test
# cooldown the crasher legitimately REVIVES a few seconds after failing).
sup_start_service "$CRASHER"
REACHED_FAILED=1
END=$(( SECONDS + 15 ))
while [[ "$SECONDS" -lt "$END" ]]; do
    sup_tick
    [[ "${SUP_STATE[$CRASHER]}" == "failed" ]] && { REACHED_FAILED=0; break; }
    sleep 1
done
check "test2: crash-looping app converged to FAILED" "$REACHED_FAILED"
[[ "${SUP_STATE[$CRIT]}" == "running" && "${SUP_STATE[$APP]}" == "running" ]]
check "test2: critical + app still running after crasher FAILED" "$?"

# --- test 3: critical death -> respawned; app untouched -------------------------
CRIT_PID_BEFORE="${SUP_PID[$CRIT]}"
APP_PID_BEFORE="${SUP_PID[$APP]}"
kill -9 "$CRIT_PID_BEFORE" 2>/dev/null
run_ticks 8
[[ "${SUP_STATE[$CRIT]}" == "running" && "${SUP_PID[$CRIT]}" != "$CRIT_PID_BEFORE" ]]
check "test3: critical was respawned (new pid, running)" "$?"
[[ "${SUP_PID[$APP]}" == "$APP_PID_BEFORE" && "${SUP_STATE[$APP]}" == "running" ]]
check "test3: app pid untouched by critical restart" "$?"

# --- test 4: app dies while critical is down -> parked, returns after recovery --
CRIT_PID_BEFORE="${SUP_PID[$CRIT]}"
APP_PID_BEFORE="${SUP_PID[$APP]}"
kill -9 "$CRIT_PID_BEFORE" 2>/dev/null
kill -9 "$APP_PID_BEFORE" 2>/dev/null
sup_tick   # observe both deaths; critical is down when the app death is handled
BUDGET_AFTER_PARK="$(sup_budget_used "$APP")"
run_ticks 10
[[ "${SUP_STATE[$CRIT]}" == "running" && "${SUP_STATE[$APP]}" == "running" ]]
check "test4: both recovered after joint kill" "$?"
[[ "$(sup_budget_used "$APP")" == "0" ]]
check "test4: app budget reset after control-plane recovery (was: $BUDGET_AFTER_PARK)" "$?"

# --- test 5: hung critical (alive, failing health) ------------------------------
# DEFAULT (operator ruling 2026-08-20): a hung-but-alive service is WARNED
# about loudly, NEVER killed — the supervisor restarts on death only.
# The banner assertion needs the supervisor log SINK (the harness normally
# logs to the terminal only).
SUP_LOG_FILE="$WORK/sup5.log"
sup_register "hung" 1 \
    "$(stub_server $((CRIT_PORT + 10)))" \
    "$WORK/hung.log" \
    "http://127.0.0.1:$((CRIT_PORT + 10))/" "http://127.0.0.1:$DEAD_PORT/" ""
HUNG=$SUP_LAST_INDEX
sup_start_service "$HUNG"
sup_await_state "$HUNG" "running" 15
HUNG_PID_BEFORE="${SUP_PID[$HUNG]}"
# Enough ticks for well over SUP_HEALTH_FAILS_MAX failed probes.
run_ticks $((SUP_HEALTH_FAILS_MAX * SUP_HEALTH_EVERY_S + 8))
kill -0 "$HUNG_PID_BEFORE" 2>/dev/null
check "test5: hung critical is NEVER killed by default (pid survives ${SUP_HEALTH_FAILS_MAX}+ failed probes)" "$?"
grep -q "NOT restarting it" "$SUP_LOG_FILE"
check "test5: the sustained-unhealthy banner is in the supervisor log" "$?"
[[ "${SUP_STATE[$HUNG]}" == "running" ]]
check "test5: state stays running while unhealthy-but-alive" "$?"

# --- test 5b: SUP_HANG_KILL=1 restores kill + respawn on hang --------------------
SUP_HANG_KILL=1
SUP_HEALTH_FAILS[$HUNG]=0
# The dead health URL keeps failing after every respawn, so the service loops
# kill -> backoff -> respawn indefinitely (correct for a critical service).
# Poll for the respawn EVENT instead of asserting a phase: old pid dead AND a
# NEW pid observed. A phase snapshot after a fixed sleep is timing-fragile.
RESPAWNED=1
END=$(( $(sup_now) + 25 ))
while [[ "$(sup_now)" -lt "$END" ]]; do
    sup_tick
    if ! kill -0 "$HUNG_PID_BEFORE" 2>/dev/null \
        && [[ -n "${SUP_PID[$HUNG]}" && "${SUP_PID[$HUNG]}" != "$HUNG_PID_BEFORE" ]]; then
        RESPAWNED=0
        break
    fi
    sleep 1
done
check "test5b: with SUP_HANG_KILL=1 the hung critical is killed and respawned" "$RESPAWNED"
[[ "${SUP_STATE[$HUNG]}" != "failed" ]]
check "test5b: critical never converges to FAILED" "$?"
SUP_HANG_KILL=0
SUP_LOG_FILE=""

# --- test 7: singleton guard ------------------------------------------------------
PIDFILE="$WORK/af_stack.pid"
sup_acquire_singleton "$PIDFILE"
check "test7: first acquire succeeds" "$?"
# A second acquire from another live process must be refused when takeover is
# disabled. It MUST run in a separate `bash` process: a `( ... )` subshell
# shares this script's $$, so with the default REPLACE semantics
# (SUP_SINGLETON_TAKEOVER=1, 2026-07-22) it "took over" by TERMing the test
# runner itself — the historical "dies at test7" (exit 143).
env SUP_SINGLETON_TAKEOVER=0 SUP_LOG_FILE="" bash -c \
    'source "$1/af_supervisor.sh"; sup_acquire_singleton "$2"' _ "$LIB_DIR" "$PIDFILE" >/dev/null 2>&1
[[ "$?" != "0" ]]
check "test7: second acquire on a LIVE pidfile is refused (SUP_SINGLETON_TAKEOVER=0)" "$?"
[[ "$(cat "$PIDFILE")" == "$$" ]]
check "test7: pidfile still names the first owner" "$?"
sup_release_singleton
[[ ! -e "$PIDFILE" ]]
check "test7: release removes the pidfile" "$?"
echo "999999" >"$PIDFILE"   # stale: no such pid
sup_acquire_singleton "$PIDFILE" >/dev/null 2>&1
check "test7: stale pidfile (dead pid) is reclaimed" "$?"
sup_release_singleton

# Default REPLACE semantics: a live previous supervisor (a stand-in `sleep`)
# is stopped and the pidfile taken over.
# The stand-in is started by a throwaway shell so it is NOT our child: a
# child of this script would linger as a zombie (kill -0 still succeeds)
# until we `wait` for it, which would fake a failed takeover.
OLD_SUP_PID="$(bash -c 'sleep 300 >/dev/null 2>&1 & echo $!')"
echo "$OLD_SUP_PID" >"$PIDFILE"
sup_acquire_singleton "$PIDFILE" >/dev/null 2>&1
check "test7: default takeover acquires a pidfile held by a live process" "$?"
kill -0 "$OLD_SUP_PID" 2>/dev/null
[[ "$?" != "0" ]]
check "test7: the previous holder was stopped by the takeover" "$?"
kill -9 "$OLD_SUP_PID" 2>/dev/null || true
[[ "$(cat "$PIDFILE")" == "$$" ]]
check "test7: pidfile names the new owner after takeover" "$?"
sup_release_singleton

# --- test 8: FAILED app revives after cooldown -----------------------------------
# The crasher FAILED in test 2 (or re-FAILED since); force the state and let
# the cooldown elapse — it must re-enter supervision with a fresh budget.
if [[ "${SUP_STATE[$CRASHER]}" != "failed" ]]; then
    SUP_STATE[$CRASHER]="failed"
    SUP_NEXT_START_AT[$CRASHER]=$((SECONDS + SUP_FAILED_RETRY_S))
fi
REVIVED=1
END=$(( SECONDS + SUP_FAILED_RETRY_S + 6 ))
while [[ "$SECONDS" -lt "$END" ]]; do
    sup_tick
    if [[ "${SUP_STATE[$CRASHER]}" != "failed" ]]; then
        REVIVED=0
        break
    fi
    sleep 1
done
check "test8: FAILED app left the failed state after the cooldown" "$REVIVED"

# --- test 9: alive-not-ready (health answers status="starting") -------------------
# The gateway's background boot answers HTTP 200 {"status":"starting"} before
# it is ready (2026-07-21 fold). The supervisor must NOT flip it to running
# (parked apps would start against a non-serving gateway) and must NOT recycle
# it at the readiness deadline (the listener is alive) — it waits, sliding the
# deadline, until the body stops saying starting.
STARTING_PORT=$((CRIT_PORT + 20))
cat >"$WORK/starting_server.py" <<'PYEOF'
import http.server, sys, time
t0 = time.time()
FLIP_AFTER = float(sys.argv[2])
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        status = b'{"status":"starting"}' if time.time() - t0 < FLIP_AFTER else b'{"status":"healthy"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(status)))
        self.end_headers()
        self.wfile.write(status)
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
# Flip to healthy after 6s: longer than the 3s readiness window used below, so
# the old code path would have recycled it before ever seeing healthy.
sup_register "booting" 1 \
    "exec $PY $WORK/starting_server.py $STARTING_PORT 6" \
    "$WORK/booting.log" \
    "http://127.0.0.1:$STARTING_PORT/" "http://127.0.0.1:$STARTING_PORT/" ""
BOOTING=$SUP_LAST_INDEX
SAVED_READY_TIMEOUT="$SUP_READY_TIMEOUT_S"
SUP_READY_TIMEOUT_S=3
sup_start_service "$BOOTING"
BOOTING_PID_FIRST="${SUP_PID[$BOOTING]}"
sup_await_state "$BOOTING" "running" 20
check "test9: starting-status service eventually becomes running" "$?"
[[ "${SUP_PID[$BOOTING]}" == "$BOOTING_PID_FIRST" ]]
check "test9: never recycled while alive-not-ready (same pid through boot)" "$?"
SUP_READY_TIMEOUT_S="$SAVED_READY_TIMEOUT"

# --- test 6 (last: destructive): shutdown stops everything ------------------------
CRIT_PID_BEFORE="${SUP_PID[$CRIT]}"
APP_PID_BEFORE="${SUP_PID[$APP]}"
sup_shutdown
sleep 1
ALIVE=0
for pid in "$CRIT_PID_BEFORE" "$APP_PID_BEFORE"; do
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && ALIVE=$((ALIVE + 1))
done
[[ "$ALIVE" == "0" ]]
check "test6: shutdown killed every service" "$?"
[[ "${SUP_STATE[$CRIT]}" == "stopped" && "${SUP_STATE[$APP]}" == "stopped" ]]
check "test6: states are stopped" "$?"

echo ""
echo "== results: $PASS passed, $FAIL failed =="
[[ "$FAIL" == "0" ]]
