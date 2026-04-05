import cv2

video_path = "outputs/videos/state_activity_output.avi"
cap = cv2.VideoCapture(video_path)

print("opened =", cap.isOpened())

ret, frame = cap.read()
print("first frame read =", ret)

if ret:
    print("frame shape =", frame.shape)

cap.release()