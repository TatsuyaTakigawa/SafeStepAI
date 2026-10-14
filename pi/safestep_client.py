import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

URL = os.environ.get("SAFESTEP_URL", "")
API_KEY = os.environ.get("SAFESTEP_API_KEY", "")
DEVICE_NAME = os.environ.get("SAFESTEP_DEVICE", "pi-01")
UTC_OFFSET_HOURS = int(os.environ.get("SAFESTEP_UTC_OFFSET", "9"))
TIMEOUT_SEC = 3

LOCAL_TZ = timezone(timedelta(hours=UTC_OFFSET_HOURS))


def send_event(track_id, direction, is_reverse):
    """Send one event. Returns True on success, False on failure (never raises)."""
    if not URL or not API_KEY:
        print("SafeStep: SAFESTEP_URL / SAFESTEP_API_KEY is not set")
        return False

    payload = {
        "device_name": DEVICE_NAME,
        "occurred_at": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "track_id": int(track_id),
        "direction": direction,
        "is_reverse": 1 if is_reverse else 0,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
            return res.status == 201
    except urllib.error.HTTPError as e:
        print(f"SafeStep: HTTP error {e.code}")
    except Exception as e:
        print(f"SafeStep: send failed ({type(e).__name__})")
    return False


if __name__ == "__main__":
    ok = send_event(track_id=1, direction="UP", is_reverse=False)
    print("sent:", ok)