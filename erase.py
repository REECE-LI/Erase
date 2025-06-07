import struct
import time
import cv2
import os
import numpy as np

import serial
import socket
import sympy as sp
import json
import re
import time

import config

import udp_utils

port = 'COM22'
baud_rate = 115200

# ser = serial.Serial(port, baud_rate)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
# cap = cv2.VideoCapture(4)
# set 240 fps

cap.set(cv2.CAP_PROP_FPS, 240)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) #640
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) #400
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))




def find_third_vertex(x1, y1, x2, y2, a, b, c):
    # Define the symbols
    x, y = sp.symbols('x y')

    # Define the equations based on the distance formula
    eq1 = sp.Eq(sp.sqrt((x - x1) ** 2 + (y - y1) ** 2), b)
    eq2 = sp.Eq(sp.sqrt((x - x2) ** 2 + (y - y2) ** 2), a)

    # Solve the system of equations
    solutions = sp.solve((eq1, eq2), (x, y))

    return solutions


# Example usage
x1, y1 = 0, 0
x2, y2 = 4, 0
a = 5
b = 3
c = 4

third_vertex = find_third_vertex(x1, y1, x2, y2, a, b, c)


# print(third_vertex)

def intMap(value, fromLow, fromHigh, toLow, toHigh):
    return (value - fromLow) * (toHigh - toLow) / (fromHigh - fromLow) + toLow



