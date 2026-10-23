import os
import threading
import time

from ultralytics import YOLO

from safestep_client import send_event

MODEL_PATH = "/workspace/yolo26n_ncnn_model"

# Provisional values for testing. Real values depend on the camera setup.
LINE_Y = 240
MARGIN = 20

# Provisional: the direction treated as normal. The opposite is reported as reverse.
NORMAL_DIRECTION = "DOWN"

# Alarm settings
REVERSE_WINDOW_SEC = 30    # count reverse crossings seen in the last N seconds
REVERSE_THRESHOLD = 1      # every reverse crossing sounds the alarm
ALARM_COOLDOWN_SEC = 0    # no cooldown here; alarm_player.py prevents overlapping
ALARM_TRIGGER_PATH = "trigger"


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


def main():
    model = YOLO(MODEL_PATH)
    previous_side = {}
    reverse_times = {}   # track_id -> time of the latest reverse crossing
    last_alarm = None

    print(f"Start. LINE_Y={LINE_Y} MARGIN={MARGIN} NORMAL_DIRECTION={NORMAL_DIRECTION}")
    print(
        f"Alarm: {REVERSE_THRESHOLD} people within {REVERSE_WINDOW_SEC}s, "
        f"cooldown {ALARM_COOLDOWN_SEC}s"
    )
    print("Press Ctrl+C to stop.")

    results = model.track(
        source=0,
        stream=True,
        classes=[0],
        persist=True,
        verbose=False,
    )

    for r in results:
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


if __name__ == "__main__":
    main()