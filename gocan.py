
import time
import heapq

class agent:
    def __init__(self):
        self.msg = []
        self.arg = {}
        self.get_ms = (lambda: time.ticks_ms()) if getattr(time, "ticks_ms", False) else (lambda: time.time() * 1000)

    def event(self, cycle, func, args=None):
        # arrived, cycle, function
        tmp = (self.get_ms() + cycle, cycle, func, args)
        self.msg.append(tmp)

    def remove(self, func):
        for pos in range(len(self.msg)):
            if self.msg[pos][2] == func:
                self.msg.remove(self.msg[pos])
                break

    def call(self, obj, pos=0):
        self.msg.pop(pos)
        self.event(obj[1], obj[2], obj[3])
        obj[2](obj[3]) if obj[3] else obj[2]()  # exec function

    def cycle(self):
        if len(self.msg):
            obj = self.msg[0]
            if self.get_ms() >= obj[0]:
                self.call(obj, 0)

    def parallel_cycle(self):
        for pos in range(len(self.msg)):
            obj = self.msg[pos]
            if self.get_ms() >= obj[0]:
                self.call(obj, pos)
                break

import heapq

class HeapItem:
    def __init__(self, priority, data):
        self.priority = priority
        self.data = data

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def __repr__(self):
        return "HeapItem(priority={}, data={})".format(self.priority, self.data)


class PriorityQueue:
    def __init__(self):
        self.heap = []

    def push_item(self, item):
        if not isinstance(item, HeapItem):
            raise TypeError("push_item expected a HeapItem object")
        heapq.heappush(self.heap, item)

    def push(self, priority, data):
        item = HeapItem(priority, data)
        heapq.heappush(self.heap, item)

    def pop(self):
        if not self.heap:
            raise IndexError("pop from an empty priority queue")
        return heapq.heappop(self.heap)

    def peek(self):
        if not self.heap:
            raise IndexError("peek from an empty priority queue")
        return self.heap[0]

    def is_empty(self):
        return len(self.heap) == 0

    def clear(self):
        self.heap = []

    def is_empty(self):
        return len(self.heap) == 0

    def size(self):
        return len(self.heap)
    
    @staticmethod
    def unit_test():
        pq = PriorityQueue()
        pq.push_item(HeapItem(2, 'apple'))  # 使用 HeapItem 对象
        pq.push(1, 'banana')               # 直接传入优先级和数据
        pq.push_item(HeapItem(3, 'cherry'))# 使用 HeapItem 对象

        while not pq.is_empty():
            item = pq.pop()

class EventContainer:
    """
    事件时间容器
    1. 记录每个事件的概率（经过平滑）
    2. 记录事件第一次出现的时间（start_ts）
    3. 记录事件最近一次被更新的时间（last_ts）
    4. 每次 update 前先做全局衰减
    """

    def __init__(self, decay_step=0.1):
        self.decay_step = decay_step
        # 结构: {event: (prob, start_ts, last_ts)}
        self.events = {}

    # ---------------- 核心接口 ----------------
    def update_events(self, new_events):
        now = time.time()
        for ev, prob in new_events.items():
            if ev in self.events:
                old_prob, start_ts, _ = self.events[ev]
                new_prob = (old_prob + prob) / 2
                self.events[ev] = (new_prob, start_ts, now)
            else:
                self.events[ev] = (prob / 1.74, now, now)

    def decay_events(self):
        for ev in list(self.events.keys()):
            prob, start_ts, last_ts = self.events[ev]
            prob = max(prob - self.decay_step, 0)
            if prob < 0.1:
                del self.events[ev]
            else:
                self.events[ev] = (prob, start_ts, last_ts)

    def get_events(self):
        return {k: v[0] for k, v in self.events.items()}

    # ---------------- 新增查询 ----------------
    def duration(self, event):
        if event not in self.events:
            return 0.0
        return time.time() - self.events[event][1]

    def last_seen(self, event):
        if event not in self.events:
            return float('inf')
        return time.time() - self.events[event][2]

    # ---------------- 调试用 ----------------
    @staticmethod
    def unit_test():
        data = [
            {'Sadness': 0.7255054},
            {'Sadness': 0.7255054},
            {'Sadness': 0.4990354},
            {'Surprise': 0.1799064, 'Sadness': 0.4954076, 'Disgust': 0.3277579, 'Happiness': 0.1888055},
            {'Sadness': 0.3509507},
            {'Sadness': 0.3509507},
            {'Sadness': 0.3509507},
            {'Sadness': 0.4951766},
            {'Sadness': 0.5500308},
            {'Sadness': 0.8343774},
            {'Face': 0.1701155},
            {'Disgust': 0.2299653, 'Sadness': 0.856757},
            {}, {}, {}, {}, {}, {}, {}, {}
        ]

        ec = EventContainer()
        for entry in data:
            import time
            time.sleep(0.1)
            ec.decay_events()
            ec.update_events(entry)
            print("Events:", ec.get_events())
            if "Sadness" in ec.events:
                print("   Sadness duration:", round(ec.duration("Sadness"), 2), "s")

