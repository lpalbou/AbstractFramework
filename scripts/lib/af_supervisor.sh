#!/usr/bin/env bash
# =============================================================================
# af_supervisor.sh — generic service supervisor for the framework stack
# =============================================================================
# Supervises long-running services with SEPARATED FAILURE DOMAINS (maintainer
# ruling 2026-07-21, dm#150: "the gateway must be extremely resilient to
# failure" — one app dying must never take the control plane down):
#
#   CRITICAL services (the gateway):
#     - app failures never touch them;
#     - restarted on death with UNLIMITED attempts and capped exponential
#       backoff (a control plane is never abandoned);
#     - actively health-probed: a hung-but-alive process (serving nothing) is
#       killed and respawned after a sustained probe-failure streak;
#     - a pre-start hook runs before EVERY spawn (first and respawns), so
#       preflight guarantees (port free, stale processes stopped, singleton
#       locks free) hold on the restart path too.
#
#   APP services (everything else):
#     - restarted on death with a BOUNDED budget (max N restarts per rolling
#       window) so a crash-looping app converges to FAILED instead of flapping
#       forever — and the rest of the stack keeps serving;
#     - PARKED while any critical service is down: restarting an app against
#       a restarting control plane burns its budget for nothing. On critical
#       recovery, budgets reset and parked apps restart (their deaths were
#       most likely collateral).
#
#   Whole-stack teardown happens ONLY on operator signal (INT/TERM): apps
#   first (reverse registration order), critical services last. An internal
#   supervisor error also tears down loudly — orphaned unmanaged children are
#   worse than a restart — but is reported as an error, never silently.
#
# The state machine is NON-BLOCKING: restarts, backoff and readiness checks
# are all scheduled through `sup_tick`, so one service's restart never blinds
# the supervisor to the others.
#
# Service states:
#   idle      registered but never started — the state machine ignores it
#             (only an explicit sup_start_service enters the machine; without
#             this, registering N services and starting the first would
#             auto-start the rest mid-launch-sequence)
#   starting  spawned, awaiting readiness probe (bounded by a deadline)
#   running   readiness confirmed; health-probed if a health URL is declared
#   waiting   scheduled to (re)start at SUP_NEXT_START_AT (backoff / parked)
#   failed    restart budget exhausted (apps only) — operator attention
#   stopped   deliberately stopped (shutdown)
#
# Portability: macOS ships bash 3.2 — parallel indexed arrays only (no
# associative arrays), no ${var,,}, no readarray. `set -u` safe.
#
# Dependencies: bash 3.2+, curl, kill/ps. Self-contained on purpose (no
# apps_common.sh dependency) so it can be tested with stub services.
# =============================================================================

# --- policies (env-tunable) --------------------------------------------------
SUP_POLL_S="${SUP_POLL_S:-2}"                               # monitor cadence
SUP_READY_TIMEOUT_S="${SUP_READY_TIMEOUT_S:-120}"           # spawn -> ready deadline
SUP_APP_RESTART_MAX="${SUP_APP_RESTART_MAX:-5}"             # app restarts per window
SUP_APP_RESTART_WINDOW_S="${SUP_APP_RESTART_WINDOW_S:-300}" # rolling budget window
SUP_APP_RESTART_DELAY_S="${SUP_APP_RESTART_DELAY_S:-2}"     # app respawn delay
SUP_CRIT_BACKOFF_CAP_S="${SUP_CRIT_BACKOFF_CAP_S:-30}"      # critical backoff cap
SUP_CRIT_STABLE_RESET_S="${SUP_CRIT_STABLE_RESET_S:-60}"    # uptime that resets backoff
SUP_HEALTH_EVERY_S="${SUP_HEALTH_EVERY_S:-10}"              # active probe cadence
SUP_HEALTH_FAILS_MAX="${SUP_HEALTH_FAILS_MAX:-6}"           # consecutive fails = hung
# Hang-kill DISARMED by default (operator ruling 2026-08-20: "the supervisor
# is here ONLY to relaunch the gateway if it crashes"). One day of af-stack.log
# showed the probe-kill executing a healthy-but-busy gateway (in-process MLX
# pins the GIL long enough to miss 6 probes) while every other restart that
# day was an EXTERNAL kill the supervisor mislabeled as its own concern. A
# sustained unhealthy streak now logs LOUDLY and keeps logging; set
# SUP_HANG_KILL=1 to restore kill-and-respawn on hang.
SUP_HANG_KILL="${SUP_HANG_KILL:-0}"
# Shared kill-receipt ledger: apps_common.sh's stop helpers append a line for
# every kill they issue, so a signal death here can name its killer. Lives in
# the user's home, not /tmp (adversarial review 2026-08-20: /tmp is world-
# writable — symlink/spoof surface — and macOS cleans it, erasing evidence
# between the kill and the incident).
AF_KILL_RECEIPTS="${AF_KILL_RECEIPTS:-$HOME/.abstractframework/kill-receipts.log}"
SUP_PROBE_TIMEOUT_S="${SUP_PROBE_TIMEOUT_S:-3}"             # per-probe curl timeout
SUP_KILL_GRACE_S="${SUP_KILL_GRACE_S:-5}"                   # TERM -> KILL grace
SUP_FAILED_RETRY_S="${SUP_FAILED_RETRY_S:-600}"             # FAILED app cooldown retry
SUP_STARTING_ALIVE_MAX_S="${SUP_STARTING_ALIVE_MAX_S:-600}" # alive-not-ready hard cap

