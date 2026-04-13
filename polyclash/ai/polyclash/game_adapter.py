"""Game adapter: implements the AlphaZero Game interface for spherical Go.

This bridges polyclash's pure rules engine with HRMGo's MCTS/Coach framework.
All state is carried in PolyclashState objects — no mutable game state.
"""

from __future__ import annotations

import numpy as np

from polyclash.ai.core.game import Game
from polyclash.ai.polyclash.rules import (
    BLACK,
    WHITE,
    apply_move,
    score,
    terminal_result,
    valid_moves,
)
from polyclash.ai.polyclash.state import PolyclashState
from polyclash.ai.polyclash.topology import (
    ACTION_SIZE,
    NUM_POINTS,
    PASS_ACTION,
    symmetry_perms,
)


class PolyclashGame(Game):
    """Spherical Go on a snub dodecahedron (302 vertices).

    Convention:
    - Player 1 = BLACK = +1
    - Player -1 = WHITE = -1
    - Board state is a PolyclashState object (not a raw ndarray)
    - canonical_form flips stones so current player always sees self as +1
    """

    # Number of random symmetry augmentations per training example (besides identity).
    # Set to 0 to disable, or up to 59 for all rotations.
    DEFAULT_SYM_SAMPLES = 5

    def __init__(self, max_moves: int = 450, sym_samples: int | None = None) -> None:
        super().__init__()
        self._max_moves = max_moves
        self._sym_samples = (
            sym_samples if sym_samples is not None else self.DEFAULT_SYM_SAMPLES
        )

    def init_board(self) -> PolyclashState:
        return PolyclashState.initial()

    def board_size(self) -> tuple[int, int]:
        return (NUM_POINTS, 1)

    def action_size(self) -> int:
        return ACTION_SIZE

    def get_max_moves(self) -> int:
        return self._max_moves

    def next_state(
        self, board: PolyclashState, player: int, action: int
    ) -> tuple[PolyclashState, int]:
        result = apply_move(board, player, action)
        if result is None:
            # Fallback: if invalid, treat as pass (should not happen with proper valid_moves)
            result = apply_move(board, player, PASS_ACTION)
            assert result is not None
        return result, -player

    def valid_moves(self, board: PolyclashState, player: int) -> np.ndarray:
        return valid_moves(board, player)

    def game_ended(self, board: PolyclashState, player: int) -> float:
        """Returns result from BLACK's perspective (absolute, not relative to player).

        0 if not ended, 1 if BLACK won, -1 if WHITE won, 1e-4 for draw.
        """
        return terminal_result(board)

    def canonical_form(self, board: PolyclashState, player: int) -> PolyclashState:
        """Return board from current player's perspective.

        If player is BLACK (1), return as-is.
        If player is WHITE (-1), flip all stones so current player sees +1.
        """
        if player == BLACK:
            return board
        return board.flip()

    def symmetries(
        self, board: PolyclashState, pi: list[float] | np.ndarray
    ) -> list[tuple[PolyclashState, list[float]]]:
        """Return symmetry-augmented (board, pi) pairs.

        Uses the 60 icosahedral rotations of the snub dodecahedron.
        Returns identity + _sym_samples random rotations to avoid
        exploding dataset size.
        """
        pi_arr = np.asarray(pi, dtype=np.float64)
        assert len(pi_arr) == ACTION_SIZE
        pi_list = pi_arr.tolist()

        result: list[tuple[PolyclashState, list[float]]] = [(board, pi_list)]

        if self._sym_samples <= 0:
            return result

        # Sample random rotation indices (1..59, excluding identity at 0)
        n = min(self._sym_samples, 59)
        chosen = np.random.choice(59, size=n, replace=False) + 1

        for idx in chosen:
            perm = symmetry_perms[idx]  # perm[new_pos] = old_pos

            # Permute stones: new_stones[i] = old_stones[perm[i]]
            new_stones = board.stones[perm]

            new_state = PolyclashState(
                stones=new_stones,
                ko_point=-1,
                consecutive_passes=board.consecutive_passes,
                move_count=board.move_count,
                zobrist_hash=0,
                history_hashes=frozenset(),
            )

            # Permute policy: new_pi[i] = old_pi[perm[i]]
            new_pi = np.empty_like(pi_arr)
            new_pi[:NUM_POINTS] = pi_arr[perm]
            new_pi[PASS_ACTION] = pi_arr[PASS_ACTION]

            result.append((new_state, new_pi.tolist()))

        return result

    def representation(self, board: PolyclashState) -> bytes:
        return board.representation()

    def score_board(self, board: PolyclashState) -> tuple[float, float, float]:
        """Score under area rules. Returns (black_ratio, white_ratio, unclaimed_ratio)."""
        return score(board)

    @staticmethod
    def display(board: PolyclashState) -> None:
        """Simple text display of board state."""
        stones = board.stones
        black_count = int(np.sum(stones == BLACK))
        white_count = int(np.sum(stones == WHITE))
        empty_count = int(np.sum(stones == 0))
        b_ratio, w_ratio, u_ratio = score(board)
        print(
            f"Move {board.move_count} | B:{black_count} W:{white_count} E:{empty_count}"
        )
        print(f"Score: B={b_ratio:.3f} W={w_ratio:.3f} U={u_ratio:.3f}")
        if board.ko_point >= 0:
            print(f"Ko at point {board.ko_point}")