import machine
import sensor, image, time, lcd
import KPU as kpu
import os, gc, sys
from Maix import utils
from Maix import freq

from machine import WDT

class protect:
    wdt = None
    def start():
        protect.wdt = WDT(id=0, timeout=3000)  # protect.stop()
    def keep():
        if protect.wdt:
            protect.wdt.feed()
    def stop():
        if protect.wdt:
            protect.wdt.stop()
    def restart():
        if protect.wdt:
            protect.wdt = None

if freq.get_cpu() != 403:
    freq.set(cpu=403)

DEBUG = False
SLEEP = 0  # 3

if DEBUG:
    lcd.init(freq=15000000)

class CameraAIManager:
    def __init__(self, model_list):
        self.model_list = model_list
        self.data_queue = []
        self.camera_powered = False
        # 初始化模型列表，添加 task 和 initialized 标记
        for model_info in self.model_list:
            model_info['task'] = None
            model_info['initialized'] = False

    def power_on(self):
        try:
            protect.stop()
            sensor.shutdown(0)
            # 初始化摄像头
            sensor.reset(dual_buff=True)
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            sensor.skip_frames(time=1000)
        finally:
            protect.start()
            protect.keep()
            pass
        self.camera_powered = True

    def power_off(self):
        sensor.shutdown(1)
        self.camera_powered = False

    def is_powered(self):
        return self.camera_powered

    def load_model(self, model_info):
        """加载单个模型"""
        if not model_info['initialized']:
            model_info['task'] = kpu.load(model_info['addr'])
            model_info['initialized'] = True

    # def unload_model(self, model_info):
    #     """卸载单个模型"""
    #     if model_info['initialized']:
    #         kpu.deinit(model_info['task'])
    #         model_info['task'] = None
    #         model_info['initialized'] = False

    # def unload_all_models(self):
    #     """卸载所有模型"""
    #     for model_info in self.model_list:
    #         self.unload_model(model_info)

    def detect_objects(self, img, model_info):
        global DEBUG
        # old = time.ticks_ms()
        gc.collect()
        task = model_info['task']
        if task is None:
            raise ValueError("Model task is not loaded.")
        kpu.init_yolo2(task, model_info['threshold'], 0.3, 5, model_info['anchors'])
        if model_info['model_size'][0] != img.width():
            img = img.cut(48, 8, 224, 224)
            img.pix_to_ai()
        objects = kpu.run_yolo2(task, img)
        kpu.deinit(task, 1)
        result = {'have_object': False, 'detections': {}, 'label_counts': {label: 0 for label in model_info['labels']}}
        if objects:
            for obj in objects:
                if DEBUG:
                    img.draw_rectangle(obj.rect())
                class_id = obj.classid()
                if class_id < len(model_info['labels']):
                    label = model_info['labels'][class_id]
                    confidence = obj.value()
                    result['rect'] = obj.rect()
                    result['label_counts'][label] += 1
                    if label not in result['detections'] or confidence > result['detections'][label]:
                        result['detections'][label] = confidence
            result['have_object'] = True
            height = 0
            for label, confidence in result['detections'].items():
                if DEBUG:
                    img.draw_string(0, height, "%s:%.2f" % (label, confidence), scale=2, color=lcd.RED)
                height += 30
        # print("detect_objects time: %d" % (time.ticks_ms() - old))
        return result, img

    def add_data(self, data):
        self.data_queue.append(data)
        if len(self.data_queue) > 10:
            self.data_queue.pop(0)

    def have_data(self):
        return len(self.data_queue) > 0

    def clear_data(self):
        self.data_queue.clear()

    def get_data(self):
        if len(self.data_queue) > 0:
            tmp = self.data_queue[0]
            self.data_queue.pop()
            return tmp
        return None

    def loop_task(self):
        global DEBUG, SLEEP
        try:
            if not self.is_powered():
                print("Camera is powered off. AI detection is disabled.")
                return

            for model_info in self.model_list:
                if not model_info['initialized']:
                    self.load_model(model_info)
                # print(model_info)
                for _ in range(1):
                    img = sensor.snapshot()
                    result, img = self.detect_objects(img, model_info)
                    # print(result, img)
                    if DEBUG:
                        lcd.display(img)
                    if result['have_object']:
                        del result['have_object']
                        self.add_data(result)
                        if DEBUG:
                            print("Detected objects:", result)

                if SLEEP > 0:
                    if SLEEP > 2:
                        self.power_off()
                    time.sleep(SLEEP)
                    if SLEEP > 2:
                        self.power_on()

        except Exception as e:
            raise e
        finally:
            gc.collect()

    @staticmethod
    def unit_test(camera_ai_manager):
        try:
            camera_ai_manager.power_on()
            while True:
            # for i in range(10):
                camera_ai_manager.loop_task()
                # while camera_ai_manager.have_data():
                #     print("result: ", camera_ai_manager.get_data())
                protect.keep()
                # print("ms: %d", time.ticks_ms())
        except Exception as e:
            sys.print_exception(e)
        finally:
            gc.collect()
            # camera_ai_manager.unload_all_models()
            # camera_ai_manager.power_off()