def detect(udp):

    lasttime = time.time()
    fps = 0
    frame_num = 0

    while True:
        # if error_flag:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # 获取帧
        ret, frame = cap.read()
        if not ret:
            continue

        frame_num = frame_num + 1
        if frame_num > 100:
            now = time.time()
            fps = 100 / (now - lasttime)
            lasttime = now
            frame_num = 0

        frame = cv2.resize(frame, ((int)(960), (int)(540)), interpolation=cv2.INTER_LINEAR)
        # cv2.imshow("frame", frame)

        blank = np.zeros_like(frame)

        # 二值化
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # 检测边缘
        edges = cv2.Canny(binary, 100, 200)
        # cv2.imshow("edges", edges)
        #
        # 检测轮廓
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        if len(contours) == 0:
            error_flag = True
            print("No contours found")
            continue
        # cv2.drawContours(blank, contours, -1, (255, 255, 255), 1)
        # cv2.imshow("blank", blank)
        #

        for contour in contours:
            print("Contour area:", cv2.contourArea(contour))

        # 去除小轮廓
        contours = [contour for contour in contours if cv2.contourArea(contour) > 10]
        if len(contours) == 0:
            error_flag = True
            print("No contours found after filtering")
            continue
        else:
            for contour in contours:
                print("Contour area:", cv2.contourArea(contour))

        cv2.drawContours(blank, contours, -1, (255, 255, 255), 1)
        # cv2.imshow("blank", blank)
        # print(len(contours))

        # all_contours = cv2.drawContours(blank, contours, -1, (255, 255, 255), 1)
        # put all contours in one
        # all_coutours = np.concatenate(contours)

        markers = []

        continue_flag = False

        for coutour in contours:
            if len(coutour)<5:
                continue_flag = True

        if continue_flag:
            print("Some contours are too small, skipping...")
            continue

        for coutour in contours:
            rrt = cv2.fitEllipse(coutour)
            cv2.ellipse(frame, rrt, (0, 255, 0), 2)
            x, y = rrt[0]
            radius = int(rrt[1][0] / 2)
            center = (int(x), int(y))
            marker = (center, radius)
            markers.append(marker)
            cv2.circle(frame, center, 1, (0, 255, 0), -1)

        print(markers)

        # 去重
        for i in range(len(markers)):
            for j in range(i + 1, len(markers)):
                if markers[i] is not None and markers[j] is not None:
                    if abs(markers[i][0][0] - markers[j][0][0]) < 2 and abs(markers[i][0][1] - markers[j][0][1]) < 2:
                        markers[i] = None
        print(markers)

        markers = [marker for marker in markers if marker is not None]

        if len(markers) != 3:
            error_flag = True
            print("Not enough markers found, expected 3 but got", len(markers))
            # print markers's area
            continue

        dist = []
        for i in range(3):
            for j in range(i + 1, 3):
                d = np.sqrt((markers[i][0][0] - markers[j][0][0]) ** 2 + (markers[i][0][1] - markers[j][0][1]) ** 2)
                dist.append(d)

        # get max distance index
        max_dist_index = dist.index(max(dist))

        max_markers = []
        min_marker = None

        # get max distance markers
        if max_dist_index == 0:
            max_markers.append(markers[0])
            max_markers.append(markers[1])
            min_marker = markers[2]
        elif max_dist_index == 1:
            max_markers.append(markers[0])
            max_markers.append(markers[2])
            min_marker = markers[1]
        elif max_dist_index == 2:
            max_markers.append(markers[1])
            max_markers.append(markers[2])
            min_marker = markers[0]

        # angle of min and max1 and max2
        angle1 = np.arctan2(min_marker[0][1] - max_markers[0][0][1],
                            min_marker[0][0] - max_markers[0][0][0]) * 180 / np.pi
        angle2 = np.arctan2(min_marker[0][1] - max_markers[1][0][1],
                            min_marker[0][0] - max_markers[1][0][0]) * 180 / np.pi
        # print("angle1: ", angle1)
        # print("angle2: ", angle2)
        cv2.line(frame, min_marker[0], max_markers[0][0], (255, 0, 0), 2)
        cv2.line(frame, min_marker[0], max_markers[1][0], (0, 0, 255), 2)
        cv2.putText(frame, "angle1: %.2f" % angle1,
                    ((min_marker[0][0] + max_markers[0][0][0]) // 2, (min_marker[0][1] + max_markers[0][0][1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, "angle2: %.2f" % angle2,
                    ((min_marker[0][0] + max_markers[1][0][0]) // 2, (min_marker[0][1] + max_markers[1][0][1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        angle2_1 = angle2 - angle1
        if angle2_1 < -180:
            angle2_1 += 360

        if angle2_1 > 180:
            angle2_1 -= 360
        if angle2_1 < 0:
            # exchange max1 and max2
            max_markers[0], max_markers[1] = max_markers[1], max_markers[0]

        center = (
            int((max_markers[0][0][0] + max_markers[1][0][0]) / 2),
            int((max_markers[0][0][1] + max_markers[1][0][1]) / 2))
        angle = (np.arctan2(max_markers[1][0][1] - max_markers[0][0][1],
                            max_markers[1][0][0] - max_markers[0][0][0]) * 180 / np.pi) + 180

        # draw line
        cv2.line(frame, max_markers[0][0], max_markers[1][0], (0, 255, 0), 2)
        # cv2.line(frame, center, min_marker[0], (0, 255, 0), 2)
        # draw angle
        cv2.putText(frame, "angle: %.2f" % angle, (center[0] + 20, center[1] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 255), 1)
        cv2.putText(frame, "center: (%d, %d)" % (center[0]*1.28, center[1]*1.28), (center[0] + 20, center[1] + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        # draw center
        cv2.circle(frame, center, 6, (0, 0, 255), -1)

        cv2.putText(frame, "A", max_markers[0][0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, "B", max_markers[1][0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, "C", min_marker[0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)


        # 发送数据
        data = {
            "data": {
                "x": center[0],
                "y": center[1],
                "angle": round(angle, 2)
            }
        }

        data = json.dumps(data).encode('utf-8')

        # send data
        udp.send(data)
        # ser.write(data)
        # show fps
        cv2.putText(frame, "fps: %.2f" % fps, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        # cv2.putText(frame, "center: (%f, %f)" % (center[0]/frame.shape[1], center[1]/frame.shape[0]), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # 显示二值化图像
        # cv2.namedWindow('binary Window', cv2.WINDOW_NORMAL)
        # cv2.imshow("binary Window", binary)
        # 显示帧
        cv2.namedWindow('frame Window', cv2.WINDOW_NORMAL)
        cv2.imshow("frame Window", frame)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    udp = udp_utils.UdpClass(('127.0.0.1', 16667),config.esp_address)
    detect(udp)
