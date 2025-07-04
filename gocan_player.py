
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
    def __init__(self):
        # 初始化一个字典来存储事件及其概率
        self.events = {}

    def update_events(self, new_events):
        # 遍历新事件，更新或添加到现有事件中
        for event, prob in new_events.items():
            if event in self.events:
                # 如果事件已存在，计算当前值与历史值的平均值
                self.events[event] = (self.events[event] + prob) / 2
            else:
                # 如果事件不存在，该值控制触发起始点，为了避免误触发的突发事件
                # 但模型很难有 0.99 的概率，假设大多数时候都是 0.7 / 0.4 = 1.74 的值
                # 为了期望的 0.7 以上的第一条不作为输入，直到叠了两条。
                self.events[event] = prob / 1.74

    def decay_events(self):
        # 每次调用时，所有事件的概率值减少0.1，但不低于0
        for event in list(self.events.keys()):
            self.events[event] = max(self.events[event] - 0.1, 0)
            # 如果概率值为0，则移除该事件
            if self.events[event] < 0.1:
                del self.events[event]

    def get_events(self):
        # 返回当前的事件数据
        return self.events

    
    @staticmethod
    def unit_test(self):
        # 示例数据，包括一些空数据
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
            {},  # 空数据
            {},  # 空数据
            {},  # 空数据
            {},  # 空数据
            {},  # 空数据
            {},  # 空数据
            {},  # 空数据
            {},  # 空数据
        ]

        # 创建事件容器实例
        event_container = EventContainer()

        # 模拟函数调用
        for entry in data:
            # 每次调用前衰减现有事件的概率值
            event_container.decay_events()
            # 更新事件
            event_container.update_events(entry)
            # 打印当前事件状态
            print("Updated events:", event_container.get_events())

import machine
import sensor, image, time, lcd
import KPU as kpu
import gc, sys
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
    {
        'addr': 0x400000,
        'labels': ['Disgust', 'Sadness', 'Fear', 'Neutral', 'Surprise', 'Happiness', 'Anger'],
        'anchors': [1.84, 1.84, 1.66, 1.66, 2.22, 2.22, 2.03, 2.03, 1.94, 1.94],
        'model_size': (224, 224),
        'threshold': 0.1
    },
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

import os
import sensor, image, time, lcd
import gc, sys

