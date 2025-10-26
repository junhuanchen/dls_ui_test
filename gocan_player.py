
import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm

camera_ai_manager = locals()['camera_ai_manager']
AnimationPlayer = locals()['AnimationPlayer']
EventContainer = locals()['EventContainer']
Emocards = locals()['Emocards']
aplay = locals()['gocan_aplay']
touch = locals()['touch']
lottie = locals()['lottie']

x_lines = [130, 190]
y_lines = [90, 150]
targets = [(-20, 20), (-20, 0), (-20, -20),
           (  0, 20), (  0, 0), (  0, -20),
           ( 20, 20), ( 20, 0), ( 20, -20)]
def get_9_dir(x, y):
    col = 2 if x >= x_lines[1] else (1 if x >= x_lines[0] else 0)
    row = 2 if y >= y_lines[1] else (1 if y >= y_lines[0] else 0)
    return col + row * 3

from gocan_config import Robot, RobotFSM

status = 0 # 0 init, 1 face, 2 uart, 3 touch
face_tick = 0

def app():

    def robot_ai_callback(self):
        global status
        # return None
        if self.is_paused():
            print("paused")
            status = 0
            player.robot.trigger_all(player, [player.robot.current_list[player.fsm._state.code]])

    player = AnimationPlayer(delay=125, callback=robot_ai_callback)  # 设置期望延时播放间隔为125ms

    player.container = EventContainer()
    player.emocards = Emocards()
    player.robot = Robot(locals())

    def camera_tick():
        global status, face_tick
        aplay.tick()
        if aplay.is_playing():
            return
        img = sensor.snapshot()
        result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[0])
        player.container.decay_events() # 衰减事件
        del img
        if result['have_object']:
            del result['have_object']
            # print(int(result["rect"][2]/2 + result["rect"][0]), int(result["rect"][3]/2 + result["rect"][1]))
            face_tick = time.ticks_ms()
            ret = get_9_dir(int(result["rect"][2]/2 + result["rect"][0]), int(result["rect"][3]/2 + result["rect"][1]))
            lottie.rotation(targets[ret][0], targets[ret][1], 1)
            player.container.update_events(result['detections'])
            for key, value in player.container.get_events().items():
                if value > 0.15: # 连续平均阈值
                    # print(value)
                    player.robot.social.add(2)
                    player.emocards.update(player.robot.event_effects, "Face")
        elif time.ticks_ms() - face_tick > 1000:
            lottie.rotation(0, 0, 1)

    player.agent.event(250, camera_tick, None)

    def uart_check(player):
        global status
        # 检查player的uart是否有数据
        if player.uart.any():
            read_data = player.uart.readline()
            print("recv = ", read_data)
            try:
                read_data = read_data.decode('utf-8')
                if read_data.isalpha() and status <= 2:
                    tmp = getattr(player.robot, 'show_' + read_data)
                    player.emocards.update(player.robot.event_effects, read_data)
                    status = 2
                    print("uart")
                    player.robot.social.add(2)
                    player.robot.trigger_all(player, tmp, loop=2)
                elif read_data.isdigit():
                    player.robot.life.set(int(read_data))
            except Exception as e:
                print("Error parsing JSON: ", e)
        else:
            pass
    player.agent.event(250, uart_check, player)

    even_val = 0
    even_old = 0
    touch_count = 0
    def touch_check(player):
        global status
        nonlocal even_val, even_old, touch_count

        if touch.get_touch():
            even_val |= 1
        else:
            even_val &= 0xfe
        even_enter = even_val & (even_old ^ even_val)
        even_out = ~even_val & (even_old ^ even_val)
        even_old = even_val
        if even_out & 2:
            status = 3
            print("touch")
            player.robot.social.add(2)
            player.emocards.update(player.robot.event_effects, "touch")
            tmp = getattr(player.robot, 'show_touch' + str(touch_count))
            player.robot.trigger_all(player, tmp, loop=2)
            if touch_count < 2:
                touch_count += 1
            else:
                touch_count = 0
            return
    player.agent.event(150, touch_check, player)

    # ------------------ 初始化与定时器 ------------------
    player.fsm = RobotFSM(player.robot, player)
    def robot_check(player):
        try:

            player.robot.social.sub(1)   # 3 秒一次的社交衰减
            player.emocards.reset()      # 稳定情绪值
            player.fsm.update()          # 驱动状态机

            # 调试打印
            # print("fsm:{}, emocards:{}, current:{}, life:{}, social:{}".format(
            #     player.fsm._state.__class__.__name__,
            #     player.emocards.current_mapped,
            #     player.robot.current.get(),
            #     player.robot.life.get(),
            #     player.robot.social.get()))

        except Exception as e:
            import sys
            sys.print_exception(e)

    player.agent.event(3000, robot_check, player)
    while True:
        player.play()
        
if __name__ == "__main__":
    app()
