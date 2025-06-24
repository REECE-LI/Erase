import os
import shutil
import re

# 设置源目录和目标根目录
src_dir = ("C:\\Users\\L2248\\Downloads\\yun")      # 原始照片所在目录
dst_root = ("C:\\Users\\L2248\\Downloads\\yun\\yun_sort")     # 输出的根目录

photos_per_folder = 10          # 每个小文件夹的照片数
folders_per_big_folder = 10     # 每个大文件夹的小文件夹数

# 1. 获取所有图片文件名
photos = [
    f for f in os.listdir(src_dir)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]

# 2. 定义一个函数：从文件名末尾提取数字
def extract_index(filename):
    name, _ = os.path.splitext(filename)
    m = re.search(r"(\d+)$", name)   # 匹配 最后 一个连续数字串
    if m:
        return int(m.group(1))
    else:
        # 如果没匹配到，放到最后面
        return float('inf')

# 3. 按提取到的数字排序
photos.sort(key=extract_index)

# 4. 遍历并移动
for idx, photo in enumerate(photos):
    small_i = idx // photos_per_folder
    big_i   = small_i // folders_per_big_folder

    big_folder   = os.path.join(dst_root, f"big_folder_{big_i}")
    small_folder = os.path.join(big_folder, f"folder_{small_i}")

    os.makedirs(small_folder, exist_ok=True)
    shutil.copy(
        os.path.join(src_dir, photo),
        os.path.join(small_folder, photo)
    )

print("整理完毕！")