import heapq

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

    def clear(self):
        self.heap = []

    def is_empty(self):
        return len(self.heap) == 0

    def size(self):
        return len(self.heap)
    
    @staticmethod
    def unit_test():
        # Initialize the priority queue
        pq = PriorityQueue()
        print("Queue is empty:", pq.is_empty())  # Should print True
        print("Queue size:", pq.size())  # Should print 0

        # Test push method
        pq.push("task1", 3)
        pq.push("task2", 1)
        pq.push("task3", 2)
        print("Queue is empty after push:", pq.is_empty())  # Should print False
        print("Queue size after push:", pq.size())  # Should print 3

        # Test peek method
        try:
            print("Highest priority item:", pq.peek())  # Should print "task2"
        except IndexError as e:
            print("Peek error:", e)

        # Test pop method
        try:
            print("Popped item:", pq.pop())  # Should print "task2"
            print("Queue size after pop:", pq.size())  # Should print 2
            print("Highest priority item after pop:", pq.peek())  # Should print "task3"
            print("Popped item:", pq.pop())  # Should print "task3"
            print("Queue size after pop:", pq.size())  # Should print 1
            print("Highest priority item after pop:", pq.peek())  # Should print "task1"
            print("Popped item:", pq.pop())  # Should print "task1"
            print("Queue size after pop:", pq.size())  # Should print 0
        except IndexError as e:
            print("Pop error:", e)

        # Test pop and peek from an empty queue
        try:
            print("Try to pop from an empty queue:", pq.pop())
        except IndexError as e:
            print("Pop from empty queue error:", e)  # Should raise IndexError

        try:
            print("Try to peek from an empty queue:", pq.peek())
        except IndexError as e:
            print("Peek from empty queue error:", e)  # Should raise IndexError

        # Test is_empty and size again
        print("Queue is empty:", pq.is_empty())  # Should print True
        print("Queue size:", pq.size())  # Should print 0

        # Test clear method
        pq.push("task4", 4)
        pq.push("task5", 5)
        print("Queue size before clear:", pq.size())  # Should print 2
        pq.clear()
        print("Queue size after clear:", pq.size())  # Should print 0
        print("Queue is empty after clear:", pq.is_empty())  # Should print True

        # Test pop and peek after clear
        try:
            print("Try to pop from an empty queue after clear:", pq.pop())
        except IndexError as e:
            print("Pop from empty queue after clear error:", e)  # Should raise IndexError

        try:
            print("Try to peek from an empty queue after clear:", pq.peek())
        except IndexError as e:
            print("Peek from empty queue after clear error:", e)  # Should raise IndexError

if __name__ == "__main__":
    PriorityQueue.unit_test()
    