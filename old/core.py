
# This file is part of MaixUI
# Copyright (c) sipeed.com
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#

class agent:

  def __init__(self):
    self.msg = []
    self.arg = {}

    import time
    self.get_ms = (lambda : time.ticks_ms()) if getattr(time, "ticks_ms", False) else (lambda : time.time() * 1000)

  def event(self, cycle, func, args=None):
    # arrived, cycle, function
    tmp = (self.get_ms() + cycle, cycle, func, args)
    #print('self.event', tmp)
    self.msg.append(tmp)

  def remove(self, func):
    #print(self.remove)
    for pos in range(len(self.msg)): # maybe use map
      #print(self.msg[pos][2], func)
      if self.msg[pos][2] == func:
          self.msg.remove(self.msg[pos])
          break
    #print(self.msg)

  def call(self, obj, pos=0):
    #print(self.call, pos, obj)
    self.msg.pop(pos)
    self.event(obj[1], obj[2], obj[3])
    obj[2](obj[3]) if obj[3] else obj[2]() # exec function

  def cycle(self):
    if (len(self.msg)):
      obj = self.msg[0]
      if (self.get_ms() >= obj[0]):
        self.call(obj, 0)

  def parallel_cycle(self):
    for pos in range(len(self.msg)): # maybe use map
      obj = self.msg[pos]
      if (self.get_ms() >= obj[0]):
        self.call(obj, pos)
        break

  def unit_test(self):

    class tmp:
        def test_0(self):
          print('test_0')

        def test_1():
          print('test_1')

        def test_2(self):
          print('test_2')
          self.remove(tmp.test_1)
          self.event(1000, tmp.test_1)
          self.remove(tmp.test_2)

    import time
    self.event(200, tmp.test_0, self)
    self.event(10, tmp.test_1)
    self.event(2000, tmp.test_2, self)
    while True:
      self.parallel_cycle()
      # time.sleep(0.1)

system = agent()

import heapq

class PriorityQueue:
    def __init__(self):
        # 初始化一个空的堆
        self.heap = []

    def push(self, item, priority):
        # 使用元组 (priority, item) 来存储元素，heapq 会根据元组的第一个元素（优先级）来排序
        heapq.heappush(self.heap, (priority, item))

    def pop(self):
        # 弹出优先级最高的元素（即优先级值最小的元素）
        if self.heap:
            return heapq.heappop(self.heap)[1]
        else:
            raise IndexError("pop from an empty priority queue")

    def peek(self):
        # 查看优先级最高的元素，但不弹出
        if self.heap:
            return self.heap[0][1]
        else:
            raise IndexError("peek from an empty priority queue")

    def is_empty(self):
        # 判断堆是否为空
        return len(self.heap) == 0

    def size(self):
        # 返回堆的大小
        return len(self.heap)

    def unit_test(self):
        pq = PriorityQueue()
        pq.push("task1", priority=3)
        pq.push("task2", priority=1)
        pq.push("task3", priority=2)

        print("Peek:", pq.peek())  # 查看优先级最高的任务
        while not pq.is_empty():
            print("Pop:", pq.pop())  # 按优先级顺序弹出任务
          
if __name__ == "__main__":
  PriorityQueue().unit_test()
  # system.unit_test()