# --- registry + runtime state (parallel arrays, index = service id) ----------
SUP_NAME=(); SUP_CMD=(); SUP_LOG=(); SUP_READY_URL=(); SUP_HEALTH_URL=()
SUP_CRITICAL=(); SUP_PRESTART=()
SUP_PID=(); SUP_STATE=(); SUP_STARTED_AT=(); SUP_READY_DEADLINE=()
SUP_NEXT_START_AT=(); SUP_RESTART_LOG=(); SUP_BACKOFF_N=()
SUP_HEALTH_FAILS=(); SUP_LAST_PROBE=(); SUP_EXIT_STATUS=()
SUP_COUNT=0
SUP_SHUTDOWN=0
SUP_LOG_FILE="${SUP_LOG_FILE:-}"
SUP_CRIT_HEALTHY_PREV=1
SUP_PIDFILE=""

# Initialize $! deterministically: on bash 3.2 under `set -u`, reading $!
# before any background job ever ran is a fatal unbound-variable error (and
# `${!:-}` does not protect it — parsed as indirect expansion). The fork
# guard in sup_start_service compares $! before/after each spawn, so it needs
# a defined baseline. One no-op job at source time provides it.
: &
wait "$!" 2>/dev/null || true

# Time base: the SECONDS builtin (relative, monotonic-enough) — NOT `date`.
# Every internal read is a direct $SECONDS variable expansion with zero forks:
# under fork exhaustion (exactly when a crash-looping service needs the
# supervisor most) a $(date) substitution fails and, under errexit, one failed
# fork would tear down a healthy stack. All stored times are relative to shell
# start, so comparisons stay consistent. sup_now stays for callers/tests.
sup_now() { echo "$SECONDS"; }

# Timestamped supervisor line: terminal + optional supervisor log file.
# The human timestamp is best-effort (`|| true` inside the substitution): a
# failed `date` fork must never abort the supervisor (errexit).
sup_log() {
    local ts line
    # `|| ts=""` catches a failed FORK of the substitution itself, not just a
    # failing date (adversarial review 2026-08-20: the incident banner logs
    # ~25 lines — exactly when fork exhaustion is most likely, one failed
    # assignment under errexit would have torn down the healthy stack).
    ts="$(date '+%H:%M:%S' 2>/dev/null || true)" || ts=""
    line="[af-stack ${ts:-+${SECONDS}s}] $*"
    echo "$line"
    if [[ -n "$SUP_LOG_FILE" ]]; then
        echo "$line" >>"$SUP_LOG_FILE" 2>/dev/null || true
    fi
}

# Decode an exit status into WHAT ACTUALLY HAPPENED (operator ruling
# 2026-08-20: a death must be a big, legible incident, not one mute line).
# >128 = death by signal: named, and explicitly NOT a crash — one day of
# af-stack.log was 10 restarts, all signals, zero crashes, and the old
# rendering made every one look like a gateway defect.
sup_describe_status() {
    local status="${1:-}"
    case "$status" in
        0)   echo "exit 0 — clean exit (something asked it to stop; NOT a crash)" ;;
        129) echo "SIGHUP (129) — hangup from outside (NOT a crash)" ;;
        130) echo "SIGINT (130) — interrupted from outside (NOT a crash)" ;;
        137) echo "SIGKILL (137) — killed from outside: an explicit kill -9 (bench/untracked scripts do this), or memory pressure (NOT a crash)" ;;
        143) echo "SIGTERM (143) — KILLED FROM OUTSIDE this supervisor: another launcher/script/agent stopped it (NOT a crash)" ;;
        "")  echo "unknown exit status" ;;
        *)   if [[ "$status" -gt 128 ]] 2>/dev/null; then
                 echo "signal $((status - 128)) (status ${status}) — killed from outside (NOT a crash)"
             else
                 echo "CRASH (exit ${status}) — read the traceback in the log tail below"
             fi ;;
    esac
}

