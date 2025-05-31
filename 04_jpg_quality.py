from PIL import Image
import os

def modify_image_quality(input_folder, output_folder, quality):
    """
    修改文件夹中所有 JPG 图像的质量
    :param input_folder: 输入文件夹路径
    :param output_folder: 输出文件夹路径
    :param quality: 图像质量（1-100，值越高，质量越好）
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有 JPG 文件
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".jpg"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # 打开图像
            with Image.open(input_path) as img:
                # 保存图像并设置质量
                img.save(output_path, format="JPEG", quality=quality)
                print(f"Processed {filename} with quality {quality}")

# 示例调用
input_folder = "03_base_jpgs"  # 替换为你的输入文件夹路径
output_folder = "_03_base_jpgs"  # 替换为你的输出文件夹路径
quality = 50  # 设置图像质量（1-100）

modify_image_quality(input_folder, output_folder, quality)