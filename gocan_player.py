
import random
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
    }
]

camera_ai_manager = CameraAIManager(model_list)
camera_ai_manager.power_on()



import os
import sensor, image, time, lcd
import gc, sys

lcd.init(freq=15000000)
lcd.rotation(1)

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
        if self.state != PlayerState.IDLE:
            self.pause()
        self._load_files(directory, start_file, end_file)
        self.loop = loop
        self.state = PlayerState.PLAYING
        self.task_start = time.ticks_ms()
        self.play_start = time.ticks_ms()


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
        # from gocan_ai import camera_ai_manager
        for model_info in camera_ai_manager.model_list:
            if not model_info['initialized']:
                camera_ai_manager.load_model(model_info)
        camera_ai_manager.task_start = time.ticks_ms()
        camera_ai_manager.task_select = 0
        def gocan_ai_callback(self):
            if self.state != PlayerState.PLAYING or time.ticks_ms() - camera_ai_manager.task_start > 250:
                camera_ai_manager.task_select += 1
                img = sensor.snapshot()
                result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[camera_ai_manager.task_select % 2])
                # lcd.display(img)
                del img
                camera_ai_manager.task_start = time.ticks_ms()
                if result['have_object']:
                    del result['have_object']
                    # print(result)
                    camera_ai_manager.add_data(result)
        return AnimationPlayer(prefix='', delay=125, callback=gocan_ai_callback)  # 设置期望延时播放间隔为125ms

if __name__ == "__main__":
    
    player = AnimationPlayer.unit_test()
    
    # player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=None, loop=False)

    # {
    #     "priority": 1,
    #     "action": "happy"
    #     "info": "nihao"
    # }

    # {
    #     "priority": 0,
    #     "action": "face"
    # }

    player.queue = PriorityQueue()
    player.container = EventContainer()


    def sensor_check(player):
        if player.uart.any():
            read_data = player.uart.readline()
            print("recv = ", read_data)
            # 解析json传入
            try:
                # 解析JSON数据
                data = json.loads(read_data)
                # 将解析后的数据放入优先队列
                player.queue.push(data.get("priority", 2), data)
            except json.JSONDecodeError as e:
                print("Error parsing JSON: ", e)
    player.agent.event(500, sensor_check, player)

    def ai_check(player):
        while camera_ai_manager.have_data():
            result = camera_ai_manager.get_data()
            # print("result: ", result)
            # camera_ai_manager.clear_data()
            ai_event = {
                "action": result['detections'],
                "info": result
            }
            player.container.update_events(result['detections'])
            player.queue.push(ai_event.get("priority", 3), ai_event)
    player.agent.event(500, ai_check, player)

    # 此处需要 优先队列 + 协议解析 + 指令执行
    def self_check(player):
        try:
            protect.keep()
            player.container.decay_events()
            print("time", time.time(), "Updated events:", player.container.get_events())
            kpu.memtest()
            if player.state != PlayerState.PLAYING:
                if player.queue.size() > 0:
                    event = player.queue.pop()
                    if event:
                        print("event: ", event.data['action'])
                        # , 'Sadness', 'Fear', 'Neutral', 'Surprise', 'Happiness', 'Anger', 'Unknown', 'Face'
                        if 'Disgust' in event.data['action']:
                            # 执行happy动作
                            print("happy")
                            player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=50, loop=False)
            if player.queue.size() > 3:
                player.queue.clear()
        except Exception as e:
            sys.print_exception(e)
            print("Error: ", e)
    player.agent.event(1000, self_check, player)

    while True:
        player.play()
        
        # status = player.get_current_status()
        # print("Current Status: %s" % status)
        # if status['is_playing'] == False:
        #     player.start(directory='/sd/_03_base_jpgs', start_file=450, end_file=None, loop=False)

        # # 第一次播放
        # player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=10, loop=True)
        # start_time = time.ticks_ms()  # 记录开始时间
        # while time.ticks_diff(time.ticks_ms(), start_time) < 4000:  # 播放2秒
        #     player.play()
            
        # player.pause()
        # 获取当前播放状态
        # # 第二次播放
        # player.start(directory='/sd/_03_base_jpgs', start_file=480, end_file=None, loop=False)
        # start_time = time.ticks_ms()  # 记录开始时间
        # while time.ticks_diff(time.ticks_ms(), start_time) < 4000:  # 播放2秒
        #     player.play()
                
        #     # 获取当前播放状态
        #     status = player.get_current_status()
        #     print("Current Status: %s" % status)