# The incident banner: loud, complete, and in BOTH sinks (terminal + the
# supervisor log). The old sup_log_tail sent the log tail to stderr only, so
# af-stack.log recorded a bare "— last log lines:" header followed by
# NOTHING — a day of restarts left zero usable evidence (operator ruling
# 2026-08-20: "BIG ERROR MESSAGES THAT WE SEE").
sup_log_incident() {
    local label="$1" log_file="$2" status="${3:-}" reason="${4:-exited}"
    local line
    sup_log "=================================================================="
    sup_log "!! INCIDENT: $label"
    if [[ "$reason" == "exited" ]]; then
        sup_log "!! cause: $(sup_describe_status "$status")"
    else
        sup_log "!! cause: stopped by THIS supervisor (${reason})"
    fi
    sup_log "!! last log lines (${log_file}):"
    tail -n 40 "$log_file" 2>/dev/null | while IFS= read -r line; do
        sup_log "!!   $line"
    done || true
    # Signal deaths: name the killer when a framework script left a receipt.
    if [[ "$reason" == "exited" && -n "$status" ]] && [[ "$status" -gt 128 ]] 2>/dev/null; then
        if [[ -s "$AF_KILL_RECEIPTS" ]]; then
            sup_log "!! last framework kill receipts (${AF_KILL_RECEIPTS}) — match the TIMESTAMPS against"
            sup_log "!! this death; the ledger also holds this supervisor's own routine prestart kills:"
            tail -n 5 "$AF_KILL_RECEIPTS" 2>/dev/null | while IFS= read -r line; do
                sup_log "!!   $line"
            done || true
        else
            sup_log "!! no framework kill receipt — the killer bypassed the framework's receipted helpers:"
            sup_log "!!   a raw kill/pkill (agent session), a bench/untracked script, a sandboxed session,"
            sup_log "!!   another checkout, or memory pressure (SIGKILL)."
        fi
    fi
    sup_log "=================================================================="
}

# Keep ONE generation of incident evidence: plain `>` truncation on respawn
# used to destroy the crashing run's log (2026-07-21 outage forensics were
# overwritten mid-investigation).
sup_rotate_log() {
    local log="$1"
    [[ -s "$log" ]] && mv -f "$log" "${log}.prev" 2>/dev/null || true
}

# -f: an HTTP >= 400 answer is NOT healthy (the old stack's wait_for_url
# accepted any status — flagged by the launcher adversary 2026-07-21).
sup_probe_url() {
    curl -sf -m "$SUP_PROBE_TIMEOUT_S" -o /dev/null "$1" 2>/dev/null
}

# Body-aware readiness: echoes ready | starting | down.
# The gateway's /api/health now answers HTTP 200 with status="starting" while
# its heavy boot runs on a background thread (gateway boot-window fold,
# 2026-07-21): that is ALIVE-NOT-READY — without this check a 200-starting
# answer would flip the service to running and release parked apps against a
# gateway that cannot serve them yet. Ready = any other 2xx answer
# (healthy|degraded for the gateway; plain HTML for app URLs, where the
# substring never matches).
sup_probe_ready() {
    local body
    # A service with no ready URL has no endpoint to probe — a desktop/tray app
    # (AbstractAssistant) serves no port at all. The only caller reaches here
    # having just confirmed the pid is alive, so alive IS ready. Without this,
    # an empty URL curls nothing, reads "down" forever, and the supervisor
    # recycles a perfectly healthy app every readiness deadline until its
    # restart budget converges it to FAILED.
    if [[ -z "${1:-}" ]]; then
        echo "ready"
        return 0
    fi
    if ! body="$(curl -sf -m "$SUP_PROBE_TIMEOUT_S" "$1" 2>/dev/null)"; then
        echo "down"
        return 0
    fi
    if printf '%s' "$body" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"starting"'; then
        echo "starting"
    else
        echo "ready"
    fi
}

