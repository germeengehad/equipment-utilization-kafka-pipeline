# import os
# import cv2
# import json
# import numpy as np
# from ultralytics import YOLO

# # =========================
# # Paths / Config
# # =========================
# INPUT_VIDEO = os.getenv("INPUT_VIDEO", "state_activity_output.mp4")
# OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
# YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
# KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
# KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "equipment_tracking_clean_v2")
# SHOW_WINDOW = os.getenv("SHOW_WINDOW", "false").lower() == "true"

# VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
# LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")

# os.makedirs(VIDEOS_DIR, exist_ok=True)
# os.makedirs(LOGS_DIR, exist_ok=True)

# OUTPUT_VIDEO = os.path.join(VIDEOS_DIR, "state_activity_output.mp4")
# OUTPUT_JSONL = os.path.join(LOGS_DIR, "tracking_payloads.jsonl")

# # =========================
# # Tunable thresholds
# # =========================
# MIN_BOX_AREA = 15000
# MIN_CONFIDENCE = 0.25

# # State thresholds
# EXCAVATOR_MOTION_THRESHOLD = 0.15
# TRUCK_MOTION_THRESHOLD = 0.75
# DEFAULT_MOTION_THRESHOLD = 0.40

# INACTIVE_MIN_FRAMES = 4
# EXCAVATOR_LIKE_AREA = 30000

# # Activity thresholds
# DIGGING_ARM_THRESHOLD = 0.10
# LOADING_MOTION_THRESHOLD = 0.25

# # Dumping heuristic
# DUMPING_ARM_THRESHOLD = 0.25
# DUMPING_FULL_MOTION_MAX = 0.35

# # Truck loading activity should be harder to trigger
# TRUCK_LOADING_THRESHOLD = 0.90

# # =========================
# # Re-ID thresholds (tightened)
# # =========================
# REID_MAX_CENTER_DISTANCE = 85.0
# REID_MIN_IOU = 0.25
# REID_AREA_RATIO_MIN = 0.70
# REID_AREA_RATIO_MAX = 1.40
# REID_MAX_MISSING_FRAMES = 12
# REID_MAX_X_SHIFT = 70.0
# REID_MAX_Y_SHIFT = 60.0

# # For this specific demo clip:
# # effectively one excavator + one main truck
# MAX_MACHINE_IDS_PER_TYPE = {
#     "excavator": 1,
#     "truck": 1,
#     "other": 1
# }


# def get_class_name(model_names, cls_id: int) -> str:
#     if isinstance(model_names, dict):
#         return model_names.get(cls_id, "unknown")
#     if 0 <= cls_id < len(model_names):
#         return model_names[cls_id]
#     return "unknown"


# def normalize_equipment_label(class_name, is_excavator_like):
#     class_name_lower = class_name.lower()
#     if is_excavator_like:
#         return "excavator"
#     if "truck" in class_name_lower:
#         return "dump_truck"
#     return "unknown_equipment"


# def compute_optical_flow_motion(prev_img, curr_img):
#     flow = cv2.calcOpticalFlowFarneback(
#         prev_img, curr_img, None, 0.5, 3, 15, 3, 5, 1.2, 0
#     )
#     mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
#     return float(np.mean(mag))


# def compute_motion_scores(prev_gray_frame, curr_gray_frame, x1, y1, x2, y2):
#     full_motion = 999.0
#     arm_motion = 0.0
#     truck_base_motion = 999.0

#     prev_roi = prev_gray_frame[y1:y2, x1:x2]
#     curr_roi = curr_gray_frame[y1:y2, x1:x2]

#     if prev_roi.size == 0 or curr_roi.size == 0:
#         return full_motion, arm_motion, truck_base_motion
#     if prev_roi.shape != curr_roi.shape:
#         return full_motion, arm_motion, truck_base_motion

#     full_motion = compute_optical_flow_motion(prev_roi, curr_roi)

#     roi_h, roi_w = curr_roi.shape[:2]

#     # Excavator arm region (top-right of ROI)
#     rx1 = int(roi_w * 0.45)
#     rx2 = roi_w
#     ry1 = 0
#     ry2 = int(roi_h * 0.65)
#     prev_arm = prev_roi[ry1:ry2, rx1:rx2]
#     curr_arm = curr_roi[ry1:ry2, rx1:rx2]
#     if prev_arm.size > 0 and curr_arm.size > 0 and prev_arm.shape == curr_arm.shape:
#         arm_motion = compute_optical_flow_motion(prev_arm, curr_arm)

#     # Truck base / lower middle region
#     bx1 = int(roi_w * 0.20)
#     bx2 = int(roi_w * 0.80)
#     by1 = int(roi_h * 0.55)
#     by2 = roi_h
#     prev_base = prev_roi[by1:by2, bx1:bx2]
#     curr_base = curr_roi[by1:by2, bx1:bx2]
#     if prev_base.size > 0 and curr_base.size > 0 and prev_base.shape == curr_base.shape:
#         truck_base_motion = compute_optical_flow_motion(prev_base, curr_base)

