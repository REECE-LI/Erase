import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("没有检测到手柄")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"检测到手柄: {joystick.get_name()}")
print(f"共有 {joystick.get_numaxes()} 个轴")

while True:
    pygame.event.pump()
    for i in range(joystick.get_numaxes()):
        value = joystick.get_axis(i)
        print(f"轴 {i}: {value:.3f}")
    print("------")
    time.sleep(0.5)