# --- singleton guard -----------------------------------------------------------
# TWO supervisors over the same stack slaughter each other's gateways forever:
# each one's prestart stop/free_port kills the other's gateway, both detect
# death, both respawn, unbounded war (P0, live-proven by the verifying seat
# 2026-07-21). The pidfile is scoped to the caller's runtime dir, so a shadow
# stack (own RUNTIME_DIR) coexists with production. macOS has no flock(1);
# noclobber-create is the atomic primitive, with a kill-0 staleness check
# (a crashed supervisor leaves a dead pid — reclaimed, never blocking).
sup_acquire_singleton() {
    # REPLACE semantics (operator incident 2026-07-22 04:05: start-local.sh's
    # whole purpose is rebuild-and-relaunch, and the first singleton guard
    # REFUSED when a previous supervisor was running — "wtf"). A live previous
    # supervisor is STOPPED (TERM -> its own teardown cascades: apps first,
    # gateway last) and this one takes over. Refusal remains only for the
    # unkillable case. SUP_SINGLETON_TAKEOVER=0 restores refuse-only.
    local pidfile="$1" attempt existing waited
    for attempt in 1 2 3; do
        if ( set -o noclobber; echo "$$" >"$pidfile" ) 2>/dev/null; then
            SUP_PIDFILE="$pidfile"
            return 0
        fi
        existing="$(cat "$pidfile" 2>/dev/null || true)"
        if [[ -n "$existing" ]] && kill -0 "$existing" 2>/dev/null; then
            if [[ "${SUP_SINGLETON_TAKEOVER:-1}" != "1" ]]; then
                sup_log "ERROR: another stack supervisor is already running (pid ${existing}, ${pidfile})."
                sup_log "  SUP_SINGLETON_TAKEOVER=0 is set — stop it yourself (kill ${existing}) and re-run."
                return 1
            fi
            sup_log "replacing the running stack supervisor (pid ${existing}) — stopping it and taking over"
            kill "$existing" 2>/dev/null || true
            # Its teardown stops every app then the gateway; wait for the pid
            # to die (bounded), then KILL if it ignored TERM.
            waited=0
            while kill -0 "$existing" 2>/dev/null && [[ "$waited" -lt 40 ]]; do
                sleep 1
                waited=$((waited + 1))
            done
            if kill -0 "$existing" 2>/dev/null; then
                sup_log "previous supervisor ignored TERM after ${waited}s — KILLing it (its services are swept by our preflights)"
                kill -9 "$existing" 2>/dev/null || true
                sleep 1
            fi
        fi
        # Stale/released file: reclaim and retry the atomic create.
        rm -f "$pidfile" 2>/dev/null || true
    done
    sup_log "ERROR: could not acquire the supervisor pidfile: ${pidfile}"
    return 1
}

# Release only OUR OWN pidfile — never a successor's (a stale-reclaim may have
# rewritten it after our crash-recovery race).
sup_release_singleton() {
    [[ -n "$SUP_PIDFILE" ]] || return 0
    if [[ "$(cat "$SUP_PIDFILE" 2>/dev/null || true)" == "$$" ]]; then
        rm -f "$SUP_PIDFILE" 2>/dev/null || true
    fi
    SUP_PIDFILE=""
}

# TERM, bounded grace, then KILL. Reaps the child so no zombies accumulate.
sup_kill_pid() {
    local pid="$1"
    [[ -n "$pid" ]] || return 0
    kill -0 "$pid" >/dev/null 2>&1 || { wait "$pid" 2>/dev/null || true; return 0; }
    kill "$pid" >/dev/null 2>&1 || true
    local i=0
    while [[ "$i" -lt "$SUP_KILL_GRACE_S" ]]; do
        kill -0 "$pid" >/dev/null 2>&1 || break
        sleep 1
        i=$((i + 1))
    done
    kill -0 "$pid" >/dev/null 2>&1 && kill -9 "$pid" >/dev/null 2>&1 || true
    wait "$pid" 2>/dev/null || true
}

# --- registration -------------------------------------------------------------
# sup_register <name> <critical 0|1> <command> <log> <ready_url> [health_url] [prestart_fn]
# The command runs via `bash -c`; the resulting pid is the service (launchers
# exec into their server process, so killing the pid kills the service).
# Sets SUP_LAST_INDEX to the new service id.
sup_register() {
    local i="$SUP_COUNT"
    SUP_NAME[$i]="$1"
    SUP_CRITICAL[$i]="$2"
    SUP_CMD[$i]="$3"
    SUP_LOG[$i]="$4"
    SUP_READY_URL[$i]="$5"
    SUP_HEALTH_URL[$i]="${6:-}"
    SUP_PRESTART[$i]="${7:-}"
    SUP_PID[$i]=""
    SUP_STATE[$i]="idle"
    SUP_STARTED_AT[$i]=0
    SUP_READY_DEADLINE[$i]=0
    SUP_NEXT_START_AT[$i]=0
    SUP_RESTART_LOG[$i]=""
    SUP_BACKOFF_N[$i]=0
    SUP_HEALTH_FAILS[$i]=0
    SUP_LAST_PROBE[$i]=0
    SUP_EXIT_STATUS[$i]=""
    SUP_COUNT=$((SUP_COUNT + 1))
    SUP_LAST_INDEX="$i"
}