#     return full_motion, arm_motion, truck_base_motion


# def infer_activity(equipment_label, state, full_motion, arm_motion, truck_base_motion):
#     if state == "INACTIVE":
#         return "WAITING"

#     if equipment_label == "dump_truck":
#         if truck_base_motion >= TRUCK_LOADING_THRESHOLD:
#             return "LOADING"
#         return "WAITING"

#     if equipment_label == "excavator":
#         if arm_motion >= DUMPING_ARM_THRESHOLD and full_motion <= DUMPING_FULL_MOTION_MAX:
#             return "DUMPING"
#         elif arm_motion >= DIGGING_ARM_THRESHOLD:
#             return "DIGGING"
#         elif full_motion >= LOADING_MOTION_THRESHOLD:
#             return "LOADING"
#         else:
#             return "SWINGING"

#     return "ACTIVE_WORK"


# def compute_iou(box_a, box_b):
#     ax1, ay1, ax2, ay2 = box_a
#     bx1, by1, bx2, by2 = box_b

#     inter_x1 = max(ax1, bx1)
#     inter_y1 = max(ay1, by1)
#     inter_x2 = min(ax2, bx2)
#     inter_y2 = min(ay2, by2)

#     inter_w = max(0, inter_x2 - inter_x1)
#     inter_h = max(0, inter_y2 - inter_y1)
#     inter_area = inter_w * inter_h

#     area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
#     area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
#     union = area_a + area_b - inter_area

#     if union <= 0:
#         return 0.0

#     return inter_area / union


# def get_center_and_area(x1, y1, x2, y2):
#     cx = (x1 + x2) / 2.0
#     cy = (y1 + y2) / 2.0
#     area = max(0, x2 - x1) * max(0, y2 - y1)
#     return cx, cy, area


# def get_machine_type(equipment_label):
#     if equipment_label == "dump_truck":
#         return "truck"
#     if equipment_label == "excavator":
#         return "excavator"
#     return "other"


# def get_zone(cx, frame_mid_x):
#     if cx < frame_mid_x:
#         return "left"
#     return "right"


# def assign_stable_machine_id(
#     frame_index,
#     equipment_label,
#     x1,
#     y1,
#     x2,
#     y2,
#     machine_memory,
#     track_to_machine,
#     track_id,
#     machine_id_counters,
#     frame_mid_x,
# ):
#     machine_type = get_machine_type(equipment_label)
#     current_box = (x1, y1, x2, y2)
#     current_cx, current_cy, current_area = get_center_and_area(x1, y1, x2, y2)
#     current_zone = get_zone(current_cx, frame_mid_x)

#     if track_id in track_to_machine:
#         machine_id = track_to_machine[track_id]
#         if machine_id in machine_memory:
#             machine_memory[machine_id]["last_box"] = current_box
#             machine_memory[machine_id]["last_center"] = (current_cx, current_cy)
#             machine_memory[machine_id]["last_area"] = current_area
#             machine_memory[machine_id]["last_seen_frame"] = frame_index
#             machine_memory[machine_id]["zone"] = current_zone
#             return machine_id

#     best_machine_id = None
#     best_score = -1.0

#     for machine_id, info in machine_memory.items():
#         if info["machine_type"] != machine_type:
#             continue

#         frames_missing = frame_index - info["last_seen_frame"]
#         if frames_missing > REID_MAX_MISSING_FRAMES:
#             continue

#         prev_box = info["last_box"]
#         prev_cx, prev_cy = info["last_center"]
#         prev_area = info["last_area"]
#         prev_zone = info.get("zone", "unknown")

#         if prev_zone != current_zone:
#             continue

#         center_distance = ((current_cx - prev_cx) ** 2 + (current_cy - prev_cy) ** 2) ** 0.5
#         x_shift = abs(current_cx - prev_cx)
#         y_shift = abs(current_cy - prev_cy)
#         iou = compute_iou(current_box, prev_box)

#         if prev_area <= 0:
#             continue

#         area_ratio = current_area / prev_area if prev_area > 0 else 999.0

#         if center_distance > REID_MAX_CENTER_DISTANCE:
#             continue
#         if x_shift > REID_MAX_X_SHIFT or y_shift > REID_MAX_Y_SHIFT:
#             continue
#         if iou < REID_MIN_IOU:
#             continue
#         if not (REID_AREA_RATIO_MIN <= area_ratio <= REID_AREA_RATIO_MAX):
#             continue

#         score = (
#             iou
#             + max(0.0, 1.0 - center_distance / REID_MAX_CENTER_DISTANCE)
#             + max(0.0, 1.0 - x_shift / REID_MAX_X_SHIFT) * 0.5
#         )

#         if score > best_score:
#             best_score = score
#             best_machine_id = machine_id

