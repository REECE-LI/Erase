import socket
import time
import threading
import json
import numpy as np
import cv2
from evdev import InputDevice, ecodes

# === 参数设置 ===
device_path = '/dev/input/event13'
udp_target = ('192.168.50.17', 11222)
video_index = 4

send_interval = 0.03  # 30ms

# === 全局共享数据 ===
joystick_data = {"x": 0, "y": 0, "z": 0}
vision_data = {"x": 0, "y": 0, "angle": 0.0}

data_lock = threading.Lock()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# === 手柄线程 ===
def joystick_thread():
    gamepad = InputDevice(device_path)
    axis_map = {
        ecodes.ABS_X: 0,
        ecodes.ABS_Y: 1,
        ecodes.ABS_RX: 3,
    }
    while True:
        for event in gamepad.read_loop():
            if event.type == ecodes.EV_ABS and event.code in axis_map:
                with data_lock:
                    axis_id = axis_map[event.code]
                    if axis_id == 0:
                        joystick_data["x"] = event.value
                    elif axis_id == 1:
                        joystick_data["y"] = event.value
                    elif axis_id == 3:
                        joystick_data["z"] = event.value

# === 图像识别线程 ===
def vision_thread():
    cap = cv2.VideoCapture(video_index)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

    lasttime = time.time()
    fps = 0
    frame_num = 0

    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        ret, frame = cap.read()
        if not ret:
            continue

        frame_num += 1
        if frame_num > 100:
            now = time.time()
            fps = 100 / (now - lasttime)
            lasttime = now
            frame_num = 0

        frame = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_LINEAR)
        blank = np.zeros_like(frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        edges = cv2.Canny(binary, 100, 200)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 10]
        if len(contours) == 0:
            continue

        markers = []
        for cnt in contours:
            if len(cnt) < 5:
                continue
            rrt = cv2.fitEllipse(cnt)
            x, y = rrt[0]
            radius = int(rrt[1][0] / 2)
            markers.append(((int(x), int(y)), radius))

        # 去重
        unique_markers = []
        for marker in markers:
            if all(abs(marker[0][0] - m[0][0]) >= 2 or abs(marker[0][1] - m[0][1]) >= 2 for m in unique_markers):
                unique_markers.append(marker)

        if len(unique_markers) != 3:
            continue

        m0, m1, m2 = unique_markers
        d01 = np.linalg.norm(np.array(m0[0]) - np.array(m1[0]))
        d02 = np.linalg.norm(np.array(m0[0]) - np.array(m2[0]))
        d12 = np.linalg.norm(np.array(m1[0]) - np.array(m2[0]))

        dists = [d01, d02, d12]
        idx = dists.index(max(dists))
        if idx == 0:
            max1, max2, min_m = m0, m1, m2
        elif idx == 1:
            max1, max2, min_m = m0, m2, m1
        else:
            max1, max2, min_m = m1, m2, m0

        angle1 = np.arctan2(min_m[0][1] - max1[0][1], min_m[0][0] - max1[0][0]) * 180 / np.pi
        angle2 = np.arctan2(min_m[0][1] - max2[0][1], min_m[0][0] - max2[0][0]) * 180 / np.pi
        angle2_1 = angle2 - angle1
        if angle2_1 < -180:
            angle2_1 += 360
        if angle2_1 > 180:
            angle2_1 -= 360
        if angle2_1 < 0:
            max1, max2 = max2, max1

        center = (
            int((max1[0][0] + max2[0][0]) / 2),
            int((max1[0][1] + max2[0][1]) / 2)
        )

        angle = (np.arctan2(max2[0][1] - max1[0][1], max2[0][0] - max1[0][0]) * 180 / np.pi + 180) % 360

        # 可视化
        # for (pt, r) in unique_markers:
        #     cv2.circle(frame, pt, r, (0, 255, 0), 2)
        # cv2.line(frame, max1[0], max2[0], (255, 0, 0), 2)
        # cv2.circle(frame, center, 6, (0, 0, 255), -1)
        # cv2.putText(frame, f"angle: {angle:.2f}", (center[0]+20, center[1]+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        #
        # # camera show
        # cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        # cv2.imshow("Camera", frame)

        with data_lock:
            vision_data["x"] = center[0]
            vision_data["y"] = center[1]
            vision_data["angle"] = round(angle)


# === UDP发送线程 ===
def udp_sender():
    while True:
        with data_lock:
            packet = {
                "joystick": joystick_data.copy(),
                "vision": vision_data.copy()
            }
        msg = json.dumps(packet)
        sock.sendto(msg.encode(), udp_target)
        print("Sent:", msg)
        time.sleep(send_interval)

# === 启动线程 ===
threading.Thread(target=joystick_thread, daemon=True).start()
threading.Thread(target=vision_thread, daemon=True).start()
threading.Thread(target=udp_sender, daemon=True).start()

# 主线程保持运行
while True:
    time.sleep(1)
