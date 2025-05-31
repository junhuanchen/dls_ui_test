# This file is part of MaixUI
# Copyright (c) sipeed.com
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#

import random
import time
import heapq

class agent:
    def __init__(self):
        self.msg = []
        self.arg = {}
        self.get_ms = (lambda: time.ticks_ms()) if getattr(time, "ticks_ms", False) else (lambda: time.time() * 1000)

    def event(self, cycle, func, args=None):
        # arrived, cycle, function
        tmp = (self.get_ms() + cycle, cycle, func, args)
        self.msg.append(tmp)

    def remove(self, func):
        for pos in range(len(self.msg)):
            if self.msg[pos][2] == func:
                self.msg.remove(self.msg[pos])
                break

    def call(self, obj, pos=0):
        self.msg.pop(pos)
        self.event(obj[1], obj[2], obj[3])
        obj[2](obj[3]) if obj[3] else obj[2]()  # exec function

    def cycle(self):
        if len(self.msg):
            obj = self.msg[0]
            if self.get_ms() >= obj[0]:
                self.call(obj, 0)

    def parallel_cycle(self):
        for pos in range(len(self.msg)):
            obj = self.msg[pos]
            if self.get_ms() >= obj[0]:
                self.call(obj, pos)
                break


class PriorityQueue:
    def __init__(self):
        self.heap = []

    def push(self, item, priority):
        heapq.heappush(self.heap, (priority, item))

    def pop(self):
        if self.heap:
            return heapq.heappop(self.heap)[1]
        else:
            raise IndexError("pop from an empty priority queue")

    def peek(self):
        if self.heap:
            return self.heap[0][1]
        else:
            raise IndexError("peek from an empty priority queue")

    def is_empty(self):
        return len(self.heap) == 0

    def size(self):
        return len(self.heap)


class dls_task:
    def __init__(self, agent_instance):
        self.agent = agent_instance

    def run(self):
        class tmp:
            def test_0(self, data):
                print(f'test_0: {data}')

            def test_1(self, data):
                print(f'test_1: {data}')

            def test_2(self, data):
                print(f'test_2: {data}')

        # 创建随机数据并分配优先级
        random_data = [random.randint(1, 100) for _ in range(10)]
        priority_queue = PriorityQueue()

        # 分配优先级：低优先级分配给高频任务，高优先级分配给低频任务
        for data in random_data:
            priority = random.randint(1, 10)  # 随机生成优先级
            if priority < 4:  # 低优先级分配给高频任务 test_1
                priority_queue.push((tmp.test_1, data), priority)
            elif priority < 7:  # 中优先级分配给 test_0
                priority_queue.push((tmp.test_0, data), priority)
            else:  # 高优先级分配给低频任务 test_2
                priority_queue.push((tmp.test_2, data), priority)

        # 将优先级队列中的任务加入到 agent 的事件队列
        while not priority_queue.is_empty():
            task, data = priority_queue.pop()
            if task == tmp.test_1:
                self.agent.event(100, task, self)  # 高频任务，周期短
            elif task == tmp.test_0:
                self.agent.event(500, task, self)  # 中频任务
            else:
                self.agent.event(2000, task, self)  # 低频任务，周期长

        # 运行任务
        while True:
            self.agent.parallel_cycle()
            time.sleep(0.1)


if __name__ == "__main__":
    system = agent()
    dls_task_instance = dls_task(system)
    dls_task_instance.run()