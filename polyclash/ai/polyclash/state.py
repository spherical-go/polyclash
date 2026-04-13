"""Immutable game state for spherical Go (PolyClash).

The state is designed to be:
- Immutable (safe for MCTS tree search)
- Hashable via representation()
- Pure-functionally transformable

Superko is tracked via Zobrist hashing: ``zobrist_hash`` stores the
current position hash and ``history_hashes`` accumulates all past
position hashes so that positional superko can be enforced in the
rules engine.
"""

from __future__ import annotations

import struct
from typing import Final

import numpy as np

from polyclash.ai.polyclash.topology import NUM_POINTS


class PolyclashState:
    """Immutable game state for spherical Go.

    Attributes:
        stones: np.ndarray of shape (302,), dtype=int8, values in {-1, 0, 1}.
                BLACK=1, WHITE=-1, EMPTY=0
        ko_point: int, the point forbidden by ko rule, or -1 if none
        consecutive_passes: int, number of consecutive passes (game ends at 2)
        move_count: int, total moves played so far
        zobrist_hash: int, Zobrist hash of the current position
        history_hashes: frozenset[int], all past position hashes (for superko)
    """

    __slots__ = (
        "stones",
        "ko_point",
        "consecutive_passes",
        "move_count",
        "zobrist_hash",
        "history_hashes",
    )

    stones: Final[np.ndarray]  # type: ignore[misc]
    ko_point: Final[int]  # type: ignore[misc]
    consecutive_passes: Final[int]  # type: ignore[misc]
    move_count: Final[int]  # type: ignore[misc]
    zobrist_hash: Final[int]  # type: ignore[misc]
    history_hashes: Final[frozenset[int]]  # type: ignore[misc]

    def __init__(
        self,
        stones: np.ndarray,
        ko_point: int = -1,
        consecutive_passes: int = 0,
        move_count: int = 0,
        zobrist_hash: int = 0,
        history_hashes: frozenset[int] = frozenset(),
    ) -> None:
        stones = np.asarray(stones, dtype=np.int8)
        assert stones.shape == (NUM_POINTS,)
        # Make read-only
        stones.flags.writeable = False
        object.__setattr__(self, "stones", stones)
        object.__setattr__(self, "ko_point", ko_point)
        object.__setattr__(self, "consecutive_passes", consecutive_passes)
        object.__setattr__(self, "move_count", move_count)
        object.__setattr__(self, "zobrist_hash", zobrist_hash)
        object.__setattr__(self, "history_hashes", history_hashes)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("PolyclashState is immutable")

    @staticmethod
    def initial() -> PolyclashState:
        """Create the initial empty board state."""
        return PolyclashState(
            stones=np.zeros(NUM_POINTS, dtype=np.int8),
            ko_point=-1,
            consecutive_passes=0,
            move_count=0,
            zobrist_hash=0,
            history_hashes=frozenset(),
        )

    def representation(self) -> bytes:
        """Unique hashable representation for MCTS transposition table.

        Includes stones, zobrist_hash, ko_point, and consecutive_passes to
        avoid false transpositions.
        """
        return self.stones.tobytes() + struct.pack(
            "<QhB", self.zobrist_hash, self.ko_point, self.consecutive_passes
        )

    def with_stones(
        self,
        stones: np.ndarray,
        ko_point: int = -1,
        consecutive_passes: int = 0,
        move_count: int | None = None,
        zobrist_hash: int | None = None,
        history_hashes: frozenset[int] | None = None,
    ) -> PolyclashState:
        """Create a new state with updated fields."""
        return PolyclashState(
            stones=stones,
            ko_point=ko_point,
            consecutive_passes=consecutive_passes,
            move_count=move_count if move_count is not None else self.move_count + 1,
            zobrist_hash=(
                zobrist_hash if zobrist_hash is not None else self.zobrist_hash
            ),
            history_hashes=(
                history_hashes if history_hashes is not None else self.history_hashes
            ),
        )

    def flip(self) -> PolyclashState:
        """Flip stone colors (for canonical form). BLACK <-> WHITE."""
        return PolyclashState(
            stones=-self.stones,
            ko_point=self.ko_point,
            consecutive_passes=self.consecutive_passes,
            move_count=self.move_count,
            zobrist_hash=self.zobrist_hash,
            history_hashes=self.history_hashes,
        )
