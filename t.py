
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
import image

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

scr = lv.obj()
img = lv.img(scr)
lv.scr_load(scr)
snapshot = image.Image()
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
del snapshot

# for i in range(499):
#     run_tim = time.ticks_ms()
#     snapshot = image.Image("/sd/cccc/%03d.jpg" % i)
#     lcd.display(snapshot)
#     print("time: %d" % (time.ticks_ms() - run_tim))

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

    img.set_src(img_dsc)
    img.set_drag(True)
    # print(snapshot)
    # lcd.display(snapshot)
    # print("time: %d" % (time.ticks_ms() - run_tim))
    # time.sleep(0.05)
