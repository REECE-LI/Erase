import socket
import time
import threading
import json
import numpy as np
import cv2
import pygame

# === 参数设置 ===
udp_target = ('192.168.50.17', 11222)
video_index = 0
send_interval = 0.03  # 30ms

# === 全局共享数据 ===
joystick_data = {"x": 0, "y": 0, "j": 0, "k": 0}
vision_data = {"x": 0, "y": 0, "angle": 0.0}
data_lock = threading.Lock()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# === 手柄线程 ===
def joystick_thread():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("没有检测到手柄")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"检测到手柄: {joystick.get_name()}")

    while True:
        pygame.event.pump()  # 必须调用来更新 joystick 状态

        with data_lock:
            # 假设：
            # 轴 0 = 左摇杆 X，对应 joystick_data["x"]
            # 轴 1 = 左摇杆 Y，对应 joystick_data["y"]
            # 轴 3 = 右摇杆 X 或扳机，对应 joystick_data["z"]
            joystick_data["x"] = (int)(joystick.get_axis(0) * 110)
            joystick_data["y"] = (int)(joystick.get_axis(1) * 110)
            joystick_data["j"] = (int)(joystick.get_axis(4) + 1)
            joystick_data["k"] = (int)(joystick.get_axis(5) + 1)
        # # 输出当前手柄状态
        # print(f"手柄状态: {joystick_data}")
        time.sleep(0.01)  # 防止占用过高 CPU


# === 图像识别线程 ===
def vision_thread():
    cap = cv2.VideoCapture(video_index, cv2.CAP_DSHOW)

    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

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

        # 显示帧
        cv2.namedWindow('frame Window', cv2.WINDOW_NORMAL)
        cv2.imshow("frame Window", frame)

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
        print(f"发送数据: {msg}")
        time.sleep(send_interval)


# === 启动线程 ===
threading.Thread(target=joystick_thread, daemon=True).start()
threading.Thread(target=vision_thread, daemon=True).start()
threading.Thread(target=udp_sender, daemon=True).start()

# 主线程保持运行
while True:
    time.sleep(1)