#     if best_machine_id is not None:
#         track_to_machine[track_id] = best_machine_id
#         machine_memory[best_machine_id]["last_box"] = current_box
#         machine_memory[best_machine_id]["last_center"] = (current_cx, current_cy)
#         machine_memory[best_machine_id]["last_area"] = current_area
#         machine_memory[best_machine_id]["last_seen_frame"] = frame_index
#         machine_memory[best_machine_id]["zone"] = current_zone
#         return best_machine_id

#     existing_same_type = [
#         (mid, info) for mid, info in machine_memory.items()
#         if info["machine_type"] == machine_type
#     ]

#     if len(existing_same_type) >= MAX_MACHINE_IDS_PER_TYPE[machine_type]:
#         fallback_mid = None
#         fallback_dist = 1e9

#         for mid, info in existing_same_type:
#             prev_zone = info.get("zone", "unknown")
#             if prev_zone != current_zone:
#                 continue
#             prev_cx, prev_cy = info["last_center"]
#             dist = ((current_cx - prev_cx) ** 2 + (current_cy - prev_cy) ** 2) ** 0.5
#             if dist < fallback_dist:
#                 fallback_dist = dist
#                 fallback_mid = mid

#         if fallback_mid is None:
#             for mid, info in existing_same_type:
#                 prev_cx, prev_cy = info["last_center"]
#                 dist = ((current_cx - prev_cx) ** 2 + (current_cy - prev_cy) ** 2) ** 0.5
#                 if dist < fallback_dist:
#                     fallback_dist = dist
#                     fallback_mid = mid

#         if fallback_mid is not None:
#             track_to_machine[track_id] = fallback_mid
#             machine_memory[fallback_mid]["last_box"] = current_box
#             machine_memory[fallback_mid]["last_center"] = (current_cx, current_cy)
#             machine_memory[fallback_mid]["last_area"] = current_area
#             machine_memory[fallback_mid]["last_seen_frame"] = frame_index
#             machine_memory[fallback_mid]["zone"] = current_zone
#             return fallback_mid

#     machine_id_counters[machine_type] += 1
#     new_machine_id = f"{machine_type}_{machine_id_counters[machine_type]}"
#     machine_memory[new_machine_id] = {
#         "machine_type": machine_type,
#         "last_box": current_box,
#         "last_center": (current_cx, current_cy),
#         "last_area": current_area,
#         "last_seen_frame": frame_index,
#         "zone": current_zone,
#     }
#     track_to_machine[track_id] = new_machine_id
#     return new_machine_id


# def main():
#     # =========================
#     # Model
#     # =========================
#     model = YOLO(YOLO_MODEL_PATH)

#     # =========================
#     # Video setup
#     # =========================
#     cap = cv2.VideoCapture(INPUT_VIDEO)

#     if not cap.isOpened():
#         raise ValueError(f"Could not open video: {INPUT_VIDEO}")

#     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     fps = cap.get(cv2.CAP_PROP_FPS)

#     if fps <= 0:
#         fps = 25.0

#     frame_time = 1.0 / fps
#     frame_mid_x = width / 2.0

#     # mp4v is safer across environments than avc1
#     fourcc = cv2.VideoWriter_fourcc(*"mp4v")
#     writer = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (width, height))

#     jsonl_file = open(OUTPUT_JSONL, "w", encoding="utf-8")
#     frame_index = 0

#     # =========================
#     # Tracking / Motion memory
#     # =========================
#     prev_gray = None

#     # keyed by STABLE machine_id
#     track_memory = {}

#     # Re-ID memory
#     machine_memory = {}
#     track_to_machine = {}
#     machine_id_counters = {
#         "excavator": 0,
#         "truck": 0,
#         "other": 0,
#     }

#     # =========================
#     # Main loop
#     # =========================
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         current_timestamp_sec = frame_index / fps
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         annotated_frame = frame.copy()

#         results = model.track(
#             frame,
#             persist=True,
#             tracker="bytetrack.yaml",
#             verbose=False
#         )

#         for result in results:
#             boxes = result.boxes
#             if boxes is None or len(boxes) == 0:
#                 continue

#             for box in boxes:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
#                 x1 = max(0, x1)
#                 y1 = max(0, y1)
#                 x2 = min(width - 1, x2)
#                 y2 = min(height - 1, y2)

#                 w = x2 - x1
#                 h = y2 - y1
#                 area = w * h

#                 if area < MIN_BOX_AREA:
#                     continue

#                 conf = float(box.conf[0].item()) if box.conf is not None else 0.0
#                 if conf < MIN_CONFIDENCE:
#                     continue

#                 cls_id = int(box.cls[0].item()) if box.cls is not None else -1
#                 class_name_raw = get_class_name(model.names, cls_id)

#                 if box.id is None:
#                     continue

#                 track_id = int(box.id[0].item())
#                 is_excavator_like = area > EXCAVATOR_LIKE_AREA
#                 equipment_label = normalize_equipment_label(class_name_raw, is_excavator_like)

#                 machine_id = assign_stable_machine_id(
#                     frame_index=frame_index,
#                     equipment_label=equipment_label,
#                     x1=x1,
#                     y1=y1,
#                     x2=x2,
#                     y2=y2,
#                     machine_memory=machine_memory,
#                     track_to_machine=track_to_machine,
#                     track_id=track_id,
#                     machine_id_counters=machine_id_counters,
#                     frame_mid_x=frame_mid_x,
#                 )

