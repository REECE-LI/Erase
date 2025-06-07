from PIL import Image, ImageDraw

# 图像尺寸和点间距
num_points = 14
spacing_mm = 5  # 5mm 间距
dpi = 300  # 设定分辨率为 300 DPI
spacing_inch = spacing_mm / 25.4  # 将毫米转换为英寸

# 图像尺寸（计算需要的图像尺寸）
image_size = (num_points - 1) * spacing_inch * dpi  # 图像宽度和高度

# 增加留白区域（单位是像素）
margin_mm = 10  # 留白区域为 10mm
margin_inch = margin_mm / 25.4  # 留白区域转换为英寸
margin_pixels = margin_inch * dpi  # 留白区域转换为像素

# 计算图像的最终尺寸
final_image_size = image_size + 2 * margin_pixels  # 加上左右、上下的留白

# 创建空白白色图像（添加留白）
image = Image.new('RGB', (int(final_image_size), int(final_image_size)), 'white')
draw = ImageDraw.Draw(image)

# 计算每个点的坐标并绘制
for i in range(num_points):
    for j in range(num_points):
        # 计算点的位置，增加留白的偏移量
        x = margin_pixels + i * spacing_inch * dpi
        y = margin_pixels + j * spacing_inch * dpi
        # 绘制黑色圆点（点的半径为1mm，转换为像素）
        radius = dpi * 1 / 25.4  # 1mm的半径转换为像素
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill='black')

# 保存图像为PNG格式
image.save('14x14_grid_with_margin.png')

print("图像已保存为 '14x14_grid_with_margin.png'")