model_list = [
    {
        'addr': 0x300000,
        'labels': ['Face'],
        'anchors': (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025),
        'model_size': (320, 240),
        'threshold': 0.1
    },
    # {
    #     'addr': 0x400000,
    #     'labels': ['Disgust', 'Sadness', 'Fear', 'Neutral', 'Surprise', 'Happiness', 'Anger'],
    #     'anchors': [1.84, 1.84, 1.66, 1.66, 2.22, 2.22, 2.03, 2.03, 1.94, 1.94],
    #     'model_size': (224, 224),
    #     'threshold': 0.1
    # },
    # {
    #     'addr': 0x600000,
    #     'labels': ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'],
    #     'anchors': [1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025],
    #     'model_size': (320, 240),
    #     'threshold': 0.1
    # },
]

camera_ai_manager = CameraAIManager(model_list)
camera_ai_manager.power_on()

import ujson as json
import random

class PlayerState:
    IDLE = 1
    PLAYING = 2
    PAUSED = 3

class AnimationPlayer:
    def __init__(self, prefix='', delay=100, callback=None):
        self.prefix = prefix
        self.delay = delay  # 期望延时播放间隔（单位：毫秒）
        self.state = PlayerState.IDLE  # 初始状态为 IDLE
        self.current_index = 0
        self.current_directory = None
        self.files = []
        self.loop = False   # 是否循环播放
        self._repeat_total = 1     # 新增：剩余播放次数
        self.callback = callback
        self.task_start = None
        self.play_start = None
        self.task_flag = None
        self.agent = agent()
        from fpioa_manager import fm
        fm.register(25, fm.fpioa.UART1_TX, force=True)
        fm.register(24, fm.fpioa.UART1_RX, force=True)
        from machine import UART
        self.uart = UART(UART.UART1, 115200, 8, 1, 0, timeout=1000, read_buf_len=4096)

    def uart_call(self, func_name, **kwargs):
        """UART JSON RPC"""
        req = {
            "jsonrpc": "2.0",
            "method": func_name,
            "params": kwargs,
            "id": str(random.randint(0, 1000000000))
        }
        self.uart.write((json.dumps(req) + '\n').encode())

    def _load_files(self, directory, start_file=1, end_file=None):
        """加载指定目录中的文件"""
        files = os.listdir(directory)
        parts = directory.split('/')
        self.prefix = parts[-1]
        self.files = [file for file in files if file.startswith(self.prefix) and file.endswith('.jpg')]
        if not self.files:
            raise ValueError("No files found with the specified prefix in the current directory.")
        # print(self.files)
        file_numbers = [int(file[len(self.prefix):-4]) for file in self.files]
        # print(file_numbers)
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

    def start(self, directory, start_file=1, end_file=None, loop=1):
        """
        loop: int
            0 -> 不重复，仅播放一次
            n -> 总共播放 n 次（n >= 1）
        """
        try:
            print(directory, loop)
            if self.state != PlayerState.IDLE:
                self.pause()

            self._load_files(directory, start_file, end_file)

            # 新语义：loop 为次数
            if loop <= 0:
                self._repeat_total = 1
                self.loop = False
            else:
                self._repeat_total = int(loop)
                self.loop = True       # 内部仍用布尔值判断是否继续循环

            self.state = PlayerState.PLAYING
            self.task_start = time.ticks_ms()
            self.play_start = time.ticks_ms()
            self.current_index = 0   # 确保每次 start 都从第一帧开始
        except Exception as e:
            sys.print_exception(e)
    def pause(self):
        """停止播放动画"""
        self.state = PlayerState.PAUSED

    def resume(self):
        """恢复播放动画"""
        if self.state == PlayerState.PAUSED:
            self.state = PlayerState.PLAYING
            # self.play_start = time.ticks_ms()
    def is_playing(self):
        """判断是否正在播放动画"""
        return self.state == PlayerState.PLAYING

    def is_paused(self):
        """判断是否暂停播放动画"""
        return self.state != PlayerState.PLAYING
        
    def play(self):
        self.agent.parallel_cycle()
        """播放动画"""
        if self.state == PlayerState.PLAYING and self.files:
            try:
                snapshot = None
                file_name = self.files[self.current_index]
                run_time = time.ticks_ms()
                image_path = self.current_directory + '/' + file_name
                snapshot = image.Image(image_path)
                lcd.display(snapshot)
                del snapshot

                if self.callback:
                    self.callback(self)

                gc.collect()
                self.current_index += 1
                if self.current_index >= len(self.files):
                    self._repeat_total -= 1          # 完成一轮
                    if self._repeat_total > 0:       # 还需继续
                        self.current_index = 0
                    else:                            # 全部播完
                        self.state = PlayerState.IDLE

                # print("time: %s/%s Playing: %s, Index: %s/%s" % (time.ticks_ms(), time.ticks_ms() - run_time, image_path, self.current_index, len(self.files)))
                elapsed_time = time.ticks_ms() - self.play_start
                expected_time = self.delay * self.current_index
                if elapsed_time > expected_time + self.delay:  # 如果滞后超过100ms，则不延时
                    pass
                else:
                    actual_delay = time.ticks_ms() - run_time
                    if actual_delay < self.delay:
                        tmp = (self.delay - actual_delay) * 0.001
                        time.sleep(tmp)  # 补充延时
                        # print("sleep: %s", tmp)
                    else:
                        time.sleep(0.01)  # 如果实际延时大于期望延时，则延时0.01秒
            except Exception as e:
                sys.print_exception(e)
                self.state = PlayerState.IDLE
            except KeyboardInterrupt:
                self.state = PlayerState.IDLE
        else:
            if self.callback:
                self.callback(self)
            time.sleep(0.1)  # 延时等待，避免CPU占用过高

    def get_current_status(self):
        """获取当前播放状态"""
        status = {
            "current_directory": self.current_directory,
            "current_file": None,
            "current_index": self.current_index,
            "total_files": len(self.files),
            "is_playing": self.state == PlayerState.PLAYING,  # 是否正在播放
        }
        if self.files and self.current_index < len(self.files):
            status["current_file"] = self.files[self.current_index]
        return status
    
    @staticmethod
    def unit_test():
        global DEBUG
        # from robot_ai import camera_ai_manager
        for model_info in camera_ai_manager.model_list:
            if not model_info['initialized']:
                camera_ai_manager.load_model(model_info)
        camera_ai_manager.task_start = time.ticks_ms()
        camera_ai_manager.task_select = 0
        def robot_ai_callback(self):
            if self.state != PlayerState.PLAYING or time.ticks_ms() - camera_ai_manager.task_start > 250:
                camera_ai_manager.task_select += 1
                img = sensor.snapshot()
                result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[camera_ai_manager.task_select % 2])
                if DEBUG:
                    lcd.display(img)
                del img
                camera_ai_manager.task_start = time.ticks_ms()
                if result['have_object']:
                    del result['have_object']
                    # print(result)
                    camera_ai_manager.add_data(result)
        player = AnimationPlayer(prefix='', delay=125, callback=robot_ai_callback)  # 设置期望延时播放间隔为125ms

        status = player.get_current_status()
        print("Current Status: %s" % status)
        if status['is_playing'] == False:
            player.start(directory='/sd/_03_base_jpgs', start_file=450, end_file=None, loop=False)

        # 第一次播放
        player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=10, loop=True)
        start_time = time.ticks_ms()  # 记录开始时间
        while time.ticks_diff(time.ticks_ms(), start_time) < 4000:  # 播放2秒
            player.play()
            
        player.pause()
        
        # 第二次播放
        player.start(directory='/sd/_03_base_jpgs', start_file=480, end_file=None, loop=False)
        start_time = time.ticks_ms()  # 记录开始时间
        while time.ticks_diff(time.ticks_ms(), start_time) < 4000:  # 播放2秒
            player.play()
                
            # 获取当前播放状态
            status = player.get_current_status()
            print("Current Status: %s" % status)

