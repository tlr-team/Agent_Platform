import operator


def shared_prefix(*args):
    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1
    return args[0][:i]

class node:
    def __init__(self,value,tree_constant):
        self.id
        self.value = id ^ tree_constant

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

class Sorted_Queue:
    def __init__(self, k, main_id):
        self.k = k
        self.queue = []
        self.mid = main_id
    
    def __add(nde: node):
        for i in range(0, len(self.queue)):
            if nde < self.queue:
                self.queue.insert(i, nde)
        if(len(self.queue) > k):
            self.queue.pop()

    def add(id):
        self.add(node(id,self.main_id))


    def getall():
        return [ i.value for i in self.queue ]