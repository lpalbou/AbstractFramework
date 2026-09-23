#!/usr/bin/env bash
# Spawn one headless playground agent by NAME — short, paste-safe command.
#
# Usage:
#   scripts/spawn_demo_agent.sh <name> [channel]
#
# Examples:
#   scripts/spawn_demo_agent.sh athena
#   scripts/spawn_demo_agent.sh apollo playground
#
# The agent must already be registered on the hub (its key in ~/.agora/keys.json).
# Register a new one with:  agora register <name> --about "headless playground agent"
#
# Rationale: the inline `AGORA_API_KEY=$(python3 -c "...")` one-liner soft-wraps
# in the terminal and zsh breaks the pasted multi-line python string. This
# resolves the key in the script, so the command a human types is one short line.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:-}"
CHANNEL="${2:-playground}"
HUB="${AGORA_URL:-http://127.0.0.1:8765}"

if [ -z "$NAME" ]; then
    echo "usage: $0 <agent-name> [channel]" >&2
    exit 2
fi

KEYS="$HOME/.agora/keys.json"
if [ ! -f "$KEYS" ]; then
    echo "error: $KEYS not found — register an agent first (agora register $NAME ...)" >&2
    exit 1
fi

# Resolve the key for HUB::NAME (single-line python, cannot paste-break here).
KEY="$(python3 -c "import json,os,sys; d=json.load(open(os.path.expanduser('$KEYS'))); print(d.get('$HUB::$NAME',''))")"
if [ -z "$KEY" ]; then
    echo "error: no key for '$NAME' on $HUB in $KEYS." >&2
    echo "       register it:  agora register $NAME --about \"headless playground agent\"" >&2
    echo "       (keys are hashed at rest — a re-register only helps if you capture the printed key)" >&2
    exit 1
fi

WORKSPACE="${ABSTRACT_DEMO_WORKSPACE:-/tmp/$NAME}"
mkdir -p "$WORKSPACE"

echo "spawning '$NAME' on $HUB channel=$CHANNEL workspace=$WORKSPACE"
echo "(provider/model resolve from the gateway baseline unless \$DEMO_PROVIDER/\$DEMO_MODEL are set)"

# Provider/model: default to the gateway baseline (the driver resolves it when
# --provider/--model are omitted); override via env for a different substrate.
EXTRA=()
if [ -n "${DEMO_PROVIDER:-}" ]; then EXTRA+=(--provider "$DEMO_PROVIDER"); fi
if [ -n "${DEMO_MODEL:-}" ]; then EXTRA+=(--model "$DEMO_MODEL"); fi

# Note the ${EXTRA[@]+...} guard: macOS bash 3.2 under `set -u` errors on an
# empty array expansion ("EXTRA[@]: unbound variable"); this expands to nothing
# when EXTRA is empty and to the flags when set.
exec env AGORA_URL="$HUB" AGORA_API_KEY="$KEY" \
    "$ROOT/.venv/bin/python" "$ROOT/scripts/headless_steer_repl.py" \
    --channel "$CHANNEL" --workspace "$WORKSPACE" --name "$NAME" ${EXTRA[@]+"${EXTRA[@]}"}
