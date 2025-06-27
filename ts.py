import random

class Emocards:
    def __init__(self):
        # 定义情绪状态的描述
        self.emotion_descriptions = {
            ("低落", "不愉悦"): ["失落", "忧郁", "沮丧", "悲伤"],
            ("低落", "中性"): ["平静", "淡然", "无感", "漠然"],
            ("低落", "愉悦"): ["平和", "宁静", "安详", "满足"],
            ("平静", "不愉悦"): ["困惑", "不满", "忧虑", "失望"],
            ("平静", "中性"): ["稳定", "冷静", "中立", "淡然"],
            ("平静", "愉悦"): ["舒适", "轻松", "满足", "惬意"],
            ("激动", "不愉悦"): ["不安", "紧张", "烦躁", "焦虑"],
            ("激动", "中性"): ["期待", "紧张", "激动", "兴奋"],
            ("激动", "愉悦"): ["开心", "愉悦", "兴奋", "快乐"]
        }
        self.current_state = ("平静", "中性")  # 初始情绪状态
        self.current_arousal = 0.5  # 初始唤醒度，范围从0.0到1.0
        self.current_pleasantness = 0.5  # 初始愉悦度，范围从0.0到1.0
        self.current_description = "中立"  # 初始情绪描述
        self.random_selection = False  # 是否随机选择情绪描述

    def update(self, event_effects, event):
        """
        根据事件更新情绪状态并获取情绪描述
        :param event_effects: 事件表，字典格式，例如 {"happy_event": {"arousal": 0.2, "pleasantness": 0.3}}
        :param event: 事件类型，例如 "happy_event", "sad_event", "shake", "touch", "see_person"
        """
        # 获取事件的影响
        effect = event_effects.get(event, {"arousal": 0, "pleasantness": 0})

        # 更新唤醒度和愉悦度，并进行边界检查
        self.current_arousal = max(0.0, min(1.0, self.current_arousal + effect["arousal"]))
        self.current_pleasantness = max(0.0, min(1.0, self.current_pleasantness + effect["pleasantness"]))

        # 将0.0到1.0的区间映射到1、2、3
        arousal_mapped = 1 if self.current_arousal < 0.33 else 2 if self.current_arousal < 0.67 else 3
        pleasantness_mapped = 1 if self.current_pleasantness < 0.33 else 2 if self.current_pleasantness < 0.67 else 3

        arousal_map = {1: "低落", 2: "平静", 3: "激动"}
        pleasantness_map = {1: "不愉悦", 2: "中性", 3: "愉悦"}

        arousal_state = arousal_map.get(arousal_mapped, "未知")
        pleasantness_state = pleasantness_map.get(pleasantness_mapped, "未知")

        self.current_state = (arousal_state, pleasantness_state)  # 更新当前情绪状态

        # 获取情绪描述
        descriptions = self.emotion_descriptions.get(self.current_state, ["未知", "未知", "未知", "未知"])

        if self.random_selection:
            self.current_description = random.choice(descriptions)
        else:
            # 根据 (arousal_mapped + pleasantness_mapped) / 2 的值选择情绪描述
            self.current_description = descriptions[int((arousal_mapped + pleasantness_mapped) / 2)]

        return self.current_state, self.current_description

    def display(self):
        return {
            "state": self.current_state,
            "description": self.current_description#//.encode('utf-8'),
        }

    def run(self, event_effects, event):
        """运行Emocards量表程序，返回情绪状态"""
        state, description = self.update(event_effects, event)
        return self.display()

    def unit_test():
        emocards = Emocards()
        event_effects = {
            "happy_event": {"arousal": 0.2, "pleasantness": 0.3},
            "sad_event": {"arousal": -0.1, "pleasantness": -0.1},
            "happy": {"arousal": 0.0, "pleasantness": 0.1},  # 开心事件
            "sad": {"arousal": 0.0, "pleasantness": -0.1},  # 悲伤事件
            "shake": {"arousal": 0.1, "pleasantness": -0.1},  # 摇晃
            "touch": {"arousal": 0.0, "pleasantness": 0.1},  # 触摸
            "see_person_positive": {"arousal": 0.1, "pleasantness": 0.0},  # 见到人（正面）
            "see_person_negative": {"arousal": -0.1, "pleasantness": 0.0}  # 未见到人（负面）
        }
        print(emocards.display())
        print(emocards.run(event_effects, "sad_event"))
        print(emocards.run(event_effects, "sad_event"))
        print(emocards.run(event_effects, "happy_event"))
        print(emocards.run(event_effects, "sad_event"))
        print(emocards.run(event_effects, "happy_event"))
        print(emocards.run(event_effects, "happy_event"))

Emocards.unit_test()