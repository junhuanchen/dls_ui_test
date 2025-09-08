
from machine import I2C
import time
from Maix import GPIO
from fpioa_manager import fm
import lcd, image
# ------------------  cst816 驱动部分（直接嵌入）  ------------------
from micropython import const

_CST816_ADDR         = const(0x15)

# 寄存器地址
_CST816_GestureID   = const(0x01)
_CST816_FingerNum   = const(0x02)
_CST816_XposH       = const(0x03)
_CST816_XposL       = const(0x04)
_CST816_YposH       = const(0x05)
_CST816_YposL       = const(0x06)
_CST816_ChipID      = const(0xA7)
_CST816_FwVersion   = const(0xA9)
_CST816_DisAutoSleep= const(0xFE)

class CST816:
    """MaixPy 下极简 CST816 驱动"""
    def __init__(self, i2c):
        self.i2c = i2c
        self.prev_x = 0
        self.prev_y = 0
        self.prev_touch = False

    def _reg_write(self, reg, value):
        self.i2c.writeto(_CST816_ADDR, bytes([reg, value]))

    def _reg_read(self, reg, len_=1):
        self.i2c.writeto(_CST816_ADDR, bytes([reg]))
        return self.i2c.readfrom(_CST816_ADDR, len_)

    def who_am_i(self):
        tmp = self._reg_read(_CST816_ChipID)[0]
        print(hex(tmp))
        return tmp == 0xB6

    def wake_up(self):
        self._reg_write(_CST816_DisAutoSleep, 0x00)
        time.sleep_ms(10)
        self._reg_write(_CST816_DisAutoSleep, 0x01)
        # time.sleep_ms(50)

    def get_point(self):
        data = self._reg_read(_CST816_XposH, 4)
        x = (((data[0] & 0x0F) << 8) | data[1])
        y = 280 - (((data[2] & 0x0F) << 8) | data[3])
        return x, y

    def get_gesture(self):
        return self._reg_read(_CST816_GestureID)[0]

    def get_touch(self):
        return self._reg_read(_CST816_FingerNum)[0] > 0

    def get_distance(self):
        x, y = self.get_point()
        touched = self.get_touch()

        if not self.prev_touch and touched:
            dx = dy = 0
        else:
            dx = x - self.prev_x
            dy = y - self.prev_y

        self.prev_x, self.prev_y, self.prev_touch = x, y, touched
        return dx, dy

# # ------------------  板级初始化 + 示例主循环  ------------------
# # 1. 复位引脚
fm.register(22, fm.fpioa.GPIOHS6, force=True)
rst = GPIO(GPIO.GPIOHS6, GPIO.OUT)
rst.value(0)
time.sleep_ms(10)
rst.value(1)
# time.sleep_ms(50)

# 2. I2C 总线
i2c = I2C(I2C.I2C4, freq=400000, scl=30, gscl=fm.fpioa.GPIOHS19, sda=31, gsda=fm.fpioa.GPIOHS20)

# 3. 扫描确认
print("I2C scan:", i2c.scan())

# 4. 初始化触摸芯片
touch = CST816(i2c)
if touch.who_am_i():
    print("CST816 detected")
    touch.wake_up()
else:
    print("CST816 not found")

import os
print(os.listdir())
# fm.register(25, fm.fpioa.GPIOHS8, force=True) # CS
# int_gpio = GPIO(GPIO.GPIOHS8, GPIO.IN, GPIO.PULL_DOWN)
#int_gpio.value(1)

import sensor, lcd

camera_ai_manager = locals()['camera_ai_manager']
player = locals()['gocan_aplay']

print('work', time.ticks_ms())
# 5. 主循环打印数据
for i in range(1000):
    try:
        if player.is_playing() == False:
            player.play('/sd/audio_gocan/kaixin.wav')
        player.tick()

        time.sleep_ms(50)
        
        if player.is_playing() == False:
            img = sensor.snapshot()
            result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[0], False)
            print("result", result)
        # lcd.display(img)

        # x, y = touch.get_point()
        # gesture = touch.get_gesture()
        # pressed = touch.get_touch()
        # dx, dy = touch.get_distance()
        # print("Pos:{},{}  Ges:{}  Press:{}  dX:{}  dY:{}".format(
        #       x, y, gesture, pressed, dx, dy))
        # time.sleep_ms(50)
        
    except Exception as e:
        print(e)
