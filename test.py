
class Number:
    def __init__(self, lower_bound, upper_bound, initial_value=None):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.value = self._clamp(initial_value) if initial_value is not None else None
        self.oalue = None  # 只保存最后一次的旧值

    def _clamp(self, value):
        return max(self.lower_bound, min(value, self.upper_bound))

    def set(self, value):
        clamped_value = self._clamp(value)
        if clamped_value != self.value:
            self.oalue = self.value  # 保存当前值为旧值
            self.value = clamped_value

    def get(self):
        return self.value

    def add(self, delta):
        new_value = self._clamp(self.value + delta)
        if new_value != self.value:
            self.oalue = self.value  # 保存当前值为旧值
            self.value = new_value

    def sub(self, delta):
        new_value = self._clamp(self.value - delta)
        if new_value != self.value:
            self.oalue = self.value  # 保存当前值为旧值
            self.value = new_value

    def old(self):  # 获取最后一次的旧值
        return self.oalue

    def update(self):  # 主动更新旧值
        self.oalue = self.value

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
        # if self.p.is_paused():
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
    
class Robot:
    def __init__(self):
        self.current = Number(0, 4, 2)  # 反馈状态，用于标记情绪表达的结果，以及唤醒或休眠的状态值，这样可以用作下一次的状态参考
        self.life   = Number(0, 10, 10) # 生命值，从 20 到 1，当生命小于 1 时，关机，刚醒来时，没有同步电量的情况下，会假定满电量
        self.social = Number(0, 10, 10) # 社交指数，从 0 到 10，当社交指数小于 1 时，准备睡觉，如果有人出现，社交指数会升到 5 ，如果到 10 则触发专属彩蛋动画。

robot = Robot()
fsm = RobotFSM(robot, None)

while True:
    import time
    robot.social.sub(1)
    fsm.update()
    print(fsm._state.code)
    time.sleep(0.1)