import random

class Emocards:
    def __init__(self):
        # 定义情绪状态的描述
        self.emotion_descriptions = {
            ("低落", "不愉悦"): ["忧郁", "沮丧", "悲伤", "失落"],
            ("低落", "中性"): ["平静", "淡然", "无感", "漠然"],
            ("低落", "愉悦"): ["宁静", "安详", "平和", "满足"],
            ("平静", "不愉悦"): ["失望", "不满", "忧虑", "困惑"],
            ("平静", "中性"): ["稳定", "中立", "冷静", "淡然"],
            ("平静", "愉悦"): ["轻松", "舒适", "满足", "惬意"],
            ("激动", "不愉悦"): ["焦虑", "烦躁", "紧张", "不安"],
            ("激动", "中性"): ["兴奋", "激动", "紧张", "期待"],
            ("激动", "愉悦"): ["开心", "兴奋", "愉悦", "快乐"]
        }
        self.emotion_images = {
            "低落": "😞", "平静": "😐", "激动": "😀",
            "不愉悦": "😠", "中性": "😑", "愉悦": "😊"
        }
        self.current_state = ("平静", "中性")  # 初始情绪状态
        self.current_arousal = 2  # 初始唤醒度
        self.current_pleasantness = 2  # 初始愉悦度

    def get_emotion(self, arousal, pleasantness):
        """根据唤醒度和愉悦度获取情绪状态，并更新当前状态"""
        arousal_map = {1: "低落", 2: "平静", 3: "激动"}
        pleasantness_map = {1: "不愉悦", 2: "中性", 3: "愉悦"}
        arousal_state = arousal_map.get(round(arousal), "未知")
        pleasantness_state = pleasantness_map.get(round(pleasantness), "未知")
        self.current_state = (arousal_state, pleasantness_state)  # 更新当前情绪状态
        return self.current_state

    def display_emotion(self, description=None):
        """返回当前情绪状态的描述"""
        descriptions = self.emotion_descriptions.get(self.current_state, ["未知情绪状态"])
        arousal_img = self.emotion_images[self.current_state[0]]
        pleasantness_img = self.emotion_images[self.current_state[1]]
        # 随机选择一个描述
        selected_description = random.choice(descriptions)
        return {
            "state": self.current_state,
            "description": selected_description,
            "icons": "{} {}".format(arousal_img, pleasantness_img)
        }

    def update_emotion(self, event_effects, event):
        """
        根据事件更新情绪状态
        :param event_effects: 事件表，字典格式，例如 {"happy_event": {"arousal": 0.5, "pleasantness": 0.5}}
        :param event: 事件类型，例如 "happy_event", "sad_event", "shake", "touch", "see_person"
        """
        # 获取事件的影响
        effect = event_effects.get(event, {"arousal": 0, "pleasantness": 0})

        # 更新唤醒度和愉悦度，并进行边界检查
        self.current_arousal = max(1, min(3, self.current_arousal + effect["arousal"]))
        self.current_pleasantness = max(1, min(3, self.current_pleasantness + effect["pleasantness"]))

        # 更新情绪状态
        return self.get_emotion(self.current_arousal, self.current_pleasantness)

    def run(self, event_effects, event):
        """运行Emocards量表程序，返回情绪状态"""
        self.update_emotion(event_effects, event)
        return self.display_emotion()

# 创建Emocards实例并运行
if __name__ == "__main__":
    # 定义事件表
    event_effects = {
        "happy_event": {"arousal": 0.5, "pleasantness": 0.5},  # 开心事件
        "sad_event": {"arousal": -0.5, "pleasantness": -0.5},  # 悲伤事件
        "shake": {"arousal": 0.5, "pleasantness": 0},  # 摇晃
        "touch": {"arousal": 0, "pleasantness": 0.5},  # 触摸
        "see_person_positive": {"arousal": 0.5, "pleasantness": 0.5},  # 见到人（正面）
        "see_person_negative": {"arousal": 0.5, "pleasantness": -0.5}  # 见到人（负面）
    }

    # 创建Emocards实例
    emocards = Emocards()

    # 初始化状态统计表
    state_counts = {
        ("低落", "不愉悦"): 0, ("低落", "中性"): 0, ("低落", "愉悦"): 0,
        ("平静", "不愉悦"): 0, ("平静", "中性"): 0, ("平静", "愉悦"): 0,
        ("激动", "不愉悦"): 0, ("激动", "中性"): 0, ("激动", "愉悦"): 0
    }

    # 随机生成事件进行测试，直到覆盖所有状态
    events = list(event_effects.keys())
    covered_states = set()

    while len(covered_states) < len(state_counts):
        event = random.choice(events)
        result = emocards.run(event_effects, event)
        state = result["state"]
        print("事件: {}, 情绪状态: {}, 描述: {}, 图标: {}".format(event, state, result["description"], result["icons"]))
        if state not in covered_states:
            covered_states.add(state)
        state_counts[state] += 1

    # 打印状态统计表
    print("情绪状态统计表：")
    print("{:<10} {:<10} {:<10} {:<10}".format("", "不愉悦", "中性", "愉悦"))
    for arousal in ["低落", "平静", "激动"]:
        print("{:<10}".format(arousal), end="")
        for pleasantness in ["不愉悦", "中性", "愉悦"]:
            print("{:<10}".format(state_counts[(arousal, pleasantness)]), end="")
        print()