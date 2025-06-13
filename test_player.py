import os
import sensor, image, time, lcd
import gc, sys
from machine import Timer

lcd.init(freq=15000000)
lcd.rotation(1)

class AnimationPlayer:
    def __init__(self, prefix='', delay=100):
        self.prefix = prefix
        self.running = False
        self.current_index = 0
        self.current_directory = None
        self.files = []
        self.delay = delay  # 期望延时播放间隔（单位：毫秒）
        self.is_stopping = False  # 标记是否正在执行 stop 操作
        self.loop = False  # 是否循环播放
        self.timer = None  # 用于存储定时器对象

    def _load_files(self, directory, start_file=0, end_file=None):
        """加载指定目录中的文件"""
        try:
            files = os.listdir(directory)
            self.files = [file for file in files if file.startswith(self.prefix) and file.endswith('.jpg')]
            if not self.files:
                raise ValueError("No files found with the specified prefix in the current directory.")
            file_numbers = [int(file[len(self.prefix):-4]) for file in self.files]
            if start_file not in file_numbers:
                raise ValueError("Start file %s not found in the current directory." % start_file)
            if end_file is not None and end_file not in file_numbers:
                raise ValueError("End file %s not found in the current directory." % end_file)
            if end_file is not None and start_file > end_file:
                raise ValueError("Start file number must be less than or equal to end file number.")
            start_index = file_numbers.index(start_file)
            if end_file is None:
                self.files = self.files[start_index:]
            else:
                end_index = file_numbers.index(end_file) + 1
                self.files = self.files[start_index:end_index]
            self.current_index = 0
            self.current_directory = directory
        except Exception as e:
            sys.print_exception(e)

    def start(self, directory, start_file=0, end_file=None, loop=False):
        """开始播放动画"""
        if self.timer and self.timer.isrunning():
            self.pause()
        self._load_files(directory, start_file, end_file)
        self.running = True
        self.loop = loop
        if not self.timer or not self.timer.isrunning():
            self.timer = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=self.delay, unit=Timer.UNIT_MS, callback=self._play, arg=None, start=True, priority=1, div=0)

    def stop(self):
        """停止播放动画"""
        self.is_stopping = True  # 标记正在执行 stop 操作
        if self.timer:
            self.timer.stop()
        while self.timer.isrunning():
            time.sleep(0.01)  # 短暂等待，避免过度占用 CPU
        self.is_stopping = False

    def pause(self):
        """暂停播放动画"""
        self.running = False
        if self.timer:
            self.timer.stop()

    def resume(self):
        """恢复播放动画"""
        self.running = True
        if self.timer:
            self.timer.start()

    def _play(self, timer):
        """播放动画"""
        if not self.is_stopping:
            if self.running and self.files:
                try:
                    snapshot = None
                    file_name = self.files[self.current_index]
                    run_time = time.ticks_ms()
                    image_path = self.current_directory + '/' + file_name
                    snapshot = image.Image(image_path)
                    lcd.display(snapshot)
                    del snapshot
                    # gc.collect()
                    # print("time: %s/%s Playing: %s, Index: %s/%s" % (time.ticks_ms(), time.ticks_ms() - run_time, image_path, self.current_index, len(self.files)))
                    self.current_index += 1
                    if self.current_index >= len(self.files):
                        if self.loop:
                            self.current_index = 0
                        else:
                            self.running = False
                except Exception as e:
                    # sys.print_exception(e)
                    self.running = False
                except KeyboardInterrupt:
                    self.running = False

    def get_current_status(self):
        """获取当前播放状态"""
        status = {
            "current_directory": self.current_directory,
            "current_file": None,
            "current_index": self.current_index,
            "total_files": len(self.files),
            "is_playing": self.running,  # 是否正在播放
            "is_looping": self.loop  # 是否循环播放
        }
        if self.files and self.current_index < len(self.files):
            status["current_file"] = self.files[self.current_index]
        return status

import gocan_ai

# 示例用法
if __name__ == "__main__":
    player = AnimationPlayer(prefix='', delay=100)  # 设置期望延时播放间隔为100ms
    # for i in range(10):
    #     # 开始播放第一个目录，循环播放
    #     player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=10, loop=True)
    #     time.sleep(2)  # 播放2秒

    #     # 获取当前播放状态
    #     status = player.get_current_status()
    #     print("Current Status: %s" % status)

    #     # 切换到另一个目录并继续播放，不循环播放
    #     player.start(directory='/sd/_03_base_jpgs', start_file=200, end_file=None, loop=False)
    #     time.sleep(4)  # 再播放1秒

    #     # 停止播放
    #     player.stop()
    # 开始播放第一个目录，循环播放
    player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=10, loop=True)

    while True:
        # if gocan_ai.camera_ai_manager.have_data():
        #     print("result: ", gocan_ai.camera_ai_manager.get_data())
        time.sleep(0.1)