import os
import threading
import time
from datetime import datetime, time as dtime, timedelta

from ultralytics import YOLO

from safestep_client import send_event

MODEL_PATH = "/workspace/yolo26n_ncnn_model"

# Provisional values for testing. Real values depend on the camera setup.
LINE_Y = 240
MARGIN = 20

# Provisional: the direction treated as normal. The opposite is reported as reverse.
NORMAL_DIRECTION = "DOWN"

# Alarm settings
REVERSE_WINDOW_SEC = 30  # count reverse crossings seen in the last N seconds
REVERSE_THRESHOLD = 1    # every reverse crossing sounds the alarm
ALARM_COOLDOWN_SEC = 0   # no cooldown here; alarm_player.py prevents overlapping
ALARM_TRIGGER_PATH = "trigger"

# Active time window (device local time). Detection runs only in [START, END).
ACTIVE_START = dtime(12, 45)
ACTIVE_END = dtime(13, 15)


def is_active(now=None):
    """True if the current local time is inside the active window."""
    t = (now or datetime.now()).time()
    return ACTIVE_START <= t < ACTIVE_END


def wait_until_active():
    """Sleep (without using camera/CPU) until the next active window starts."""
    announced = False
    while not is_active():
        now = datetime.now()
        start = datetime.combine(now.date(), ACTIVE_START)
        if now >= start:
            start += timedelta(days=1)
        wait = (start - now).total_seconds()
        if not announced:
            print(f"Outside active window. Next start: {start:%Y-%m-%d %H:%M}")
            announced = True
        # Sleep in short chunks so clock changes / NTP sync are handled.
        time.sleep(max(1, min(wait, 30)))


def send_async(track_id, direction, is_reverse):
    """Send in a background thread so detection never waits for the network."""

    def worker():
        ok = send_event(track_id, direction, is_reverse)
        print(f"  -> sent to dashboard: {ok}")

    threading.Thread(target=worker, daemon=True).start()


def fire_alarm():
    """Update the trigger file. The player on the Pi host plays the sound."""
    try:
        with open(ALARM_TRIGGER_PATH, "w") as f:
            f.write(str(time.time()))
        os.chmod(ALARM_TRIGGER_PATH, 0o666)
        return True
    except OSError as e:
        print(f"  -> alarm trigger failed ({type(e).__name__})")
        return False
        
def count_recent_reverse(reverse_times, now):
    """Drop old entries and return how many different people crossed in reverse recently."""
    old_ids = [t for t, ts in reverse_times.items() if now - ts > REVERSE_WINDOW_SEC]
    for tid in old_ids:
        del reverse_times[tid]
    return len(reverse_times)


def run_session(model):
    """Run detection until the active window ends, then release the camera."""
    previous_side = {}
    reverse_times = {}  # track_id -> time of the latest reverse crossing
    last_alarm = None

    # Force a fresh tracker for each session (avoids stale IDs from the previous day).
    model.predictor = None

    print(f"Session start. LINE_Y={LINE_Y} MARGIN={MARGIN} NORMAL_DIRECTION={NORMAL_DIRECTION}")
    print(
        f"Active window: {ACTIVE_START:%H:%M}-{ACTIVE_END:%H:%M} | "
        f"Alarm: {REVERSE_THRESHOLD} people within {REVERSE_WINDOW_SEC}s, "
        f"cooldown {ALARM_COOLDOWN_SEC}s"
    )

    results = model.track(
        source=0,
        stream=True,
        classes=[0],
        persist=True,
        verbose=False,
    )

    try:
        for r in results:
            # Check the window on every frame, before anything else.
            if not is_active():
                print("Active window ended. Stopping detection.")
                break

            if r.boxes.id is None:
                continue

            ids = r.boxes.id.int().cpu().tolist()
            boxes = r.boxes.xyxy.cpu().tolist()

            for track_id, box in zip(ids, boxes):
                x1, y1, x2, y2 = box
                cy = (y1 + y2) / 2

                if cy < LINE_Y - MARGIN:
                    side = "UP"
                elif cy > LINE_Y + MARGIN:
                    side = "DOWN"
                else:
                    continue

                if track_id in previous_side:
                    old_side = previous_side[track_id]
                    if old_side != side:
                        direction = side
                        is_reverse = direction != NORMAL_DIRECTION
                        label = "REVERSE" if is_reverse else "normal"
                        print(
                            f"ID:{track_id} LINE CROSS {old_side} -> {side} "
                            f"cy:{cy:.1f} [{label}]"
                        )
                        send_async(track_id, direction, is_reverse)

                        if is_reverse:
                            now = time.monotonic()
                            reverse_times[track_id] = now
                            count = count_recent_reverse(reverse_times, now)
                            print(
                                f"  -> reverse count in last {REVERSE_WINDOW_SEC}s: "
                                f"{count}/{REVERSE_THRESHOLD}"
                            )
                            if count >= REVERSE_THRESHOLD:
                                cooled_down = (
                                    last_alarm is None
                                    or now - last_alarm >= ALARM_COOLDOWN_SEC
                                )
                                if cooled_down:
                                    print("  -> ALARM")
                                    if fire_alarm():
                                        last_alarm = now
                                        reverse_times.clear()
                                else:
                                    print("  -> threshold reached, but cooling down")

                previous_side[track_id] = side
    finally:
        results.close()  # closes the generator -> releases the camera


def main():
    model = YOLO(MODEL_PATH)
    print(f"Scheduler started. Active window: {ACTIVE_START:%H:%M}-{ACTIVE_END:%H:%M}")
    print("Press Ctrl+C to stop.")

    while True:
        wait_until_active()
        run_session(model)


if __name__ == "__main__":
    main()
