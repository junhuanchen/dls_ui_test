
import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm

from gocan import aplay, protect, AnimationPlayer, EventContainer, Emocards, PriorityQueue, camera_ai_manager, PlayerState, DEBUG, Number
from gocan_config import robot_base

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

def app():

    for model_info in camera_ai_manager.model_list:
        if not model_info['initialized']:
            camera_ai_manager.load_model(model_info)
    camera_ai_manager.task_start = time.ticks_ms()
    camera_ai_manager.task_select = 0
    def robot_ai_callback(self):
        # return None
        if self.is_paused() or time.ticks_ms() - camera_ai_manager.task_start > 250:
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

    player = AnimationPlayer(prefix='', delay=125, callback=robot_ai_callback)  # 设置期望延时播放间隔为125ms

    player.queue = PriorityQueue()
    player.container = EventContainer()
    player.emocards = Emocards()
    player.robot = Robot()

    def aplay_tick():
        import aplay
        aplay.tick()

    player.agent.event(20, aplay_tick, None)

    def sensor_check(player):
        # 检查player的uart是否有数据
        if player.uart.any():
            read_data = player.uart.readline()
            print("recv = ", read_data)
            try:
                sensor_event = json.loads(read_data)
                # sensor_event = {
                #     "action": "battry_down",
                #     "priority": 2
                #     "value": "10"
                # }
                # {
                #     "action": "emoji",
                #     "priority": 2
                #     "value": "10"
                #     "loop": "3"
                # }

                print(sensor_event)
                player.queue.push(sensor_event.get("priority", 2), sensor_event)
            except Exception as e:
                print("Error parsing JSON: ", e)
        else:
            pass
    player.agent.event(250, sensor_check, player)

    def ai_check(player):
        player.container.decay_events() # 衰减事件
        if camera_ai_manager.have_data():
            result = camera_ai_manager.get_data()
            # print(result)
            player.container.update_events(result['detections'])
    player.agent.event(250, ai_check, player)

    def event_check(player):
        # kpu.memtest()
        protect.keep()

        # ==================== 02 AI 事件发布区域 ====================
        # print("time", time.time(), "Updated events:", player.container.get_events()) 
        for key, value in player.container.get_events().items():
            if value > 0.15: # 连续平均阈值
                ai_event = {
                    "action": key,
                    "value": value,
                }
                player.queue.push(ai_event.get("priority", 3), ai_event) # 事件优先级，默认为 3
            print(key, value, player.container.duration(key)) # 事件 概率 持续时间

        # ==================== 02 优先事件处理区域 ====================

        # 集中处理事件，事件一定会被处理完，串口事件优先 AI 事件，有利于先响应 
        if player.queue.size() > 0:
            event = player.queue.pop()
            if event:
                print("event", event.data)
                player.robot.event_express(event)
                # 情感需求处理
                player.emocards.update(robot.event_effects, event.data["action"])

    player.agent.event(1000, event_check, player)
    
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
            """外部强制跳转到指定状态"""·
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
        def enter(self):
            super().enter()
            self.r.trigger_all(self.p, self.r.get_current_path(), loop=1, audio='/sd/audio/1.wav')

        def next_code(self):
            # 避免立即醒来：改为 social>5 且至少待 3 秒
            if self.r.social.get() > 5:
                return 2
            return None

    # ===================== SleepState =====================
    class SleepState(StateBase):
        code = 1
        def enter(self):
            super().enter()
            self.r.social.set(3)
            self.r.trigger_all(self.p, self.r.get_current_path(), loop=3, audio='/sd/audio/2.wav')

        def next_code(self):
            if self.p.is_paused():
                return 0
            return None

    # ===================== AwakeState =====================
    class AwakeState(StateBase):
        code = 2
        def enter(self):
            super().enter()
            # 副作用移至 enter，仅执行一次
            if self.p.is_paused():
                self.p.start(directory=self.r.get_current_path(), loop=5)
                self.r.social.add(1)

        def tick(self):
            if self.p.is_paused():
                self.r.trigger_all(self.p, self.r.get_current_path(), loop=3, audio='/sd/audio/3.wav')
            
        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            if self.r.social.get() > 4:
                return 3
            return None

    # ===================== BoredState =====================
    class BoredState(StateBase):
        code = 3
        def enter(self):
            super().enter()
            if self.p.is_paused():
                self.r.trigger_all(self.p, self.r.get_current_path(), loop=3, audio='/sd/audio/1.wav')

        def tick(self):
            if self.p.is_paused():
                self.r.trigger_all(self.p, self.r.get_current_path(), loop=3, audio='/sd/audio/3.wav')

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
        def enter(self):
            super().enter()
            self.r.trigger_all(self.p, self.r.get_current_path(), loop=3, audio='/sd/audio/4.wav')

        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            # 当 social 降到 ≤8 时才回到 Bored
            if self.r.social.get() < 8:
                return 3
            return None

    # ------------------ 初始化与定时器 ------------------
    player.fsm = RobotFSM(robot, player)

    def robot_check(player):
        try:
            player.delay = 100
            if 0:
                robot.show_all_loop(player)
                return  # 测试动画的模式

            robot.social.sub(1)          # 3 秒一次的社交衰减
            player.fsm.update()          # 驱动状态机

            # 调试打印
            print("fsm:{}, emocards:{}, current:{}, life:{}, social:{}".format(
                player.fsm._state.__class__.__name__,
                player.emocards.current_mapped,
                robot.current.get(),
                robot.life.get(),
                robot.social.get()))

            player.emocards.reset()      # 稳定情绪
        except Exception as e:
            import sys
            sys.print_exception(e)

    player.agent.event(2000, robot_check, player)
    while True:
        player.play()
        
if __name__ == "__main__":
    app()