lcd.init(freq=15000000)
# lcd.rotation(1)

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
        self.loop = False  # 是否循环播放
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

    def start(self, directory, start_file=1, end_file=None, loop=False):
        """开始播放动画"""
        try:
            print(directory)
            if self.state != PlayerState.IDLE:
                self.pause()
            self._load_files(directory, start_file, end_file)
            self.loop = loop
            self.state = PlayerState.PLAYING
            self.task_start = time.ticks_ms()
            self.play_start = time.ticks_ms()
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
                    if self.loop:
                        self.current_index = 0
                    else:
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
        获取当前播放状态
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
        # 定义情绪状态的描述
        self.emotion_descriptions = {
            ("低落", "不愉悦"): ["失落", "忧郁", "沮丧", "悲伤"],
            ("低落", "中性"): ["平静", "淡然", "无感", "漠然"],
            ("低落", "愉悦"): ["平和", "宁静", "安详", "满足"],
            ("平静", "不愉悦"): ["困惑", "不满", "忧虑", "失望"],
            ("平静", "中性"): ["稳定", "冷静", "中立", "淡然"],
            ("平静", "愉悦"): ["舒适", "轻松", "满足", "惬意"],
            ("激动", "不愉悦"): ["不安", "烦躁", "焦虑", "易怒"],
            ("激动", "中性"): ["期待", "紧张", "激动", "兴奋"],
            ("激动", "愉悦"): ["开心", "愉悦", "兴奋", "快乐"]
        }
        self.current_mapped = (2, 2)  # 初始情绪状态映射
        self.current_state = ("平静", "中性")  # 初始情绪状态
        self.current_arousal = 0.5  # 初始唤醒度，范围从0.0到1.0
        self.current_pleasantness = 0.5  # 初始愉悦度，范围从0.0到1.0
        self.current_description = "中立"  # 初始情绪描述
        self.random_selection = False  # 是否随机选择情绪描述

    def update(self, event_effects, event):
        """
        根据事件更新情绪状态并获取情绪描述
        :param event_effects: 事件表，字典格式，例如 {"happy_event": {"arousal": 0.2, "pleasantness": 0.3}}
        :param event: 事件类型，例如 "happy_event", "sad_event", "shake", "touch", "see_person"
        """
        # 获取事件的影响
        effect = event_effects.get(event, {"arousal": 0, "pleasantness": 0})

        # 更新唤醒度和愉悦度，并进行边界检查
        self.current_arousal = max(0.0, min(1.0, self.current_arousal + effect["arousal"]))
        self.current_pleasantness = max(0.0, min(1.0, self.current_pleasantness + effect["pleasantness"]))

        # 将0.0到1.0的区间映射到1、2、3
        arousal_mapped = 1 if self.current_arousal < 0.33 else 2 if self.current_arousal < 0.67 else 3
        pleasantness_mapped = 1 if self.current_pleasantness < 0.33 else 2 if self.current_pleasantness < 0.67 else 3
        self.current_mapped = (arousal_mapped, pleasantness_mapped)
        
        arousal_map = {1: "低落", 2: "平静", 3: "激动"}
        pleasantness_map = {1: "不愉悦", 2: "中性", 3: "愉悦"}

        arousal_state = arousal_map.get(arousal_mapped, "未知")
        pleasantness_state = pleasantness_map.get(pleasantness_mapped, "未知")

        self.current_state = (arousal_state, pleasantness_state)  # 更新当前情绪状态

        # 获取情绪描述
        descriptions = self.emotion_descriptions.get(self.current_state, ["未知", "未知", "未知", "未知"])

        if self.random_selection:
            import random
            self.current_description = random.choice(descriptions)
        else:
            # 根据 (arousal_mapped + pleasantness_mapped) / 2 的值选择情绪描述
            self.current_description = descriptions[int((arousal_mapped + pleasantness_mapped) / 2)]

        return self.current_state, self.current_description

    def display(self):
        return {
            "state": self.current_state,
            "description": self.current_description.encode('utf-8'),
        }

    def run(self, event_effects, event):
        """运行Emocards量表程序，返回情绪状态"""
        state, description = self.update(event_effects, event)
        return self.display()

    def unit_test():
        emocards = Emocards()
        event_effects = {
            "happy_event": {"arousal": 0.2, "pleasantness": 0.3},
            "sad_event": {"arousal": 0.1, "pleasantness": 0.3}
        }
        print(emocards.display())
        print(emocards.run(event_effects, "happy_event"))
        print(emocards.run(event_effects, "sad_event"))

