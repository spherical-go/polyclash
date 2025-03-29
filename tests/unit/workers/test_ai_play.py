import pytest
from unittest.mock import Mock, patch
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from polyclash.game.board import Board, BLACK, WHITE, SimulatedBoard
from polyclash.workers.ai_play import AIPlayerWorker
from polyclash.game.controller import SphericalGoController
from polyclash.game.player import Player


class TestAIPlayerWorker:
    def test_ai_player_worker_creation(self):
        """Test basic AI player worker creation."""
        # Create a mock player
        mock_player = Mock()
        mock_player.board = Board()
        
        worker = AIPlayerWorker(mock_player)
        
        assert worker.player is mock_player
        assert isinstance(worker, QThread)
        assert hasattr(worker, 'trigger')
        # We can't check directly if trigger is a pyqtSignal since it becomes a bound method
        # Instead, verify we can call connect on it
        assert hasattr(worker.trigger, 'connect')
        assert not worker.is_running
    
    def test_ai_player_worker_on_turn(self):
        """Test the on_turn method."""
        # Create a mock player
        mock_player = Mock()
        mock_player.board = Mock()
        
        worker = AIPlayerWorker(mock_player)
        worker.waiting = False  # Set to not waiting
        
        # Call on_turn
        worker.on_turn()
        
        # Verify the player's auto_place method was called
        mock_player.auto_place.assert_called_once()
        # Verify the board's switch_player method was called
        mock_player.board.switch_player.assert_called_once()
