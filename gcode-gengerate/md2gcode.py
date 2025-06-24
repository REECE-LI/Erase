import json
import time
import numpy as np
from matplotlib import pyplot as plt
import serial
import serial.tools.list_ports
import os
import re
import csv
from pypinyin import pinyin, lazy_pinyin

fontPath1 = '../json/AlibabaHealthFont20CN-45R.json'
fontPath2 = '../json/FZSJ-MLXQTJW.json'


# Function to extract characters from CSV file (assuming one character per row in the first column)
def extract_characters_from_csv(csv_file):
    characters = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Assuming the characters are in the first column
        for row in reader:
            if row:  # Skip empty rows
                char = row[0].strip()  # Remove any leading or trailing whitespace
                if char:  # Only add non-empty characters
                    characters.append(char)
    return characters


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
        for line in command:
            self.ser.write(line.encode('utf-8'))
            self.ser.write('\r'.encode('utf-8'))
            time.sleep(0.01)
            print(line)

    def receive(self):
        self.ser.write('?'.encode('utf-8'))
        self.ser.write('\r'.encode('utf-8'))

        line = None
        start_time = time.time()
        last_send_time = time.time()
        while (time.time() - start_time) < 60:
            line = self.ser.readline()
            line = line.decode('utf-8').strip('\r\n')
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

    def write_down(self):
        return "G0 Z{0} F{1}\n".format(self.write_down_z, self.speed_z)

    def write_up(self):
        return "G0 Z{0} F{1}\n".format(self.write_up_z, self.speed_z)


class Slicer:
    def __init__(self, writer, font_path_1, font_path_2=None):
        self.gap = 1
        self.width = None
        self.writer = writer
        self.font_1 = None
        self.font_2 = None
        self.text = []
        self.global_location = [0, 0]

        # 加载两个字体文件，一个作为主字体，另一个作为备用字体
        # self.set_font(font_path_1, font_path_2)

    def set_text(self, text):
        self.text = list(text)  # 保持字符本身

    def set_font(self, font_path_1, font_path_2=None):
        # 加载主字体文件
        self.font_1 = json.load(open(font_path_1, "r"))
        # 如果存在备用字体文件，则加载备用字体
        # if font_path_2:
        #     self.font_2 = json.load(open(font_path_2, "r"))

    def set_width(self, width):
        self.width = width

    def set_gap(self, gap):
        self.gap = gap

    def set_global_location(self, location):
        self.global_location = location

    def slice(self):
        pointer = 0
        offset_xy = [1, 0]
        offset_xy = np.array(offset_xy)
        width = self.width

        num = 1
        # For each character, generate a separate G-code file
        for char in self.text:
            char_code = ord(char)  # 获取字符的 Unicode 编码
            print(f"正在切割字符: {char} (Unicode 编码: {char_code})")  # 输出当前字符和其 Unicode 编码
            char_str = str(char_code)  # 使用字符的 Unicode 编码作为键

            # 获取该字符的拼音
            char_pinyin = ''.join(lazy_pinyin(char))  # 获取拼音（简拼）

            # Prepare the G-code list for the current character
            gcode = []  # 清空 gcode 列表，确保每个字符只有自己的 G-code

            paths = None

            # 优先查找主字体文件
            if char_str in self.font_1:
                paths = self.font_1[char_str]
            # 如果主字体文件中找不到，再查找备用字体文件
            # elif self.font_2 and char_str in self.font_2:
            #     paths = self.font_2[char_str]
            # 如果两个文件中都没有找到字符，则使用 "口" 字符替代
            if not paths:
                print(f"字符 '{char}' 在两个字体文件中都没有找到，使用 '口' 替代。")
                tempchar = "口"  # 替换为 '口'
                char_code = ord(tempchar)  # 更新字符的 Unicode 编码
                char_pinyin = ''.join(lazy_pinyin(char))

                char_str = str(char_code)  # 更新字符的 Unicode 编码字符串
                if char_str in self.font_1:
                    paths = self.font_1[char_str]
                elif self.font_2 and char_str in self.font_2:
                    paths = self.font_2[char_str]

            if paths:  # 如果找到了路径
                for path in paths:
                    self.writer.speed_x = self.writer.speed_x  # 直接设置速度
                    first_node = path[0]
                    offset = offset_xy * pointer * width * self.gap
                    x = (first_node[0] * width + offset[0] + self.global_location[0])
                    y = width - (first_node[1] * width + offset[1] + self.global_location[1])
                    gcode.append(self.writer.move_to(x, y))
                    gcode.append(self.writer.write_down())
                    for node in path[1:]:
                        offset = offset_xy * pointer * width * self.gap
                        x = (node[0] * width + offset[0] + self.global_location[0])
                        y = width - (node[1] * width + offset[1] + self.global_location[1])
                        gcode.append(self.writer.move_to(x, y))
                    gcode.append(self.writer.write_up())
            else:
                print(f"字符 '{char}' (Unicode 编码: {char_code}) 在两个字体文件中都没有找到。")  # 如果字符没找到，则打印信息

            # Save the G-code for the current character to a separate file
            file_name = f"gcode_{num}.gcode"  # 使用拼音作为文件名的一部分
            output_path = os.path.join("../2025-06-08-gcode-78/121+", file_name)  # 确保目录存在
            # output_path = os.path.join("../2025-06-08-gcode-78/base_gcode", file_name)  # 确保目录存在
            num = num + 1
            # Make sure the "gcode" folder exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write the G-code to the file
            with open(output_path, "w") as f:
                f.writelines(gcode)

            print(f"G-code for character '{char}' saved to: {output_path}")
            # pointer += 1

        return gcode, []  # 返回 gcode 和空的 text_list


if __name__ == '__main__':
    # Define the CSV file path
    # csv_file = '../2025-06-08-gcode-78/big_characters.csv'  # Adjust as needed
    csv_file = '../2025-06-08-gcode-78/character.csv'  # Adjust as needed

    # Extract characters from the CSV file (first column)
    characters = extract_characters_from_csv(csv_file)
    print(characters)

    # Set up the Slicer and Writer
    s = Slicer(Writer(0x7523, 0x1a86), fontPath1, fontPath2)

    s.set_font(fontPath1, fontPath2)  # Path to your font file

    # Set the text for G-code generation (for example, using the characters extracted)
    text = ''.join(characters)
    s.set_text(text)

    # s.set_width(65)
    s.set_width(65)
    s.set_gap(1)
    s.set_global_location([0, -20])

    output, _ = s.slice()
