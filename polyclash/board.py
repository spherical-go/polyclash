import numpy as np

from polyclash.data import neighbors


BLACK = 1
WHITE = -1


class Board:
    def __init__(self):
        self.board_size = 302
        self.board = np.zeros([self.board_size])
        self.current_player = BLACK
        self.neighbors = neighbors

        self._observers = []

    def register_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self, message, **kwargs):
        for observer in self._observers:
            observer.handle(message, **kwargs)

    def has_liberty(self, point, color=None, visited=None):
        if color is None:
            color = self.board[point]

        if visited is None:
            visited = set()  # 用于记录已经检查过的点

        if point in visited:
            return False  # 如果已经访问过这个点，不再重复检查
        visited.add(point)

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == 0:  # 如果邻居是空的，则有气
                return True
            elif self.board[neighbor] == color and self.has_liberty(neighbor, color, visited):
                # 如果邻居是同色，并且递归发现有气，那么这个点也有气
                return True

        # 如果所有路径都检查完毕，仍然没有发现有气，返回False
        return False

    def remove_stones(self, point):
        color = self.board[point]
        self.board[point] = 0
        self.notify_observers("remove_stones", point=point)  # 通知观察者，有棋子被移除

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == color:
                self.remove_stones(neighbor)

    def play(self, point, color):
        if self.board[point] != 0:
            raise ValueError("Invalid move: position already occupied.")

        self.board[point] = color

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == -color:       # Opponent's stone
                if not self.has_liberty(neighbor):
                    self.remove_stones(neighbor)

        if not self.has_liberty(point):
            # 如果自己的棋也没有气，则为自杀棋，撤回落子
            self.board[point] = 0
            raise ValueError("Invalid move: suicide is not allowed.")

    def genmove(self, color):
        from random import randint
        # 从盘面空闲处（值为 0 处）随机的选择一个位置
        candidate = []
        for i in range(self.board_size):
            if self.board[i] == 0:
                candidate.append(i)
        return candidate[randint(len(candidate))]

