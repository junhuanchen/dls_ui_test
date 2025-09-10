import os
from pypinyin import pinyin, Style

def to_pinyin(file_name):
    # 提取文件名和扩展名
    name, ext = os.path.splitext(file_name)
    # 将中文转换为拼音
    pinyin_name = ''.join([word[0] for word in pinyin(name, style=Style.NORMAL)])
    return f"{pinyin_name}{ext}"

def rename_files_to_pinyin(folder_path):
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 构造完整的文件路径
        old_file_path = os.path.join(folder_path, filename)
        # 检查是否为文件
        if os.path.isfile(old_file_path):
            # 转换文件名为拼音
            new_filename = to_pinyin(filename)
            # new_filename = filename.split("成品")[1]
            new_file_path = os.path.join(folder_path, new_filename)
            # 重命名文件
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {filename} -> {new_filename}")

# 示例：将指定文件夹中的所有文件名转换为拼音
folder_path = r"audio_gocan"  # 替换为你的文件夹路径
rename_files_to_pinyin(folder_path)