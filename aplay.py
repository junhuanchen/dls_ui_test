# =================== audio_player.py ===================
from fpioa_manager import fm
from Maix import I2S, GPIO
import audio
import gc
import time

# # ---------- 硬件一次性初始化 ----------
# fm.register(8,  fm.fpioa.GPIO0, force=True)
# fm.register(32, fm.fpioa.GPIO1, force=True)
# tmp = GPIO(GPIO.GPIO0, GPIO.OUT); tmp.value(0)
# tmp = GPIO(GPIO.GPIO1, GPIO.OUT); tmp.value(1)

# fm.register(34, fm.fpioa.I2S0_OUT_D1, force=True)
# fm.register(35, fm.fpioa.I2S0_SCLK,   force=True)
# fm.register(33, fm.fpioa.I2S0_WS,     force=True)

# ---------- 硬件一次性初始化 ----------
fm.register(9,  fm.fpioa.GPIO0, force=True)
fm.register(10, fm.fpioa.GPIO1, force=True)
tmp = GPIO(GPIO.GPIO0, GPIO.OUT); tmp.value(0)
tmp = GPIO(GPIO.GPIO1, GPIO.OUT); tmp.value(1)

fm.register(11, fm.fpioa.I2S0_OUT_D1, force=True)
fm.register(12, fm.fpioa.I2S0_SCLK,   force=True)
fm.register(13, fm.fpioa.I2S0_WS,     force=True)

_i2s = I2S(I2S.DEVICE_0)

# ---------- 模块级变量 ----------
_player      = None    # audio.Audio
_path        = None    # 当前正在播放的文件
_on_finish   = None    # 播完回调

# ---------- 内部工具 ----------
def _stop():
    """真正清理资源的地方"""
    global _player, _on_finish
    if _player:
        _player.finish()
        time.sleep_ms(20)
        _player = None
    gc.collect()
    if _on_finish:
        cb = _on_finish
        _on_finish = None   # 先清掉，防止递归
        cb()

# ---------- 对外 API ----------
def play(path, callback=None):
    """播放 wav；播完自动调用 callback"""
    global _player, _path, _on_finish

    stop()                   # 先停掉之前的
    _path = path
    _on_finish = callback

    # 打开文件
    _player = audio.Audio(path=path)
    _player.volume(100)
    wav_info = _player.play_process(_i2s)
    _i2s.channel_config(_i2s.CHANNEL_1, _i2s.TRANSMITTER,
                        resolution=_i2s.RESOLUTION_16_BIT,
                        cycles=_i2s.SCLK_CYCLES_32,
                        align_mode=_i2s.STANDARD_MODE)
    _i2s.set_sample_rate(wav_info[1])

def stop():
    """强制停止当前播放"""
    _stop()

def is_playing():
    return _player is not None

def tick():
    """需要在 while True: 中周期性调用"""
    global _player
    if _player is None:
        return

    ret = _player.play()
    if ret is None:          # 格式错误
        _stop()
    elif ret == 0:           # 播完
        _stop()
    # ret > 0 继续播放，不做任何动作

# ---------- 简单的单测 ----------
def unit_test_play(tmp='/sd/6.wav'):
    def done():
        print('3')
    play(tmp, callback=done)
    print('1')
    while is_playing():
        tick()
    print('2')