#                 if machine_id not in track_memory:
#                     track_memory[machine_id] = {
#                         "inactive_frames": 0,
#                         "state": "ACTIVE",
#                         "activity": "UNKNOWN",
#                         "idle_time": 0.0,
#                         "active_time": 0.0,
#                         "current_idle_session": 0.0,
#                         "utilization_percent": 0.0,
#                     }

#                 full_motion = 999.0
#                 arm_motion = 0.0
#                 truck_base_motion = 999.0

#                 if prev_gray is not None:
#                     full_motion, arm_motion, truck_base_motion = compute_motion_scores(
#                         prev_gray, gray, x1, y1, x2, y2
#                     )

#                 if equipment_label == "dump_truck":
#                     effective_motion = truck_base_motion
#                     current_threshold = TRUCK_MOTION_THRESHOLD
#                 elif equipment_label == "excavator":
#                     effective_motion = max(full_motion, arm_motion * 3.5)
#                     current_threshold = EXCAVATOR_MOTION_THRESHOLD
#                 else:
#                     effective_motion = full_motion
#                     current_threshold = DEFAULT_MOTION_THRESHOLD

#                 if effective_motion < current_threshold:
#                     track_memory[machine_id]["inactive_frames"] += 1
#                 else:
#                     track_memory[machine_id]["inactive_frames"] = 0

#                 if track_memory[machine_id]["inactive_frames"] >= INACTIVE_MIN_FRAMES:
#                     track_memory[machine_id]["state"] = "INACTIVE"
#                 else:
#                     track_memory[machine_id]["state"] = "ACTIVE"

#                 state = track_memory[machine_id]["state"]

#                 activity = infer_activity(
#                     equipment_label=equipment_label,
#                     state=state,
#                     full_motion=full_motion,
#                     arm_motion=arm_motion,
#                     truck_base_motion=truck_base_motion
#                 )
#                 track_memory[machine_id]["activity"] = activity

#                 if state == "INACTIVE":
#                     track_memory[machine_id]["idle_time"] += frame_time
#                     track_memory[machine_id]["current_idle_session"] += frame_time
#                     color = (0, 0, 255)
#                 else:
#                     track_memory[machine_id]["active_time"] += frame_time
#                     track_memory[machine_id]["current_idle_session"] = 0.0
#                     color = (0, 255, 0)

#                 idle_time = track_memory[machine_id]["idle_time"]
#                 active_time = track_memory[machine_id]["active_time"]
#                 current_idle_session = track_memory[machine_id]["current_idle_session"]

#                 total_tracked_time = idle_time + active_time
#                 utilization_percent = (
#                     (active_time / total_tracked_time) * 100.0
#                     if total_tracked_time > 0
#                     else 0.0
#                 )
#                 track_memory[machine_id]["utilization_percent"] = utilization_percent

#                 payload = {
#                     "frame_index": frame_index,
#                     "timestamp_sec": round(current_timestamp_sec, 2),
#                     "track_id": track_id,
#                     "machine_id": machine_id,
#                     "equipment_class_raw": class_name_raw,
#                     "equipment_class": equipment_label,
#                     "bbox": {
#                         "x1": x1,
#                         "y1": y1,
#                         "x2": x2,
#                         "y2": y2
#                     },
#                     "state": state,
#                     "activity": activity,
#                     "current_idle_session_sec": round(current_idle_session, 2),
#                     "total_idle_sec": round(idle_time, 2),
#                     "total_active_sec": round(active_time, 2),
#                     "utilization_percent": round(utilization_percent, 2),
#                     "full_motion": round(full_motion, 4),
#                     "arm_motion": round(arm_motion, 4),
#                     "truck_base_motion": round(truck_base_motion, 4)
#                 }

#                 jsonl_file.write(json.dumps(payload) + "\n")
#                 jsonl_file.flush()

#                 label = (
#                     f"MID:{machine_id} TID:{track_id} {equipment_label} {state}/{activity} "
#                     f"Idle:{idle_time:.1f}s Sess:{current_idle_session:.1f}s "
#                     f"Util:{utilization_percent:.1f}%"
#                 )

#                 cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
#                 cv2.putText(
#                     annotated_frame,
#                     label,
#                     (x1, max(y1 - 10, 20)),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     0.38,
#                     color,
#                     2
#                 )

#         writer.write(annotated_frame)

#         if SHOW_WINDOW:
#             cv2.imshow("Tracking + State + Activity", annotated_frame)

#         prev_gray = gray.copy()
#         frame_index += 1

#         if SHOW_WINDOW and cv2.waitKey(1) & 0xFF == ord("q"):
#             break

#     cap.release()
#     writer.release()
#     jsonl_file.close()

#     if SHOW_WINDOW:
#         cv2.destroyAllWindows()

