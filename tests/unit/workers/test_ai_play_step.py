from unittest.mock import Mock, patch

import numpy as np
import pytest
from PyQt5.QtCore import QMutex, QThread, QWaitCondition, pyqtSignal

from polyclash.workers.ai_play import AIPlayerWorker


class TestAIPlayerWorkerMethods:
    def test_wake_up(self):
        """Test the wake_up method."""
        mock_player = Mock()
        mock_player.board = Mock()

        worker = AIPlayerWorker(mock_player)

        # Mock the wait_condition to verify it's called
        worker.wait_condition = Mock()

        # Call wake_up
        worker.wake_up()

        # Verify state changed
        assert not worker.waiting
        # Verify wait_condition.wakeAll was called
        worker.wait_condition.wakeAll.assert_called_once()

    def test_sleep(self):
        """Test the sleep method."""
        mock_player = Mock()
        worker = AIPlayerWorker(mock_player)

        # Set waiting to False initially
        worker.waiting = False

        # Call sleep
        worker.sleep()

        # Verify state changed
        assert worker.waiting

    def test_step(self):
        """Test the step method."""
        mock_player = Mock()
        worker = AIPlayerWorker(mock_player)

        # Mock thread start and trigger methods
        worker.start = Mock()
        worker.trigger = Mock()
        worker.wake_up = Mock()

        # Call step
        worker.step()

        # Verify is_running was set to True
        assert worker.is_running
        # Verify start was called
        worker.start.assert_called_once()
        # Verify wake_up was called
        worker.wake_up.assert_called_once()
        # Verify trigger.emit was called
        worker.trigger.emit.assert_called_once()

    def test_stop(self):
        """Test the stop method."""
        mock_player = Mock()
        worker = AIPlayerWorker(mock_player)

        # Mock methods
        worker.wake_up = Mock()
        worker.wait = Mock()

        # Call stop
        worker.stop()

        # Verify state changed
        assert not worker.is_running
        # Verify wake_up was called
        worker.wake_up.assert_called_once()
        # Verify wait was called
        worker.wait.assert_called_once()

    def test_run(self):
        """Test the run method, though it's more challenging to test completely."""
        # This is a simplified test of the run method
        mock_player = Mock()
        worker = AIPlayerWorker(mock_player)

        # Mock the mutex and wait_condition to avoid actual waiting
        worker.mutex = Mock()
        worker.wait_condition = Mock()

        # Set up a side effect to change is_running after first loop
        def side_effect(*args, **kwargs):
            worker.is_running = False

        worker.wait_condition.wait.side_effect = side_effect

        # Set initial state
        worker.is_running = True
        worker.waiting = True

        # Call run
        worker.run()

        # Verify locks were used properly
        worker.mutex.lock.assert_called()
        worker.mutex.unlock.assert_called()
        # Verify wait_condition.wait was called
        worker.wait_condition.wait.assert_called_once_with(worker.mutex)
