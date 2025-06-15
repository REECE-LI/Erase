import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import re
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# === GCode_t 结构体类 ===
class GCode_t:
    def __init__(self, x=0.0, y=0.0, isPen=False):
        self.x = round(x, 2)
        self.y = round(y, 2)
        self.isPen = isPen

    def __repr__(self):
        return f"{{{self.x}f, {self.y}f, {str(self.isPen).lower()}}}"

# === G-code 解析（识别落笔/抬笔）===
def parse_gcode(gcode):
    lines = gcode.splitlines()
    coords = []
    pen_down = False

    last_x, last_y = None, None
    path_segments = []

    for line in lines:
        line = line.strip()
        if line.startswith(';') or not line:
            continue

        if 'Z' in line:
            z_match = re.search(r'Z([-\d.]+)', line)
            if z_match:
                z_val = float(z_match.group(1))
                pen_down = z_val >= 10000  # Z ≥ 10000 为落笔

        if line.startswith('G0') or line.startswith('G1'):
            x_match = re.search(r'X([-\d.]+)', line)
            y_match = re.search(r'Y([-\d.]+)', line)

            if x_match and y_match:
                x = float(x_match.group(1))
                y = float(y_match.group(1))

                coords.append({'x': x, 'y': y, 'pen': pen_down})

                if last_x is not None and last_y is not None:
                    path_segments.append(((last_x, last_y), (x, y), pen_down))

                last_x, last_y = x, y

    return coords, path_segments

# === 拖动类 ===
class DraggablePoints:
    def __init__(self, ax, coords, segments):
        self.ax = ax
        self.coords = coords
        self.segments = segments
        self._ind = None

        self.lines = []
        for (x0, y0), (x1, y1), pen in segments:
            color = 'green' if pen else 'red'
            line, = ax.plot([x0, x1], [y0, y1], color=color)
            self.lines.append(line)

        self.points = ax.plot([c['x'] for c in coords], [c['y'] for c in coords], 'o', color='blue')[0]

        # 绑定事件
        self.cid_press = self.points.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.points.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.points.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def get_ind_under_point(self, event):
        threshold = 0.5
        for i, c in enumerate(self.coords):
            if abs(c['x'] - event.xdata) < threshold and abs(c['y'] - event.ydata) < threshold:
                return i
        return None

    def on_press(self, event):
        self._ind = self.get_ind_under_point(event)

    def on_release(self, event):
        self._ind = None

    def on_motion(self, event):
        if self._ind is None or event.xdata is None or event.ydata is None:
            return
        self.coords[self._ind]['x'] = event.xdata
        self.coords[self._ind]['y'] = event.ydata

        self.points.set_data(
            [c['x'] for c in self.coords],
            [c['y'] for c in self.coords]
        )

        for i, ((_, _), (_, _), pen) in enumerate(self.segments):
            if i + 1 >= len(self.coords):
                continue
            x0, y0 = self.coords[i]['x'], self.coords[i]['y']
            x1, y1 = self.coords[i + 1]['x'], self.coords[i + 1]['y']
            self.lines[i].set_data([x0, x1], [y0, y1])

        self.ax.figure.canvas.draw()

    # 清除事件连接
    def clear_events(self):
        self.ax.figure.canvas.mpl_disconnect(self.cid_press)
        self.ax.figure.canvas.mpl_disconnect(self.cid_release)
        self.ax.figure.canvas.mpl_disconnect(self.cid_motion)

