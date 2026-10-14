import threading

from ultralytics import YOLO

from safestep_client import send_event

MODEL_PATH = "/workspace/yolo26n_ncnn_model"

# Provisional values for testing. Real values depend on the camera setup.
LINE_Y = 240
MARGIN = 20

# Provisional: the direction treated as normal. The opposite is reported as reverse.
NORMAL_DIRECTION = "DOWN"


def send_async(track_id, direction, is_reverse):
    """Send in a background thread so detection never waits for the network."""

    def worker():
        ok = send_event(track_id, direction, is_reverse)
        print(f"  -> sent to dashboard: {ok}")

    threading.Thread(target=worker, daemon=True).start()


def main():
    model = YOLO(MODEL_PATH)
    previous_side = {}

    print(f"Start. LINE_Y={LINE_Y} MARGIN={MARGIN} NORMAL_DIRECTION={NORMAL_DIRECTION}")
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

            previous_side[track_id] = side


if __name__ == "__main__":
    main()