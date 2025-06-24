import cv2
import numpy as np
from tkinter import Tk, filedialog


def nothing(x):
    pass


# ———— 1. 弹出文件对话框选择叠加图片 ————
root = Tk()
root.withdraw()  # 隐藏主窗口
file_path = filedialog.askopenfilename(
    title="选择要叠加的图片",
    filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files", "*.*")]
)
if not file_path:
    print("⚠️ 未选择任何文件，程序退出")
    exit(0)

# 读取图片（保留 alpha 通道如果有）
overlay = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
if overlay is None:
    print(f"⚠️ 无法加载图片: {file_path}")
    exit(1)

# 分离 BGR 和 Alpha（如果有）
if overlay.shape[2] == 4:
    bgr_ov = overlay[..., :3]
    alpha_ov = overlay[..., 3] / 255.0
else:
    bgr_ov = overlay
    alpha_ov = None

# ———— 2. 打开摄像头并设置 MJPG + 高分辨率 ————
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("⚠️ 无法打开摄像头")
    exit(1)

# 强制 MJPG 模式并设置分辨率 3824×2144
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

# 读取首帧确认分辨率
ret, frame = cap.read()
if not ret:
    print("⚠️ 读取首帧失败")
    cap.release()
    exit(1)
h_f, w_f = frame.shape[:2]
print(f"已设置分辨率：{w_f}×{h_f}")

# ———— 3. 创建可缩放窗口和滑动条 ————
win = 'Overlay'
cv2.namedWindow(win, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.resizeWindow(win, 1280, 720)  # 可根据需要调整初始窗口大小

cv2.createTrackbar('Scale %', win, 100, 200, nothing)  # 叠加图缩放比例：0–200%
cv2.createTrackbar('Overlay Opacity %', win, 100, 100, nothing)  # 叠加图透明度：0–100%
cv2.createTrackbar('Pos X', win, 0, w_f, nothing)  # 叠加图 X 坐标
cv2.createTrackbar('Pos Y', win, 0, h_f, nothing)  # 叠加图 Y 坐标

# ———— 4. 主循环：读取摄像头、调整叠加并显示 ————
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 4.1 读取滑动条参数
    scale = cv2.getTrackbarPos('Scale %', win) / 100.0
    overlay_op = cv2.getTrackbarPos('Overlay Opacity %', win) / 100.0
    pos_x = cv2.getTrackbarPos('Pos X', win)
    pos_y = cv2.getTrackbarPos('Pos Y', win)

    # 4.2 缩放叠加图并应用透明度
    h_ov, w_ov = bgr_ov.shape[:2]
    new_w = max(1, int(w_ov * scale))
    new_h = max(1, int(h_ov * scale))
    ov_resized = cv2.resize(bgr_ov, (new_w, new_h), interpolation=cv2.INTER_AREA)
    if alpha_ov is not None:
        alpha_resized = cv2.resize(alpha_ov, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        alpha_resized = np.ones((new_h, new_w), dtype=float)
    alpha_resized *= overlay_op  # 只改变叠加图透明度

    # 4.3 计算叠加区域 ROI 并裁剪边界
    x1, y1 = pos_x, pos_y
    x2, y2 = x1 + new_w, y1 + new_h
    x1c, y1c = max(0, x1), max(0, y1)
    x2c, y2c = min(w_f, x2), min(h_f, y2)
    ov_x1, ov_y1 = x1c - x1, y1c - y1
    ov_x2 = ov_x1 + (x2c - x1c)
    ov_y2 = ov_y1 + (y2c - y1c)

    # 4.4 叠加混合
    roi_bg = frame[y1c:y2c, x1c:x2c]
    roi_ov = ov_resized[ov_y1:ov_y2, ov_x1:ov_x2]
    alpha_m = alpha_resized[ov_y1:ov_y2, ov_x1:ov_x2][:, :, None]
    frame[y1c:y2c, x1c:x2c] = (alpha_m * roi_ov + (1 - alpha_m) * roi_bg).astype(np.uint8)

    # 4.5 显示 & 退出控制
    cv2.imshow(win, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 清理
cap.release()
cv2.destroyAllWindows()
