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
        protect.wdt = WDT(id=0, timeout=6000) # protect.stop()
    def keep():
        if protect.wdt != None:
            protect.wdt.feed()
    def stop():
        protect.wdt.stop()
    def restart():
        protect.wdt = None

protect.start()

if freq.get_cpu() != 403:
    freq.set(cpu=403)

lcd.init(freq=15000000)

DEBUG = False
SLEEP = 1 # 3

class CameraAIManager:
    def __init__(self, model_list):
        self.model_list = model_list
        self.data_queue = []
        self.camera_powered = False
        self.task = None

    def power_on(self):
        sensor.shutdown(0)
        # 初始化摄像头
        sensor.reset(dual_buff=True)
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.skip_frames(time=1000)
        self.camera_powered = True

    def power_off(self):
        sensor.shutdown(1)
        self.camera_powered = False

    def is_powered(self):
        return self.camera_powered

    def init_model(self, model_info):
        self.task = kpu.load(model_info['addr'])
        kpu.init_yolo2(self.task, model_info['threshold'], 0.3, 5, model_info['anchors'])

    def deinit_model(self):
        if self.task is not None:
            kpu.deinit(self.task)

    def detect_objects(self, img, model_info):
        global DEBUG
        gc.collect()
        if model_info['model_size'][0] != img.width():
            img = img.cut(48, 8, 224, 224)
            img.pix_to_ai()
        objects = kpu.run_yolo2(self.task, img)
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
            for model_info in self.model_list:
                if not self.is_powered():
                    print("Camera is powered off. AI detection is disabled.")
                    continue

                self.init_model(model_info)

                for i in range(1):
                    img = sensor.snapshot()
                    result, img = self.detect_objects(img, model_info)
                    if DEBUG:
                        lcd.display(img)
                    if result['have_object']:
                        del result['have_object']
                        self.add_data(result)
                        if DEBUG:
                            print("Detected objects:", result)

                self.deinit_model()
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

    def unit_test(camera_ai_manager):
        try:
            camera_ai_manager.power_on()
            while True:
                camera_ai_manager.loop_task()
                tmp = camera_ai_manager.have_data()
                while camera_ai_manager.have_data():
                    print("result: ", camera_ai_manager.get_data())
                # print(time.time())
                # time.sleep(0.01)
                protect.keep()
        except Exception as e:
            sys.print_exception(e)
        finally:
            gc.collect()
            camera_ai_manager.power_off()

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

import _thread
def func(name):
    while 1:
        CameraAIManager.unit_test(camera_ai_manager)

_thread.start_new_thread(func,("1",))

if __name__ == '__main__':
    while 1:
        time.sleep(1)