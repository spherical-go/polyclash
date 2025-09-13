# 004 - AI Component Tests

This implementation plan outlines the approach for expanding test coverage of the AI components, focusing on the AI play workers, game simulation, and decision-making algorithms.

## Goals

1. Increase test coverage for `polyclash/workers/ai_play.py` from the current 40% to at least 80%
2. Verify the correct functioning of AI decision-making algorithms
3. Test the integration between AI components and the game board
4. Ensure AI behaviors are consistent and optimal in various game scenarios
5. Test the performance characteristics of AI algorithms under different conditions

## Implementation Steps

### 1. Setup Test Environment for AI Components

```python
import pytest
from unittest.mock import Mock, patch
import numpy as np

from polyclash.game.board import Board, BLACK, WHITE, SimulatedBoard
from polyclash.workers.ai_play import AIPlayer, AIWorker, AIManager
from polyclash.game.controller import SphericalGoController
```

### 2. Test AIPlayer Class

#### 2.1 Test AIPlayer Initialization

```python
class TestAIPlayerInitialization:
    def test_ai_player_creation(self):
        """Test basic AI player creation."""
        board = Board()
        ai = AIPlayer(board, BLACK)

        assert ai.board is board
        assert ai.color == BLACK
        assert ai.difficulty is not None

    def test_ai_player_with_difficulty(self):
        """Test AI player creation with specific difficulty."""
        board = Board()
        ai = AIPlayer(board, WHITE, difficulty=3)

        assert ai.difficulty == 3
```

#### 2.2 Test AI Move Generation

```python
class TestAIMoveGeneration:
    def test_ai_genmove(self):
        """Test AI move generation returns a valid move."""
        board = Board()
        ai = AIPlayer(board, BLACK)

        move = ai.genmove()

        assert isinstance(move, int)
        assert 0 <= move < board.board_size

    def test_ai_genmove_with_occupied_positions(self):
        """Test AI move generation with some occupied positions."""
        board = Board()
        # Occupy some positions
        board.board[0] = BLACK
        board.board[1] = WHITE

        ai = AIPlayer(board, BLACK)
        move = ai.genmove()

        assert move != 0 and move != 1  # Should not select occupied positions

    def test_ai_genmove_near_endgame(self):
        """Test AI move generation near endgame."""
        board = Board()
        # Set up a near-endgame scenario with only a few legal moves
        empty_positions = [10, 20, 30]
        for i in range(board.board_size):
            if i not in empty_positions:
                board.board[i] = BLACK if i % 2 == 0 else WHITE

        ai = AIPlayer(board, BLACK)
        move = ai.genmove()

        assert move in empty_positions
```

### 3. Test AIWorker Class

#### 3.1 Test AIWorker Initialization and Processing

```python
class TestAIWorker:
    def test_ai_worker_creation(self):
        """Test AIWorker initialization."""
        worker = AIWorker()
        assert worker is not None

    def test_ai_worker_process(self):
        """Test AIWorker process method."""
        worker = AIWorker()
        board = Board()

        # Mock the signals
        worker.started = Mock()
        worker.finished = Mock()

        # Process a request
        worker.process(board, BLACK)

        # Verify signals were emitted
        worker.started.emit.assert_called_once()
        worker.finished.emit.assert_called_once()

        # Extract the move from the finished signal
        args = worker.finished.emit.call_args[0]
        move = args[0]
        assert isinstance(move, int)
        assert 0 <= move < board.board_size
```

### 4. Test AIManager Class

```python
class TestAIManager:
    def test_ai_manager_initialization(self):
        """Test AIManager initialization."""
        manager = AIManager()
        assert manager.worker is not None
        assert manager.thread is not None

    def test_ai_manager_request_move(self):
        """Test AIManager request_move method."""
        manager = AIManager()
        board = Board()

        # Mock the signals and move callback
        move_callback = Mock()

        # Request a move
        manager.request_move(board, BLACK, move_callback)

        # Since this runs in a thread, we'll need to wait for it to complete
        # This is a simplified approach; in a real test, use QSignalSpy or similar
        import time
        time.sleep(0.5)

        # Verify callback was called
        move_callback.assert_called_once()

        # Extract the move from the callback
        args = move_callback.call_args[0]
        move = args[0]
        assert isinstance(move, int)
        assert 0 <= move < board.board_size
```

### 5. Test AI Strategy and Decision Making

