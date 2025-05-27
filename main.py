import time

import erase
import threading
import queue

import udp_utils  
import gcode_utils
import json

import config

import serial

port = '/dev/tty.usbmodem1301'
baud_rate = 115200

ser = serial.Serial(port, baud_rate, timeout=0.001)
# ser.rts = False

udp = udp_utils.UdpClass(('127.0.0.1', 15558), ('127.0.0.1', 15556))

udp_local = udp_utils.UdpClass(('127.0.0.1', 15556), ('127.0.0.1', 15558))

def detect_thread():
    print("detect_thread")
    erase.detect(udp)

def gcode_thread():
    gcode_utils.main(udp)

def send2serial():
    # ser.timeout(0.1)
    while True:
        buffer = udp_local.recv()
        if buffer != '0':
            ser.write(buffer[0])
            # print(buffer[0])
        ser_buffer = ser.readall()
        if ser_buffer != b'':
            udp_local.send(str(int(ser_buffer)).encode())
        # if ser_buffer is


if __name__ == '__main__':
    print("main start")
    t1 = threading.Thread(target=detect_thread)
    t2 = threading.Thread(target=gcode_thread)
    t3 = threading.Thread(target=send2serial)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
    print("main end")
    udp.close()

