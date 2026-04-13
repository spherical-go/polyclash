"""Bridge between polyclash's mutable Board and the built-in MCTS engine.

Usage:
    from polyclash.ai.bridge import HRMPlayer
    player = HRMPlayer(checkpoint_dir="path/to/temp")
    move = player.genmove(board, side)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from polyclash.ai.core.mcts import MCTS
from polyclash.ai.core.utils import dotdict
from polyclash.ai.nn import NNetWrapper
from polyclash.ai.polyclash.game_adapter import PolyclashGame
from polyclash.ai.polyclash.state import PolyclashState
from polyclash.ai.polyclash.topology import PASS_ACTION

log = logging.getLogger(__name__)

HF_REPO_ID = "mingli/hrm-polyclash"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "hrm-polyclash"


def _ensure_weights(
    cache_dir: Path,
    filename: str = "best.safetensors",
    repo_id: str = HF_REPO_ID,
) -> Path:
    """Download weights from HuggingFace Hub if not cached locally."""
    local_path = cache_dir / filename
    if local_path.exists():
        log.info("Using cached weights: %s", local_path)
        return local_path

    log.info("Downloading weights from %s ...", repo_id)
    try:
        from huggingface_hub import hf_hub_download

        downloaded = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(cache_dir),
        )
        log.info("Downloaded weights to: %s", downloaded)
        return Path(downloaded)
    except Exception as e:
        log.error("Failed to download weights: %r", e)
        raise FileNotFoundError(
            f"Could not find or download weights '{filename}' from {repo_id}. "
            f"Check network or provide a local checkpoint."
        ) from e


def board_to_state(board: object) -> PolyclashState:
    """Convert a polyclash Board object to an immutable PolyclashState.

    Handles the mutable Board's fields:
    - board.board: np.ndarray of shape (302,)
    - board.zobrist_hash / board.history_hashes: for superko
    """
    stones = np.array(getattr(board, "board"), dtype=np.int8)
    zobrist_hash = getattr(board, "zobrist_hash", 0)
    history_hashes_set: set[int] = getattr(board, "history_hashes", set())
    move_count = len(getattr(board, "turns", {}))

    return PolyclashState(
        stones=stones,
        ko_point=-1,
        consecutive_passes=getattr(board, "consecutive_passes", 0),
        move_count=move_count,
        zobrist_hash=zobrist_hash,
        history_hashes=frozenset(history_hashes_set),
    )


class HRMPlayer:
    """HRM+MCTS AI player that can be plugged into polyclash."""

    def __init__(
        self,
        checkpoint_dir: Optional[str] = None,
        checkpoint_file: str = "best.safetensors",
        num_mcts_sims: int = 50,
        cpuct: float = 1.0,
        temp: float = 0.0,
        min_moves_before_pass: int = 40,
        auto_download: bool = True,
    ) -> None:
        self.temp = temp
        self.min_moves_before_pass = min_moves_before_pass

        self.game = PolyclashGame(sym_samples=0)
        self.nnet = NNetWrapper(self.game)

        # Resolve checkpoint location
        if checkpoint_dir is not None:
            # Explicit local path provided
            self.nnet.load_checkpoint(checkpoint_dir, checkpoint_file)
            log.info(
                "HRMPlayer loaded from local: %s/%s", checkpoint_dir, checkpoint_file
            )
        elif auto_download:
            # Auto-download from HuggingFace Hub
            cache_dir = Path(
                os.environ.get("HRM_POLYCLASH_CACHE", str(DEFAULT_CACHE_DIR))
            )
            weights_path = _ensure_weights(cache_dir, filename=checkpoint_file)
            self.nnet.load_checkpoint(str(weights_path.parent), weights_path.name)
            log.info("HRMPlayer loaded from Hub cache: %s", weights_path)
        else:
            log.warning("HRMPlayer: no checkpoint loaded (no dir, auto_download=False)")

        self.args = dotdict({"numMCTSSims": num_mcts_sims, "cpuct": cpuct})
        self.mcts = MCTS(self.game, self.nnet, self.args)

        log.info("HRMPlayer ready: %d MCTS sims", num_mcts_sims)

    def genmove(self, board: object, player: int) -> Optional[int]:
        """Generate a move for the given polyclash Board and player side.

        Args:
            board: polyclash Board object (mutable)
            player: BLACK (1) or WHITE (-1)

        Returns:
            Point index (0..301) to play, or None if pass is chosen.
        """
        state = board_to_state(board)
        canonical = self.game.canonical_form(state, player)

        self.mcts.reset()
        pi = np.array(
            self.mcts.action_prob(canonical, temp=self.temp), dtype=np.float64
        )

        # Suppress pass in early game to force real play
        if state.move_count < self.min_moves_before_pass:
            non_pass_sum = pi[:PASS_ACTION].sum()
            if non_pass_sum > 0:
                pi[PASS_ACTION] = 0.0
                pi[:PASS_ACTION] /= non_pass_sum

        action = int(np.argmax(pi))

        if action == PASS_ACTION:
            log.info("HRMPlayer: pass")
            return None

        log.info("HRMPlayer: point %d (p=%.3f)", action, pi[action])
        return action
