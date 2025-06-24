import socket
import time
import threading
import json
import numpy as np
import cv2
import pygame
import math
import signal
import sys
from collections import deque


WINDOW_SIZE = 20
x_buf     = deque(maxlen=WINDOW_SIZE)
y_buf     = deque(maxlen=WINDOW_SIZE)
ang_buf   = deque(maxlen=WINDOW_SIZE)


# === 全局退出事件 ===
stop_event = threading.Event()

def handle_exit(signum, frame):
    print(f"收到退出信号 {signum}，准备关闭…")
    stop_event.set()

# 捕获 Ctrl+C（SIGINT）和 PyCharm 停止按钮（SIGTERM）
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# === 参数设置 ===
# 小黄
udp_target = ('192.168.50.17', 11222)
# 小绿
# udp_target = ('192.168.50.166', 11222)
video_index = 0
send_interval = 0.03  # 30ms

# === 全局共享数据 ===
joystick_data = {"x": 0, "y": 0, "j": 0, "k": 0, "z":0}
vision_data   = {"x": 0, "y": 0, "angle": 0.0}
data_lock     = threading.Lock()
sock          = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signed_angle(p1, p2):
    """
    计算从 x 轴正方向 到 向量 p1->p2 的有符号角度，范围 -180~180
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle_rad = math.atan2(dy, dx)  # 返回 -π ~ π
    return math.degrees(angle_rad)

def midpoint(p1, p2):
    return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

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

    while not stop_event.is_set():
        pygame.event.pump()  # 必须调用来更新 joystick 状态
        with data_lock:
            joystick_data["x"] = int(joystick.get_axis(0) * 110)
            joystick_data["y"] = int(joystick.get_axis(1) * 110)
            joystick_data["j"] = int(joystick.get_axis(4) + 1)
            joystick_data["k"] = int(joystick.get_axis(5) + 1)
            joystick_data["z"] = int(joystick.get_button(8))
        time.sleep(0.01)  # 防止占用过高 CPU

# === 图像识别线程 ===
def vision_thread():
    cap = cv2.VideoCapture(video_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FPS, 180)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    lasttime = time.time()
    frame_num = 0

    while not stop_event.is_set():
        # 如果按下 'q' 也退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

        ret, frame = cap.read()
        if not ret:
            continue

        frame_num += 1
        if frame_num >= 100:
            now = time.time()
            fps = 100 / (now - lasttime)
            lasttime = now
            frame_num = 0
            # print(f"FPS: {fps:.1f}")

        frame = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = cv2.bitwise_not(binary)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.dilate(binary, kernel, iterations=1)
        binary = cv2.bitwise_not(binary)
        binary = cv2.dilate(binary, kernel, iterations=1)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]

        if len(contours) < 3:
            # print("Not enough valid contours found")
            continue

        centers = []
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            centers.append((cx, cy))

        if len(centers) == 3:
            # 找出 3 号点：距离其他两点之和最大
            distsums = [sum(np.linalg.norm(np.array(centers[i]) - np.array(centers[j]))
                            for j in range(3) if i != j) for i in range(3)]
            idx3 = int(np.argmax(distsums))
            p3 = centers[idx3]
            rem = [i for i in range(3) if i != idx3]
            pA, pB = centers[rem[0]], centers[rem[1]]

            # 初始：最长边为 1 号
            if np.linalg.norm(np.array(pA)-np.array(p3)) > np.linalg.norm(np.array(pB)-np.array(p3)):
                p1, p2 = pA, pB
            else:
                p1, p2 = pB, pA

            # 令 (p1,p2,p3) 顺时针
            def orientation(a,b,c):
                return (b[0]-a[0])*(c[1]-a[1]) - (c[0]-a[0])*(b[1]-a[1])

            if orientation(p1, p2, p3) < 0:
                p1, p2 = p2, p1

            p1, p2 = p2, p1
            # 计算角度和中点
            angle = signed_angle(p1, p3)
            mid = midpoint(p2, p3)
            raw_x = mid[0] / 0.4
            raw_y = mid[1] / 0.4
            raw_ang = angle

            # 更新 buffers
            x_buf.append(raw_x)
            y_buf.append(raw_y)
            ang_buf.append(raw_ang)

            # 计算平均值
            filt_x = sum(x_buf) / len(x_buf)
            filt_y = sum(y_buf) / len(y_buf)
            filt_ang = sum(ang_buf) / len(ang_buf)

            with data_lock:
                vision_data["x"] = int(filt_x)
                vision_data["y"] = int(filt_y)
                vision_data["angle"] = round(filt_ang)

            # 可视化
            cv2.circle(frame, mid, 5, (255, 0, 255), -1)
            cv2.putText(frame, f"M({mid[0]},{mid[1]})", (mid[0]+5, mid[1]-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
            for idx, pt in enumerate([p1, p2, p3], start=1):
                cv2.putText(frame, f"{idx}", (pt[0]-10, pt[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("result", frame)

    # 清理摄像头资源
    cap.release()

# === UDP发送线程 ===
def udp_sender():
    while not stop_event.is_set():
        with data_lock:
            packet = {
                "joystick": joystick_data.copy(),
                "vision":  vision_data.copy()
            }
        sock.sendto(json.dumps(packet).encode(), udp_target)
        print(f"发送数据: {packet}")
        time.sleep(send_interval)
    sock.close()

# 启动线程
threads = [
    threading.Thread(target=joystick_thread),
    threading.Thread(target=vision_thread),
    threading.Thread(target=udp_sender),
]
for t in threads:
    t.start()

# 主线程等待退出事件并统一清理
try:
    while not stop_event.is_set():
        time.sleep(0.5)
except KeyboardInterrupt:
    stop_event.set()
finally:
    print("清理 OpenCV 窗口并退出")
    cv2.destroyAllWindows()
    sys.exit(0)
