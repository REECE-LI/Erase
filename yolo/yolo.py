import cv2
from ultralytics import YOLO

# 加载 YOLOv8 模型
model = YOLO("best.pt")  # 使用小型模型，也可以使用 yolov8s.pt、yolov8m.pt、yolov8l.pt、yolov8x.pt 等

# 打开默认摄像头（0 为默认摄像头）
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 对视频帧进行推理
    results = model(frame)

    # 绘制检测结果
    annotated_frame = results[0].plot()  # 绘制框并标注

    # 显示带有检测框的视频
    cv2.imshow("YOLOv8 Camera Detection", annotated_frame)

    # 按 'q' 键退出视频窗口
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
