from ultralytics import YOLO

model = YOLO("/workspace/yolo26n_ncnn_model")

LINE_Y = 240
MARGIN = 20

previous_side = {}

results = model.track(
    source=0,
    stream=True,
    classes=[0],
    persist=True,
    verbose=False
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
                print(
                    f"ID:{track_id} LINE CROSS "
                    f"{old_side} -> {side} "
                    f"cy:{cy:.1f}"
                )

        previous_side[track_id] = side
