import wave
import numpy as np
import librosa

# 频率到音符映射表（基于A4=440Hz，12平均律）
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
def freq_to_note(f):
    if f <= 0:
        return 'p', 4  # 休止符
    h = round(12 * np.log2(f / 440) + 69)
    octave = (h // 12) - 1
    note = NOTE_NAMES[h % 12]
    return note, octave

# 量化时值
def quantize_duration(sec, bpm=120):
    beat_dur = 60 / bpm
    dur = sec / beat_dur
    if dur <= 0.125:
        return 32
    elif dur <= 0.25:
        return 16
    elif dur <= 0.5:
        return 8
    elif dur <= 1:
        return 4
    elif dur <= 2:
        return 2
    else:
        return 1

# 读取wav并转为RTTTL
def wav_to_rtttl(wav_path, title="MyTune", bpm=120):
    y, sr = librosa.load(wav_path, sr=None)
    hop_length = int(sr * 0.1)  # 每100ms一帧
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)

    notes = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        freq = pitches[index, t]
        note, octave = freq_to_note(freq)
        duration = hop_length / sr
        dur = quantize_duration(duration, bpm)
        notes.append(f"{dur}{note}{octave}")

    body = ",".join(notes)
    return f"{title}:d=4,o=5,b={bpm}:{body}"

# 示例使用
if __name__ == "__main__":
    rtttl_str = wav_to_rtttl("input.wav", title="MySong", bpm=120)
    print("RTTTL Output:\n")
    print(rtttl_str)
    