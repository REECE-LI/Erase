import cv2

# 打开默认摄像头（0表示 /dev/video0）
cap = cv2.VideoCapture(6)

# 设置摄像头捕获分辨率
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)  # 设置宽度
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)  # 设置高度

# 检查是否成功打开摄像头
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 创建一个窗口并设置窗口大小
cv2.namedWindow('Camera', cv2.WINDOW_NORMAL)  # 必须设置为 WINDOW_NORMAL 才能改变大小
cv2.resizeWindow('Camera', 1280, 720)  # 设置窗口大小为 1280x720

# 循环读取每一帧
while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取画面")
        break

    # 显示这一帧
    cv2.imshow('Camera', frame)

    # 按 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头资源并关闭窗口
cap.release()
cv2.destroyAllWindows()
