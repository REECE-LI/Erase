import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import re


# === 解析 G-code 坐标并识别抬笔落笔 ===
def parse_gcode(gcode):
    lines = gcode.splitlines()
    coords = []
    pen_down = False

    last_x, last_y = None, None
    path_segments = []  # [(x0, y0), (x1, y1), pen_down]

    for line in lines:
        line = line.strip()
        if line.startswith(';') or not line:
            continue

        if 'Z' in line:
            z_match = re.search(r'Z([-\d.]+)', line)
            if z_match:
                z_val = float(z_match.group(1))
                pen_down = z_val <= 10000  # Z ≤ 0 表示落笔

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


# === 可拖动点类 ===
class DraggablePoints:
    def __init__(self, ax, coords, segments):
        self.ax = ax
        self.coords = coords
        self.segments = segments
        self._ind = None

        # 绘制线段
        self.lines = []
        for (x0, y0), (x1, y1), pen in segments:
            color = 'green' if pen else 'red'
            line, = ax.plot([x0, x1], [y0, y1], color=color)
            self.lines.append(line)

        # 绘制点
        self.points = ax.plot([c['x'] for c in coords], [c['y'] for c in coords], 'o', color='blue')[0]

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

        # 重新绘制线段
        for i, ((_, _), (_, _), pen) in enumerate(self.segments):
            if i + 1 >= len(self.coords):
                continue
            x0, y0 = self.coords[i]['x'], self.coords[i]['y']
            x1, y1 = self.coords[i+1]['x'], self.coords[i+1]['y']
            self.lines[i].set_data([x0, x1], [y0, y1])

        self.ax.figure.canvas.draw()


# === 保存 G-code ===
def save_gcode(coords, file_path):
    gcode_lines = []
    current_pen = False  # 初始为抬笔状态（Z < 10000）

    gcode_lines.append(f"G1 X{coords[0]['x']:.2f} Y{coords[0]['y']:.2f}")
    for i, c in enumerate(coords):
        if i == 0:
            # 起始移动前状态判断
            if c['pen']:
                gcode_lines.append("G0 Z1 F10000")
                current_pen = True
            else:
                gcode_lines.append("G0 Z22000 F10000")
                current_pen = False

            cmd = "G1"
            gcode_lines.append(f"{cmd} X{c['x']:.2f} Y{c['y']:.2f}")
        else:
            # 检查是否状态变更
            if current_pen != c['pen']:
                if c['pen']:
                    gcode_lines.append("G0 Z1 F10000")  # 落笔
                else:
                    gcode_lines.append("G0 Z22000 F10000")       # 抬笔
                current_pen = c['pen']

            cmd = "G1"
            gcode_lines.append(f"{cmd} X{c['x']:.2f} Y{c['y']:.2f}")

    with open(file_path, 'w') as f:
        f.write('\n'.join(gcode_lines))
    print(f"G-code saved to {file_path}")



# === 主程序 ===
if __name__ == '__main__':
    gcode_path = './gcode/hanzi-jian.gcode'
    save_path = './gcode/hanzi-jian-edited.gcode'

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

    # 保存按钮
    ax_save = plt.axes([0.8, 0.05, 0.1, 0.075])
    btn_save = Button(ax_save, 'Save')

    def on_save(event):
        save_gcode(dp.coords, save_path)

    btn_save.on_clicked(on_save)

    plt.show()