#     print(f"Saved output video to: {OUTPUT_VIDEO}")
#     print(f"Saved JSONL payloads to: {OUTPUT_JSONL}")
#     print(f"Kafka bootstrap servers config: {KAFKA_BOOTSTRAP_SERVERS}")
#     print(f"Kafka topic config: {KAFKA_TOPIC}")


# if __name__ == "__main__":
#     main()

import os
import cv2
import json
import numpy as np
from ultralytics import YOLO
import subprocess

# =========================
# Paths / Config
# =========================
INPUT_VIDEO = os.getenv("INPUT_VIDEO", "state_activity_output.mp4")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "equipment_tracking_clean_v2")
SHOW_WINDOW = os.getenv("SHOW_WINDOW", "false").lower() == "true"

VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

OUTPUT_VIDEO_RAW = os.path.join(VIDEOS_DIR, "state_activity_output.mp4")
OUTPUT_VIDEO_H264 = os.path.join(VIDEOS_DIR, "state_activity_output_h264.mp4")
OUTPUT_JSONL = os.path.join(LOGS_DIR, "tracking_payloads.jsonl")

# =========================
# Tunable thresholds
# =========================
MIN_BOX_AREA = 15000
MIN_CONFIDENCE = 0.25

# State thresholds
EXCAVATOR_MOTION_THRESHOLD = 0.15
TRUCK_MOTION_THRESHOLD = 0.75
DEFAULT_MOTION_THRESHOLD = 0.40

INACTIVE_MIN_FRAMES = 4
EXCAVATOR_LIKE_AREA = 30000

# Activity thresholds
DIGGING_ARM_THRESHOLD = 0.10
LOADING_MOTION_THRESHOLD = 0.25

# Dumping heuristic
DUMPING_ARM_THRESHOLD = 0.25
DUMPING_FULL_MOTION_MAX = 0.35

# Truck loading activity should be harder to trigger
TRUCK_LOADING_THRESHOLD = 0.90

# =========================
# Re-ID thresholds (tightened)
# =========================
REID_MAX_CENTER_DISTANCE = 85.0
REID_MIN_IOU = 0.25
REID_AREA_RATIO_MIN = 0.70
REID_AREA_RATIO_MAX = 1.40
REID_MAX_MISSING_FRAMES = 12
REID_MAX_X_SHIFT = 70.0
REID_MAX_Y_SHIFT = 60.0

# For this specific demo clip:
# effectively one excavator + one main truck
MAX_MACHINE_IDS_PER_TYPE = {
    "excavator": 1,
    "truck": 1,
    "other": 1
}


def get_class_name(model_names, cls_id: int) -> str:
    if isinstance(model_names, dict):
        return model_names.get(cls_id, "unknown")
    if 0 <= cls_id < len(model_names):
        return model_names[cls_id]
    return "unknown"


def normalize_equipment_label(class_name, is_excavator_like):
    class_name_lower = class_name.lower()

    # Keep truck labels first
    if "truck" in class_name_lower:
        return "dump_truck"

    # Only then fallback to excavator-like by size
    if is_excavator_like:
        return "excavator"

    return "unknown_equipment"


def compute_optical_flow_motion(prev_img, curr_img):
    flow = cv2.calcOpticalFlowFarneback(
        prev_img, curr_img, None, 0.5, 3, 15, 3, 5, 1.2, 0
    )
    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    return float(np.mean(mag))


def compute_motion_scores(prev_gray_frame, curr_gray_frame, x1, y1, x2, y2):
    full_motion = 999.0
    arm_motion = 0.0
    truck_base_motion = 999.0

    prev_roi = prev_gray_frame[y1:y2, x1:x2]
    curr_roi = curr_gray_frame[y1:y2, x1:x2]

    if prev_roi.size == 0 or curr_roi.size == 0:
        return full_motion, arm_motion, truck_base_motion
    if prev_roi.shape != curr_roi.shape:
        return full_motion, arm_motion, truck_base_motion

    full_motion = compute_optical_flow_motion(prev_roi, curr_roi)

    roi_h, roi_w = curr_roi.shape[:2]

    # Excavator arm region (top-right of ROI)
    rx1 = int(roi_w * 0.45)
    rx2 = roi_w
    ry1 = 0
    ry2 = int(roi_h * 0.65)
    prev_arm = prev_roi[ry1:ry2, rx1:rx2]
    curr_arm = curr_roi[ry1:ry2, rx1:rx2]
    if prev_arm.size > 0 and curr_arm.size > 0 and prev_arm.shape == curr_arm.shape:
        arm_motion = compute_optical_flow_motion(prev_arm, curr_arm)

    # Truck base / lower middle region
    bx1 = int(roi_w * 0.20)
    bx2 = int(roi_w * 0.80)
    by1 = int(roi_h * 0.55)
    by2 = roi_h
    prev_base = prev_roi[by1:by2, bx1:bx2]
    curr_base = curr_roi[by1:by2, bx1:bx2]
    if prev_base.size > 0 and curr_base.size > 0 and prev_base.shape == curr_base.shape:
        truck_base_motion = compute_optical_flow_motion(prev_base, curr_base)

    return full_motion, arm_motion, truck_base_motion