# --- restart budget (apps) ----------------------------------------------------
# The budget is a rolling window of restart timestamps kept as a space-
# separated string (bash-3.2 friendly). Returns 0 when a restart is allowed.
sup_budget_allows() {
    local i="$1" now cutoff kept ts n=0
    now="$SECONDS"
    cutoff=$((now - SUP_APP_RESTART_WINDOW_S))
    kept=""
    for ts in ${SUP_RESTART_LOG[$i]}; do
        if [[ "$ts" -gt "$cutoff" ]]; then
            kept="$kept $ts"
            n=$((n + 1))
        fi
    done
    SUP_RESTART_LOG[$i]="${kept# }"
    [[ "$n" -lt "$SUP_APP_RESTART_MAX" ]]
}

sup_budget_charge() {
    local i="$1"
    SUP_RESTART_LOG[$i]="${SUP_RESTART_LOG[$i]} $SECONDS"
    SUP_RESTART_LOG[$i]="${SUP_RESTART_LOG[$i]# }"
}

sup_budget_used() {
    local i="$1" n=0 ts
    for ts in ${SUP_RESTART_LOG[$i]}; do n=$((n + 1)); done
    echo "$n"
}

# --- critical-domain health ----------------------------------------------------
# 0 when every critical service is confirmed running. Apps only (re)start when
# the critical domain is healthy — restarting them against a restarting
# control plane wastes their budget.
sup_critical_healthy() {
    local i=0
    while [[ "$i" -lt "$SUP_COUNT" ]]; do
        if [[ "${SUP_CRITICAL[$i]}" == "1" && "${SUP_STATE[$i]}" != "running" ]]; then
            return 1
        fi
        i=$((i + 1))
    done
    return 0
}

# --- spawn --------------------------------------------------------------------
sup_start_service() {
    local i="$1" now prev_bang
    now="$SECONDS"

    if [[ -n "${SUP_PRESTART[$i]}" ]]; then
        # A failing prestart (e.g. singleton lock still held) must not kill the
        # supervisor: log loudly and retry through the normal schedule.
        if ! "${SUP_PRESTART[$i]}" "$i"; then
            sup_log "ERROR: ${SUP_NAME[$i]} pre-start hook failed; retrying in ${SUP_CRIT_BACKOFF_CAP_S}s"
            SUP_STATE[$i]="waiting"
            SUP_NEXT_START_AT[$i]=$((now + SUP_CRIT_BACKOFF_CAP_S))
            return 1
        fi
    fi

    sup_rotate_log "${SUP_LOG[$i]}"
    # FORK GUARD: if the async spawn fails (fork exhaustion), `$!` silently
    # keeps its PREVIOUS value — a SIBLING service's pid. Tracking that would
    # mean false liveness now and killing the wrong service later. Detect by
    # comparing $! before/after ($! is always set: source-time init job).
    prev_bang="$!"
    # NOTE: when the supervisor later kills this child, bash prints an
    # asynchronous "Terminated: 15" job notice. It is deliberate noise: it
    # names the pid and signal, and suppressing it would cost either exit-
    # status capture (disown) or child reaping (subshell spawn).
    bash -c "${SUP_CMD[$i]}" >"${SUP_LOG[$i]}" 2>&1 &
    if [[ "$!" == "$prev_bang" ]]; then
        sup_log "ERROR: ${SUP_NAME[$i]}: spawn failed (fork pressure?); retrying in ${SUP_CRIT_BACKOFF_CAP_S}s"
        SUP_PID[$i]=""
        SUP_STATE[$i]="waiting"
        SUP_NEXT_START_AT[$i]=$((now + SUP_CRIT_BACKOFF_CAP_S))
        return 1
    fi
    SUP_PID[$i]=$!
    SUP_STATE[$i]="starting"
    SUP_STARTED_AT[$i]="$now"
    SUP_READY_DEADLINE[$i]=$((now + SUP_READY_TIMEOUT_S))
    SUP_HEALTH_FAILS[$i]=0
    SUP_LAST_PROBE[$i]=0
    sup_log "${SUP_NAME[$i]}: starting (pid ${SUP_PID[$i]})"
    return 0
}

