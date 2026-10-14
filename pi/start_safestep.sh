#!/bin/bash
# Start SafeStep detection in Docker.
# Asks for the dashboard host IP and the API key, checks the connection, then runs.

PROJECT_DIR="$HOME/SafeStepAI"
IP_FILE="$PROJECT_DIR/.last_host_ip"

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

if [ -z "$SAFESTEP_API_KEY" ]; then
    read -r -s -p "API key: " SAFESTEP_API_KEY
    echo
    export SAFESTEP_API_KEY
fi

CODE=$(curl -s -o /dev/null -m 3 -w "%{http_code}" "$SAFESTEP_URL")
if [ "$CODE" != "405" ]; then
    echo "Cannot reach the dashboard API (HTTP code: $CODE)."
    echo "Check the IP address, the Wi-Fi, Apache and the Windows firewall."
    exit 1
fi

echo "$HOST_IP" > "$IP_FILE"
echo "Dashboard API reachable. Starting detection..."

docker run --rm -it \
  --device /dev/video0:/dev/video0 \
  -e SAFESTEP_URL -e SAFESTEP_DEVICE -e SAFESTEP_API_KEY \
  -v "$PROJECT_DIR":/workspace \
  -w /workspace \
  ultralytics/ultralytics:latest-arm64 \
  python safestep_run.py

