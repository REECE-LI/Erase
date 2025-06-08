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
import math

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

def signed_angle(p1, p2):
    """
    计算从 x 轴正方向 到 向量 p1->p2 的有符号角度，范围 -180~180
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle_rad = math.atan2(dy, dx)  # 返回 -π ~ π
    angle_deg = math.degrees(angle_rad)
    return angle_deg


def midpoint(p1, p2):
    return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)


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
        ret, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        binary = cv2.bitwise_not(binary)
        # 膨胀 + 腐蚀
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        binary = cv2.dilate(binary, kernel, iterations=1)
        binary = cv2.bitwise_not(binary)
        binary = cv2.dilate(binary, kernel, iterations=1)
        # binary = cv2.erode(binary, kernel, iterations=1)

        # 直接在二值图像上找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # # 过滤小轮廓
        # contours = [c for c in contours if cv2.contourArea(c) > 10]

        # 按面积排序，取最大的三个轮廓
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]

        if len(contours) < 3:
            print("Not enough valid contours found")
            error_flag = True
            continue

        # 计算三个轮廓的重心
        centers = []
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            centers.append((cx, cy))

            if len(centers) == 3:
                # === 找出3号点：距离其他两点之和最大 ===
                distsums = []
                for i in range(3):
                    dist_sum = 0
                    for j in range(3):
                        if i != j:
                            dist_sum += np.linalg.norm(np.array(centers[i]) - np.array(centers[j]))
                    distsums.append(dist_sum)
                index3 = np.argmax(distsums)
                point3 = centers[index3]

                # === 剩下两个点 ===
                remaining_indices = [i for i in range(3) if i != index3]
                ptA = centers[remaining_indices[0]]
                ptB = centers[remaining_indices[1]]

                # === 通过边长判断哪个是1号（但我们稍后要交换） ===
                len_A3 = np.linalg.norm(np.array(ptA) - np.array(point3))
                len_B3 = np.linalg.norm(np.array(ptB) - np.array(point3))

                # 初始：最长边对角是1号，另一个是2号
                if len_A3 > len_B3:
                    point1 = ptA
                    point2 = ptB
                else:
                    point1 = ptB
                    point2 = ptA

                # === 交换 1号 和 2号顺序 ===


                # === 可选：叉乘判断是否方向一致，若需要可以打开 ===
                def orientation(p1, p2, p3):
                    return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (p2[1] - p1[1])

                # 如果方向不对（逆时针），交换1、2号使其统一为顺时针
                if orientation(point1, point2, point3) < 0:
                    point1, point2 = point2, point1

                point1, point2 = point2, point1

                angle = signed_angle(point1, point3)
                mid = midpoint(point2, point3)
                print(angle)

                cv2.circle(frame, mid, 5, (255, 0, 255), -1)
                cv2.putText(frame, f"M({mid[0]},{mid[1]})", (mid[0] + 5, mid[1] - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)

                # === 显示编号在图上 ===
                for i, pt in enumerate([point1, point2, point3], start=1):
                    cv2.putText(frame, f"{i}", (pt[0] - 10, pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255),
                                2)

            # 可视化重心
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"({cx},{cy})", (cx + 5, cy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

            cv2.imshow("result", frame)


    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    udp = udp_utils.UdpClass(('127.0.0.1', 16667),config.esp_address)
    detect(udp)