def infer_activity(equipment_label, state, full_motion, arm_motion, truck_base_motion):
    if state == "INACTIVE":
        return "WAITING"

    if equipment_label == "dump_truck":
        if truck_base_motion >= TRUCK_LOADING_THRESHOLD:
            return "LOADING"
        return "WAITING"

    if equipment_label == "excavator":
        if arm_motion >= DUMPING_ARM_THRESHOLD and full_motion <= DUMPING_FULL_MOTION_MAX:
            return "DUMPING"
        elif arm_motion >= DIGGING_ARM_THRESHOLD:
            return "DIGGING"
        elif full_motion >= LOADING_MOTION_THRESHOLD:
            return "LOADING"
        else:
            return "SWINGING"

    return "ACTIVE_WORK"


def infer_motion_source(equipment_label, state, full_motion, arm_motion, truck_base_motion):
    if state == "INACTIVE":
        return "none"

    if equipment_label == "dump_truck":
        return "truck_base"

    if equipment_label == "excavator":
        if arm_motion >= DIGGING_ARM_THRESHOLD and full_motion <= DUMPING_FULL_MOTION_MAX:
            return "arm_only"
        return "full_body"

    return "full_body"


def build_submission_payload(
    frame_index,
    timestamp_sec,
    track_id,
    machine_id,
    class_name_raw,
    equipment_label,
    x1,
    y1,
    x2,
    y2,
    state,
    activity,
    current_idle_session,
    idle_time,
    active_time,
    utilization_percent,
    full_motion,
    arm_motion,
    truck_base_motion,
):
    total_tracked_time = idle_time + active_time

    motion_source = infer_motion_source(
        equipment_label=equipment_label,
        state=state,
        full_motion=full_motion,
        arm_motion=arm_motion,
        truck_base_motion=truck_base_motion,
    )

    return {
        "frame_id": frame_index,
        "timestamp": round(timestamp_sec, 2),
        "equipment_id": machine_id,
        "track_id": track_id,
        "equipment_class": equipment_label,
        "equipment_class_raw": class_name_raw,
        "bbox": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        },
        "utilization": {
            "current_state": state,
            "current_activity": activity,
            "motion_source": motion_source
        },
        "time_analytics": {
            "current_idle_session_seconds": round(current_idle_session, 2),
            "total_tracked_seconds": round(total_tracked_time, 2),
            "total_active_seconds": round(active_time, 2),
            "total_idle_seconds": round(idle_time, 2),
            "utilization_percent": round(utilization_percent, 2)
        },
        "motion_metrics": {
            "full_motion": round(full_motion, 4),
            "arm_motion": round(arm_motion, 4),
            "truck_base_motion": round(truck_base_motion, 4)
        }
    }


def compute_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter_area

    if union <= 0:
        return 0.0

    return inter_area / union


def get_center_and_area(x1, y1, x2, y2):
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    area = max(0, x2 - x1) * max(0, y2 - y1)
    return cx, cy, area


def get_machine_type(equipment_label):
    if equipment_label == "dump_truck":
        return "truck"
    if equipment_label == "excavator":
        return "excavator"
    return "other"


def get_zone(cx, frame_mid_x):
    if cx < frame_mid_x:
        return "left"
    return "right"


