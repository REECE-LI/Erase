from PIL import Image, ImageDraw
import matplotlib.pyplot as plt


PALETTE = {
    "dark_blue":    ( 29,  63, 137),
    "golden_yellow":(212, 160,  23),
    "orange_yellow":(227, 168,  35),
    "light_blue":   (102, 204, 255),
}

def nearest_color(rgb):
    """返回 rgb 在 PALETTE 中最接近的颜色（欧氏距离）。"""
    r, g, b = rgb
    best = None
    best_d2 = None
    for name, (pr, pg, pb) in PALETTE.items():
        d2 = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
        if best_d2 is None or d2 < best_d2:
            best_d2 = d2
            best = (pr, pg, pb)
    return best


# 1. 加载原始图像
orig = Image.open('./dark_blue.png').convert('RGB')

# 2. 网格参数：200cm x 100cm，点距8mm ⇒ 横向250点，纵向125点
grid_w, grid_h = 2000 // 8, 1000 // 8  # 250, 125
thumb = orig.resize((grid_w, grid_h), Image.LANCZOS)

# 3. 创建白底画板，1像素 = 1mm ⇒ 2000x1000像素
canvas = Image.new('RGB', (2000, 1000), (255, 255, 255))
draw = ImageDraw.Draw(canvas)

# 4. 在每个网格点位置绘制小圆点，采样颜色
radius = 3  # 半径3像素
for j in range(grid_h):
    for i in range(grid_w):
        color = thumb.getpixel((i, j))
        cx, cy = i * 8 + 4, j * 8 + 4  # 点心位置向内偏移4像素
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)

# canvas.save('dots_200x100cm.png')

# 5. 显示结果
plt.figure(figsize=(10, 5), dpi=1000)
plt.imshow(canvas)
plt.axis('off')
plt.title('200cm×100cm 点阵图（8mm间距）')
plt.show()