```python
class TestAIStrategy:
    def test_ai_capture_preference(self):
        """Test that AI prefers capturing moves when available."""
        board = Board()

        # Set up a scenario where capturing is possible
        # For example, surround a black stone except for one liberty
        target_point = 10
        board.board[target_point] = BLACK

        # Surround it except for one liberty
        liberty_point = None
        for n in board.neighbors[target_point]:
            if liberty_point is None:
                liberty_point = n
            else:
                board.board[n] = WHITE

        ai = AIPlayer(board, WHITE)
        move = ai.genmove()

        # AI should prioritize the capturing move
        assert move == liberty_point

    def test_ai_avoid_suicide(self):
        """Test that AI avoids suicide moves."""
        board = Board()

        # Set up a scenario where playing would be suicide
        suicide_point = 10
        for n in board.neighbors[suicide_point]:
            board.board[n] = WHITE

        ai = AIPlayer(board, BLACK)
        move = ai.genmove()

        # AI should not choose the suicide point
        assert move != suicide_point

    def test_ai_territory_control(self):
        """Test AI territorial control strategy."""
        board = Board()

        # Set up a board with some established territories
        # This will be specific to the game rules and board representation
        # but the general idea is to create a scenario where territory control
        # is the best strategy

        ai = AIPlayer(board, BLACK)
        move = ai.genmove()

        # Verify the move improves territory control
        # This could involve simulating the move and checking territory scores
        board_copy = Board()
        board_copy.board = np.copy(board.board)
        score_before = board_copy.score()[0]  # BLACK's score

        board_copy.play(move, BLACK)
        score_after = board_copy.score()[0]

        assert score_after >= score_before
```

### 6. Test AI Integration with Game Controller

```python
class TestAIIntegration:
    def test_ai_integration_with_controller(self):
        """Test integration of AI with game controller."""
        controller = SphericalGoController()

        # Add a human player (BLACK) and AI player (WHITE)
        controller.add_player(BLACK, kind="human")
        controller.add_player(WHITE, kind="ai")

        # Start the game
        controller.start()

        # Mock the move function for the AI player
        with patch.object(controller.players[1], 'genmove', return_value=10):
            # Trigger the AI's turn
            controller.current_player_ix = 1
            controller.play_current()

            # Verify the AI's move was processed
            assert controller.board.board[10] == WHITE
```

### 7. Test AI Difficulty Levels

```python
class TestAIDifficulty:
    def test_ai_difficulty_levels(self):
        """Test that different difficulty levels produce different gameplay."""
        board = Board()

        # Create AIs with different difficulty levels
        ai_easy = AIPlayer(board, BLACK, difficulty=1)
        ai_hard = AIPlayer(board, BLACK, difficulty=3)

        # Run multiple simulations and collect moves
        easy_moves = [ai_easy.genmove() for _ in range(5)]
        hard_moves = [ai_hard.genmove() for _ in range(5)]

        # There should be some difference in the moves chosen
        # This is a probabilistic test, so it could occasionally fail
        assert len(set(easy_moves) - set(hard_moves)) > 0 or len(set(hard_moves) - set(easy_moves)) > 0

    def test_ai_calculation_depth(self):
        """Test that higher difficulty increases calculation depth."""
        board = Board()

        with patch('polyclash.workers.ai_play.calculate_depth') as mock_depth:
            ai_easy = AIPlayer(board, BLACK, difficulty=1)
            ai_easy.genmove()
            easy_depth = mock_depth.call_args[0][0]

            ai_hard = AIPlayer(board, BLACK, difficulty=3)
            ai_hard.genmove()
            hard_depth = mock_depth.call_args[0][0]

            assert hard_depth > easy_depth
```

## Verification

To verify that the tests are working correctly and improving coverage:

1. Run all the newly added AI component tests:
   ```
   python -m pytest tests/unit/workers/test_ai_play.py -v
   ```

2. Check the test coverage for the AI module:
   ```
   python -m pytest tests/unit/workers/test_ai_play.py --cov=polyclash.workers.ai_play --cov-report=term
   ```

3. Verify that the coverage has increased from 40% to at least 80%.

4. Ensure that all tests pass, indicating that the AI components are working as expected.

## Next Steps

After successfully implementing and verifying the extended test coverage for the AI components:

1. Continue with implementing the next phase of testing improvements, focusing on:
   - Network Component Tests
   - UI Component Tests

2. Update the implementation plan README.md to mark "004 - AI Component Tests" as FINISHED.

3. Consider extracting key metrics about AI performance for future benchmarking.

## Test Implementation Timeline

| Day | Focus Area | Tasks |
|-----|------------|-------|
| 1 | Setup & AIPlayer Basics | Implement basic AIPlayer initialization and move generation tests |
| 2 | AIWorker & AIManager | Implement tests for the worker and manager classes |
| 3 | AI Strategy Tests | Implement tests for strategic decision making |
| 4 | Integration Tests | Implement tests for integration with game controller |
| 5 | Difficulty Levels | Implement tests for different difficulty settings |
| 6 | Edge Cases | Test AI behavior in edge cases and unusual board positions |
| 7 | Review & Verification | Review all tests, verify coverage and fix any issues |

## Notes and Considerations

1. Some tests may need to be asynchronous to handle the threaded nature of the AI workers.

2. AI strategy tests are inherently difficult to make deterministic, as good AI often includes randomness to avoid predictability. Consider using fixed seeds or mocking random functions for reproducible tests.

3. Performance tests for the AI should consider both speed and quality of moves.

4. Difficulty level tests should verify not just that the AI behaves differently at different difficulty levels, but that higher difficulty levels actually make stronger moves.

5. If the AI components rely on external resources (like an opening book or trained models), ensure those resources are properly mocked or provided in the test environment.
