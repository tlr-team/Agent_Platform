from collections import deque


class TaskScheduler:
    '''
        Represents an ordered Scheduler.
    '''

    def __init__(self):
        self._task_deque = deque()

    def new_task(self, task):
        '''
            Admit a newly started task to the scheduler\n
            (must be a generator `yield`)
        '''
        self._task_deque.append(task)

    def run(self):
        '''
            Run until there are no more tasks
        '''
        while self._task_deque:
            task = self._task_deque.popleft()
            try:
                # Run the task until the next yield
                next(task)

                # Not ended
                self._task_deque.append(task)
            except StopIteration:
                # Generator is no longer executing
                pass


# Two simple generator functions
def __countdown(n):
    while n > 0:
        print('T-minus', n)
        yield
        n -= 1
    print('Blastoff!')


def __countup(n):
    x = 0
    while x < n:
        print('Counting up', x)
        yield
        x += 1


if __name__ == "__main__":
    # Example use
    sched = TaskScheduler()
    sched.new_task(__countdown(10))
    sched.new_task(__countdown(5))
    sched.new_task(__countup(15))
    sched.run()

    # output:
    # T-minus 10
    # T-minus 5
    # Counting up 0
    # T-minus 9
    # T-minus 4
    # Counting up 1
    # T-minus 8
    # T-minus 3
    # Counting up 2
    # T-minus 7
    # T-minus 2
    # Counting up 3
    # T-minus 6
    # T-minus 1
    # Counting up 4
    # T-minus 5
    # Blastoff!
    # Counting up 5
    # T-minus 4
    # Counting up 6
    # T-minus 3
    # Counting up 7
    # T-minus 2
    # Counting up 8
    # T-minus 1
    # Counting up 9
    # Blastoff!
    # Counting up 10
    # Counting up 11
    # Counting up 12
    # Counting up 13
    # Counting up 14

