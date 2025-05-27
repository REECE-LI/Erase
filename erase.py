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

# port = 'COM22'
baud_rate = 115200

# ser = serial.Serial(port, baud_rate)

cap = cv2.VideoCapture(0)  # , cv2.CAP_DSHOW # Use cv2.CAP_DSHOW to avoid camera initialization issues on Windows
# cap = cv2.VideoCapture(0)
# set 240 fps
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2000)  # 640
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1000)  # 400
cap.set(cv2.CAP_PROP_FPS, 240)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))


#
# def gcode_to_json(gcode_line):
#     match = re.match(r'(?P<command>[A-Z]+)(?P<parameters>.*)', gcode_line.strip())
#     if match:
#         command = match.group('command')
#         parameters_str = match.group('parameters').strip()
#         parameters = {}
#         if parameters_str:
#             param_pairs = re.findall(r'([A-Z_]+)([-+]?\d*\.?\d*)', parameters_str)
#             for param, value in param_pairs:
#                 if value:
#                     parameters[param] = float(value)
#                 else:
#                     parameters[param] = None
#         return {command: parameters}
#
#
# def data_to_json(x, y, angle):
#     data = {
#         "data": {
#             "x": x,
#             "y": y,
#             "angle": angle
#         }
#     }
#     return data
#
#
# def send_json_udp(json_data, esp32_ip, esp32_port, is_gcode=False):
#     # 将 JSON 数据转换为字节流
#     message = json.dumps(json_data).encode('utf-8')
#     # 创建 UDP 套接字
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         # 发送数据
#         sock.sendto(message, (esp32_ip, esp32_port))
#         print(f"Sent {len(message)} bytes to {esp32_port}")
#         if is_gcode:
#             # 等待接收回复
#             sock.settimeout(5)  # 设置超时时间为 5 秒
#             try:
#                 data, addr = sock.recvfrom(1024)
#                 if data.decode('utf-8') == "OK":
#                     print("Received OK from ESP32")
#                     return True
#                 else:
#                     print("Received unexpected reply from ESP32")
#                     return False
#             except socket.timeout:
#                 print("Timeout waiting for reply from ESP32")
#                 return False
#         else:
#             return True
#     except Exception as e:
#         print(f"Error sending data: {e}")
#         return False
#     finally:
#         sock.close()
#
#
# filename = 'C:/Users/26621/Desktop/Project/H_project/GCode/何21/何.gcode'
# # try:
# #     with open(filename, 'r') as file:
# #         gcode_lines = file.readlines()
# #         print(gcode_lines)
# # except FileNotFoundError:
# #     print("Gcode file not found.")
#
# x_values = []
# y_values = []
# try:
#     with open(filename, 'r') as file:
#         for line in file:
#             stripped_line = line.strip()
#             if stripped_line.startswith('G'):  # 只处理以 G 开头的行，通常包含坐标信息
#                 parts = stripped_line.split()
#                 x = None
#                 y = None
#                 for part in parts:
#                     if part.startswith('X'):
#                         # 提取 X 坐标并转换为浮点数
#                         x = float(part[1:])
#                     elif part.startswith('Y'):
#                         # 提取 Y 坐标并转换为浮点数
#                         y = float(part[1:])
#                 if x is not None:
#                     x_values.append(x)
#                 if y is not None:
#                     y_values.append(y)
# except FileNotFoundError:
#     print(f"文件 {filename} 未找到。")


