import cv2
import matplotlib.pyplot as plt
import numpy as np


def find_and_sort_black_spots(input_path):
    # 加载图像（灰度模式）
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

    # 使用大金法进行二值化
    ret, binary_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 膨胀白色背景
    kernel = np.ones((10, 10), np.uint8)  # 定义膨胀的结构元素
    dilated_img = cv2.dilate(binary_img, kernel, iterations=1)

    dilated_img = cv2.bitwise_not(dilated_img)  # 反转图像，将黑色区域转为前景，白色区域转为背景
    # show dilated_img
    plt.imshow(dilated_img, cmap='gray')
    plt.axis('on')  # 关闭坐标轴
    plt.show()


    # 查找轮廓
    contours, _ = cv2.findContours(dilated_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)  # 转为彩色图以便显示

    # 存储黑色块的重心和宽度
    centroids = []

    for contour in contours:
        # 获取轮廓的边界框，计算宽度
        x, y, w, h = cv2.boundingRect(contour)

        # 计算重心
        moments = cv2.moments(contour)
        if moments["m00"] != 0:
            cX = int(moments["m10"] / moments["m00"])
            cY = int(moments["m01"] / moments["m00"])

            centroids.append((cX, cY, contour, w))

    # 按 y 坐标（行数）对重心进行分组
    centroids.sort(key=lambda x: x[1], reverse=True)  # 从下到上排序

    # 存储每行的坐标
    rows = []
    current_y = None
    row = []

    # 按行分组
    for cX, cY, contour, w in centroids:
        if current_y is None or abs(current_y - cY) < 20:  # y坐标相近的点在同一行
            row.append((cX, cY, contour, w))
        else:
            rows.append(sorted(row, key=lambda x: x[0], reverse=True))  # 按x坐标排序，从右到左
            row = [(cX, cY, contour, w)]  # 新的一行
        current_y = cY
    rows.append(sorted(row, key=lambda x: x[0], reverse=True))  # 处理最后一行

    # 创建一个 Lut_t 数组来存储点信息
    Lut = []
    label = 0

    # 计算targetPoint的目标点
    first_point = (rows[0][0][0], rows[0][0][1])  # 第一个点的坐标 (cX, cY)
    last_point = (rows[-1][-1][0], rows[-1][-1][1])  # 第255个点的坐标 (cX, cY)

    print("First point:", first_point)
    print("Last point:", last_point)

    # 计算两点之间的距离差
    delta_x = (last_point[0] - first_point[0]) / 14
    delta_y = (last_point[1] - first_point[1]) / 14

    deltaDistance = (abs(delta_x) + abs(delta_y)) * 0.5

    k = 5 / deltaDistance
    if delta_x > 0:
        delta_x = deltaDistance
    else:
        delta_x = -deltaDistance

    if delta_y > 0:
        delta_y = deltaDistance
    else:
        delta_y = -deltaDistance

    print(delta_x, delta_y)

    # 第99号点的行列坐标
    base_index = 98
    base_row = base_index // 15  # 6
    base_col = base_index % 15  # 8

    # 假设你已经知道第99号点的位置是 base_point
    base_point = (rows[6][8][0], rows[6][8][1])  # 你需要把这里替换成第99号点的实际坐标

    for row in rows:
        for cX, cY, contour, w in row:

            # 当前label要计算的目标点
            target_cX = round(base_point[0] + delta_x * ((label % 15) - base_col)-15, 2)
            target_cY = round(base_point[1] + delta_y * ((label // 15) - base_row), 2)

            # 计算deltaX和deltaY
            deltaX = round((cX - target_cX) * k, 2)
            deltaY = round((cY - target_cY) * k, 2)

            # 创建一个 Lut_t 结构体并添加到 Lut 数组中
            lut_point = {
                "drawPoint": {"x": float(cX), "y": float(cY)},
                "targetPoint": {"x": float(target_cX), "y": float(target_cY)},
                "deltaX": deltaX,
                "deltaY": deltaY
            }
            Lut.append(lut_point)

            # 输出到控制台
            print(f"Black spot {label} at ({cX}, {cY}), Width: {w}, Target: ({target_cX}, {target_cY}), "
                  f"deltaX: {deltaX}, deltaY: {deltaY}")

            # 在重心位置绘制红色圆点
            cv2.circle(color_img, (cX, cY), 20, (0, 0, 255), -1)  # 红色圆点，半径为5
            cv2.circle(color_img, (int(target_cX), int(target_cY)), 20, (0, 255, 0), -1)
            # 在重心位置添加标号
            cv2.putText(color_img, str(label), (cX + 10, cY), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

            # 增加标号
            label += 1

    # 将 Lut 数组打印为 C++ 代码格式
    print("\nC++ Code Output:")
    print("Lut_t Lut[255] = {")
    for lut_point in Lut:
        print(f"    {{ {{ {lut_point['drawPoint']['x']}, {lut_point['drawPoint']['y']} }}, "
              f"{{ {lut_point['targetPoint']['x']}, {lut_point['targetPoint']['y']} }}, "
              f"{lut_point['deltaX']}, {lut_point['deltaY']} }},")
    print("};")

    # 显示最终图像
    plt.imshow(cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB))
    plt.axis('on')  # 关闭坐标轴
    plt.show()


# 使用示例
input_image = ('./picture/20250616-155647.jpg')  # 输入图片路径
find_and_sort_black_spots(input_image)
