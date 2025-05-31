
# init
from Maix import freq
tmp = freq.get_cpu()
print(tmp)
if tmp != 598:
  freq.set(cpu = 600)


import lvgl as lv
import lvgl_helper as lv_h
import lcd
import time
import ustruct as struct
from machine import Timer
from machine import I2C
from touch import Touch, TouchLow
import KPU as kpu
import gc
import image

TOUCH = None
DEBUG = False

def read_cb(drv, ptr):
    # print(ptr, b)
    data = lv.indev_data_t.cast(ptr)
    TOUCH.event()
    if DEBUG:
        print(TOUCH.state, TOUCH.points)
    data.point = lv.point_t({'x': TOUCH.points[1][0], 'y': TOUCH.points[1][1]})
    data.state = lv.INDEV_STATE.PR if TOUCH.state == 1 else lv.INDEV_STATE.REL
    return False

i2c = I2C(I2C.I2C0, freq=400*1000, scl=15, sda=10)  # 24 27)
devices = i2c.scan()
print("devs", devices)  # devs 0 [16, 38, 52, 56]
TouchLow.config(i2c)
TOUCH = Touch(320, 240, 200)


lcd.init(freq=20000000)
# lcd.register(0x36, 0x20)
# lcd.register(0x36, 0x60)
lcd.rotation(3)

lv.init()

disp_buf1 = lv.disp_buf_t()
buf1_1 = bytearray(320*20)
lv.disp_buf_init(disp_buf1,buf1_1, None, len(buf1_1)//4)
disp_drv = lv.disp_drv_t()
lv.disp_drv_init(disp_drv)
disp_drv.buffer = disp_buf1
disp_drv.flush_cb = lv_h.flush
disp_drv.hor_res = 240
disp_drv.ver_res = 320
lv.disp_drv_register(disp_drv)

indev_drv = lv.indev_drv_t()
lv.indev_drv_init(indev_drv)
indev_drv.type = lv.INDEV_TYPE.POINTER
indev_drv.read_cb = read_cb
lv.indev_drv_register(indev_drv)


# lv.log_register_print_cb(lv_h.log)
lv.log_register_print_cb(lambda level,path,line,msg: print('%s(%d): %s' % (path, line, msg)))

# run_tim = time.ticks_ms()
def on_timer(timer):
    # global run_tim
    lv.tick_inc(20)
    lv.task_handler()
    # print("time: %d" % (time.ticks_ms() - run_tim))
    # run_tim = time.ticks_ms()
    # print("tick")
	
timer = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=20, unit=Timer.UNIT_MS, callback=on_timer, arg=None)

def creat_img(src, path):
    img = lv.img(src)
    snapshot = image.Image(path)
    img_data = snapshot.to_bytes()
    img_dsc = lv.img_dsc_t({
        'header':{
            'always_zero': 0,
            'w':snapshot.width(),
            'h':snapshot.height(),
            'cf':lv.img.CF.TRUE_COLOR
        },
        'data_size': len(img_data),
        'data': img_data
    })
    img.set_src(img_dsc)
    return img


scr = lv.obj()
lv.scr_load(scr)

# resolution of the screen
HOR_RES = lv.disp_get_hor_res(lv.disp_get_default())
VER_RES = lv.disp_get_ver_res(lv.disp_get_default())

tileview = lv.tileview(lv.scr_act())
tileview.set_edge_flash(True)

# delete clean
img = None
index = 0
def creat_tile(x):

    def event1_handler(obj, event):
        global tileview, index, img
        if event == lv.EVENT.CLICKED:
            tileview.clean()
            img = creat_img(tileview, "/sd/dddd/001.jpg")
            img.set_click(True)
            img.set_event_cb(img_handler)
            index=0
    def event2_handler(obj, event):
        global tileview, index, img
        if event == lv.EVENT.CLICKED:
            tileview.clean()
            img = creat_img(tileview, "/sd/badapple/0001.jpg")
            img.set_click(True)
            img.set_event_cb(img_handler)
            index=1

    def make_tilelabel(obj, x, text, event_handler):
        tile = lv.obj(obj)
        tile.set_size(HOR_RES, VER_RES)
        tile.set_pos(x, 0)
        tile.set_style(lv.style_pretty)
        tile.set_click(True)
        tile.set_event_cb(event_handler)
        tileview.add_element(tile)

        label = lv.label(tile)
        label.set_text(text)
        label.align(None, lv.ALIGN.CENTER, 0, 0)

        return label
    make_tilelabel(tileview, 0, "Tile 1", event1_handler)
    make_tilelabel(tileview, HOR_RES, "Tile 2", event2_handler)

    valid_pos = [{"x": x,"y": 0}]
    tileview.set_valid_positions(valid_pos, len(valid_pos))

    valid_pos = [{"x":0, "y": 0}, {"x": 1, "y": 0}, {"x": 2,"y": 0}]
    tileview.set_valid_positions(valid_pos, len(valid_pos))

def img_handler(obj, event):
    global img, tileview
    if event == lv.EVENT.CLICKED:
        img = None
        tileview.delete()
        tileview = lv.tileview(lv.scr_act())
        tileview.set_edge_flash(True)
        creat_tile(index)
        print("click")

creat_tile(0)

import time
while True:
    if img:
        print("in")
        if index == 0:
            for i in range(499):
                # run_tim = time.ticks_ms()
                snapshot = image.Image("/sd/dddd/%03d.jpg" % i)
                img_data = snapshot.to_bytes()
                # print("img_data", len(img_data))
                # img.align(scr, lv.ALIGN.CENTER, 0, 0)
                img_dsc = lv.img_dsc_t({
                    'header':{
                        'always_zero': 0,
                        'w':snapshot.width(),
                        'h':snapshot.height(),
                        'cf':lv.img.CF.TRUE_COLOR
                    },
                    'data_size': len(img_data),
                    'data': img_data
                })
                if img is None:
                    break
                img.set_src(img_dsc)
                img.set_drag(True)
        else:
            for i in range(1, 1001):
                # run_tim = time.ticks_ms()
                snapshot = image.Image("/sd/badapple/%04d.jpg" % i)
                img_data = snapshot.to_bytes()
                # print("img_data", len(img_data))
                # img.align(scr, lv.ALIGN.CENTER, 0, 0)
                img_dsc = lv.img_dsc_t({
                    'header':{
                        'always_zero': 0,
                        'w':snapshot.width(),
                        'h':snapshot.height(),
                        'cf':lv.img.CF.TRUE_COLOR
                    },
                    'data_size': len(img_data),
                    'data': img_data
                })
                if img is None:
                    break
                img.set_src(img_dsc) if img is not None else None
                img.set_drag(True) if img is not None else None
    else:
        if time.ticks_ms() - TOUCH.last_time > 5000:
            img = creat_img(tileview, "/sd/dddd/001.jpg")
            img.set_click(True)
            img.set_event_cb(img_handler)