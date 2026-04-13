"""Pure functional rules engine for spherical Go.

All functions are stateless — they take a PolyclashState and return
a new PolyclashState (or computed results). No mutation, no side effects.

Rule semantics follow polyclash's Board implementation:
- BLACK = 1, WHITE = -1, EMPTY = 0
- Capture: remove opponent groups with zero liberties after placement
- Suicide: forbidden (move rejected if own group has zero liberties after captures)
- Ko: positional superko via Zobrist hashing
- Game ends after 2 consecutive passes
- Scoring: area-based using polysmall/polylarge face contributions
- Komi: DEFAULT_KOMI (0.025) is added to white's score for tie-breaking
"""

from __future__ import annotations

import hashlib
from collections import deque

import numpy as np

from polyclash.ai.polyclash.state import PolyclashState
from polyclash.ai.polyclash.topology import (
    ACTION_SIZE,
    NUM_POINTS,
    PASS_ACTION,
    neighbor_tuple,
    polylarge_area,
    polylarges,
    polysmall_area,
    polysmalls,
    total_area,
)

BLACK = 1
WHITE = -1
EMPTY = 0
DEFAULT_KOMI = 0.025


def _init_zobrist() -> tuple[list[int], list[int]]:
    keys_black: list[int] = []
    keys_white: list[int] = []
    for i in range(NUM_POINTS):
        seed_b = hashlib.sha256(f"zobrist_black_{i}".encode()).digest()
        seed_w = hashlib.sha256(f"zobrist_white_{i}".encode()).digest()
        keys_black.append(int.from_bytes(seed_b[:8], "big"))
        keys_white.append(int.from_bytes(seed_w[:8], "big"))
    return keys_black, keys_white


ZOBRIST_BLACK, ZOBRIST_WHITE = _init_zobrist()


def find_group(stones: np.ndarray, point: int) -> tuple[set[int], set[int]]:
    """Find the connected group and its liberties starting from point.

    Returns:
        (group, liberties): sets of point indices.
    """
    color = stones[point]
    if color == EMPTY:
        return set(), set()

    group: set[int] = set()
    liberties: set[int] = set()
    queue = deque([point])
    visited = {point}

    while queue:
        p = queue.popleft()
        group.add(p)
        for nb in neighbor_tuple[p]:
            if nb in visited:
                continue
            if stones[nb] == color:
                visited.add(nb)
                queue.append(nb)
            elif stones[nb] == EMPTY:
                liberties.add(nb)

    return group, liberties


def _has_liberty(stones: np.ndarray, point: int) -> bool:
    """Fast check: does the group at point have at least one liberty?

    Like find_group but returns True immediately on first liberty found.
    Avoids building full group/liberties sets.
    """
    color = stones[point]
    if color == EMPTY:
        return True

    visited = {point}
    stack = [point]

    while stack:
        p = stack.pop()
        for nb in neighbor_tuple[p]:
            if nb in visited:
                continue
            val = stones[nb]
            if val == EMPTY:
                return True  # found a liberty — early exit
            if val == color:
                visited.add(nb)
                stack.append(nb)

    return False


def apply_move(
    state: PolyclashState, player: int, action: int
) -> PolyclashState | None:
    """Apply a move and return the new state, or None if illegal.

    Args:
        state: current game state
        player: BLACK (1) or WHITE (-1)
        action: point index (0..301) or PASS_ACTION (302)

    Returns:
        New PolyclashState if legal, None if illegal.
    """
    if action == PASS_ACTION:
        return state.with_stones(
            stones=state.stones,
            ko_point=-1,
            consecutive_passes=state.consecutive_passes + 1,
            zobrist_hash=state.zobrist_hash,
            history_hashes=state.history_hashes,
        )

    if not (0 <= action < NUM_POINTS):
        return None

    if state.stones[action] != EMPTY:
        return None

    new_stones = np.array(state.stones, dtype=np.int8)
    new_stones[action] = player

    # Capture opponent groups with zero liberties
    captured: list[int] = []
    opponent = -player
    for nb in neighbor_tuple[action]:
        if new_stones[nb] == opponent:
            group, liberties = find_group(new_stones, nb)
            if not liberties:
                for p in group:
                    new_stones[p] = EMPTY
                    captured.append(p)

    # Check suicide (fast early-exit version)
    if not _has_liberty(new_stones, action):
        return None  # suicide forbidden

    # Compute Zobrist hash for the new position
    new_hash = state.zobrist_hash
    zkey = ZOBRIST_BLACK if player == BLACK else ZOBRIST_WHITE
    new_hash ^= zkey[action]
    opp_zkey = ZOBRIST_WHITE if player == BLACK else ZOBRIST_BLACK
    for cp in captured:
        new_hash ^= opp_zkey[cp]

    # Positional superko check
    if new_hash in state.history_hashes:
        return None

    new_history = state.history_hashes | {new_hash}

    return state.with_stones(
        stones=new_stones,
        ko_point=-1,
        consecutive_passes=0,
        zobrist_hash=new_hash,
        history_hashes=new_history,
    )


