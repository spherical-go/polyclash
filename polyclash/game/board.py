import hashlib
import math
import os
from collections import OrderedDict
from random import sample

import numpy as np

from polyclash.data.data import (
    cities,
    encoder,
    neighbors,
    polylarge_area,
    polylarges,
    polysmall_area,
    polysmalls,
    total_area,
)

BLACK = 1
WHITE = -1

# Default komi as a fraction of total area (0.025 = 2.5%, ≈ 7.6 positions).
# Override with POLYCLASH_KOMI environment variable.
DEFAULT_KOMI: float = float(os.environ.get("POLYCLASH_KOMI", "0.025"))


def _init_zobrist() -> tuple[list[int], list[int]]:
    """Generate Zobrist random numbers deterministically from a seed."""
    keys_black: list[int] = []
    keys_white: list[int] = []
    for i in range(302):
        seed_b = hashlib.sha256(f"zobrist_black_{i}".encode()).digest()
        seed_w = hashlib.sha256(f"zobrist_white_{i}".encode()).digest()
        keys_black.append(int.from_bytes(seed_b[:8], "big"))
        keys_white.append(int.from_bytes(seed_w[:8], "big"))
    return keys_black, keys_white


ZOBRIST_BLACK, ZOBRIST_WHITE = _init_zobrist()


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
    def __init__(self) -> None:
        self.board_size = 302
        self.board = np.zeros([self.board_size])
        self.current_player = BLACK
        self.neighbors = neighbors
        self.latest_player: int | None = None
        self.latest_removes: list[list[int]] = [[]]
        self.black_suicides: set[int] = set()
        self.white_suicides: set[int] = set()

        self.turns: OrderedDict[int, tuple[int, ...]] = OrderedDict()

        self._observers: list[object] = []
        self.notification_enabled = True

        self.simulator: "SimulatedBoard | None" = None

        self.zobrist_hash: int = 0
        self.history_hashes: set[int] = set()
        self.komi: float = DEFAULT_KOMI
        self.consecutive_passes: int = 0

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
            elif self.board[neighbor] == color and self.has_liberty(
                neighbor, color, visited
            ):
                # 如果邻居是同色，并且递归发现有气，那么这个点也有气
                return True

        # 如果所有路径都检查完毕，仍然没有发现有气，返回False
        return False

    def remove_stone(self, point: int) -> None:
        color = self.board[point]
        if color == BLACK:
            self.zobrist_hash ^= ZOBRIST_BLACK[point]
        elif color == WHITE:
            self.zobrist_hash ^= ZOBRIST_WHITE[point]
        self.board[point] = 0
        self.latest_removes[-1].append(point)
        # Removing a stone may open liberties, so clear cached suicide sets
        self.black_suicides.discard(point)
        self.white_suicides.discard(point)
        self.notify_observers("remove_stone", point=point, score=self.score())

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == color:
                self.remove_stone(neighbor)

    def reset(self) -> None:
        self.board = np.zeros([self.board_size])
        self.current_player = BLACK
        self.latest_removes = [[]]
        self.black_suicides = set()
        self.white_suicides = set()
        self.turns = OrderedDict()
        self.zobrist_hash = 0
        self.history_hashes = set()
        self.consecutive_passes = 0
        self.notify_observers("reset", **{})

    def switch_player(self):
        self.current_player = -self.current_player
        self.notify_observers("switch_player", side=self.current_player)

    def play(self, point: int, player: int, turn_check: bool = True) -> None:
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

        # Save zobrist hash before the move for rollback on suicide
        prev_zobrist = self.zobrist_hash

        # Start a new capture list for this move
        self.latest_removes.append([])

        self.board[point] = player
        if player == BLACK:
            self.zobrist_hash ^= ZOBRIST_BLACK[point]
        else:
            self.zobrist_hash ^= ZOBRIST_WHITE[point]

        for neighbor in self.neighbors[point]:
            if self.board[neighbor] == -player:  # Opponent's stone
                if not self.has_liberty(neighbor, -player):
                    self.remove_stone(neighbor)

        if not self.has_liberty(point):
            self.board[point] = 0
            self.zobrist_hash = prev_zobrist
            if player == BLACK:
                self.black_suicides.add(point)
            else:
                self.white_suicides.add(point)
            raise ValueError("Invalid move: suicide is not allowed.")

        if self.zobrist_hash in self.history_hashes:
            # Undo the move: restore board and zobrist hash
            self.board[point] = 0
            for removed in self.latest_removes[-1]:
                self.board[removed] = -player
            self.zobrist_hash = prev_zobrist
            raise ValueError("Invalid move: superko violation.")

        self.history_hashes.add(self.zobrist_hash)
        self.turns[self.counter] = encoder[point]
        self.notify_observers(
            "add_stone", point=point, player=player, score=self.score()
        )
        self.latest_player = player

    def get_empties(self, player: int) -> list[int]:
        empty_points = set([ix for ix, point in enumerate(self.board) if point == 0])
        if player == BLACK:
            for point in self.black_suicides:
                empty_points.discard(point)
        if player == WHITE:
            for point in self.white_suicides:
                empty_points.discard(point)
        return list(empty_points)

    def score(self):
        total_black_area, total_white_area, total_unclaimed_area = 0, 0, 0
        for piece in polysmalls:
            black_area, white_area, unclaimed_area = calculate_area(
                self.board, piece, polysmall_area
            )
            total_black_area += black_area
            total_white_area += white_area
            total_unclaimed_area += unclaimed_area
        for piece in polylarges:
            black_area, white_area, unclaimed_area = calculate_area(
                self.board, piece, polylarge_area
            )
            total_black_area += black_area
            total_white_area += white_area
            total_unclaimed_area += unclaimed_area

        return (
            total_black_area / total_area,
            total_white_area / total_area,
            total_unclaimed_area / total_area,
        )

    def final_score(self) -> tuple[float, float]:
        """Return (black_score, white_score) with komi applied to white.

        ``komi`` is a fraction of total area (e.g. 0.025 = 2.5%).
        """
        black_ratio, white_ratio, _ = self.score()
        return black_ratio, white_ratio + self.komi

    def is_game_over(self) -> bool:
        if self.consecutive_passes >= 2:
            return True
        return len(self.get_empties(self.current_player)) == 0

    def to_dict(self) -> dict:
        """Serialize board state to a JSON-compatible dict."""
        return {
            "board": self.board.tolist(),
            "current_player": self.current_player,
            "latest_player": self.latest_player,
            "latest_removes": self.latest_removes,
            "black_suicides": sorted(self.black_suicides),
            "white_suicides": sorted(self.white_suicides),
            "turns": {str(k): list(v) for k, v in self.turns.items()},
            "zobrist_hash": self.zobrist_hash,
            "history_hashes": sorted(self.history_hashes),
            "komi": self.komi,
            "consecutive_passes": self.consecutive_passes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Board":
        """Restore a Board from a serialized dict."""
        board = cls()
        board.board = np.array(data["board"])
        board.current_player = data["current_player"]
        board.latest_player = data["latest_player"]
        board.latest_removes = data["latest_removes"]
        board.black_suicides = set(data["black_suicides"])
        board.white_suicides = set(data["white_suicides"])
        board.turns = OrderedDict((int(k), tuple(v)) for k, v in data["turns"].items())
        board.zobrist_hash = data["zobrist_hash"]
        board.history_hashes = set(data["history_hashes"])
        board.komi = data["komi"]
        board.consecutive_passes = data["consecutive_passes"]
        board.disable_notification()
        return board

    def result(self):
        return {}

    def genmove(self, player):
        if self.simulator is None:
            self.simulator = SimulatedBoard()
        self.simulator.redirect(self)
        return self.simulator.genmove(player)

    def rank_moves(self, player: int) -> list[int]:
        """Return all candidate moves sorted by score (best first)."""
        if self.simulator is None:
            self.simulator = SimulatedBoard()
        self.simulator.redirect(self)
        return self.simulator.rank_moves(player)


class SimulatedBoard(Board):
    def __init__(self):
        super().__init__()

    def redirect(self, board: Board) -> None:
        self.board = board.board.copy()
        self.current_player = board.current_player
        self.latest_removes = board.latest_removes.copy()
        self.black_suicides = board.black_suicides.copy()
        self.white_suicides = board.white_suicides.copy()
        self.orginal_counter = board.counter
        self.turns = board.turns.copy()
        self.zobrist_hash = board.zobrist_hash
        self.history_hashes = set()  # don't enforce superko in simulation

    def genmove(self, player):
        ranked = self.rank_moves(player)
        return ranked[0] if ranked else None

    def rank_moves(self, player: int) -> list[int]:
        """Return all candidate moves sorted by heuristic score (best first)."""
        scored: list[tuple[float, float, int]] = []

        for point in self.get_empties(player):
            simulated_score, gain = self.simulate_score(0, point, player)
            simulated_score = simulated_score + 2 * gain
            potential = calculate_potential(self.board, point, self.counter)
            scored.append((simulated_score, potential, point))

        # Sort by score descending, then potential ascending
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [point for _, _, point in scored]

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
            black_area_ratio, white_area_ratio, unclaimed_area_ratio = (
                self.score()
            )  # 计算得分

            empty_points = sample(self.get_empties(-player), trail)
            total_rival_area_ratio, total_rival_gain = 0, 0
            for rival_point in empty_points:
                rival_area_ratio, rival_gain = self.simulate_score(
                    depth + 1, rival_point, -player
                )  # 递归计算对手的得分
                total_rival_area_ratio += rival_area_ratio
                total_rival_gain += rival_gain
            mean_rival_area_ratio = total_rival_area_ratio / trail
            mean_rival_gain = total_rival_gain / trail
        except ValueError:
            # Move is illegal (suicide, superko, etc.) — skip this point
            self.latest_removes.pop()
            return -math.inf, 0

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
