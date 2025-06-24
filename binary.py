import cv2

# 1. 读取图像（灰度模式）
image = cv2.imread('picture/orange.jpg', cv2.IMREAD_GRAYSCALE)

# 2. 应用二值化处理（阈值为127，最大值为255）
_, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# 3. 显示原图和二值化图像
cv2.imshow('Original', image)
cv2.imshow('Binary', binary)

# 4. 保存二值化图像
cv2.imwrite('picture/orange_binary_output.jpg', binary)

# 5. 等待按键并关闭窗口
cv2.waitKey(0)
cv2.destroyAllWindows()
