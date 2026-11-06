#!/usr/bin/env bash
# Real child exits; no gateway/network or operator processes touched.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/af_supervisor.sh"
WORK="$(mktemp -d /tmp/af-desktop-policy.XXXXXX)"
trap 'sup_shutdown >/dev/null 2>&1; rm -rf "$WORK"' EXIT
SUP_LOG_FILE="$WORK/supervisor.log"
SUP_APP_RESTART_DELAY_S=30
SUP_KILL_GRACE_S=1
check() { if ! eval "$2"; then echo "FAIL: $1" >&2; exit 1; fi; echo "PASS: $1"; }

sup_register gateway 1 'exec sleep 60' "$WORK/gateway.log" ''
GATEWAY=$SUP_LAST_INDEX
sup_start_service "$GATEWAY"
sup_tick
GATEWAY_PID="${SUP_PID[$GATEWAY]}"
sup_register desktop 0 'echo "$AF_SUPERVISOR_RESTART_POLICY"; exit 0' "$WORK/desktop.log" '' '' '' on-failure
DESKTOP=$SUP_LAST_INDEX
sup_start_service "$DESKTOP"
sleep 0.2
# A Quit during a control-plane outage must stop, not park for later restart.
SUP_STATE[$GATEWAY]=waiting
sup_handle_death "$DESKTOP"
check 'clean Quit is stopped even during an outage' '[[ ${SUP_STATE[$DESKTOP]} == stopped ]]'
check 'Quit did not consume crash budget' '[[ -z ${SUP_RESTART_LOG[$DESKTOP]} ]]'
check 'new policy is passed to launcher' '[[ $(cat "$WORK/desktop.log") == on-failure ]]'
check 'Quit is not logged as an incident' '! grep -q "INCIDENT: desktop" "$SUP_LOG_FILE"'
SUP_STATE[$GATEWAY]=running
SUP_CRIT_HEALTHY_PREV=0
SUP_NEXT_START_AT[$DESKTOP]=0
sup_tick
sup_tick
check 'recovery and elapsed cooldown do not reopen desktop' '[[ ${SUP_STATE[$DESKTOP]} == stopped && -z ${SUP_PID[$DESKTOP]} ]]'

SUP_CMD[$DESKTOP]='exit 7'
sup_start_service "$DESKTOP"
sleep 0.2
sup_tick
check 'nonzero desktop exit schedules crash recovery' '[[ ${SUP_STATE[$DESKTOP]} == waiting && ${SUP_EXIT_STATUS[$DESKTOP]} == 7 ]]'
check 'crash charges the bounded budget' '[[ $(sup_budget_used "$DESKTOP") == 1 ]]'
SUP_CMD[$DESKTOP]='exec sleep 60'
SUP_NEXT_START_AT[$DESKTOP]=0
sup_tick
sup_tick
check 'crashed desktop really restarts' '[[ ${SUP_STATE[$DESKTOP]} == running ]]'
check 'gateway PID is unchanged' '[[ ${SUP_PID[$GATEWAY]} == "$GATEWAY_PID" ]] && kill -0 "$GATEWAY_PID"'

sup_register web 0 'exit 0' "$WORK/web.log" ''
WEB=$SUP_LAST_INDEX
sup_start_service "$WEB"
sleep 0.2
sup_tick
check 'server default still restarts on clean exit' '[[ ${SUP_STATE[$WEB]} == waiting ]]'

sup_register critical 1 'exit 0' "$WORK/critical.log" '' '' '' on-failure
CRITICAL=$SUP_LAST_INDEX
sup_start_service "$CRITICAL"
sleep 0.2
sup_tick
check 'critical recovery is unconditional' '[[ ${SUP_STATE[$CRITICAL]} == waiting ]]'

# Recycling a service for failed readiness is not an explicit Quit, even if
# its shutdown handler exits zero.
sup_register recycled 0 'exit 0' "$WORK/recycled.log" '' '' '' on-failure
RECYCLED=$SUP_LAST_INDEX
sup_start_service "$RECYCLED"
sleep 0.2
sup_handle_death "$RECYCLED" 'failed readiness'
check 'supervisor-initiated recycling is not classified as Quit' '[[ ${SUP_STATE[$RECYCLED]} == waiting ]]'
echo 'Desktop restart policy checks passed.'
