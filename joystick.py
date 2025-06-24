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
n_buttons = joystick.get_numbuttons()
print("Buttons:", n_buttons)
for i in range(n_buttons):
    print(f"Button {i} state:", joystick.get_button(i))

while True:
    pygame.event.pump()
    for i in range(joystick.get_numaxes()):
        value = joystick.get_axis(i)
        print(f"轴 {i}: {value:.3f}")
    print("------")
    for i in range(n_buttons):
        print(f"Button {i} state:", joystick.get_button(i))

    time.sleep(0.5)