# print("X 坐标:", x_values)
# print("Y 坐标:", y_values)

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
    error_flag = False

    # 圆心轨迹
    circle_center = []

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

        # cv2.imshow("frame", frame)

        blank = np.zeros_like(frame)
        #
        # height, width, channels = frame.shape
        # print("图像的高度（长）为:", height)
        # print("图像的宽度为:", width)
        # 二值化
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # 检测边缘
        edges = cv2.Canny(binary, 100, 200)
        # cv2.imshow("edges", edges)
        #
        # 检测轮廓
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        if len(contours) == 0:
            error_flag = True
            continue
        # cv2.drawContours(blank, contours, -1, (255, 255, 255), 1)
        # cv2.imshow("blank", blank)
        #
        # 去除小轮廓
        contours = [contour for contour in contours if cv2.contourArea(contour) > 20]
        if len(contours) == 0:
            error_flag = True
            continue

        cv2.drawContours(blank, contours, -1, (255, 255, 255), 1)
        # cv2.imshow("blank", blank)
        # print(len(contours))

        # all_contours = cv2.drawContours(blank, contours, -1, (255, 255, 255), 1)
        # put all contours in one
        # all_coutours = np.concatenate(contours)

        markers = []

        continue_flag = False

        for coutour in contours:
            if len(coutour) < 5:
                continue_flag = True

        if continue_flag:
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

        # print(markers)

        # 去重
        for i in range(len(markers)):
            for j in range(i + 1, len(markers)):
                if markers[i] is not None and markers[j] is not None:
                    if abs(markers[i][0][0] - markers[j][0][0]) < 2 and abs(markers[i][0][1] - markers[j][0][1]) < 2:
                        markers[i] = None
        # print(markers)

        markers = [marker for marker in markers if marker is not None]

        if len(markers) != 3:
            error_flag = True
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
        # print("center: ", center, int(angle*10))
        # print("angle: ", angle)

        # draw line
        cv2.line(frame, max_markers[0][0], max_markers[1][0], (0, 255, 0), 2)
        # cv2.line(frame, center, min_marker[0], (0, 255, 0), 2)
        # draw angle
        cv2.putText(frame, "angle: %.2f" % angle, (center[0] + 20, center[1] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 255), 1)
        cv2.putText(frame, "center: (%d, %d)" % (center[0] * 1.28, center[1] * 1.28), (center[0] + 20, center[1] + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        # draw center
        cv2.circle(frame, center, 6, (0, 0, 255), -1)

        cv2.putText(frame, "A", max_markers[0][0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, "B", max_markers[1][0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, "C", min_marker[0], cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # # 仿射变换开始
        # ab = np.sqrt((max_markers[0][0][0] - max_markers[1][0][0])**2 + (max_markers[0][0][1] - max_markers[1][0][1])**2)
        # ac = np.sqrt((max_markers[0][0][0] - min_marker[0][0])**2 + (max_markers[0][0][1] - min_marker[0][1])**2)
        # bc = np.sqrt((max_markers[1][0][0] - min_marker[0][0])**2 + (max_markers[1][0][1] - min_marker[0][1])**2)
        #
        # #          ab ac bc
        # dist_gt = [0, 1, 0.8]
        # dist_gt[0] = np.sqrt((dist_gt[1])**2 + (dist_gt[2])**2)
        # ab_gt = ab
        # bc_gt = ab * (dist_gt[2] / dist_gt[0])
        # ac_gt = ab * (dist_gt[1] / dist_gt[0])
        #
        # min_marker_gt = find_third_vertex(max_markers[0][0][0], max_markers[0][0][1], max_markers[1][0][0], max_markers[1][0][1], bc_gt, ac_gt, ab_gt)
        #
        # cv2.circle(frame, np.array(min_marker_gt[0], dtype=int), 1, (0, 255, 0), -1)
        # cv2.circle(frame, np.array(min_marker_gt[1], dtype=int), 1, (0, 255, 0), -1)
        #
        # min_marker_gt_1_dist = abs(min_marker_gt[0][0] - min_marker[0][0]) + abs(min_marker_gt[0][1] - min_marker[0][1])
        # min_marker_gt_2_dist = abs(min_marker_gt[1][0] - min_marker[0][0]) + abs(min_marker_gt[1][1] - min_marker[0][1])
        #
        # if min_marker_gt_1_dist < min_marker_gt_2_dist:
        #     min_marker_gt = min_marker_gt[0]
        # else:
        #     min_marker_gt = min_marker_gt[1]
        #
        # # 仿射变换
        # # 3个点
        # pts1 = np.float32([max_markers[0][0], max_markers[1][0], min_marker[0]])
        # pts2 = np.float32([max_markers[0][0], max_markers[1][0], min_marker_gt])
        # M = cv2.getAffineTransform(pts1, pts2)
        # dst = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))
        # cv2.imshow("dst", dst)

        # # 保存圆心轨迹
        # circle_center.append(center)
        # circle_center = circle_center[-200:]
        #
        # # 显示轨迹
        # for i in range(1, len(circle_center)):
        #     cv2.line(frame, circle_center[i - 1], circle_center[i], (255, 255, 0), 2)
        #
        # cv2.circle(blank, center, int(radius*0.8), (255, 255, 255), 1)
        # cv2.imshow("blank", blank)
        # # 仿射变换结束

        # 发送数据
        data = {
            "data": {
                "x": center[0],
                "y": center[1],
                "angle": round(angle, 2)
            }
        }

        # 发送数据
        data2 = {
            "data": {
                "x": center[0]* 1.28,
                "y": center[1] * 1.28,
                "angle": round(angle, 2)
            }
        }

        # 打印结果
        print(f"x: {int(data2['data']['x'])}, y: {int(data2['data']['y'])}, angle: {int(data2['data']['angle'])}")


        data = json.dumps(data).encode('utf-8')
        # print("data: ", data)

        # send data
        udp.send(data)
        # ser.write(data)
        # show fps
        # cv2.putText(frame, "fps: %.2f" % fps, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        # cv2.putText(frame, "center: (%f, %f)" % (center[0]/frame.shape[1], center[1]/frame.shape[0]), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # 显示二值化图像
        # cv2.namedWindow('binary Window', cv2.WINDOW_NORMAL)
        # cv2.imshow("binary Window", binary)
        # 显示帧
        # cv2.namedWindow('frame Window', cv2.WINDOW_NORMAL)
        # cv2.imshow("frame Window", frame)

        # send

        # # 按 'q' 键退出
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    udp = udp_utils.UdpClass(('127.0.0.1', 16667), config.esp_address)
    detect(udp)

# {
#  "data" : {
#     "x": 100.0,
#     "y": 200.0,
#     "angle": 150.12
#   }
# }


# gcode = {
#     "G1": {
#       "X": 100.11,
#       "Y": 200.22,
#     }
# }

# gcode = {
#     "M3": {
#       "s": 1
#     }
# }
