from time import sleep

from gcodeparser import GcodeParser as GP
import json

import udp_utils
import config
import serial

port = 'COM22'
baud_rate = 115200

# ser = serial.Serial(port, baud_rate)

def get_gcode_data(gcode_file):
    with open(gcode_file, 'r') as f:
        gcode = f.read()
    parser = GP(gcode)
    return parser


def main(udp):
    print("gcode_thread")
    gcode_line_index = 0
    gcode = get_gcode_data(config.gcode_path)
    while True:
        data = udp.recv()
        print(str(int(data[0])) + "  " +str(gcode_line_index+1))
        if str(int(data[0])) == str(gcode_line_index+1):
            print(str(int(data[0])))
            udp_buffer = {
                # "gcode":{
                    gcode.lines[gcode_line_index].command_str: {
                    },
                    "index":gcode_line_index+1
                # }
            }
            # gcode.lines[gcode_line_index].params : {'S':1}
            for key in gcode.lines[gcode_line_index].params:
                udp_buffer[gcode.lines[gcode_line_index].command_str][key] = gcode.lines[gcode_line_index].params[key]
            udp_buffer = json.dumps(udp_buffer).encode()
            udp.send(udp_buffer)
            # print(udp_buffer)
            if gcode_line_index < len(gcode.lines) - 1:
                gcode_line_index += 1
            else:
                break
        else:
            udp_buffer = {
                # "gcode":{
                gcode.lines[gcode_line_index].command_str: {
                },
                    "index":gcode_line_index+1
                # }
            }
            # gcode.lines[gcode_line_index].params : {'S':1}
            for key in gcode.lines[gcode_line_index].params:
                udp_buffer[gcode.lines[gcode_line_index].command_str][key] = gcode.lines[gcode_line_index].params[key]
            udp_buffer = json.dumps(udp_buffer).encode()
            udp.send(udp_buffer)
            # ser.write(udp_buffer)
            # print("noAsk")
            sleep(0.002)



if __name__ == '__main__':
    udp = udp_utils.UdpClass(config.receiver_address, config.esp_address)
    main(udp)
