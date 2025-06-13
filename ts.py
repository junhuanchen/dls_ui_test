import random

class Emocards:
    def __init__(self):
        # 定义情绪状态的描述
        self.emotion_descriptions = {
            ("激动", "愉悦"): ["非常兴奋和快乐", "开心", "兴奋", "愉悦"],
            ("激动", "中性"): ["非常兴奋但情绪中性", "紧张", "激动", "期待"],
            ("激动", "不愉悦"): ["非常兴奋但感到不快", "焦虑", "不安", "烦躁"],
            ("中等", "愉悦"): ["情绪中等但感到快乐", "轻松", "满足", "舒适"],
            ("中等", "中性"): ["情绪中等且情绪中性", "平静", "稳定", "中立"],
            ("中等", "不愉悦"): ["情绪中等但感到不快", "失望", "沮丧", "不满"],
            ("平静", "愉悦"): ["情绪平静且感到快乐", "宁静", "安详", "愉悦"],
            ("平静", "中性"): ["情绪平静且情绪中性", "平和", "冷静", "稳定"],
            ("平静", "不愉悦"): ["情绪平静但感到不快", "忧郁", "低落", "悲伤"]
        }
        self.emotion_images = {
            "激动": "😀", "中等": "😐", "平静": "😞",
            "愉悦": "😊", "中性": "😑", "不愉悦": "😠"
        }
        self.current_state = ("平静", "中性")  # 初始情绪状态

    def get_emotion(self, arousal, pleasantness):
        """根据唤醒度和愉悦度获取情绪状态"""
        arousal_map = {1: "平静", 2: "中等", 3: "激动"}
        pleasantness_map = {1: "不愉悦", 2: "中性", 3: "愉悦"}
        arousal_state = arousal_map.get(arousal, "未知")
        pleasantness_state = pleasantness_map.get(pleasantness, "未知")
        return (arousal_state, pleasantness_state)

    def update_state(self, target_state):
        """更新当前情绪状态"""
        self.current_state = target_state

    def display_emotion(self):
        """显示当前情绪状态"""
        descriptions = self.emotion_descriptions.get(self.current_state, ["未知情绪状态"])
        arousal_img = self.emotion_images[self.current_state[0]]
        pleasantness_img = self.emotion_images[self.current_state[1]]
        print(f"当前情绪状态: {arousal_img} {pleasantness_img} ({self.current_state[0]}, {self.current_state[1]})")
        for description in descriptions:
            print(f"描述: {description}")

    def random_test(self):
        """随机测试所有情绪状态"""
        print("开始随机测试所有情绪状态...")
        all_states = [(a, p) for a in range(1, 4) for p in range(1, 4)]  # 生成所有可能的情绪状态组合
        random.shuffle(all_states)  # 打乱顺序以随机化测试
        for arousal, pleasantness in all_states:
            target_state = self.get_emotion(arousal, pleasantness)
            self.update_state(target_state)
            self.display_emotion()
            print("-" * 40)

    def run(self):
        """运行Emocards量表程序"""
        print("欢迎使用Emocards情绪评估工具！")
        self.random_test()

# 创建Emocards实例并运行
if __name__ == "__main__":
    emocards = Emocards()
    emocards.run()