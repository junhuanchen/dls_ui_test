
import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm

# from gocan import aplay, protect, AnimationPlayer, EventContainer, Emocards, PriorityQueue, camera_ai_manager, PlayerState, Number
camera_ai_manager = locals()['camera_ai_manager']
AnimationPlayer = locals()['AnimationPlayer']
EventContainer = locals()['EventContainer']
aplay = locals()['gocan_aplay']
touch = locals()['touch']
print(touch)

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
# fm.register(34,fm.fpioa.GPIO4)
# rd=GPIO(GPIO.GPIO4,GPIO.OUT)
# rd.value(1)
# lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=39, dcx=38, ss=37, clk=36, invert=1)
# lcd.direction(lcd.YX_RLDU)

status = 0 # 0 init, 1 face, 2 uart, 3 touch

def app():
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

    def camera_tick():
        global status
        # camera_ai_manager.task_select += 1
        aplay.tick()
        if aplay.is_playing():
            return
        img = sensor.snapshot()
        if len(camera_ai_manager.model_list) == 1:
            result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[0])
        else:
            result, img = camera_ai_manager.detect_objects(img, camera_ai_manager.model_list[camera_ai_manager.task_select % 1])
        del img
        camera_ai_manager.task_start = time.ticks_ms()
        if result['have_object']:
            del result['have_object']
            print(result)
            camera_ai_manager.add_data(result)

    player.agent.event(250, camera_tick, None)

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
    touch_count = 0
    def ai_check(player):
        global status
        nonlocal even_val, even_old, touch_count
        player.container.decay_events() # 衰减事件
        if camera_ai_manager.have_data():
            result = camera_ai_manager.get_data()
            player.container.update_events(result['detections'])
        for key, value in player.container.get_events().items():
            print(value)
            if value > 0.15 and status <= 1: # 连续平均阈值
                # todo show
                even_val |= 1
                break
            else:
                even_val &= 0xfe
        if touch.get_touch():
            even_val |= 2
        else:
            even_val &= 0xfd
            # status = 3
            # print("touch")
            # player.robot.trigger_all(player, player.robot.show_face)
        even_enter = even_val & (even_old ^ even_val)
        even_out = ~even_val & (even_old ^ even_val)
        even_old = even_val
        if even_out & 2:
            status = 2
            print("touch")
            
            tmp = getattr(player.robot, 'show_touch'+str(touch_count))
            player.robot.trigger_all(player, tmp, loop=2)
            if touch_count < 2:
                touch_count += 1
            else:
                touch_count = 0
            return
        if even_enter & 1:
            status = 1
            print("face")
            player.robot.trigger_all(player, player.robot.show_face)
    player.agent.event(100, ai_check, player)

    # def tp_touch(player):
    #     global status
    #     x, y = touch.get_point()
    #     gesture = touch.get_gesture()
    #     pressed = touch.get_touch()
    #     dx, dy = touch.get_distance()
    #     print("Pos:{},{}  Ges:{}  Press:{}  dX:{}  dY:{}".format(
    #           x, y, gesture, pressed, dx, dy))
    #     if touch.get_touch():
    #         status = 3
    #         print("touch")
    #         player.robot.trigger_all(player, player.robot.show_face)
    # player.agent.event(100, tp_touch, player)
    # =============== 状态机 ===============

    class RobotFSM:
        def __init__(self, robot, player):
            self.robot  = robot
            self.player = player
            self._state_map = {
                0: DeepSleepState(self, robot, player),
                1: SleepState(self, robot, player),
                2: AwakeState(self, robot, player),
                3: BoredState(self, robot, player),
                4: ExpressState(self, robot, player),
            }
            self._state = self._state_map[2]   # 默认 awake
            self._force_code = None            # 强制跳转标志
            self._state.enter()

        def transit(self, code):
            """外部强制跳转到指定状态"""
            if code in self._state_map:
                self._force_code = code

        def update(self):
            # 优先处理强制跳转
            if self._force_code is not None and self._force_code != self._state.code:
                self._state.exit()
                self._state = self._state_map[self._force_code]
                self._state.enter()
                self._force_code = None
                self._state.tick()
                return

            # 正常条件转移
            next_code = self._state.next_code()
            if next_code is not None and next_code != self._state.code:
                self._state.exit()
                self._state = self._state_map[next_code]
                self._state.enter()
            self._state.tick()

    # ===================== 状态基类 =====================
    class StateBase:
        code = -1
        def __init__(self, fsm, robot, player):
            self.fsm = fsm
            self.r   = robot
            self.p   = player
        def enter(self):
            self.r.current.set(self.code)  # 同步状态码
        def exit(self): pass
        def tick(self): pass
        def next_code(self): return None

    # ===================== DeepSleepState =====================
    class DeepSleepState(StateBase):
        code = 0

        def next_code(self):
            # 避免立即醒来：改为 social>5 且至少待 3 秒
            if self.r.social.get() > 5:
                return 2
            return None

    # ===================== SleepState =====================
    class SleepState(StateBase):
        code = 1

        def next_code(self):
            if self.p.is_paused():
                return 0
            return None

    # ===================== AwakeState =====================
    class AwakeState(StateBase):
        code = 2
            
        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            if self.r.social.get() > 4:
                return 3
            return None

    # ===================== BoredState =====================
    class BoredState(StateBase):
        code = 3

        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            if self.r.social.get() <= 5:
                return 2
            if self.r.social.get() >= 8:
                return 4
            return None

    # ===================== ExpressState =====================
    class ExpressState(StateBase):
        code = 4

        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            # 当 social 降到 ≤8 时才回到 Bored
            if self.r.social.get() < 8:
                return 3
            return None

    # ------------------ 初始化与定时器 ------------------
    player.fsm = RobotFSM(player.robot, player)
    def robot_check(player):
        try:

            player.robot.social.sub(1)          # 3 秒一次的社交衰减
            player.emocards.reset()      # 稳定情绪值
            player.fsm.update()          # 驱动状态机

            # 调试打印
            # print("fsm:{}, emocards:{}, current:{}, life:{}, social:{}".format(
            #     player.fsm._state.__class__.__name__,
            #     player.emocards.current_mapped,
            #     robot.current.get(),
            #     robot.life.get(),
            #     robot.social.get()))

        except Exception as e:
            import sys
            sys.print_exception(e)

    player.agent.event(3000, robot_check, player)
    while True:
        player.play()
        
if __name__ == "__main__":
    app()