def valid_moves(state: PolyclashState, player: int) -> np.ndarray:
    """Return binary vector of size ACTION_SIZE (303). 1 = legal, 0 = illegal."""
    valids = np.zeros(ACTION_SIZE, dtype=np.int32)
    stones = state.stones
    opponent = -player

    # Single mutable copy reused for all points
    stones_sim = np.array(stones, dtype=np.int8)

    for point in range(NUM_POINTS):
        if stones[point] != EMPTY:
            continue

        # Simulate placement (mutate in place, revert after)
        stones_sim[point] = player

        # Check if any adjacent opponent group is captured (has no liberty)
        captures_any = False
        for nb in neighbor_tuple[point]:
            if stones_sim[nb] == opponent:
                if not _has_liberty(stones_sim, nb):
                    captures_any = True
                    break

        if captures_any:
            valids[point] = 1
            stones_sim[point] = EMPTY  # revert
            continue

        # No captures — check if own group has liberties (suicide check)
        if _has_liberty(stones_sim, point):
            valids[point] = 1

        stones_sim[point] = EMPTY  # revert

    # Pass is always legal
    valids[PASS_ACTION] = 1
    return valids


def _calculate_face_area(
    stones: np.ndarray, face: np.ndarray, area: float
) -> tuple[float, float, float]:
    """Calculate area contribution of a single face (polysmall or polylarge).

    Each face is defined by its vertex indices. The area is divided among
    the colors present at those vertices.
    """
    parties = stones[face]
    parties_set = set(parties.tolist())

    has_black = BLACK in parties_set
    has_white = WHITE in parties_set

    if not has_black and not has_white:
        return 0.0, 0.0, area  # unclaimed
    if has_black and not has_white:
        return area, 0.0, 0.0  # all black
    if has_white and not has_black:
        return 0.0, area, 0.0  # all white

    # Mixed: divide proportionally
    black_count = int(np.sum(parties == BLACK))
    white_count = int(np.sum(parties == WHITE))
    total_colored = black_count + white_count
    return (
        area * black_count / total_colored,
        area * white_count / total_colored,
        0.0,
    )


def score(state: PolyclashState) -> tuple[float, float, float]:
    """Calculate area-based score.

    Returns:
        (black_ratio, white_ratio, unclaimed_ratio): each in [0, 1], summing to 1.
    """
    total_black = 0.0
    total_white = 0.0
    total_unclaimed = 0.0

    for row in polysmalls:
        b, w, u = _calculate_face_area(state.stones, row, polysmall_area)
        total_black += b
        total_white += w
        total_unclaimed += u

    for row in polylarges:
        b, w, u = _calculate_face_area(state.stones, row, polylarge_area)
        total_black += b
        total_white += w
        total_unclaimed += u

    return (
        total_black / total_area,
        total_white / total_area,
        total_unclaimed / total_area,
    )


def is_terminal(state: PolyclashState) -> bool:
    """Check if the game has ended (2 consecutive passes)."""
    return state.consecutive_passes >= 2


def terminal_result(state: PolyclashState) -> float:
    """Return game result from BLACK's perspective.

    White receives DEFAULT_KOMI added to its area ratio before comparison.

    Returns:
        1.0 if BLACK wins, -1.0 if WHITE wins, 1e-4 for draw, 0.0 if not terminal.
    """
    if not is_terminal(state):
        return 0.0

    black_ratio, white_ratio, _ = score(state)
    white_with_komi = white_ratio + DEFAULT_KOMI
    if black_ratio > white_with_komi:
        return 1.0
    if white_with_komi > black_ratio:
        return -1.0
    return 1e-4