# --- death handling -------------------------------------------------------------
# Reap the child, log the evidence, and decide the next state per failure
# domain. `reason` distinguishes a real exit from a supervisor-initiated kill.
sup_handle_death() {
    local i="$1" reason="${2:-exited}" status="" now
    now="$SECONDS"

    if [[ -n "${SUP_PID[$i]}" ]]; then
        # `wait` returns the child's (non-zero) exit status — keep it out of
        # errexit's reach while capturing it.
        if wait "${SUP_PID[$i]}" 2>/dev/null; then status=0; else status=$?; fi
    fi
    SUP_EXIT_STATUS[$i]="$status"
    SUP_PID[$i]=""

    sup_log_incident "${SUP_NAME[$i]} ${reason} (status ${status:-?})" "${SUP_LOG[$i]}" "$status" "$reason"

    if [[ "${SUP_CRITICAL[$i]}" == "1" ]]; then
        # Critical: never abandoned. Exponential backoff, capped; reset after
        # stable uptime (sup_tick does the reset when running long enough).
        local delay
        delay=$((1 << SUP_BACKOFF_N[$i]))
        [[ "$delay" -gt "$SUP_CRIT_BACKOFF_CAP_S" ]] && delay="$SUP_CRIT_BACKOFF_CAP_S"
        [[ "${SUP_BACKOFF_N[$i]}" -lt 10 ]] && SUP_BACKOFF_N[$i]=$((SUP_BACKOFF_N[$i] + 1))
        SUP_STATE[$i]="waiting"
        SUP_NEXT_START_AT[$i]=$((now + delay))
        sup_log "${SUP_NAME[$i]} is CRITICAL — restarting in ${delay}s (attempt ${SUP_BACKOFF_N[$i]})"
        return 0
    fi

    if ! sup_critical_healthy; then
        # Collateral of a control-plane outage: park without charging budget.
        SUP_STATE[$i]="waiting"
        SUP_NEXT_START_AT[$i]=0
        sup_log "${SUP_NAME[$i]}: parked until the control plane recovers"
        return 0
    fi

    if sup_budget_allows "$i"; then
        sup_budget_charge "$i"
        SUP_STATE[$i]="waiting"
        SUP_NEXT_START_AT[$i]=$((now + SUP_APP_RESTART_DELAY_S))
        sup_log "${SUP_NAME[$i]}: restarting in ${SUP_APP_RESTART_DELAY_S}s ($(sup_budget_used "$i")/${SUP_APP_RESTART_MAX} restarts in the last ${SUP_APP_RESTART_WINDOW_S}s)"
    else
        # FAILED is loud but not forever: a cooldown retry (fresh budget)
        # keeps the app supervised. Advising a manual launcher run here would
        # create an UNSUPERVISED process beside the supervisor (verifier
        # finding c4044) — the operator restarts the stack, not one app.
        SUP_STATE[$i]="failed"
        SUP_NEXT_START_AT[$i]=$((now + SUP_FAILED_RETRY_S))
        sup_log "${SUP_NAME[$i]} FAILED: restart budget exhausted (${SUP_APP_RESTART_MAX} in ${SUP_APP_RESTART_WINDOW_S}s). The rest of the stack keeps running."
        sup_log "  inspect ${SUP_LOG[$i]}; the supervisor retries it in ${SUP_FAILED_RETRY_S}s (or right after a control-plane recovery)"
    fi
}

# A FAILED app re-enters supervision with a fresh budget (cooldown expiry or
# control-plane recovery). Never applies to critical services (they never
# reach FAILED) or to shutdown.
sup_revive_failed() {
    local i="$1" why="$2"
    SUP_RESTART_LOG[$i]=""
    SUP_STATE[$i]="waiting"
    SUP_NEXT_START_AT[$i]="$SECONDS"
    sup_log "${SUP_NAME[$i]}: retrying after FAILED (${why}; fresh restart budget)"
}

