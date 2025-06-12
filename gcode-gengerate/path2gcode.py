import json
import time

import numpy as np
from matplotlib import pyplot as plt
import serial
import serial.tools.list_ports


# $MD : 电机失能
# $ME : 电机使能

class Writer:
    def __init__(self, vid, pid):
        self.device = None
        self.ser = None
        self.speed_x = 10000
        self.speed_y = 10000
        self.speed_z = 10000
        self.write_down_z = 22000
        self.write_up_z = 1
        self.vid = vid
        self.pid = pid
        self.connect()

    def send(self, command):
        # command is a list, send line by line add \r
        for line in command:
            self.ser.write(line.encode('utf-8'))
            self.ser.write('\r'.encode('utf-8'))
            time.sleep(0.01)
            print(line)

        # self.receive()

    #     receive data from serial port
    def receive(self):
        self.ser.write('?'.encode('utf-8'))
        self.ser.write('\r'.encode('utf-8'))

        line = None
    #     get time stamp
        start_time = time.time()
        last_send_time = time.time()
        print('start_time:'+str(start_time))
        while (time.time() - start_time) < 60:
            print(time.time() - start_time)
            line = self.ser.readline()
            line = line.decode('utf-8')
            line = line.strip('\r\n')
            print('receive:'+str(line))
            if time.time() - last_send_time > 0.2:
                self.ser.write('?'.encode('utf-8'))
                self.ser.write('\r'.encode('utf-8'))
                last_send_time = time.time()

    def find_serial_device(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == self.vid and port.pid == self.pid:
                return port.device
        return None

    def connect(self):
        self.device = self.find_serial_device()
        if self.device is None:
            print("Device not found")
            return
        self.ser = serial.Serial(self.device, 115200, timeout=0.5)

    def move_to(self, x, y):
        return "G1 X{0} Y{1} F{2}\n".format(x, y, self.speed_x)

    def go_home(self):
        return "G28\n"

    def set_speed(self, speed):
        self.speed_x = speed
        return "G1 F{0}\n".format(self.speed_x)

    def set_speed_z(self, speed):
        self.speed_z = speed

    # put z down
    def write_down(self):
        return "G0 Z{0} F{1}\n".format(self.write_down_z, self.speed_z)

    # put z up
    def write_up(self):
        return "G0 Z{0} F{1}\n".format(self.write_up_z, self.speed_z)

    def motor_enable(self):
        return "$ME\n"

    def motor_disable(self):
        return "$MD\n"

    def stop(self):
        return "!\n"


class Slicer:
    def __init__(self, writer):
        self.gap = 1
        self.width = None
        self.writer = writer
        self.font = None
        self.text = []
        self.global_location = [0, 0]
        # self.pointer = 0
        # self.location = []
        # self.location_list = []
        # self.location_1 = np.array([[1, 0.5]])
        # self.location_2 = np.array([[1, 0.5], [2, 0.5]])
        # self.location_3 = np.array([[0.2, 0.5], [1.2, 0.5], [2.2, 0.5]])
        # self.location_4 = np.array([[0.2, 0.2], [1.2, 0.2], [2.2, 0.2], [3.2, 0.2]])
        # self.location_5 = self.location_6 = self.location_7 = self.location_8 = np.array(
        #     [[0, 0], [1, 0], [2, 0], [3, 0],
        #      [0, 1], [1, 1], [2, 1], [3, 1]])
        # self.location_list.append(self.location_1)
        # self.location_list.append(self.location_2)
        # self.location_list.append(self.location_3)
        # self.location_list.append(self.location_4)
        # self.location_list.append(self.location_5)
        # self.location_list.append(self.location_6)
        # self.location_list.append(self.location_7)
        # self.location_list.append(self.location_8)
        #
        # self.width_offset_list = [1.5, 1.5, 1.2, 1.1, 1, 1, 1, 1]

    def set_text(self, text):
        #       text is string
        self.text = list(text)
        #         text to unicode
        self.text = [ord(char) for char in self.text]
        # check text in font
        for char in self.text:
            if str(char) not in self.font:
                print("char {0} not in font".format(char))
                return
        # htx_str = list("何同学")
        # htx = [ord(char) for char in htx_str]
        # print(htx)
        #
        # for i in range(len(self.text)):
        #     if self.text[i] == htx[0]:
        #         print("find h")
        #         h_index = i
        #         t_index = i + 1
        #         x_index = i + 2
        #         if h_index < len(self.text) and t_index < len(self.text) and x_index < len(self.text):
        #             if self.text[h_index] == htx[0] and self.text[t_index] == htx[1] and self.text[x_index] == htx[2]:
        #                 self.text[h_index] = -1
        #                 self.text[t_index] = -2
        #                 self.text[x_index] = -3
        #                 break
        #
        # print(self.text)

    def set_font(self, font_path):
        self.font = json.load(open(font_path, "r"))

    def set_width(self, width):
        self.width = width

    def set_gap(self, gap):
        self.gap = gap

    def set_global_location(self, location):
        self.global_location = location

    def slice(self):
        gcode = []
        text_list = []
        pointer = 0
        # global_location = [17, -97]
        # global_location = [0, 0]
        # global_location = [-55, -95]
        # gcode.append(self.writer.motor_enable())
        # self.location = self.location_list[len(self.text) - 1]
        # width_offset = self.width_offset_list[len(self.text) - 1]
        # width = self.width * width_offset
        offset_xy = [1, 0]
        offset_xy = np.array(offset_xy)
        width = self.width
        for char in self.text:
            print('slice:'+str(char))
            plt.axis((0, 1, 0, 1))
            plt.gca().invert_yaxis()
            paths = self.font[str(char)]
            char_list = []
            for path in paths:
                self.writer.set_speed(self.writer.speed_x)
                first_node = path[0]
                offset = offset_xy * pointer * width * self.gap
                x =  (first_node[0] * width + offset[0] + self.global_location[0])
                y = width - (first_node[1] * width + offset[1] + self.global_location[1])
                gcode.append(self.writer.move_to(x, y))
                gcode.append(self.writer.write_down())
                for node in path[1:]:
                    offset = offset_xy * pointer * width * self.gap
                    x =  (node[0] * width + offset[0] + self.global_location[0])
                    y = width - (node[1] * width + offset[1] + self.global_location[1])
                    gcode.append(self.writer.move_to(x, y))
                gcode.append(self.writer.write_up())

                path = np.array(path)
                # print(line)
                # draw line [[0.0, 0.77], [1.0, 0.77]] [[x1, y1], [x2, y2]]
                x = path[:, 0]
                y = path[:, 1]
                char_list.append([x, y])
                plt.plot(x, y)
            pointer += 1
            text_list.append(char_list)
            #     print char on plt
            # plt.text(0.5, 0.5, char, fontsize=20)
            # plt.show()
        # gcode.append(self.writer.motor_disable())
        gcode.append(self.writer.move_to(0, 0))
        return gcode, text_list



if __name__ == '__main__':
    s = Slicer(Writer(0x7523, 0x1a86))
    s.set_font('../json/AlibabaHealthFont20CN-45R.json')#FZSJ-MLXQTJW  AlibabaHealthFont20CN-45R
    s.set_text("大")#出分,AI监控评分
    s.set_width(50)
    s.set_gap(1)#1.1
    s.set_global_location([0, -20])
    output, _ = s.slice()
    print(output)
    # save to txt
    with open("../gcode/da.gcode", "w") as f:
        f.writelines(output)