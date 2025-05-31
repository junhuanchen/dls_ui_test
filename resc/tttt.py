import heapq

class PriorityQueue:
    def __init__(self):
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
        return len(self.heap) == 0

    def size(self):
        return len(self.heap)

# 使用示例
if __name__ == "__main__":
    pq = PriorityQueue()
    pq.push("task1", priority=3)
    pq.push("task2", priority=1)
    pq.push("task3", priority=2)

    print("Peek:", pq.peek())  # 查看优先级最高的任务
    while not pq.is_empty():
        print("Pop:", pq.pop())  # 按优先级顺序弹出任务
        