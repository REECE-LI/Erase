import threading
import queue
import time
import cv2
import numpy as np
import json
import udp_utils
import config

# 视频读取设置
cap = cv2.VideoCapture(6)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)

# 图像队列
frame_queue = queue.Queue(maxsize=10)

# UDP通信类
udp = udp_utils.UdpClass(('127.0.0.1', 16667), config.esp_address)


def capture_thread():
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        if not frame_queue.full():
            frame_queue.put(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def process_thread():
    last_time = time.time()
    frame_count = 0
    fps = 0

    while True:
        if frame_queue.empty():
            time.sleep(0.005)
            continue

        frame = frame_queue.get()
        frame_count += 1

        if frame_count >= 100:
            now = time.time()
            fps = 100 / (now - last_time)
            last_time = now
            frame_count = 0

        blank = np.zeros_like(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        edges = cv2.Canny(binary, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted([c for c in contours if cv2.contourArea(c) > 20], key=cv2.contourArea, reverse=True)

        if len(contours) < 3:
            continue

        markers = []
        for contour in contours:
            if len(contour) < 5:
                continue
            rrt = cv2.fitEllipse(contour)
            x, y = rrt[0]
            radius = int(rrt[1][0] / 2)
            center = (int(x), int(y))
            marker = (center, radius)
            markers.append(marker)
            if len(markers) >= 3:
                break

        # 去重
        unique_markers = []
        for m in markers:
            if all(abs(m[0][0] - um[0][0]) >= 2 or abs(m[0][1] - um[0][1]) >= 2 for um in unique_markers):
                unique_markers.append(m)

        if len(unique_markers) != 3:
            continue

        # 三个点的距离
        dist = []
        for i in range(3):
            for j in range(i + 1, 3):
                d = np.linalg.norm(np.array(unique_markers[i][0]) - np.array(unique_markers[j][0]))
                dist.append(d)

        max_idx = dist.index(max(dist))
        idx_map = [(0, 1), (0, 2), (1, 2)]
        i1, i2 = idx_map[max_idx]
        max_markers = [unique_markers[i1], unique_markers[i2]]
        min_marker = [m for i, m in enumerate(unique_markers) if i not in [i1, i2]][0]

        # 角度计算
        angle1 = np.arctan2(min_marker[0][1] - max_markers[0][0][1],
                            min_marker[0][0] - max_markers[0][0][0]) * 180 / np.pi
        angle2 = np.arctan2(min_marker[0][1] - max_markers[1][0][1],
                            min_marker[0][0] - max_markers[1][0][0]) * 180 / np.pi
        angle_diff = angle2 - angle1
        if angle_diff < -180:
            angle_diff += 360
        if angle_diff > 180:
            angle_diff -= 360
        if angle_diff < 0:
            max_markers[0], max_markers[1] = max_markers[1], max_markers[0]

        center = (
            int((max_markers[0][0][0] + max_markers[1][0][0]) / 2),
            int((max_markers[0][0][1] + max_markers[1][0][1]) / 2),
        )
        angle = (np.arctan2(max_markers[1][0][1] - max_markers[0][0][1],
                            max_markers[1][0][0] - max_markers[0][0][0]) * 180 / np.pi + 180) % 360

        # 构建数据并发送
        data = {
            "data": {
                "x": center[0] * 1.28,
                "y": center[1] * 1.28,
                "angle": round(angle, 2)
            }
        }

        udp.send(json.dumps(data).encode('utf-8'))

        # 可选：显示调试窗口
        # cv2.putText(frame, f"fps: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        # cv2.imshow("Tracking", frame)
        print(f"[fps={fps:.2f}] center=({center[0]}, {center[1]}), angle={angle:.2f}")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == '__main__':
    t1 = threading.Thread(target=capture_thread, daemon=True)
    t2 = threading.Thread(target=process_thread, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    cap.release()
    cv2.destroyAllWindows()