def assign_stable_machine_id(
    frame_index,
    equipment_label,
    x1,
    y1,
    x2,
    y2,
    machine_memory,
    track_to_machine,
    track_id,
    machine_id_counters,
    frame_mid_x,
):
    machine_type = get_machine_type(equipment_label)
    current_box = (x1, y1, x2, y2)
    current_cx, current_cy, current_area = get_center_and_area(x1, y1, x2, y2)
    current_zone = get_zone(current_cx, frame_mid_x)

    if track_id in track_to_machine:
        machine_id = track_to_machine[track_id]
        if machine_id in machine_memory:
            machine_memory[machine_id]["last_box"] = current_box
            machine_memory[machine_id]["last_center"] = (current_cx, current_cy)
            machine_memory[machine_id]["last_area"] = current_area
            machine_memory[machine_id]["last_seen_frame"] = frame_index
            machine_memory[machine_id]["zone"] = current_zone
            return machine_id

    best_machine_id = None
    best_score = -1.0

    for machine_id, info in machine_memory.items():
        if info["machine_type"] != machine_type:
            continue

        frames_missing = frame_index - info["last_seen_frame"]
        if frames_missing > REID_MAX_MISSING_FRAMES:
            continue

        prev_box = info["last_box"]
        prev_cx, prev_cy = info["last_center"]
        prev_area = info["last_area"]
        prev_zone = info.get("zone", "unknown")

        if prev_zone != current_zone:
            continue

        center_distance = ((current_cx - prev_cx) ** 2 + (current_cy - prev_cy) ** 2) ** 0.5
        x_shift = abs(current_cx - prev_cx)
        y_shift = abs(current_cy - prev_cy)
        iou = compute_iou(current_box, prev_box)

        if prev_area <= 0:
            continue

        area_ratio = current_area / prev_area if prev_area > 0 else 999.0

        if center_distance > REID_MAX_CENTER_DISTANCE:
            continue
        if x_shift > REID_MAX_X_SHIFT or y_shift > REID_MAX_Y_SHIFT:
            continue
        if iou < REID_MIN_IOU:
            continue
        if not (REID_AREA_RATIO_MIN <= area_ratio <= REID_AREA_RATIO_MAX):
            continue

        score = (
            iou
            + max(0.0, 1.0 - center_distance / REID_MAX_CENTER_DISTANCE)
            + max(0.0, 1.0 - x_shift / REID_MAX_X_SHIFT) * 0.5
        )

        if score > best_score:
            best_score = score
            best_machine_id = machine_id

    if best_machine_id is not None:
        track_to_machine[track_id] = best_machine_id
        machine_memory[best_machine_id]["last_box"] = current_box
        machine_memory[best_machine_id]["last_center"] = (current_cx, current_cy)
        machine_memory[best_machine_id]["last_area"] = current_area
        machine_memory[best_machine_id]["last_seen_frame"] = frame_index
        machine_memory[best_machine_id]["zone"] = current_zone
        return best_machine_id

    existing_same_type = [
        (mid, info) for mid, info in machine_memory.items()
        if info["machine_type"] == machine_type
    ]

    if len(existing_same_type) >= MAX_MACHINE_IDS_PER_TYPE[machine_type]:
        fallback_mid = None
        fallback_dist = 1e9

        for mid, info in existing_same_type:
            prev_zone = info.get("zone", "unknown")
            if prev_zone != current_zone:
                continue
            prev_cx, prev_cy = info["last_center"]
            dist = ((current_cx - prev_cx) ** 2 + (current_cy - prev_cy) ** 2) ** 0.5
            if dist < fallback_dist:
                fallback_dist = dist
                fallback_mid = mid

        if fallback_mid is None:
            for mid, info in existing_same_type:
                prev_cx, prev_cy = info["last_center"]
                dist = ((current_cx - prev_cx) ** 2 + (current_cy - prev_cy) ** 2) ** 0.5
                if dist < fallback_dist:
                    fallback_dist = dist
                    fallback_mid = mid

        if fallback_mid is not None:
            track_to_machine[track_id] = fallback_mid
            machine_memory[fallback_mid]["last_box"] = current_box
            machine_memory[fallback_mid]["last_center"] = (current_cx, current_cy)
            machine_memory[fallback_mid]["last_area"] = current_area
            machine_memory[fallback_mid]["last_seen_frame"] = frame_index
            machine_memory[fallback_mid]["zone"] = current_zone
            return fallback_mid

    machine_id_counters[machine_type] += 1
    new_machine_id = f"{machine_type}_{machine_id_counters[machine_type]}"
    machine_memory[new_machine_id] = {
        "machine_type": machine_type,
        "last_box": current_box,
        "last_center": (current_cx, current_cy),
        "last_area": current_area,
        "last_seen_frame": frame_index,
        "zone": current_zone,
    }
    track_to_machine[track_id] = new_machine_id
    return new_machine_id


