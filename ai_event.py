class EventContainer:
    def __init__(self):
        # 初始化一个字典来存储事件及其概率
        self.events = {}

    def update_events(self, new_events):
        # 遍历新事件，更新或添加到现有事件中
        for event, prob in new_events.items():
            if event in self.events:
                # 如果事件已存在，计算当前值与历史值的平均值
                self.events[event] = (self.events[event] + prob) / 2
            else:
                # 如果事件不存在，该值控制触发起始点，为了避免误触发的突发事件
                # 但模型很难有 0.99 的概率，假设大多数时候都是 0.7 / 0.4 = 1.74 的值
                # 为了期望的 0.7 以上的第一条不作为输入，直到叠了两条。
                self.events[event] = prob / 1.74

    def decay_events(self):
        # 每次调用时，所有事件的概率值减少0.1，但不低于0
        for event in list(self.events.keys()):
            self.events[event] = max(self.events[event] - 0.1, 0)
            # 如果概率值为0，则移除该事件
            if self.events[event] < 0.1:
                del self.events[event]

    def get_events(self):
        # 返回当前的事件数据
        return self.events

# 示例数据，包括一些空数据
data = [
    {'Sadness': 0.7255054},
    {'Sadness': 0.7255054},
    {'Sadness': 0.4990354},
    {'Surprise': 0.1799064, 'Sadness': 0.4954076, 'Disgust': 0.3277579, 'Happiness': 0.1888055},
    {'Sadness': 0.3509507},
    {'Sadness': 0.3509507},
    {'Sadness': 0.3509507},
    {'Sadness': 0.4951766},
    {'Sadness': 0.5500308},
    {'Sadness': 0.8343774},
    {'Face': 0.1701155},
    {'Disgust': 0.2299653, 'Sadness': 0.856757},
    {},  # 空数据
    {},  # 空数据
    {},  # 空数据
    {},  # 空数据
    {},  # 空数据
    {},  # 空数据
    {},  # 空数据
    {},  # 空数据
]

# 创建事件容器实例
event_container = EventContainer()

# 模拟函数调用
for entry in data:
    # 每次调用前衰减现有事件的概率值
    event_container.decay_events()
    # 更新事件
    event_container.update_events(entry)
    # 打印当前事件状态
    print("Updated events:", event_container.get_events())