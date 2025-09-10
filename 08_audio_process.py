import os
import subprocess

def convert_wav_files(input_folder, output_folder):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if filename.endswith(".mp3"):
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + ".wav"# + "_converted.wav"
            output_path = os.path.join(output_folder, output_filename)

            # 构造 ffmpeg 命令
            command = [
                "ffmpeg",
                "-i", input_path,
                "-ac", "2",
                "-ar", "44100",
                "-sample_fmt", "s16",
                "-f", "wav",
                "-filter:a", "acompressor=threshold=-12dB:ratio=4:attack=10:release=100,volume=12dB",
                output_path
            ]

            # 调用 ffmpeg 命令
            try:
                subprocess.run(command, check=True)
                print(f"Converted {input_path} to {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting {input_path}: {e}")

# 示例用法
input_folder = "audio_gocan"
output_folder = "output_audio"
convert_wav_files(input_folder, output_folder)