# --- the state machine ----------------------------------------------------------
# One non-blocking pass over every service. Called by sup_monitor on a cadence
# and by sup_await_state while the launch sequence waits.
sup_tick() {
    local i=0 now crit_healthy_now
    now="$SECONDS"

    while [[ "$i" -lt "$SUP_COUNT" ]]; do
        case "${SUP_STATE[$i]}" in
            starting|running)
                if ! kill -0 "${SUP_PID[$i]:-}" >/dev/null 2>&1; then
                    sup_handle_death "$i" "exited"
                    i=$((i + 1)); continue
                fi
                if [[ "${SUP_STATE[$i]}" == "starting" ]]; then
                    case "$(sup_probe_ready "${SUP_READY_URL[$i]}")" in
                        ready)
                            SUP_STATE[$i]="running"
                            sup_log "${SUP_NAME[$i]}: ready"
                            ;;
                        starting)
                            # Alive-not-ready (gateway background boot): the
                            # listener answered, so this is never a readiness
                            # miss — keep sliding the deadline. A hard cap
                            # still catches a boot wedged forever in
                            # "starting". SUP_LAST_PROBE doubles as the
                            # logged-once marker here (reset on every spawn;
                            # the running branch reads it as a stale probe
                            # time and probes immediately — harmless).
                            if [[ $((now - SUP_STARTED_AT[$i])) -gt "$SUP_STARTING_ALIVE_MAX_S" ]]; then
                                sup_log "${SUP_NAME[$i]}: still 'starting' after ${SUP_STARTING_ALIVE_MAX_S}s — wedged boot, recycling"
                                sup_kill_pid "${SUP_PID[$i]}"
                                sup_handle_death "$i" "wedged boot"
                            else
                                if [[ "${SUP_LAST_PROBE[$i]}" == "0" ]]; then
                                    sup_log "${SUP_NAME[$i]}: alive, boot in progress (status=starting) — waiting without charging the readiness deadline"
                                    SUP_LAST_PROBE[$i]=1
                                fi
                                SUP_READY_DEADLINE[$i]=$((now + SUP_READY_TIMEOUT_S))
                            fi
                            ;;
                        down)
                            if [[ "$now" -gt "${SUP_READY_DEADLINE[$i]}" ]]; then
                                sup_log "${SUP_NAME[$i]}: not ready after ${SUP_READY_TIMEOUT_S}s — recycling"
                                sup_kill_pid "${SUP_PID[$i]}"
                                sup_handle_death "$i" "failed readiness"
                            fi
                            ;;
                    esac
                else
                    # Running: reset critical backoff after stable uptime, and
                    # actively probe declared health URLs to catch hung-alive.
                    if [[ "${SUP_CRITICAL[$i]}" == "1" && "${SUP_BACKOFF_N[$i]}" -gt 0 ]] \
                        && [[ $((now - SUP_STARTED_AT[$i])) -ge "$SUP_CRIT_STABLE_RESET_S" ]]; then
                        SUP_BACKOFF_N[$i]=0
                    fi
                    if [[ -n "${SUP_HEALTH_URL[$i]}" ]] \
                        && [[ $((now - SUP_LAST_PROBE[$i])) -ge "$SUP_HEALTH_EVERY_S" ]]; then
                        SUP_LAST_PROBE[$i]="$now"
                        if sup_probe_url "${SUP_HEALTH_URL[$i]}"; then
                            if [[ "${SUP_HEALTH_FAILS[$i]}" -gt 0 ]]; then
                                sup_log "${SUP_NAME[$i]}: healthy again (after ${SUP_HEALTH_FAILS[$i]} failed probes — it was busy, not dead)"
                            fi
                            SUP_HEALTH_FAILS[$i]=0
                        else
                            SUP_HEALTH_FAILS[$i]=$((SUP_HEALTH_FAILS[$i] + 1))
                            sup_log "${SUP_NAME[$i]}: health probe failed (${SUP_HEALTH_FAILS[$i]}/${SUP_HEALTH_FAILS_MAX})"
                            if [[ "${SUP_HEALTH_FAILS[$i]}" -ge "$SUP_HEALTH_FAILS_MAX" ]]; then
                                if [[ "$SUP_HANG_KILL" == "1" ]]; then
                                    sup_log "${SUP_NAME[$i]}: hung (alive but unhealthy for ${SUP_HEALTH_FAILS_MAX} probes) — killing for restart (SUP_HANG_KILL=1)"
                                    sup_kill_pid "${SUP_PID[$i]}"
                                    sup_handle_death "$i" "hung"
                                elif [[ $((SUP_HEALTH_FAILS[$i] % SUP_HEALTH_FAILS_MAX)) -eq 0 ]]; then
                                    # Operator ruling 2026-08-20: the supervisor
                                    # restarts on DEATH only. A busy gateway
                                    # (in-process MLX pinning the GIL) can miss
                                    # probes for minutes while doing real work —
                                    # killing it destroyed more than it saved.
                                    # Stay LOUD (every ${SUP_HEALTH_FAILS_MAX}
                                    # fails), never lethal.
                                    sup_log "=================================================================="
                                    sup_log "!! ${SUP_NAME[$i]}: UNHEALTHY for ${SUP_HEALTH_FAILS[$i]} probes (~$((SUP_HEALTH_FAILS[$i] * SUP_HEALTH_EVERY_S))s) — alive but not answering ${SUP_HEALTH_URL[$i]}"
                                    sup_log "!! NOT restarting it (this supervisor restarts on death only; SUP_HANG_KILL=1 restores hang-recycling)"
                                    sup_log "!! likely busy (in-process model inference); investigate: tail -f ${SUP_LOG[$i]}"
                                    sup_log "=================================================================="
                                fi
                            fi
                        fi
                    fi
                fi
                ;;
            waiting)
                if [[ "${SUP_CRITICAL[$i]}" == "1" ]]; then
                    [[ "$now" -ge "${SUP_NEXT_START_AT[$i]}" ]] && sup_start_service "$i" || true
                else
                    # Apps wait for both their schedule and a healthy critical
                    # domain (their launchers preflight the gateway anyway;
                    # this avoids burning budget on doomed starts).
                    if sup_critical_healthy && [[ "$now" -ge "${SUP_NEXT_START_AT[$i]}" ]]; then
                        sup_start_service "$i" || true
                    fi
                fi
                ;;
            failed)
                # Cooldown retry: FAILED stays supervised (fresh budget) once
                # the cooldown elapses and the control plane is healthy.
                if sup_critical_healthy && [[ "$now" -ge "${SUP_NEXT_START_AT[$i]}" ]]; then
                    sup_revive_failed "$i" "cooldown of ${SUP_FAILED_RETRY_S}s elapsed"
                fi
                ;;
            idle|stopped)
                : # inert until explicit start / shutdown
                ;;
        esac
        i=$((i + 1))
    done

    # Critical-domain recovery edge: reset app budgets (their crashes were
    # most likely collateral) and revive FAILED apps immediately — the outage
    # that exhausted their budget is over. Only announce when something was
    # actually cleared (a first launch also crosses this edge).
    if sup_critical_healthy; then crit_healthy_now=1; else crit_healthy_now=0; fi
    if [[ "$crit_healthy_now" == "1" && "$SUP_CRIT_HEALTHY_PREV" == "0" ]]; then
        local cleared=0
        i=0
        while [[ "$i" -lt "$SUP_COUNT" ]]; do
            if [[ "${SUP_CRITICAL[$i]}" != "1" ]]; then
                if [[ "${SUP_STATE[$i]}" == "failed" ]]; then
                    sup_revive_failed "$i" "control plane recovered"
                    cleared=$((cleared + 1))
                elif [[ -n "${SUP_RESTART_LOG[$i]}" ]]; then
                    SUP_RESTART_LOG[$i]=""
                    cleared=$((cleared + 1))
                fi
            fi
            i=$((i + 1))
        done
        if [[ "$cleared" -gt 0 ]]; then
            sup_log "control plane recovered — reset/revived ${cleared} app(s)"
        fi
    fi
    SUP_CRIT_HEALTHY_PREV="$crit_healthy_now"
}

