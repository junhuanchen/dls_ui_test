"""
wav2pcm_carray.py
pip install numpy
"""

import wave
import numpy as np
import sys
import os

# ffmpeg -i input.wav -ac 1 -ar 8000 -sample_fmt u8 -acodec pcm_u8 output.wav
# ========= 用户参数 =========
WAV_FILE   = "output.wav"      # 输入文件
ARRAY_NAME = "audioData"      # C 数组名字
LINE_BYTES = 12               # 每行打印多少个数（排版好看）
OUT_H      = "audioData.h"    # 生成的头文件名
# ============================

# 1. 读取 wav
with wave.open(WAV_FILE, "rb") as wf:
    params = wf.getparams()
    if params.nchannels != 1 or params.sampwidth != 1 or params.framerate != 8000:
        raise ValueError("仅支持 8-bit unsigned / mono / 8 kHz")
    pcm = wf.readframes(params.nframes)

# 2. 转为 8-bit 无符号 numpy 数组
samples = np.frombuffer(pcm, dtype=np.uint8)

# 3. 生成 C 字符串
lines = []
for i in range(0, len(samples), LINE_BYTES):
    chunk = ", ".join(str(x) for x in samples[i:i+LINE_BYTES])
    lines.append(chunk)

c_code = f"""\
// Auto-generated from {os.path.basename(WAV_FILE)}
const uint8_t {ARRAY_NAME}[] = {{
{chr(10).join('  ' + ln + ',' for ln in lines)}
}};
const size_t {ARRAY_NAME}_LEN = sizeof({ARRAY_NAME});
"""

# 4. 输出
if OUT_H:
    with open(OUT_H, "w", encoding="utf-8") as f:
        f.write(c_code)
    print(f"已写入 {OUT_H}")
else:
    print(c_code)