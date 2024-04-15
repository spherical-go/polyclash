import numpy as np

from collections import OrderedDict
from polyclash.data import neighbors, polysmalls, polylarges, polylarge_area, polysmall_area, total_area, encoder

BLACK = 1
WHITE = -1

counter = 0
turns = OrderedDict()


def calculate_area(boarddata, piece, area):
    black_area, white_area, unclaimed_area = 0, 0, 0
    parties = boarddata[piece]
    parties_set = set(parties)
    if BLACK not in parties_set and WHITE not in parties_set:
        unclaimed_area += area
    if BLACK in parties_set and WHITE not in parties_set:
        black_area += area
    if WHITE in parties_set and BLACK not in parties_set:
        white_area += area
    if BLACK in parties_set and WHITE in parties_set:
        black_side, white_side = 0, 0
        for part in parties:
            if part == BLACK:
                black_side += 1
            if part == WHITE:
                white_side += 1
        black_area += area / (black_side + white_side) * black_side
        white_area += area / (black_side + white_side) * white_side
    return black_area, white_area, unclaimed_area


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
            observer.handle_notification(message, **kwargs)

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
        self.notify_observers("remove_stones", point=point, score=self.score())

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == color:
                self.remove_stones(neighbor)

    def switch_player(self):
        self.current_player = -self.current_player
        self.notify_observers("switch_player", side=self.current_player)

    def play(self, point, color):
        global counter
        if self.board[point] != 0:
            raise ValueError("Invalid move: position already occupied.")

        if color != self.current_player:
            raise ValueError("Invalid move: not the player's turn.")

        if point >= 302:
            raise ValueError("Invalid move: position not on the board.")

        if color == BLACK and counter % 2 == 1:
            raise ValueError("Invalid move: not the player's turn.")

        if color == WHITE and counter % 2 == 0:
            raise ValueError("Invalid move: not the player's turn.")

        self.board[point] = color

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == -color:  # Opponent's stone
                if not self.has_liberty(neighbor):
                    self.remove_stones(neighbor)

        if not self.has_liberty(point):
            # 如果自己的棋也没有气，则为自杀棋，撤回落子
            self.board[point] = 0
            raise ValueError("Invalid move: suicide is not allowed.")

        turns[counter] = encoder[point]
        counter += 1

        self.notify_observers("add_stone", point=point, color=color, score=self.score())

    def genmove(self, color):
        from random import randint
        # 从盘面空闲处（值为 0 处）随机的选择一个位置
        candidate = []
        for i in range(self.board_size):
            if self.board[i] == 0:
                candidate.append(i)
        return candidate[randint(len(candidate))]

    def score(self):
        total_black_area, total_white_area, total_unclaimed_area = 0, 0, 0
        for piece in polysmalls:
            black_area, white_area, unclaimed_area = calculate_area(self.board, piece, polysmall_area)
            total_black_area += black_area
            total_white_area += white_area
            total_unclaimed_area += unclaimed_area
        for piece in polylarges:
            black_area, white_area, unclaimed_area = calculate_area(self.board, piece, polylarge_area)
            total_black_area += black_area
            total_white_area += white_area
            total_unclaimed_area += unclaimed_area

        return total_black_area / total_area, total_white_area / total_area, total_unclaimed_area / total_area


board = Board()