# Block (ticking the machine) until service <i> reaches <state> or timeout.
# Returns 0 on reached, 1 on timeout or terminal failure.
sup_await_state() {
    local i="$1" want="$2" timeout_s="${3:-$SUP_READY_TIMEOUT_S}" deadline
    deadline=$(( SECONDS + timeout_s ))
    while [[ "$SECONDS" -lt "$deadline" ]]; do
        sup_tick
        [[ "${SUP_STATE[$i]}" == "$want" ]] && return 0
        [[ "${SUP_STATE[$i]}" == "failed" ]] && return 1
        [[ "$SUP_SHUTDOWN" == "1" ]] && return 1
        sleep 1
    done
    return 1
}

# --- shutdown -------------------------------------------------------------------
# Operator-initiated (or supervisor-error) teardown: apps first in REVERSE
# registration order, critical services last. Releases the singleton pidfile.
sup_shutdown() {
    SUP_SHUTDOWN=1
    sup_release_singleton
    local i
    i=$((SUP_COUNT - 1))
    while [[ "$i" -ge 0 ]]; do
        if [[ "${SUP_CRITICAL[$i]}" != "1" && -n "${SUP_PID[$i]}" ]]; then
            sup_log "stopping ${SUP_NAME[$i]}"
            sup_kill_pid "${SUP_PID[$i]}"
            SUP_PID[$i]=""
        fi
        SUP_STATE[$i]="stopped"
        i=$((i - 1))
    done
    i=$((SUP_COUNT - 1))
    while [[ "$i" -ge 0 ]]; do
        if [[ "${SUP_CRITICAL[$i]}" == "1" && -n "${SUP_PID[$i]}" ]]; then
            sup_log "stopping ${SUP_NAME[$i]} (control plane last)"
            sup_kill_pid "${SUP_PID[$i]}"
            SUP_PID[$i]=""
        fi
        SUP_STATE[$i]="stopped"
        i=$((i - 1))
    done
}

# --- monitor loop -----------------------------------------------------------------
# Runs until an operator signal. Never exits on service failure: failure
# handling lives in the state machine, and a FAILED app leaves the rest of
# the stack serving.
sup_monitor() {
    while [[ "$SUP_SHUTDOWN" == "0" ]]; do
        sup_tick
        sleep "$SUP_POLL_S"
    done
}

sup_status_line() {
    local i=0 out=""
    while [[ "$i" -lt "$SUP_COUNT" ]]; do
        out="$out ${SUP_NAME[$i]}=${SUP_STATE[$i]}"
        i=$((i + 1))
    done
    echo "${out# }"
}
