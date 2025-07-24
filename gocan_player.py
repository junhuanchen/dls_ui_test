
import os
import sensor, image, time, lcd, json
import gc, sys
from Maix import GPIO
from fpioa_manager import fm

from gocan import protect, AnimationPlayer, EventContainer, Emocards, PriorityQueue, camera_ai_manager, PlayerState, DEBUG, Number

# # cube
# lcd.init(freq=15000000, type=2, invert=True, offset_w0=0, offset_h0=0, offset_w1=0, offset_h1=0, width=240, height=240, rst=37, dcx=38, ss=36, clk=39)
# lcd.rotation(2)

# maix bit
lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=37, dcx=38, ss=36, clk=39)
lcd.clear(color=(0,0,0))

fm.register(17, fm.fpioa.GPIOHS6, force=True)
rst = GPIO(GPIO.GPIOHS6, GPIO.OUT)
rst.value(0)

# gocan
# lcd.init(freq=15000000, offset_w0=20, offset_h0=0, offset_w1=20, offset_h1=0, width=280, height=240, rst=39, dcx=38, ss=37, clk=36)
# lcd.direction(lcd.YX_RLDU)

def app():

    for model_info in camera_ai_manager.model_list:
        if not model_info['initialized']:
            camera_ai_manager.load_model(model_info)
    camera_ai_manager.task_start = time.ticks_ms()
    camera_ai_manager.task_select = 0
    def robot_ai_callback(self):
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

    def body_vibrate(val, ms):
        player.uart_call("vibrate", val=val, ms=ms)

    def body_play(val):
        player.uart_call("play", val=val)

    # player.start(directory='/sd/03_base_jpgs', start_file=0, end_file=None, loop=False)

    player.queue = PriorityQueue()
    player.container = EventContainer()
    player.emocards = Emocards()

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

    class robot_base:
        def __init__(self):
            # ==================== 01 事件定义区域 ====================

            self.event_effects = {
                "shake": {"arousal": 0.1, "pleasantness": -0.5},  # 摇晃
                "touch": {"arousal": 0.0, "pleasantness": 0.5},  # 触摸
                "sleep": {"arousal": -0.5, "pleasantness": 0.0},  # 触摸
                "Face": {"arousal": 0.5, "pleasantness": 0.5},  # 人脸
                "Disgust": {"arousal": -0.3, "pleasantness": -0.4},  # 厌恶
                "Sadness": {"arousal": -0.2, "pleasantness": -0.4},  # 悲伤
                "Fear": {"arousal": -0.4, "pleasantness": -0.4},  # 恐惧
                "Neutral": {"arousal": 0.0, "pleasantness": 0.0},  # 中性
                "Surprise": {"arousal": 0.3, "pleasantness": 0.2},  # 惊讶
                "Happiness": {"arousal": 0.2, "pleasantness": 0.5},  # 快乐
                "Anger": {"arousal": 0.5, "pleasantness": -0.5}  # 愤怒
            }

            self.base_path = "/sd/base"
            # self.current_list = ["deep", "sleep", "awake", "bored", "express"]
            self.current_list = ["pc", "xm", "pj", "xy", "kx"] # 关机、休眠、平静，喜悦，开心
            self.current = Number(0, 4, 2)  # 反馈状态，用于标记情绪表达的结果，以及唤醒或休眠的状态值，这样可以用作下一次的状态参考
            self.life   = Number(0, 10, 10) # 生命值，从 20 到 1，当生命小于 1 时，关机，刚醒来时，没有同步电量的情况下，会假定满电量
            self.social = Number(0, 10, 10) # 社交指数，从 0 到 10，当社交指数小于 1 时，准备睡觉，如果有人出现，社交指数会升到 5 ，如果到 10 则触发专属彩蛋动画。

            # 每当电量小于 2 会期望关机，大于 2 小于 5 则其值为强度 0.1*（n），触发饥饿事件，影响 激动 不愉悦 的倾向状态
            # 电量降低的时候，会发布电量降低，唤醒度下降，当 饥饿 事件 触发 的时候 处于 睡眠 ，那就进入 休眠 。

            # player.xyz = [0, 0, 0] # 摇晃强度，不需要把原始数据上传，只需要考虑触发事件
            # 当 IMU 没有剧烈变化则陆续发布睡眠事件，当调整到 "平静", "愉悦" 进入睡眠状态，从睡眠到，进一步走休眠。
            # 摇晃的强度变化会产生轻重事件，如 摇晃，剧烈摇晃，剧烈摇晃会触发 激动，不愉悦 的倾向状态，反正会走向愉悦的安抚状态。

            # player.social 需要社交值 0 - 10，没有朋友的时候，触发自娱自乐，随着强度的不同，不同程度不同动画效果。
            # 它的娱乐方式也不同，大于 5 可以不需要，朋友或人脸存在的时候，社交值跳进 5 持续增加，如果社交值掉到 1 以下了，就可以准备睡觉了。

        def get_path(self, obj=""):
            tmp = "{}/{}".format(self.base_path, obj)
            # print("get_path", tmp)
            return tmp
            
        def get_current_path(self):
            return self.get_path(self.current_list[self.current.get()])


        # ---------- 初始化 ----------
        def show_all_init(self):
            """在主循环开始前调用一次，初始化遍历列表。"""
            try:
                self._show_all_dirs = [d for d in os.listdir(self.base_path)]
            except OSError:
                self._show_all_dirs = []

            self._show_all_idx = 0          # 当前播放下标
            self._show_all_start_ts = None  # 当前目录开始时间（None 表示未启动）

        # ---------- 每帧调用 ----------
        def show_all_loop(self, player):
            # 1. 首次或目录列表为空时初始化
            try:
                if not self._show_all_dirs:
                    self.show_all_init()
                    return
            except AttributeError:
                self.show_all_init()

            now = time.time()

            # 2. 当前没有任何目录在播放 -> 立即启动第一个
            if self._show_all_start_ts is None:
                self._switch_to_idx(player, self._show_all_idx)
                return

            # 3. 判断是否到达 3 s 时间片
            if now - self._show_all_start_ts >= 3.0:
                # 切换到下一个目录
                next_idx = (self._show_all_idx + 1) % len(self._show_all_dirs)
                if next_idx == 0:
                    print("show_all: 全部动画播放完成")

                self._switch_to_idx(player, next_idx)

        # ---------- 内部工具 ----------
        def _switch_to_idx(self, player, idx: int):
            """真正切换到指定 idx 的目录并记录时间。"""
            anim_dir = self._show_all_dirs[idx]
            anim_path = self.get_path(anim_dir)

            player.start(directory=anim_path, loop=True)
            self._show_all_idx = idx
            self._show_all_start_ts = time.time()
            
    robot = robot_base()

    def event_check(player):
        # kpu.memtest()
        protect.keep()

        # ==================== 02 AI 事件发布区域 ====================
        # print("time", time.time(), "Updated events:", player.container.get_events()) 
        for key, value in player.container.get_events().items():
            if value > 0.25: # 连续平均阈值
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
                if event.data["action"] == "Face" or event.data["action"] == "shake": # 区分走路和运动。
                    # if player.is_paused():
                    #     player.start(directory=robot.get_path('awake'), loop=False)
                    robot.social.add(2) # 强烈摇晃 或 看到人，社交值拉爆
                # 生理需求处理
                if event.data["action"] == "battry_down" or event.data["action"] == "battry_up":
                    robot.life.set(event.data["value"]) # 电量事件，直接设置电量
                # 测试表情表达处理
                if event.data["action"] == "emoji":
                    player.start(directory=robot.get_path(event.data["value"]), loop=int(event.data["loop"]))
                # 情感需求处理
                player.emocards.update(robot.event_effects, event.data["action"])

                # 这一轮的情绪表达就符合预期了，可以进入下一轮了

    player.agent.event(1000, event_check, player)
    
    # # =============== 状态机 ===============

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
            self._state.enter()

        def transit(self, code):
            """外部强制跳转到指定状态"""
            if code in self._state_map and code != self._state.code:
                self._state.exit()
                self._state = self._state_map[code]
                self._state.enter()
                
        def update(self):
            next_code = self._state.next_code() # 状态转移每一次的期望，但不是必须的
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
            self.r.current.set(self.code)  # ✅ 同步状态码
        def exit(self): pass
        def tick(self): pass
        def next_code(self): return None

    # ===================== DeepSleepState =====================
    class DeepSleepState(StateBase):
        code = 0
        def enter(self):
            super().enter()
            self.p.start(directory=self.r.get_current_path(), loop=1)

        def next_code(self):
            if self.r.social.get() > 3:
                return 2
            return None

    # ===================== SleepState =====================
    class SleepState(StateBase):
        code = 1
        def enter(self):
            super().enter()
            self.r.social.set(3)
            self.p.start(directory=self.r.get_current_path(), loop=3)

        def next_code(self):
            if self.p.is_paused():
                return 0
            return None

    # ===================== AwakeState =====================
    class AwakeState(StateBase):
        code = 2
        def next_code(self):
            if self.p.is_paused():
                self.p.start(directory=self.r.get_current_path(), loop=5)
                self.r.social.add(1)
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
                self.p.start(directory=self.r.get_current_path(), loop=2)

        def tick(self):
            if self.p.is_paused():
                self.p.start(directory=self.r.get_current_path(), loop=2)


        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            if self.r.social.get() < 5:
                return 2
            if self.r.social.get() > 8:
                return 4
            return None

    # ===================== ExpressState =====================
    class ExpressState(StateBase):
        code = 4
        def enter(self):
            super().enter()
            self.p.start(directory=self.r.get_current_path(), loop=2)
            if self.p.is_paused():
                self.r.social.sub(2)
            else:
                self.r.social.add(1)

        def next_code(self):
            if self.r.life.get() < 1 or self.r.social.get() < 1:
                return 1
            return 3

    player.fsm = RobotFSM(robot, player)   # 放在 player 初始化之后即可

    def robot_check(player):
        try:
            player.delay = 100
            # robot.show_all_loop(player)
            # return # 测试动画的模式

            robot.social.sub(1)          # 3 秒一次的社交衰减
            player.fsm.update()          # 驱动状态机

            # 调试打印
            print("fsm:{}, emocards:{}, current:{}, life:{}, social:{}".format(
                player.fsm._state.__class__.__name__,
                player.emocards.current_mapped,
                robot.current.get(),
                robot.life.get(),
                robot.social.get()))

            player.emocards.reset()      # 稳定情绪，让情绪值期望回到中位。
        except Exception as e:
            import sys
            sys.print_exception(e)

    player.agent.event(2000, robot_check, player)

    while True:
        player.play()
        
if __name__ == "__main__":
    app()
