import re

def adjust_gcode_coordinates(input_path, output_path, x_offset=800, y_offset=200):
    with open(input_path, 'r') as f:
        lines = f.readlines()

    adjusted_lines = []
    for line in lines:
        # 查找X和Y坐标
        x_match = re.search(r'X([-+]?[0-9]*\.?[0-9]+)', line)
        y_match = re.search(r'Y([-+]?[0-9]*\.?[0-9]+)', line)

        if x_match:
            x_value = float(x_match.group(1))
            new_x = x_value + x_offset
            line = re.sub(r'X([-+]?[0-9]*\.?[0-9]+)', f'X{new_x:.3f}', line)

        if y_match:
            y_value = float(y_match.group(1))
            new_y = y_value + y_offset
            line = re.sub(r'Y([-+]?[0-9]*\.?[0-9]+)', f'Y{new_y:.3f}', line)

        adjusted_lines.append(line)

    with open(output_path, 'w') as f:
        f.writelines(adjusted_lines)

# 示例调用方式，替换成你自己的路径：
input_file = r'gcode/wang.gcode'
output_file = r'./gcode/wang_adjusted.gcode'
adjust_gcode_coordinates(input_file, output_file)
