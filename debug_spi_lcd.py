
import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm


try:
    import gc, lcd, image
    gc.collect()
    lcd.init(type = 3, freq=24*100000, width=240, height=320, rst=35, dcx=34, ss=33, clk=32, data=31)
    # fm.register(31, fm.fpioa.SPI0_D0, force=True)
    
    lcd.register(0x11, None)
    lcd.register(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33])
    lcd.register(0x35, 0x00)
    lcd.register(0x36, 0x00)
    lcd.register(0x3A, 0x05)
    lcd.register(0xB7, 0x35)
    lcd.register(0xBB, 0x34)
    lcd.register(0xC0, 0x2C)
    lcd.register(0xC2, 0x01)
    lcd.register(0xC3, [0x13, 0x13])
    lcd.register(0xC4, 0x20)
    lcd.register(0xC6, 0x0F)
    lcd.register(0xD0, [0xA4, 0xA1])
    lcd.register(0xD6, 0xA1)
    lcd.register(0xE0, [0xD0, 0x0A, 0x10, 0x0C, 0x0C, 0x18, 0x35, 0x43, 0x4D, 0x39, 0x13, 0x13, 0x2D, 0x34])
    lcd.register(0xE1, [0xD0, 0x05, 0x0B, 0x06, 0x05, 0x02, 0x35, 0x43, 0x4D, 0x16, 0x15, 0x15, 0x2E, 0x32])

    lcd.register(0x21, None)
    lcd.register(0x29, None)
    lcd.register(0x2C, None)
    
    # lcd.direction(lcd.YX_RLDU)
    loading = image.Image(size=(lcd.width(), lcd.height()))
    loading.draw_rectangle((0, 0, lcd.width(), lcd.height()), fill=True, color=(255, 0, 0))
    info = "Welcome to MaixPy"
    loading.draw_string(int(lcd.width()//2 - len(info) * 5), (lcd.height())//4, info, color=(255, 255, 255), scale=2, mono_space=0)
    v = sys.implementation.version
    vers = 'V{}.{}.{} : maixpy.sipeed.com'.format(v[0],v[1],v[2])
    loading.draw_string(int(lcd.width()//2 - len(info) * 6), (lcd.height())//3 + 20, vers, color=(255, 255, 255), scale=1, mono_space=1)
    while True:
        lcd.display(loading)
    del loading, v, info, vers
    gc.collect()
finally:
    gc.collect()

