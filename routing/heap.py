"""Binary min-heap, written by hand (no heapq).

Stored in a list: the children of index i are at 2i+1 and 2i+2,
and the parent of i is at (i-1)//2. push and pop are O(log n).
"""


class MinHeap:
    def __init__(self):
        self._items = []  # list of (priority, value)

    def __len__(self):
        return len(self._items)

    def push(self, value, priority):
        self._items.append((priority, value))
        self._sift_up(len(self._items) - 1)

    def pop(self):
        """Remove and return (value, priority) with the smallest priority, or None if empty."""
        items = self._items
        if not items:
            return None
        top = items[0]
        last = items.pop()
        if items:
            items[0] = last
            self._sift_down(0)
        return top[1], top[0]

    def _sift_up(self, i):
        items = self._items
        while i > 0:
            parent = (i - 1) // 2
            if items[parent][0] <= items[i][0]:
                break
            items[parent], items[i] = items[i], items[parent]
            i = parent

    def _sift_down(self, i):
        items = self._items
        n = len(items)
        while True:
            left = 2 * i + 1
            right = left + 1
            smallest = i
            if left < n and items[left][0] < items[smallest][0]:
                smallest = left
            if right < n and items[right][0] < items[smallest][0]:
                smallest = right
            if smallest == i:
                return
            items[smallest], items[i] = items[i], items[smallest]
            i = smallest
