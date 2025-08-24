import os
import shutil
import subprocess
import argparse
from PIL import Image

def convert_video(input_file, output_base_folder, frame_rate):
    # 获取输入文件的名称（不包含扩展名）
    input_file_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # 构造输出文件夹路径
    output_folder = os.path.join(output_base_folder, input_file_name)
    
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 构造输出文件路径
    output_file_base = os.path.join(output_folder, input_file_name)
    
    # 构造 FFmpeg 命令
    ffmpeg_command = [
        "ffmpeg",
        "-i", input_file,  # 输入文件
        "-r", str(frame_rate),  # 设置帧率
        "-vf", "scale=280:240",  # 设置分辨率
        # "-vf", "crop=ih*6/7:ih,scale=280:240",
        "-c:v", "mjpeg",  # 使用 MJPEG 编码
        "-pix_fmt", "yuvj420p",  # 设置像素格式
        # "-aspect", "3:4",  # 设置显示宽高比
        "-g", "1",  # 设置 GOP（I 帧间隔）为 1，确保每帧都是 I 帧
        f"{output_file_base}_%03d.jpg"  # 输出文件名格式
    ]
    
    # 执行 FFmpeg 命令
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"转换完成，输出文件保存在：{output_folder}")
        return output_folder
    except subprocess.CalledProcessError as e:
        print(f"转换失败：{e}")
    except Exception as e:
        print(f"发生错误：{e}")

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
                
def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="从文件夹中获取所有视频文件并转换为 JPG 图片序列，然后调整 JPG 图像质量。")
    parser.add_argument("input_folder", type=str, help="输入文件夹路径")
    parser.add_argument("output_base_folder", type=str, help="输出文件夹的基路径")
    parser.add_argument("frame_rate", type=int, help="目标帧率（如 15fps）")
    parser.add_argument("image_quality", type=int, help="JPG 图像质量（1-100）")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 确保输出文件夹存在，如果存在则先删除再创建
    if os.path.exists(args.output_base_folder):
        shutil.rmtree(args.output_base_folder)  # 删除已存在的文件夹
    os.makedirs(args.output_base_folder)  # 创建新的文件夹
    
    # 遍历输入文件夹中的所有视频文件
    for filename in os.listdir(args.input_folder):
        input_file_path = os.path.join(args.input_folder, filename)
        if os.path.isfile(input_file_path) and filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            print(f"正在处理视频文件：{filename}")
            output_folder = convert_video(input_file_path, args.output_base_folder, args.frame_rate)
            if output_folder:
                modify_image_quality(output_folder, output_folder, args.image_quality)

if __name__ == "__main__":
    main()

# python process_videos.py input_folder outputs 15 95
