#!/bin/bash
# Start SafeStep detection in Docker, together with the alarm player on the Pi host.
# Asks for the dashboard host IP, loads or asks for the API key, checks the
# connection, then runs.
#
# Usage:
#   ./start_safestep.sh              normal start
#   ./start_safestep.sh --reset-key  delete the saved API key, then start

PROJECT_DIR="$HOME/SafeStepAI"
IP_FILE="$PROJECT_DIR/.last_host_ip"
ALARM_LOG="$PROJECT_DIR/alarm_player.log"
KEY_DIR="$HOME/.config/safestep"
KEY_FILE="$KEY_DIR/api_key"

if [ "$1" = "--reset-key" ]; then
    rm -f "$KEY_FILE"
    unset SAFESTEP_API_KEY
    echo "Saved API key deleted."
fi

LAST_IP=""
if [ -f "$IP_FILE" ]; then
    LAST_IP=$(cat "$IP_FILE")
fi

read -r -p "Dashboard host IP [${LAST_IP}]: " HOST_IP
HOST_IP="${HOST_IP:-$LAST_IP}"

if ! [[ "$HOST_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
    echo "Invalid IP address."
    exit 1
fi

export SAFESTEP_URL="http://${HOST_IP}/safestep/host/api/event.php"
export SAFESTEP_DEVICE="${SAFESTEP_DEVICE:-pi-01}"

# --- API key: environment variable first, then the key file, then ask ---
if [ -f "$KEY_FILE" ] && [ "$(stat -c %a "$KEY_FILE")" != "600" ]; then
    chmod 600 "$KEY_FILE"
fi

if [ -z "$SAFESTEP_API_KEY" ] && [ -f "$KEY_FILE" ]; then
    SAFESTEP_API_KEY=$(tr -d '[:space:]' < "$KEY_FILE")
    echo "API key loaded from $KEY_FILE"
    echo "(If you see HTTP error 401, run: ./start_safestep.sh --reset-key)"
fi

if [ -z "$SAFESTEP_API_KEY" ]; then
    read -r -s -p "API key: " SAFESTEP_API_KEY
    echo
    read -r -p "Save the API key to $KEY_FILE for next time? [y/N]: " SAVE_KEY
    if [[ "$SAVE_KEY" =~ ^[Yy]$ ]]; then
        mkdir -p "$KEY_DIR"
        chmod 700 "$KEY_DIR"
        ( umask 077; printf '%s\n' "$SAFESTEP_API_KEY" > "$KEY_FILE" )
        chmod 600 "$KEY_FILE"
        echo "Saved to $KEY_FILE"
    fi
fi
export SAFESTEP_API_KEY

CODE=$(curl -s -o /dev/null -m 3 -w "%{http_code}" "$SAFESTEP_URL")
if [ "$CODE" != "405" ]; then
    echo "Cannot reach the dashboard API (HTTP code: $CODE)."
    echo "Check the IP address, the Wi-Fi, Apache and the Windows firewall."
    exit 1
fi

echo "$HOST_IP" > "$IP_FILE"

# --- Alarm player (runs on the Pi host, outside Docker) ---
mkdir -p "$PROJECT_DIR/alarm"
PLAYER_PID=""
if pgrep -f "python3.* alarm_player.py" > /dev/null; then
    echo "Alarm player is already running. Using it."
else
    python3 -u "$PROJECT_DIR/alarm_player.py" > "$ALARM_LOG" 2>&1 &
    PLAYER_PID=$!
    sleep 1
    if kill -0 "$PLAYER_PID" 2>/dev/null; then
        echo "Alarm player started (log: $ALARM_LOG)."
    else
        echo "WARNING: the alarm player did not start. Detection will run without sound."
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

echo "Dashboard API reachable. Starting detection..."

docker run --rm -it \
  --device /dev/video0:/dev/video0 \
  -e SAFESTEP_URL -e SAFESTEP_DEVICE -e SAFESTEP_API_KEY \
  -v "$PROJECT_DIR":/workspace \
  -w /workspace \
  ultralytics/ultralytics:latest-arm64 \
  python safestep_run.py