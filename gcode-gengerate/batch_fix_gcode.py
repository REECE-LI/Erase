import re
import os


# === GCode_t 结构体类 ===
class GCode_t:
    def __init__(self, x=0.0, y=0.0, isPen=False):
        self.x = round(x, 2)
        self.y = round(y, 2)
        self.isPen = isPen

    def __repr__(self):
        return f"{{{self.x}f, {self.y}f, {str(self.isPen).lower()}}}"


# === G-code 解析（识别落笔/抬笔）===
def parse_gcode(gcode_text):
    lines = gcode_text.splitlines()
    coords = []
    pen_down = False
    last_x = last_y = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith(';'):
            continue

        # 检测 Z 值决定笔触
        if 'Z' in line:
            m = re.search(r'Z([-\d.]+)', line)
            if m:
                pen_down = float(m.group(1)) >= 10000

        if line.startswith(('G0', 'G1')):
            mx = re.search(r'X([-\d.]+)', line)
            my = re.search(r'Y([-\d.]+)', line)
            if mx and my:
                x = float(mx.group(1))
                y = float(my.group(1))
                coords.append({'x': x, 'y': y, 'pen': pen_down})
                last_x, last_y = x, y

    return coords


# === 保存修正后的 G-code 并输出结构体 ===
def save_and_print_struct(coords, orig_path):
    dirname, fn = os.path.split(orig_path)
    base, _ = os.path.splitext(fn)
    fix_fn = base + "_fix.gcode"
    fix_path = os.path.join(dirname, fix_fn)

    # —— 写入修正后的 G-code ——
    lines = []
    if coords:
        # 初始移动不提笔
        lines.append(f"G1 X{coords[0]['x']:.2f} Y{coords[0]['y']:.2f}")
        cur_pen = coords[0]['pen']
        # 笔状态指令
        lines.insert(1, "G0 Z22000 F10000" if cur_pen else "G0 Z1 F10000")
    for c in coords:
        # 状态切换
        if c['pen'] != cur_pen:
            cur_pen = c['pen']
            lines.append("G0 Z22000 F10000" if cur_pen else "G0 Z1 F10000")
        lines.append(f"G1 X{c['x']:.2f} Y{c['y']:.2f}")
    lines.append("G0 Z1 F10000")

    with open(fix_path, 'w') as f:
        f.write('\n'.join(lines))
    # print(f"✅ Saved fixed G-code to: {fix_path}")

    # —— 输出 C++ 数组 ——
    struct_name = f"{base}_hello"
    print(f"\nconst GCode_t {struct_name}[] = {{")
    for c in coords:
        print(f"    {GCode_t(c['x'], c['y'], c['pen'])},")
    print("};\n")


if __name__ == '__main__':
    # 假设所有 gcode 文件都在同一目录下，路径根据需要修改
    gcode_dir = '../2025-06-08-gcode-78/helloworld_gcode'
    for i in range(1, 8):
        src = os.path.join(gcode_dir, f"gcode_{i}.gcode")
        if not os.path.isfile(src):
            print(f"⚠️  File not found: {src}")
            continue
        with open(src, 'r') as f:
            txt = f.read()
        coords = parse_gcode(txt)
        save_and_print_struct(coords, src)
