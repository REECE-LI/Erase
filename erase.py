import cv2
import numpy as np
import json
import time
import udp_utils
import config

cap = cv2.VideoCapture(6)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)


def detect(udp):
    error_flag = False
    lasttime = time.time()
    frame_num = 0
    fps = 0

    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
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

        # 图像预处理
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        edges = cv2.Canny(binary, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted([cnt for cnt in contours if cv2.contourArea(cnt) > 20], key=cv2.contourArea, reverse=True)[:5]

        if len(contours) < 3:
            error_flag = True
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
            error_flag = True
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

        angle_diff = angle2 - angle1
        angle_diff = (angle_diff + 360) % 360
        if angle_diff > 180:
            max1, max2 = max2, max1

        center = (
            int((max1[0][0] + max2[0][0]) / 2),
            int((max1[0][1] + max2[0][1]) / 2)
        )

        angle = np.arctan2(max2[0][1] - max1[0][1], max2[0][0] - max1[0][0]) * 180 / np.pi
        angle = (angle + 180) % 360

        data = {
            "data": {
                "x": center[0],
                "y": center[1],
                "angle": round(angle, 2)
            }
        }

        udp.send(json.dumps(data).encode('utf-8'))

        print(f"[fps={fps:.2f}] center=({center[0]}, {center[1]}), angle={angle:.2f}")


    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    udp = udp_utils.UdpClass(('127.0.0.1', 16667), config.esp_address)
    detect(udp)
