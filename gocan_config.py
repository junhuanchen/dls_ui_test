import time

MOTOR = [
    255, 300,
    0, 0
]

class Robot:
    def __init__(self, locals):
        self.locals = locals

        self.event_effects = {
            "shake": {"arousal": 0.1, "pleasantness": -0.5},  # 摇晃
            "touch": {"arousal": 0.0, "pleasantness": 0.5},  # 触摸
            "down": {"arousal": -0.5, "pleasantness": 0.0},  # 睡觉
            "Face": {"arousal": 0.5, "pleasantness": 0.5},  # 人脸
            "Disgust": {"arousal": -0.3, "pleasantness": -0.4},  # 厌恶
            "Sadness": {"arousal": -0.2, "pleasantness": -0.4},  # 悲伤
            "Fear": {"arousal": -0.4, "pleasantness": -0.4},  # 恐惧
            "Neutral": {"arousal": 0.0, "pleasantness": 0.0},  # 中性
            "charge": {"arousal": 0.3, "pleasantness": 0.2},  # 惊讶
            "up": {"arousal": 0.2, "pleasantness": 0.5},  # 快乐
            "fall": {"arousal": 0.5, "pleasantness": -0.5}  # 愤怒
        }
        self.current = locals['Number'](0, 4, 2)  # 反馈状态，用于标记情绪表达的结果，以及唤醒或休眠的状态值，这样可以用作下一次的状态参考
        self.life   = locals['Number'](0, 10, 10) # 生命值，从 20 到 1，当生命小于 1 时，关机，刚醒来时，没有同步电量的情况下，会假定满电量
        self.social = locals['Number'](0, 10, 10) # 社交指数，从 0 到 10，当社交指数小于 1 时，准备睡觉，如果有人出现，社交指数会升到 5 ，如果到 10 则触发专属彩蛋动画。

        self.show_path = ["/sd/lottie", "/sd/audio"]
        self.current_list = ["wuliao.json", "wunai.json", "jingzhizhuangtai.json", "liezuidaxiao.json", "aixinyan.json"] # 关机、休眠、平静，喜悦，开心
        self.show_up = ["liezuidaxiao.json", "liezuidaxiao.wav"]
        self.show_shake = ["haoqi.json", "haoqi.wav", MOTOR]
        self.show_down = ["jingyin.json", "jingyin.wav"]
        self.show_charge = ["chongdian.json", "dianliangdi.wav"]
        self.show_touch0 = ["xinglaihouwunai.json", "xinglaihouwunai.wav"]
        self.show_touch1 = ["jingzhizhuangtai.json", "jingzhizhuangtai.wav"]
        self.show_touch2 = ["shengqi.json", "shengqi.wav"]

        self.show_fall = ["shengqi.json", "shengqi.wav"]
        
    def get_path(self, obj):
        ret = list(obj)
        for i in range(len(ret)):
            if i <= 1:
                ret[i] = "{}/{}".format(self.show_path[i], ret[i])
        ret += (4 - len(ret)) * [None]
        return ret
        
    def trigger_all(self, player, show_type, loop=1):
        ret = self.get_path(show_type)
        print("trigger_all", ret)
        player.start(file_path=ret[0], loop=loop)
        # from gocan import aplay
        aplay = locals()['gocan_aplay']
        if aplay.is_playing():
            aplay.stop()
        if ret[1]:
            print(ret[1])
            aplay.play(ret[1])
        if ret[2]:
            player.body_vibrate(ret[2])
        if ret[3]:
            player.body_play(ret[3])



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
    def enter(self):
        self.p.body_poweroff(3000)
        return super().enter()

    def next_code(self):
        # 避免立即醒来：改为 social>5 且至少待 3 秒
        if self.r.social.get() > 5:
            return 2
        return None

# ===================== SleepState =====================
class SleepState(StateBase):
    code = 1
    sleep_tick = 0
    def enter(self):
        self.sleep_tick = time.ticks_ms()
        return super().enter()
    
    def next_code(self):
        if time.ticks_ms() - self.sleep_tick > 3000:
            return 0
        if self.r.social.get() > 4:
            return 3
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