def app():

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

    # player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=None, loop=False)

    player.queue = PriorityQueue()
    player.container = EventContainer()
    player.emocards = Emocards()

    def sensor_check(player):
        if player.uart.any():
            read_data = player.uart.readline()
            print("recv = ", read_data)
            try:
                sensor_event = json.loads(read_data)
                # sensor_event = {
                #     "action": "battry_down",
                #     "priority": 2
                #     "value": "10"
                # }
                player.queue.push(sensor_event.get("priority", 2), sensor_event)
            except json.JSONDecodeError as e:
                print("Error parsing JSON: ", e)
    player.agent.event(500, sensor_check, player)

    def ai_check(player):
        while camera_ai_manager.have_data():
            result = camera_ai_manager.get_data()
            player.container.update_events(result['detections'])
    player.agent.event(500, ai_check, player)

    def ai_update(player):
        # kpu.memtest()
        protect.keep()

        # 持续触发的事件调试区域，如 AI 的事件输入
        # print("time", time.time(), "Updated events:", player.container.get_events()) 
        for key, value in player.container.get_events().items():
            if value > 0.25: # 连续平均阈值
                ai_event = {
                    "action": key,
                    "value": value,
                }
                player.queue.push(ai_event.get("priority", 3), ai_event)
        player.container.decay_events() # 衰减
    player.agent.event(1000, ai_update, player)

    class Number:
        def __init__(self, lower_bound, upper_bound, initial_value=None):
            self.lower_bound = lower_bound
            self.upper_bound = upper_bound
            self.value = self._clamp(initial_value) if initial_value is not None else None

        def _clamp(self, value):
            return max(self.lower_bound, min(value, self.upper_bound))

        def set(self, value):
            self.value = self._clamp(value)

        def get(self):
            return self.value

        def add(self, delta):
            self.value = self._clamp(self.value + delta)

        def sub(self, delta):
            self.value = self._clamp(self.value - delta)

    # 示例用法
        def unit_test():
            num = Number(0, 100, 50)
            print("初始值：", num.get())

            num.add(20)
            print("增加20后：", num.get())

            num.sub(30)
            print("减少30后：", num.get())

            num.set(150)
            print("设置超出边界值150后：", num.get())


    class robot_base:
        # ==================== 01 事件定义区域 ====================

        event_effects = {
            "shake": {"arousal": 0.1, "pleasantness": -0.5},  # 摇晃
            "touch": {"arousal": 0.0, "pleasantness": 0.5},  # 触摸
            "sleep": {"arousal": -0.5, "pleasantness": 0.0},  # 触摸
            "Face": {"arousal": 0.5, "pleasantness": 0.5},  # 人脸
            "Disgust": {"arousal": -0.3, "pleasantness": -0.4},  # 厌恶
            "Sadness": {"arousal": -0.2, "pleasantness": -0.4},  # 悲伤
            "Fear": {"arousal": -0.4, "pleasantness": -0.4},  # 恐惧
            "Neutral": {"arousal": 0.0, "pleasantness": 0.0},  # 中性
            "Surprise": {"arousal": 0.3, "pleasantness": 0.2},  # 惊讶
            "Happiness": {"arousal": 0.2, "pleasantness": 0.5},  # 快乐
            "Anger": {"arousal": 0.5, "pleasantness": -0.5}  # 愤怒
        }

        current_list = ["deep", "sleep", "awake", "bored", "express"]
        current = Number(0, 4, 2)  # 反馈状态，用于标记情绪表达的结果，以及唤醒或休眠的状态值，这样可以用作下一次的状态参考
        life   = Number(0, 10, 10) # 生命值，从 20 到 1，当生命小于 1 时，关机，刚醒来时，没有同步电量的情况下，会假定满电量
        social = Number(0, 10, 10) # 社交指数，从 0 到 10，当社交指数小于 1 时，准备睡觉，如果有人出现，社交指数会升到 5 ，如果到 10 则触发专属彩蛋动画。

        # 每当电量小于 2 会期望关机，大于 2 小于 5 则其值为强度 0.1*（n），触发饥饿事件，影响 激动 不愉悦 的倾向状态
        # 电量降低的时候，会发布电量降低，唤醒度下降，当 饥饿 事件 触发 的时候 处于 睡眠 ，那就进入 休眠 。

        # player.xyz = [0, 0, 0] # 摇晃强度，不需要把原始数据上传，只需要考虑触发事件
        # 当 IMU 没有剧烈变化则陆续发布睡眠事件，当调整到 "平静", "愉悦" 进入睡眠状态，从睡眠到，进一步走休眠。
        # 摇晃的强度变化会产生轻重事件，如 摇晃，剧烈摇晃，剧烈摇晃会触发 激动，不愉悦 的倾向状态，反正会走向愉悦的安抚状态。

        # player.social 需要社交值 0 - 10，没有朋友的时候，触发自娱自乐，随着强度的不同，不同程度不同动画效果。
        # 它的娱乐方式也不同，大于 5 可以不需要，朋友或人脸存在的时候，社交值跳进 5 持续增加，如果社交值掉到 1 以下了，就可以准备睡觉了。
        
    robot = robot_base()

    def self_check(player):
        try:
            # ==================== 02 事件处理区域 ====================

            # 集中处理事件，事件一定会被处理完，串口事件优先 AI 事件，有利于先响应 
            while player.queue.size() > 0:
                event = player.queue.pop()
                if event: 
                    print("event", event.data)
                    if event.data["action"] == "Face" or event.data["action"] == "shake": # 区分走路和运动。
                        robot.social.add(3) # 强烈摇晃 或 看到人，社交值拉爆
                    # 生理需求处理
                    if event.data["action"] == "battry_down" or event.data["action"] == "battry_up":
                        robot.life.set(event.data["value"]) # 电量事件，直接设置电量
                    # 情感需求处理
                    player.emocards.update(robot_base.event_effects, event.data["action"])

                    # 这一轮的情绪表达就符合预期了，可以进入下一轮了

            # ==================== 03 机身状态区域 ====================

            #### 状态主要有 current，life，social，emocards

            robot.social.sub(1) # 社交值会持续衰减，但可以通过 AI 事件来增加，当社交值低于 1 时，会进入睡眠
    
            if robot.current.get() == 0:
                if robot.social.get() < 1:
                    print("deep sleep")
                    while True:
                        pass
                elif robot.social.get() > 3:
                    robot.current.set(3) # 阻止进入睡眠
            elif robot.current.get() == 1:
                robot.social.set(3) # 进入睡眠时，还要再来一轮，才能正式进入睡眠
                robot.current.set(0)
                print("into sleep")
                ai_event = {
                    "action": "sleep",
                }
                player.queue.push(ai_event.get("priority", 3), ai_event)
            elif robot.life.get() < 1 or robot.social.get() < 1:
                robot.current.set(1) # 转睡眠状态，电量低，社交低
            elif robot.current.get():
                if robot.social.get() < 3:
                    robot.current.set(2) # 社交值=低 转去清醒状态，想独处
                elif robot.social.get() > 8:
                    robot.current.set(4) # 转去表达状态，社交值高，想表达
                else:
                    robot.current.set(3) # 转去无聊状态，社交值正常，想自娱自乐
            else:
                pass

            # 物理状态，温度冷热、湿度、电量、震动等基础安全感，

            # ==================== 04 机器人表达区域 ====================
            if robot.current.get() == 1:
                print("sleep")
                ai_event = {
                    "action": "sleep",
                }
                player.queue.push(ai_event.get("priority", 3), ai_event)
                player.start(directory='/sd/sleep', loop=True)
            # 社交值高的时候，可以打断播放，情绪表达之间是平级的。，社交值低的时候
            elif robot.current.get() == 4: # 社交强的专属动画效果，因宠物性格而定。
                player.start(directory='/sd/super', loop=False)
                robot.social.sub(2)
            else:
                if player.state != PlayerState.PLAYING:
                    result = player.emocards.display()
                    # print("[{}, {}, {}, {}.decode()]".format(player.emocards.current_arousal, player.emocards.current_pleasantness, result["state"], result["description"]))
                    # 如果情绪是中立情况，则根据社交值表达
                    if ('\u5e73\u9759', '\u4e2d\u6027') == result["state"]:
                        if robot.current.get() == 2:
                            player.start(directory='/sd/awake', loop=True)
                        elif robot.current.get() == 3:
                            player.start(directory='/sd/bored', loop=True)
                        else:
                            pass
                    # 其他情绪，目前没有那么多情绪动画，只能挑典型动画
                    elif ('\u611f\u52a8', '\u611f\u52a8') == result["state"]:
                        print("emotion")
                
            # ==================== 05 反馈状态区域 ====================
            print("emocards : {} state : {}, life : {}, social : {}".format(player.emocards.current_mapped, robot.current.get(), robot.life.get(), robot.social.get()))
        
        except Exception as e:
            sys.print_exception(e)
            print("Error: ", e)
    player.agent.event(3000, self_check, player)

    while True:
        player.play()
        
if __name__ == "__main__":
    app()
