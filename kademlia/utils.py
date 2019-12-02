import operator


def shared_prefix(*args):
    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1
    return args[0][:i]


class Node:
    def __init__(self, value, tree_constant):
        self.id = value.id
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value


class SortedQueue:
    def __init__(self, k, main_id):
        self.k = k
        self.queue = []
        self.mid = main_id

    def __add(self, nde: Node):
        for i in range(0, len(self.queue)):
            if nde < self.queue[i]:
                self.queue.insert(i, nde)
        if len(self.queue) > self.k:
            self.queue.pop()

    def add(self, _id):
        self.add(Node(_id, self.mid))

    def getall(self):
        return [i.value for i in self.queue]

