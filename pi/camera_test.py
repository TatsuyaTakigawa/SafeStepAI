import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera could not be opened.")
    exit()

ret, frame = cap.read()

print("Capture successful:", ret)

if ret:
    print("Image size:", frame.shape)

    cv2.imwrite("camera_test.jpg", frame)
    print("Saved: camera_test.jpg")

cap.release()