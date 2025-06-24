import matplotlib
matplotlib.use('TkAgg')

import re
import math
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from tkinter import Tk, filedialog



# === 解析 G-code ===
def parse_gcode(content):
    commands = []
    for line in content.splitlines():
        line = line.strip()
        m = re.match(r'^G1 X([\d\.\-]+)Y([\d\.\-]+)F([\d\.\-]+)', line)
        if m:
            x = float(m.group(1))
            y = float(m.group(2))
            f = float(m.group(3))
            commands.append({'line': line, 'x': x, 'y': y, 'f': f})
        else:
            # 非轨迹指令（如 G0 Z...）原样保留
            commands.append({'line': line, 'x': None, 'y': None, 'f': None})
    return commands

# === Douglas-Peucker 算法 ===
def perpendicular_distance(p, p1, p2):
    if p1 == p2:
        return math.hypot(p['x'] - p1['x'], p['y'] - p1['y'])
    else:
        x0, y0 = p['x'], p['y']
        x1, y1 = p1['x'], p1['y']
        x2, y2 = p2['x'], p2['y']
        return abs((y2 - y1)*x0 - (x2 - x1)*y0 + x2*y1 - y2*x1) / math.hypot(x2 - x1, y2 - y1)

def douglas_peucker(points, epsilon):
    if len(points) < 3:
        return points
    dmax = 0.0
    index = 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d
    if dmax >= epsilon:
        rec_results1 = douglas_peucker(points[:index+1], epsilon)
        rec_results2 = douglas_peucker(points[index:], epsilon)
        return rec_results1[:-1] + rec_results2
    else:
        return [points[0], points[-1]]

# === 分段+简化 ===
def segment_and_simplify(commands, epsilon):
    simplified = []
    segment = []
    for cmd in commands:
        if cmd['x'] is not None and cmd['y'] is not None:
            segment.append(cmd)
        else:
            if segment:
                simplified += douglas_peucker(segment, epsilon)
                segment = []
            simplified.append(cmd)
    if segment:
        simplified += douglas_peucker(segment, epsilon)
    return simplified

# === 画轨迹 ===
def plot_trajectories(original, simplified):
    ax.clear()
    ox, oy = [], []
    sx, sy = [], []
    for cmd in original:
        if cmd['x'] is not None:
            ox.append(cmd['x'])
            oy.append(cmd['y'])
    for cmd in simplified:
        if cmd['x'] is not None:
            sx.append(cmd['x'])
            sy.append(cmd['y'])
    ax.plot(ox, oy, 'r-', label='Original')
    ax.plot(sx, sy, 'g-', label='Simplified')
    ax.set_title(f'原始点数: {len(ox)} | 简化后: {len(sx)}')
    ax.legend()
    fig.canvas.draw_idle()

# === 文件选择 ===
root = Tk()
root.withdraw()
gcode_path = filedialog.askopenfilename(title="选择 G-code 文件")
with open(gcode_path, 'r') as f:
    raw_content = f.read()

# === 初始化 ===
commands = parse_gcode(raw_content)
epsilon = 0.5
simplified = segment_and_simplify(commands, epsilon)

# === Matplotlib 窗口 ===
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)
plot_trajectories(commands, simplified)

# === Slider ===
axcolor = 'lightgoldenrodyellow'
ax_slider = plt.axes([0.15, 0.1, 0.7, 0.03], facecolor=axcolor)
slider = Slider(ax_slider, 'Epsilon', 0.01, 5.0, valinit=epsilon, valstep=0.05)

def update(val):
    t = slider.val
    global simplified
    simplified = segment_and_simplify(commands, t)
    plot_trajectories(commands, simplified)

slider.on_changed(update)

# === Save 按钮 ===
saveax = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(saveax, 'Save', color=axcolor, hovercolor='0.975')

def save(event):
    save_path = filedialog.asksaveasfilename(
        defaultextension='.gcode',
        title="保存简化后 G-code"
    )
    if save_path:
        with open(save_path, 'w') as f:
            for cmd in simplified:
                f.write(cmd['line'] + '\n')
        print(f"已保存: {save_path}")

button.on_clicked(save)

plt.show()
