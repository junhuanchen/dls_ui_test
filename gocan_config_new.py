Twinkle_Melody = [
    262, 40, 0, 3,
    262, 40, 0, 3,
    392, 40, 0, 3,
    392, 40, 0, 3,
    440, 40, 0, 3,
    440, 40, 0, 3,
    392, 80, 0, 3, 0, 3,
    349, 40, 0, 3,
    349, 40, 0, 3,
    330, 40, 0, 3,
    330, 40, 0, 3,
    294, 40, 0, 3,
    294, 40, 0, 3,
    262, 80, 0, 3, 0, 3,
    0, 0
]

EMO_JOY_Melody = [
    523, 12,
    659, 12,
    784, 16,
    0, 6,
    659, 12,
    784, 12,
    1047, 30,
    0, 0
]

EMO_FEAR_Melody = [
    1047, 10,
    0, 5,
    622, 8,
    659, 8,
    622, 8,
    659, 8,
    440, 30,
    349, 20,
    0, 0
]

EMO_TENSION_Melody = [
    392, 22,
    415, 20,
    440, 18,
    466, 16,
    494, 14,
    523, 40,
    0, 0
]

EMO_SUCCESS_Melody = [
    784, 12,
    988, 12,
    1175, 20,
    1568, 35,
    0, 0
]

EMO_ERROR_Melody = [
    622, 15,
    523, 35,
    0, 0
]

V0_Melody = [
    1760, 6,
    1661, 6,
    1568, 7,
    0, 5,
    1760, 6,
    1661, 6,
    1568, 7,
    0, 0
]

V1_Melody = [
    1760, 6,
    1661, 6,
    1568, 7,
    0, 5,
    1568, 6,
    1480, 6,
    1397, 7,
    0, 0
]


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

        self.emocards_list = ["shangxin", "xiyue", "nushi", "kaixin"]
        self.current_list = ["guanji", "xiumian", "wuliao", "xiyue", "kaixin"] # 关机、休眠、平静，喜悦，开心
        
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
        print("show_all: ", self._show_all_dirs)

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
                print("show_all: over")

            self._switch_to_idx(player, next_idx)

    # ---------- 内部工具 ----------
    def _switch_to_idx(self, player, idx: int):
        """真正切换到指定 idx 的目录并记录时间。"""
        anim_dir = self._show_all_dirs[idx]
        anim_path = self.get_path(anim_dir)

        player.start(directory=anim_path, loop=5)
        self._show_all_idx = idx
        self._show_all_start_ts = time.time()
        
    def trigger_all(self, player, directory, loop, audio=None, rpc=None):
        if player.emocards.current_mapped == (1, 1):
            print("1,1,0,shangxin")
        elif player.emocards.current_mapped == (1, 3):
            print("1,3,1,xiyue")
        elif player.emocards.current_mapped == (3, 1):
            print("3,1,2,nushi")
        elif player.emocards.current_mapped == (3, 3):
            print("3,3,3,kaixin")
            player.start(directory=self.get_path(self.emocards_list[]), loop=loop)
        else:
            player.start(directory=directory, loop=loop)
        if audio:
            print(audio)
            aplay.play(audio) # '/sd/audio/1.wav'
        if rpc:
            print(rpc)
            player.uart_call(rpc)
        