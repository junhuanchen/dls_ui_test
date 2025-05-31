import os
import subprocess

def convert_bmp_to_rgb565(input_folder, output_folder):
    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        # 检查文件是否为 BMP 格式
        if filename.lower().endswith('.bmp'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # 使用 FFmpeg 命令进行格式转换
            command = [
                'ffmpeg',
                '-i', input_path,  # 输入文件
                '-pix_fmt', 'rgb565',  # 设置像素格式为 RGB565
                output_path  # 输出文件
            ]

            try:
                subprocess.run(command, check=True)
                print(f"Converted {filename} to RGB565 format successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error converting {filename}: {e}")

if __name__ == "__main__":
    input_folder = "cccc"  # 替换为你的输入文件夹路径
    output_folder = "dddd"  # 替换为你的输出文件夹路径
    convert_bmp_to_rgb565(input_folder, output_folder)