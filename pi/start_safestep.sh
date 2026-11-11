#!/bin/bash

#!/bin/bash

# SafeStep detection startup configuration

PROJECT_DIR="$HOME/SafeStepAI"
ALARM_LOG="$PROJECT_DIR/alarm_player.log"

# Dashboard Raspberry Pi (fixed IP)
DASHBOARD_HOST="172.16.1.128"
export SAFESTEP_URL="http://${DASHBOARD_HOST}:8080/api/event.php"

# Unique device ID for this detection Raspberry Pi
export SAFESTEP_DEVICE="${SAFESTEP_DEVICE:-pi-01}"

KEY_DIR="$HOME/.config/safestep"
KEY_FILE="$KEY_DIR/api_key"

# --- API key reset ---
if [ "$1" = "--reset-key" ]; then
    rm -f "$KEY_FILE"
    unset SAFESTEP_API_KEY
    echo "Saved API key deleted."
fi

# --- Load API key ---
if [ -f "$KEY_FILE" ] && [ "$(stat -c %a "$KEY_FILE")" != "600" ]; then
    chmod 600 "$KEY_FILE"
fi

if [ -z "$SAFESTEP_API_KEY" ] && [ -f "$KEY_FILE" ]; then
    SAFESTEP_API_KEY=$(tr -d '[:space:]' < "$KEY_FILE")
    echo "API key loaded from $KEY_FILE"
fi

if [ -z "$SAFESTEP_API_KEY" ]; then
    if [ ! -t 0 ]; then
        echo "ERROR: API key is not saved. Run this script manually first."
        exit 1
    fi

    read -r -s -p "API key: " SAFESTEP_API_KEY
    echo

    read -r -p "Save the API key? [y/N]: " SAVE_KEY

    if [[ "$SAVE_KEY" =~ ^[Yy]$ ]]; then
        mkdir -p "$KEY_DIR"
        chmod 700 "$KEY_DIR"
        ( umask 077; printf '%s\n' "$SAFESTEP_API_KEY" > "$KEY_FILE" )
        chmod 600 "$KEY_FILE"
        echo "API key saved."
    fi
fi

export SAFESTEP_API_KEY

# --- Check dashboard API connection ---
CODE=$(curl -sS -o /dev/null -m 5 -w "%{http_code}" "$SAFESTEP_URL")

if [ "$CODE" != "405" ]; then
    echo "Cannot reach the dashboard API (HTTP code: $CODE)."
    echo "Check the dashboard Raspberry Pi and network connection."
    exit 1
fi

echo "Dashboard API reachable."

# --- Start alarm player ---
mkdir -p "$PROJECT_DIR/alarm"

PLAYER_PID=""

if pgrep -f "python3.* alarm_player.py" > /dev/null; then
    echo "Alarm player is already running."
else
    python3 -u "$PROJECT_DIR/alarm_player.py" > "$ALARM_LOG" 2>&1 &
    PLAYER_PID=$!

    sleep 1

    if kill -0 "$PLAYER_PID" 2>/dev/null; then
        echo "Alarm player started."
    else
        echo "WARNING: Alarm player did not start."
        echo "See $ALARM_LOG"
        PLAYER_PID=""
    fi
fi

cleanup() {
    if [ -n "$PLAYER_PID" ]; then
        kill "$PLAYER_PID" 2>/dev/null
    fi
}

trap cleanup EXIT

echo "Starting SafeStep detection..."

# --- Run detection in Docker ---
# -it removed for systemd compatibility

docker run --rm \
  --device /dev/video0:/dev/video0 \
  -e SAFESTEP_URL \
  -e SAFESTEP_DEVICE \
  -e SAFESTEP_API_KEY \
  -v "$PROJECT_DIR":/workspace \
  -w /workspace \
  ultralytics/ultralytics:latest-arm64 \
  python safestep_run.py