# === 保存并生成结构体 ===
def save_gcode_and_generate_struct(coords, file_path):
    gcode_lines = []
    current_pen = False

    gcode_lines.append(f"G1 X{coords[0]['x']:.2f} Y{coords[0]['y']:.2f}")

    for i, c in enumerate(coords):
        if i == 0:
            if c['pen']:
                gcode_lines.append("G0 Z22000 F10000")
                current_pen = True
            else:
                gcode_lines.append("G0 Z1 F10000")
                current_pen = False

            gcode_lines.append(f"G1 X{c['x']:.2f} Y{c['y']:.2f}")
        else:
            if current_pen != c['pen']:
                if c['pen']:
                    gcode_lines.append("G0 Z22000 F10000")  # 落笔
                else:
                    gcode_lines.append("G0 Z1 F10000")       # 抬笔
                current_pen = c['pen']

            gcode_lines.append(f"G1 X{c['x']:.2f} Y{c['y']:.2f}")
    gcode_lines.append("G0 Z1 F10000")
    with open(file_path, 'w') as f:
        f.write('\n'.join(gcode_lines))
    print(f"\n✅ G-code saved to {file_path}")

    # === 输出结构体数组 ===
    file_name = os.path.splitext(os.path.basename(file_path))[0]  # 获取文件名，不含扩展名
    print( f"\nconst GCode_t {file_name}[] = {{")
    for c in coords:
        print(f"    {GCode_t(c['x'], c['y'], c['pen'])},")
    print("};\n")


# === 选择新 G-code 文件 ===
def choose_new_gcode_path():
    Tk().withdraw()  # 不显示主窗口
    new_gcode_path = askopenfilename(filetypes=[("G-code files", "*.gcode")])  # 选择文件
    return new_gcode_path if new_gcode_path else gcode_path

# === 主程序 ===
if __name__ == '__main__':
    global gcode_path  # 声明为全局变量
    global dp
    gcode_path = '../2025-06-08-gcode-78/big_gcode/gcode_1.gcode'  # 初始路径
    base_name = os.path.splitext(os.path.basename(gcode_path))[0]
    save_path = os.path.join(os.path.dirname(gcode_path), base_name + "_fix.gcode")

    with open(gcode_path, 'r') as f:
        gcode_text = f.read()

    coords, segments = parse_gcode(gcode_text)

    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)

    ax.set_title("Editable G-code Path")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)
    ax.set_xlim(min(c['x'] for c in coords) - 5, max(c['x'] for c in coords) + 5)
    ax.set_ylim(min(c['y'] for c in coords) - 5, max(c['y'] for c in coords) + 5)

    dp = DraggablePoints(ax, coords, segments)

    ax_save = plt.axes([0.8, 0.05, 0.1, 0.075])
    btn_save = Button(ax_save, 'Save')

    def on_save(event):
        save_gcode_and_generate_struct(dp.coords, save_path)

    btn_save.on_clicked(on_save)

    # "选择文件"按钮，放置在保存按钮的左边
    ax_choose = plt.axes([0.55, 0.05, 0.2, 0.075])  # 修改位置
    btn_choose = Button(ax_choose, 'Choose File')

    def on_choose(event):
        global gcode_path, save_path  # 使用 global 关键字
        global dp
        new_path = choose_new_gcode_path()  # 选择新路径
        if new_path:  # 如果有选中的文件
            gcode_path = new_path  # 更新全局变量 gcode_path
            base_name = os.path.splitext(os.path.basename(gcode_path))[0]  # 更新 base_name
            save_path = os.path.join(os.path.dirname(gcode_path), base_name + "_fix.gcode")  # 重新计算 save_path

            with open(gcode_path, 'r') as f:
                gcode_text = f.read()
            coords, segments = parse_gcode(gcode_text)

            # 清除并更新图形
            ax.clear()
            ax.set_title(f"Editable G-code Path ({gcode_path})")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.grid(True)
            ax.set_xlim(min(c['x'] for c in coords) - 5, max(c['x'] for c in coords) + 5)
            ax.set_ylim(min(c['y'] for c in coords) - 5, max(c['y'] for c in coords) + 5)

            # 清除旧的事件连接
            dp.clear_events()

            # 重新初始化 DraggablePoints 实例
            dp = DraggablePoints(ax, coords, segments)
            plt.draw()

    btn_choose.on_clicked(on_choose)

    plt.show()
