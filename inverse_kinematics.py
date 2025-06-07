import numpy as np
import matplotlib.pyplot as plt
import math

# 逆运动学计算
def inverse_kinematics(x, y, L1, L2):
    # 计算 r，即末端执行器到原点的距离
    r = math.sqrt(x**2 + y**2)

    # 验证目标位置是否在可达范围内
    if r > (L1 + L2) or r < abs(L1 - L2):
        raise ValueError("目标位置超出可达范围")

    # 计算 θ2（第二关节角度）
    cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    sin_theta2 = math.sqrt(1 - cos_theta2**2)  # 求解 sin(θ2)

    # 选择正解或负解（这取决于具体应用）
    theta2 = math.atan2(sin_theta2, cos_theta2)

    # 计算 θ1（第一个关节角度）
    k1 = L1 + L2 * math.cos(theta2)
    k2 = L2 * math.sin(theta2)
    theta1 = math.atan2(y, x) - math.atan2(k2, k1)

    return math.degrees(theta1), math.degrees(theta2)

# 绘制机械臂图形
def plot_arm(L1, L2, theta1, theta2):
    # 计算关节位置
    x1 = L1 * np.cos(np.radians(theta1))
    y1 = L1 * np.sin(np.radians(theta1))
    x2 = x1 + L2 * np.cos(np.radians(theta1 + theta2))
    y2 = y1 + L2 * np.sin(np.radians(theta1 + theta2))

    # 绘制图形
    plt.figure(figsize=(8, 8))
    plt.plot([0, x1], [0, y1], 'b-', lw=4, label="Link 1 (L1)")  # 第一个连杆
    plt.plot([x1, x2], [y1, y2], 'r-', lw=4, label="Link 2 (L2)")  # 第二个连杆
    plt.scatter([x2], [y2], color='green', s=100, label="End Effector")  # 末端执行器位置
    plt.scatter([x1], [y1], color='blue', s=100, label="Joint 1")  # 第一个关节位置

    # 标注关节和末端执行器
    plt.text(x1, y1, f"Joint 1\nθ1 = {theta1:.2f}°", fontsize=12, ha='right')
    plt.text(x2, y2, f"End Effector\n({x2:.2f}, {y2:.2f})", fontsize=12, ha='right')

    # 标注第二个关节的角度
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    plt.text(mid_x, mid_y, f"θ2 = {theta2:.2f}°", fontsize=12, ha='center')

    plt.xlim(-L1 - L2 - 1, L1 + L2 + 1)
    plt.ylim(-L1 - L2 - 1, L1 + L2 + 1)
    plt.gca().set_aspect('equal', adjustable='box')  # 保持比例
    plt.axhline(0, color='black',linewidth=1)
    plt.axvline(0, color='black',linewidth=1)
    plt.grid(True)
    plt.title("2-Link Robot Arm - Inverse Kinematics")
    plt.legend()
    plt.show()

# 测试参数
L1 = 70.0  # 第一个连杆长度
L2 = 70.0  # 第二个连杆长度
x = -95.0   # 末端执行器的 x 坐标
y = 95.0   # 末端执行器的 y 坐标

# 求解逆运动学
theta1, theta2 = inverse_kinematics(x, y, L1, L2)

# 输出关节角度
print(f"第一个关节角度 θ1: {theta1}°")
print(f"第二个关节角度 θ2: {theta2}°")

# 绘制机械臂图形
plot_arm(L1, L2, theta1, theta2)
