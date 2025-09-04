
import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm

from gocan import aplay, protect, AnimationPlayer, EventContainer, Emocards, PriorityQueue, camera_ai_manager, PlayerState, DEBUG, Number
from gocan_config import Robot

# # cube
# lcd.init(freq=15000000, type=2, invert=True, offset_w0=0, offset_h0=0, offset_w1=0, offset_h1=0, width=240, height=240, rst=37, dcx=38, ss=36, clk=39)
# lcd.rotation(2)

# maix bit
# lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=37, dcx=38, ss=36, clk=39)
# lcd.clear(color=(0,0,0))

# fm.register(17, fm.fpioa.GPIOHS6, force=True)
# rst = GPIO(GPIO.GPIOHS6, GPIO.OUT)
# rst.value(0)

# gocan
fm.register(34,fm.fpioa.GPIO4)
rd=GPIO(GPIO.GPIO4,GPIO.OUT)
rd.value(1)
lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=39, dcx=38, ss=37, clk=36, invert=1)
lcd.direction(lcd.YX_RLDU)

status = 0 # 0 init, 1 face, 2 uart

def app():

    for model_info in camera_ai_manager.model_list:
        if not model_info['initialized']:
            camera_ai_manager.load_model(model_info)
    camera_ai_manager.task_start = time.ticks_ms()
    camera_ai_manager.task_select = 0
    def robot_ai_callback(self):
        global status
        # return None
        if self.is_paused():
            print("paused")
            status = 0
            player.robot.trigger_all(player, player.robot.show_base)

    player = AnimationPlayer(delay=125, callback=robot_ai_callback)  # 设置期望延时播放间隔为125ms

    player.container = EventContainer()
    player.robot = Robot()

    def aplay_tick():
        aplay.tick()

    player.agent.event(250, aplay_tick, None)

    def camera_tick():
        global status
        # camera_ai_manager.task_select += 1
        img = sensor.snapshot()
        if len(camera_ai_manager.model_list) == 1:
            result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[0])
        else:
            result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[camera_ai_manager.task_select % 1])
        if DEBUG:
            lcd.display(img)
        del img
        camera_ai_manager.task_start = time.ticks_ms()
        if result['have_object']:
            del result['have_object']
            # print(result)
            camera_ai_manager.add_data(result)

    # player.agent.event(250, camera_tick, None)

    def uart_check(player):
        global status
        # 检查player的uart是否有数据
        if player.uart.any():
            read_data = player.uart.readline()
            print("recv = ", read_data)
            try:
                tmp = getattr(player.robot, 'show_' + read_data.decode('utf-8'))
                status = 2
                print("uart")
                player.robot.trigger_all(player, tmp, loop=2)
            except Exception as e:
                print("Error parsing JSON: ", e)
        else:
            pass
    player.agent.event(250, uart_check, player)


    even_val = 0
    even_old = 0
    def ai_check(player):
        global status
        nonlocal even_val, even_old
        player.container.decay_events() # 衰减事件
        if camera_ai_manager.have_data():
            result = camera_ai_manager.get_data()
            player.container.update_events(result['detections'])
        for key, value in player.container.get_events().items():
            if value > 0.15 and status <= 1: # 连续平均阈值
                # todo show
                even_val = 1
                break
            else:
                even_val = 0
        even_enter = even_val & (even_old ^ even_val)
        # even_out = ~even_val & (even_old ^ even_val)
        even_old = even_val
        if even_enter:
            status = 1
            print("face")
            player.robot.trigger_all(player, player.robot.show_face)
    player.agent.event(250, ai_check, player)

    while True:
        player.play()
        
if __name__ == "__main__":
    app()
