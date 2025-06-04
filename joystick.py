import socket
import time
import threading
from evdev import InputDevice, ecodes

# ============ 设置区域 ============
device_path = '/dev/input/event13'  # ← 替换为实际的设备路径
udp_ip = '192.168.50.17'           # ← 目标IP
udp_port = 11222                   # ← 目标端口
send_interval = 0.03               # 20ms
# ==================================

gamepad = InputDevice(device_path)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 映射：evdev code => axis编号
axis_map = {
    ecodes.ABS_X: 0,
    ecodes.ABS_Y: 1,
    ecodes.ABS_RX: 3,  # 修改为你实际的 Axis 3 代码（可用 ABS_Z、ABS_RY）
}
axis_values = {0: 0, 1: 0, 3: 0}

# === 实时更新线程 ===
def input_thread():
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS and event.code in axis_map:
            axis_num = axis_map[event.code]
            axis_values[axis_num] = event.value

# === UDP发送线程 ===
def send_thread():
    while True:
        msg = f"{axis_values[0]},{axis_values[1]},{axis_values[3]}"
        sock.sendto(msg.encode(), (udp_ip, udp_port))
        print("Sent:", msg)
        time.sleep(send_interval)

# === 启动两个线程 ===
threading.Thread(target=input_thread, daemon=True).start()
threading.Thread(target=send_thread, daemon=True).start()

# 防止主线程退出
while True:
    time.sleep(1)