class Emocards:
    def __init__(self):
        self.emotion_descriptions = {
            ("低落", "不愉悦"): ["失落", "忧郁", "沮丧", "悲伤"],
            ("低落", "中性"):   ["平静", "淡然", "无感", "漠然"],
            ("低落", "愉悦"):   ["平和", "宁静", "安详", "满足"],
            ("平静", "不愉悦"): ["困惑", "不满", "忧虑", "失望"],
            ("平静", "中性"):   ["稳定", "冷静", "中立", "淡然"],
            ("平静", "愉悦"):   ["舒适", "轻松", "满足", "惬意"],
            ("激动", "不愉悦"): ["不安", "烦躁", "焦虑", "易怒"],
            ("激动", "中性"):   ["期待", "紧张", "激动", "兴奋"],
            ("激动", "愉悦"):   ["开心", "愉悦", "兴奋", "快乐"]
        }

        # 中立锚点
        self.reset_anchor_arousal      = 0.5
        self.reset_anchor_pleasantness = 0.5
        self.reset_factor = 0.25

        # 当前状态
        self.current_arousal      = 0.5
        self.current_pleasantness = 0.5
        self.current_mapped       = (2, 2)
        self.current_state        = ("平静", "中性")
        self.current_description  = "中立"
        self.random_selection     = False

    # ---------------- 内部工具 ----------------
    def _remap(self):
        """根据当前 arousal / pleasantness 重新计算派生字段"""
        # 0~1 转 1,2,3
        if self.current_arousal < 0.33:
            a_idx = 1
        elif self.current_arousal < 0.67:
            a_idx = 2
        else:
            a_idx = 3

        if self.current_pleasantness < 0.33:
            p_idx = 1
        elif self.current_pleasantness < 0.67:
            p_idx = 2
        else:
            p_idx = 3

        self.current_mapped = (a_idx, p_idx)

        # 文字映射
        arousal_map      = {1: "低落", 2: "平静", 3: "激动"}
        pleasantness_map = {1: "不愉悦", 2: "中性", 3: "愉悦"}

        self.current_state = (arousal_map[a_idx], pleasantness_map[p_idx])

        # 描述
        desc_list = self.emotion_descriptions.get(self.current_state, ["未知"])
        if self.random_selection:
            import random
            self.current_description = random.choice(desc_list)
        else:
            self.current_description = desc_list[(a_idx + p_idx) // 2]

    # ---------------- 公开接口 ----------------
    def update(self, event_effects, event):
        """
        根据事件更新情绪
        event_effects: 字典，如 {"happy": {"arousal": 0.2, "pleasantness": 0.3}}
        event: 字符串，事件 key
        返回 (current_state, current_description)
        """
        eff = event_effects.get(event, {"arousal": 0, "pleasantness": 0})

        self.current_arousal      = max(0.0, min(1.0, self.current_arousal      + eff["arousal"]))
        self.current_pleasantness = max(0.0, min(1.0, self.current_pleasantness + eff["pleasantness"]))

        self._remap()
        return self.current_state, self.current_description

    def reset(self, dt=1.0):
        """
        向中立锚点收敛一步
        dt: 步长系数
        返回 display() 结果
        """
        # 指数衰减公式
        k = self.reset_factor
        diff_a = self.current_arousal      - self.reset_anchor_arousal
        diff_p = self.current_pleasantness - self.reset_anchor_pleasantness

        self.current_arousal      = self.reset_anchor_arousal      + diff_a * (2.718 ** (-k * dt))
        self.current_pleasantness = self.reset_anchor_pleasantness + diff_p * (2.718 ** (-k * dt))

        # 保证边界
        self.current_arousal      = max(0.0, min(1.0, self.current_arousal))
        self.current_pleasantness = max(0.0, min(1.0, self.current_pleasantness))

        self._remap()
        return self.display()

    def display(self):
        """返回当前状态字典"""
        return {
            "state":       self.current_state,
            "description": self.current_description.encode("utf-8"),
            "arousal":     self.current_arousal,
            "pleasantness":self.current_pleasantness
        }

    def run(self, event_effects, event):
        """update + display 的快捷方式"""
        self.update(event_effects, event)
        return self.display()

    # ---------------- 单元测试 ----------------
    @staticmethod
    def unit_test():
        emo = Emocards()
        effects = {
            "happy": {"arousal": 0.2, "pleasantness": 0.3},
            "sad":   {"arousal": -0.1, "pleasantness": -0.4},
            "panic": {"arousal": 0.5, "pleasantness": -0.3}
        }

        print("=== 初始 ===")
        print(emo.display())

        print("\n=== 发生 panic 事件 ===")
        emo.update(effects, "panic")
        print(emo.display())

        print("\n=== 连续 5 次 reset ===")
        for i in range(1, 6):
            emo.reset()
            print("第%d次:" % i, emo.display())

        print("\n=== 发生 happy 事件 ===")
        emo.update(effects, "happy")
        print(emo.display())

        print("\n=== 连续 5 次 reset ===")
        for i in range(1, 6):
            emo.reset()
            print("第%d次:" % i, emo.display())


class Number:
    def __init__(self, lower_bound, upper_bound, initial_value=None):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.value = self._clamp(initial_value) if initial_value is not None else None
        self.oalue = None  # 只保存最后一次的旧值

    def _clamp(self, value):
        return max(self.lower_bound, min(value, self.upper_bound))

    def set(self, value):
        clamped_value = self._clamp(value)
        if clamped_value != self.value:
            self.oalue = self.value  # 保存当前值为旧值
            self.value = clamped_value

    def get(self):
        return self.value

    def add(self, delta):
        new_value = self._clamp(self.value + delta)
        if new_value != self.value:
            self.oalue = self.value  # 保存当前值为旧值
            self.value = new_value

    def sub(self, delta):
        new_value = self._clamp(self.value - delta)
        if new_value != self.value:
            self.oalue = self.value  # 保存当前值为旧值
            self.value = new_value

    def old(self):  # 获取最后一次的旧值
        return self.oalue

    def update(self):  # 主动更新旧值
        self.oalue = self.value
