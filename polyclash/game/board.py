

import numpy as np
import math

from random import sample
from collections import OrderedDict
from polyclash.data.data import cities, neighbors, polysmalls, polylarges, polylarge_area, polysmall_area, total_area, \
    encoder

BLACK = 1
WHITE = -1


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


def calculate_distance(point1, point2):
    city1 = cities[point1]
    city2 = cities[point2]
    return np.linalg.norm(city1 - city2)


def calculate_potential(board, point, counter):
    potential = 0
    for i, stone in enumerate(board):
        if stone != 0:
            distance = calculate_distance(point, i)
            if distance > 0:
                potential += (1 / distance) * np.tanh(0.5 - counter / 302)
    return potential


class Board:
    def __init__(self):
        self.board_size = 302
        self.board = np.zeros([self.board_size])
        self.current_player = BLACK
        self.neighbors = neighbors
        self.latest_player = None
        self.latest_removes = [[]]
        self.black_suicides = set()
        self.white_suicides = set()

        self.turns = OrderedDict()

        self._observers = []
        self.notification_enabled = True

        self.simulator = None

    @property
    def counter(self):
        return len(self.turns)

    def register_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister_observer(self, observer):
        self._observers.remove(observer)

    def enable_notification(self):
        self.notification_enabled = True

    def disable_notification(self):
        self.notification_enabled = False

    def notify_observers(self, message, **kwargs):
        for observer in self._observers:
            if self.notification_enabled:
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

    def remove_stone(self, point):
        color = self.board[point]
        self.board[point] = 0
        self.latest_removes[-1].append(point)
        self.notify_observers("remove_stone", point=point, score=self.score())

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == color:
                self.remove_stone(neighbor)

    def reset(self):
        self.board = np.zeros([self.board_size])
        self.current_player = BLACK
        self.latest_removes = [[]]
        self.black_suicides = set()
        self.white_suicides = set()
        self.turns = OrderedDict()
        self.notify_observers("reset", **{})

    def switch_player(self):
        self.current_player = -self.current_player
        self.notify_observers("switch_player", side=self.current_player)

    def play(self, point, player, turn_check=True):
        if self.latest_player and self.latest_player == player:
            return

        if self.board[point] != 0:
            raise ValueError("Invalid move: position already occupied.")

        if point >= 302:
            raise ValueError("Invalid move: position not on the board.")

        if player == BLACK and self.counter % 2 == 1:
            raise ValueError("Invalid move: not the player's turn.")

        if player == WHITE and self.counter % 2 == 0:
            raise ValueError("Invalid move: not the player's turn.")

        if turn_check and player != self.current_player:
            raise ValueError("Invalid move: not the player's turn.")

        if self.latest_removes and len(self.latest_removes[-1]) == 1 and point == self.latest_removes[-1][0]:
            raise ValueError("Invalid move: ko rule violation.")

        # if player == BLACK and point in self.white_suicides:
        #     self.white_suicides.remove(point)

        # if player == WHITE and point in self.black_suicides:
        #     self.black_suicides.remove(point)

        self.board[point] = player
        # print(point, encoder[point], self.neighbors[point])

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == -player:  # Opponent's stone
                if not self.has_liberty(neighbor, -player):
                    self.remove_stone(neighbor)

        if not self.has_liberty(point):
            # 如果自己的棋也没有气，则为自杀棋，撤回落子
            self.board[point] = 0
            if player == BLACK:
                self.black_suicides.add(point)
            else:
                self.white_suicides.add(point)
            raise ValueError("Invalid move: suicide is not allowed.")

        self.turns[self.counter] = encoder[point]
        self.notify_observers("add_stone", point=point, player=player, score=self.score())
        self.latest_player = player

    def get_empties(self, player):
        empty_points = set([ix for ix, point in enumerate(self.board) if point == 0])
        if self.latest_removes and len(self.latest_removes[-1]) == 1 and self.latest_removes[-1][0] in empty_points:
            empty_points.remove(self.latest_removes[-1][0])
        if player == BLACK:
            for point in self.black_suicides:
                empty_points.remove(point)
        if player == WHITE:
            for point in self.white_suicides:
                empty_points.remove(point)
        return list(empty_points)

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

    def is_game_over(self):
        return len(self.get_empties(self.current_player)) == 0

    def result(self):
        return {}

    def genmove(self, player):
        if self.simulator is None:
            self.simulator = SimulatedBoard()
        self.simulator.redirect(self)
        return self.simulator.genmove(player)


class SimulatedBoard(Board):
    def __init__(self):
        super().__init__()

    def redirect(self, board):
        self.board = board.board.copy()
        self.current_player = board.current_player
        self.latest_removes = board.latest_removes.copy()
        self.black_suicides = board.black_suicides.copy()
        self.white_suicides = board.white_suicides.copy()
        self.orginal_counter = board.counter
        self.turns = board.turns.copy()

    def genmove(self, player):
        best_score = -math.inf
        best_potential = math.inf
        best_move = None

        for point in self.get_empties(player):
            simulated_score, gain = self.simulate_score(0, point, player)
            simulated_score = simulated_score + 2 * gain
            if simulated_score > best_score:
                best_score = simulated_score
                best_potential = calculate_potential(self.board, point, self.counter)
                best_move = point
            elif simulated_score == best_score:
                potential = calculate_potential(self.board, point, self.counter)
                if potential < best_potential:
                    best_potential = potential
                    best_move = point

        return best_move

    def simulate_score(self, depth, point, player):
        if depth == 1:
            return 0, 0

        trail = 2
        self.latest_removes.append([])
        black_area_ratio, white_area_ratio, unclaimed_area_ratio = 0, 0, 0
        mean_rival_area_ratio, gain, mean_rival_gain = 0, 0, 0
        try:
            # 假设在 point 落子，计算得分，需要考虑复原棋盘的状态
            self.play(point, player, turn_check=False)  # 模拟落子
            black_area_ratio, white_area_ratio, unclaimed_area_ratio = self.score()  # 计算得分

            empty_points = sample(self.get_empties(-player), trail)
            total_rival_area_ratio, total_rival_gain = 0, 0
            for rival_point in empty_points:
                rival_area_ratio, rival_gain = self.simulate_score(depth + 1, rival_point, -player)  # 递归计算对手的得分
                total_rival_area_ratio += rival_area_ratio
                total_rival_gain += rival_gain
            mean_rival_area_ratio = total_rival_area_ratio / trail
            mean_rival_gain = total_rival_gain / trail
        except ValueError as e:
            print(e)
            if 'suicide' in str(e):
                raise e

        self.board[point] = 0  # 恢复棋盘状态
        gain = 0
        if self.latest_removes and len(self.latest_removes) > 0:
            for removed in self.latest_removes[-1]:
                self.board[removed] = -self.current_player
            gain = len(self.latest_removes[-1]) / len(self.board)
            self.latest_removes.pop()

        if self.counter > self.orginal_counter:
            self.turns.pop(self.counter - 1)

        if player == BLACK:
            # print(black_area_ratio, mean_rival_area_ratio, gain, mean_rival_gain)
            return black_area_ratio - mean_rival_area_ratio, gain - mean_rival_gain
        else:
            # print(white_area_ratio, mean_rival_area_ratio, gain, mean_rival_gain)
            return white_area_ratio - mean_rival_area_ratio, gain - mean_rival_gain