def main():
    # =========================
    # Model
    # =========================
    model = YOLO(YOLO_MODEL_PATH)
    print("YOLO class names:", model.names)

    # =========================
    # Video setup
    # =========================
    cap = cv2.VideoCapture(INPUT_VIDEO)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {INPUT_VIDEO}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 25.0

    frame_time = 1.0 / fps
    frame_mid_x = width / 2.0

    # mp4v is safer across environments than avc1
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUTPUT_VIDEO_RAW, fourcc, fps, (width, height))

    jsonl_file = open(OUTPUT_JSONL, "w", encoding="utf-8")
    frame_index = 0

    # =========================
    # Tracking / Motion memory
    # =========================
    prev_gray = None

    # keyed by STABLE machine_id
    track_memory = {}

    # Re-ID memory
    machine_memory = {}
    track_to_machine = {}
    machine_id_counters = {
        "excavator": 0,
        "truck": 0,
        "other": 0,
    }

    # =========================
    # Main loop
    # =========================
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_timestamp_sec = frame_index / fps
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        annotated_frame = frame.copy()

        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(width - 1, x2)
                y2 = min(height - 1, y2)

                w = x2 - x1
                h = y2 - y1
                area = w * h

                if area < MIN_BOX_AREA:
                    continue

                conf = float(box.conf[0].item()) if box.conf is not None else 0.0
                if conf < MIN_CONFIDENCE:
                    continue

                cls_id = int(box.cls[0].item()) if box.cls is not None else -1
                class_name_raw = get_class_name(model.names, cls_id)

                if box.id is None:
                    continue

                track_id = int(box.id[0].item())
                is_excavator_like = area > EXCAVATOR_LIKE_AREA
                equipment_label = normalize_equipment_label(class_name_raw, is_excavator_like)

                machine_id = assign_stable_machine_id(
                    frame_index=frame_index,
                    equipment_label=equipment_label,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    machine_memory=machine_memory,
                    track_to_machine=track_to_machine,
                    track_id=track_id,
                    machine_id_counters=machine_id_counters,
                    frame_mid_x=frame_mid_x,
                )

                if machine_id not in track_memory:
                    track_memory[machine_id] = {
                        "inactive_frames": 0,
                        "state": "ACTIVE",
                        "activity": "UNKNOWN",
                        "idle_time": 0.0,
                        "active_time": 0.0,
                        "current_idle_session": 0.0,
                        "utilization_percent": 0.0,
                    }

                # Keep old safer fallback behavior
                full_motion = 999.0
                arm_motion = 0.0
                truck_base_motion = 999.0

                if prev_gray is not None:
                    full_motion, arm_motion, truck_base_motion = compute_motion_scores(
                        prev_gray, gray, x1, y1, x2, y2
                    )

                if equipment_label == "dump_truck":
                    effective_motion = truck_base_motion
                    current_threshold = TRUCK_MOTION_THRESHOLD
                elif equipment_label == "excavator":
                    effective_motion = max(full_motion, arm_motion * 3.5)
                    current_threshold = EXCAVATOR_MOTION_THRESHOLD
                else:
                    effective_motion = full_motion
                    current_threshold = DEFAULT_MOTION_THRESHOLD

                if effective_motion < current_threshold:
                    track_memory[machine_id]["inactive_frames"] += 1
                else:
                    track_memory[machine_id]["inactive_frames"] = 0

                if track_memory[machine_id]["inactive_frames"] >= INACTIVE_MIN_FRAMES:
                    track_memory[machine_id]["state"] = "INACTIVE"
                else:
                    track_memory[machine_id]["state"] = "ACTIVE"

                state = track_memory[machine_id]["state"]

                activity = infer_activity(
                    equipment_label=equipment_label,
                    state=state,
                    full_motion=full_motion,
                    arm_motion=arm_motion,
                    truck_base_motion=truck_base_motion
                )
                track_memory[machine_id]["activity"] = activity

                if state == "INACTIVE":
                    track_memory[machine_id]["idle_time"] += frame_time
                    track_memory[machine_id]["current_idle_session"] += frame_time
                    color = (0, 0, 255)
                else:
                    track_memory[machine_id]["active_time"] += frame_time
                    track_memory[machine_id]["current_idle_session"] = 0.0
                    color = (0, 255, 0)

                idle_time = track_memory[machine_id]["idle_time"]
                active_time = track_memory[machine_id]["active_time"]
                current_idle_session = track_memory[machine_id]["current_idle_session"]

                total_tracked_time = idle_time + active_time
                utilization_percent = (
                    (active_time / total_tracked_time) * 100.0
                    if total_tracked_time > 0
                    else 0.0
                )
                track_memory[machine_id]["utilization_percent"] = utilization_percent

                payload = build_submission_payload(
                    frame_index=frame_index,
                    timestamp_sec=current_timestamp_sec,
                    track_id=track_id,
                    machine_id=machine_id,
                    class_name_raw=class_name_raw,
                    equipment_label=equipment_label,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    state=state,
                    activity=activity,
                    current_idle_session=current_idle_session,
                    idle_time=idle_time,
                    active_time=active_time,
                    utilization_percent=utilization_percent,
                    full_motion=full_motion,
                    arm_motion=arm_motion,
                    truck_base_motion=truck_base_motion,
                )

                jsonl_file.write(json.dumps(payload) + "\n")
                jsonl_file.flush()

                label = (
                    f"MID:{machine_id} TID:{track_id} {equipment_label} {state}/{activity} "
                    f"Idle:{idle_time:.1f}s Sess:{current_idle_session:.1f}s "
                    f"Util:{utilization_percent:.1f}%"
                )

                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.38,
                    color,
                    2
                )

        writer.write(annotated_frame)

        if SHOW_WINDOW:
            cv2.imshow("Tracking + State + Activity", annotated_frame)

        prev_gray = gray.copy()
        frame_index += 1

        if SHOW_WINDOW and cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    writer.release()
    jsonl_file.close()

    try:
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", OUTPUT_VIDEO_RAW,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            OUTPUT_VIDEO_H264
        ], check=True)
        print(f"Saved H.264 output video to: {OUTPUT_VIDEO_H264}")
    except Exception as e:
        print(f"Failed to convert video to H.264: {e}")

    if SHOW_WINDOW:
        cv2.destroyAllWindows()

    print(f"Saved raw output video to: {OUTPUT_VIDEO_RAW}")
    print(f"Expected dashboard video path: {OUTPUT_VIDEO_H264}")
    print(f"Saved JSONL payloads to: {OUTPUT_JSONL}")
    print(f"Kafka bootstrap servers config: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Kafka topic config: {KAFKA_TOPIC}")


if __name__ == "__main__":
    main()