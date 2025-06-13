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
            # protect.stop()
            sensor.shutdown(0)
            # 初始化摄像头
            sensor.reset(dual_buff=True)
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            sensor.skip_frames(time=1000)
        finally:
            # protect.start()
            # protect.keep()
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
        result = {'have_object': False, 'detections': {}, 'label_counts': {label: 0 for label in model_info['labels']}}
        if objects:
            for obj in objects:
                if DEBUG:
                    img.draw_rectangle(obj.rect())
                class_id = obj.classid()
                if class_id < len(model_info['labels']):
                    label = model_info['labels'][class_id]
                    confidence = obj.value()
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

# from machine import Timer
# import time

# def on_timer(timer):
#     try:
#         camera_ai_manager.loop_task()
#         protect.keep()
#         print("ms: %d" % time.ticks_ms())
#     except Exception as e:
#         sys.print_exception(e)
#     finally:
#         gc.collect()
#     # print("time up:",timer)
#     # print("param:",timer.callback_arg())

# # tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_ONE_SHOT, period=1000, callback=on_timer, arg=on_timer)
# camera_ai_tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=1, unit=Timer.UNIT_S, callback=on_timer, arg=on_timer, start=False, priority=1, div=0)
# camera_ai_tim.start()
# time.sleep(5)
# camera_ai_tim.stop()
# time.sleep(5)
# camera_ai_tim.restart()
# time.sleep(5)
# camera_ai_tim.stop()
# del tim

# if __name__ == '__main__':
#     while 1:
#         time.sleep(1)
#         while camera_ai_manager.have_data():
#             print("result: ", camera_ai_manager.get_data())
#     # CameraAIManager.unit_test(camera_ai_manager)
#     # CameraAIManager.unit_test(camera_ai_manager)