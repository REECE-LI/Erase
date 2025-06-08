class GCode_t:
    def __init__(self, x=0.0, y=0.0, isPen=False):
        self.x = round(x, 2)  # Round to two decimal places
        self.y = round(y, 2)  # Round to two decimal places
        self.isPen = isPen

    def __repr__(self):
        return f"{{{self.x}f, {self.y}f, {str(self.isPen).lower()}}}"


def generate_gcode_for_cpp_structure_from_file(gcode_file):
    gcode_structures = []
    is_pen_down = False
    last_move = None  # To store the last move before pen up

    # Read the G-code file
    with open(gcode_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if 'G0' in line:
            is_pen_down = 'Z22000' in line  # Check if it's a pen down or pen up
        elif 'G1' in line:
            parts = line.split()
            x = float(parts[1][1:]) if 'X' in parts[1] else 0.0
            y = float(parts[2][1:]) if 'Y' in parts[2] else 0.0
            # Round the coordinates to two decimal places
            gcode_structures.append(GCode_t(round(x, 2), round(y, 2), isPen=is_pen_down))
            last_move = (x, y, is_pen_down)  # Store the last G1 move

    # Ensure that the last movement only raises the pen without moving the position
    if last_move:
        gcode_structures.append(GCode_t(last_move[0], last_move[1], isPen=False))  # Raise pen without moving

    return gcode_structures


if __name__ == '__main__':
    # Path to the .gcode file you uploaded
    gcode_file_path = '../gcode/hanzi-jian-edited.gcode'

    # Generate corresponding GCode_t structures from the G-code file
    gcode_structures = generate_gcode_for_cpp_structure_from_file(gcode_file_path)

    # Print the C++ array in the desired format
    print("GCode_t gcodeBuff[] = {")
    for item in gcode_structures:
        print(f"    {item},")
    print("};")
