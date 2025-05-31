import os
import subprocess
import argparse

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
        "-vf", "scale=240:320",  # 设置分辨率
        "-c:v", "mjpeg",  # 使用 MJPEG 编码
        "-pix_fmt", "yuvj420p",  # 设置像素格式
        "-aspect", "3:4",  # 设置显示宽高比
        "-g", "1",  # 设置 GOP（I 帧间隔）为 1，确保每帧都是 I 帧
        f"{output_file_base}_%03d.jpg"  # 输出文件名格式
    ]
    
    # 执行 FFmpeg 命令
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"转换完成，输出文件保存在：{output_folder}")
    except subprocess.CalledProcessError as e:
        print(f"转换失败：{e}")
    except Exception as e:
        print(f"发生错误：{e}")

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="使用 FFmpeg 转换视频文件为 JPG 图片序列。")
    parser.add_argument("input_file", type=str, help="输入视频文件路径")
    parser.add_argument("output_base_folder", type=str, help="输出文件夹的基路径")
    parser.add_argument("frame_rate", type=int, help="目标帧率（如 15fps）")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 调用转换函数
    convert_video(args.input_file, args.output_base_folder, args.frame_rate)

if __name__ == "__main__":
    main()
    # python convert_video.py test.mp4 output 15