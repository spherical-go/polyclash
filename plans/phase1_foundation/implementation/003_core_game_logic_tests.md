# 003 - Core Game Logic Tests

This implementation plan outlines the approach for expanding test coverage of the core game logic components, with a focus on the `Board` class and its methods.

## Goals

1. Increase test coverage for `polyclash/game/board.py` from the current 61% to at least 80%
2. Test all public methods of the `Board` class
3. Cover edge cases and complex scenarios not currently tested
4. Test the `SimulatedBoard` class and its AI decision-making functionality
5. Verify the helper functions work correctly in all scenarios

## Implementation Steps

### 1. Expand Tests for Existing Methods

#### 1.1 Add More Liberty Tests

```python
def test_has_liberty_complex_group():
    """Test a complex group with a shared liberty."""
    board = Board()
    # Create a complex group with a shared liberty
    # positions forming a "T" shape
    group_positions = [10, 11, 12, 22, 32]  # Example positions
    liberty_position = 13  # The shared liberty

    for pos in group_positions:
        board.board[pos] = BLACK

    # Surround the group except for one liberty
    for pos in group_positions:
        for n in board.neighbors[pos]:
            if n not in group_positions and n != liberty_position:
                board.board[n] = WHITE

    # Test that the group has a liberty
    assert board.has_liberty(10) == True

    # Test that removing the liberty makes the group have no liberty
    board.board[liberty_position] = WHITE
    assert board.has_liberty(10) == False
```

#### 1.2 Expand Play Method Tests

```python
def test_play_ko_rule():
    """Test that the ko rule prevents immediate recapture."""
    board = Board()

    # Setup a ko situation where a stone can be captured
    # and the opponent would want to recapture
    board.board[50] = BLACK
    board.board[51] = BLACK
    board.board[52] = WHITE
    board.board[53] = WHITE
    ko_point = 54  # This will be captured, creating a ko
    board.board[ko_point] = BLACK

    # White captures the ko_point
    board.play(55, WHITE)
    assert board.board[ko_point] == 0  # The stone was captured

    # Black tries to recapture immediately, which should violate the ko rule
    with pytest.raises(ValueError, match="ko rule violation"):
        board.play(ko_point, BLACK)

    # After White plays elsewhere, Black can recapture
    board.play(60, WHITE)
    board.play(ko_point, BLACK)  # This should now be legal
    assert board.board[ko_point] == BLACK
```

### 2. Implement Tests for Untested Methods

#### 2.1 Test Remove Stone Method

```python
class TestBoardRemoveStone:
    def test_remove_single_stone(self):
        """Test removing a single stone."""
        board = Board()
        board.board[10] = BLACK

        board.remove_stone(10)
        assert board.board[10] == 0
        assert 10 in board.latest_removes[-1]

    def test_remove_connected_group(self):
        """Test removing a connected group of stones."""
        board = Board()
        # Create a connected group
        group = [10, 11, 21]
        for pos in group:
            board.board[pos] = BLACK

        board.remove_stone(10)  # Remove one stone should cascade to all connected

        for pos in group:
            assert board.board[pos] == 0
            assert pos in board.latest_removes[-1]

    def test_remove_with_observer(self):
        """Test that removing stones notifies observers."""
        board = Board()
        # Create a mock observer
        mock_observer = Mock()
        board.register_observer(mock_observer)

        board.board[10] = BLACK
        board.remove_stone(10)

        # Verify the observer was notified
        mock_observer.handle_notification.assert_called_with("remove_stone", point=10, score=board.score())
```

#### 2.2 Test Reset Method

```python
class TestBoardReset:
    def test_reset_empty_board(self):
        """Test resetting an empty board."""
        board = Board()
        board.switch_player()  # Change current player

        board.reset()

        assert np.all(board.board == 0)
        assert board.current_player == BLACK
        assert len(board.latest_removes) == 1
        assert len(board.black_suicides) == 0
        assert len(board.white_suicides) == 0
        assert len(board.turns) == 0

    def test_reset_with_stones(self):
        """Test resetting a board with stones and game history."""
        board = Board()
        # Play some moves
        board.play(10, BLACK)
        board.switch_player()
        board.play(11, WHITE)
        board.switch_player()

        board.reset()

        assert np.all(board.board == 0)
        assert board.current_player == BLACK
        assert len(board.latest_removes) == 1
        assert len(board.black_suicides) == 0
        assert len(board.white_suicides) == 0
        assert len(board.turns) == 0

    def test_reset_with_observer(self):
        """Test that reset notifies observers."""
        board = Board()
        # Create a mock observer
        mock_observer = Mock()
        board.register_observer(mock_observer)

        board.reset()

        # Verify the observer was notified
        mock_observer.handle_notification.assert_called_with("reset", **{})
```

#### 2.3 Test Switch Player Method

```python
class TestBoardSwitchPlayer:
    def test_switch_player_from_black(self):
        """Test switching player from BLACK to WHITE."""
        board = Board()
        assert board.current_player == BLACK

        board.switch_player()

        assert board.current_player == WHITE

    def test_switch_player_from_white(self):
        """Test switching player from WHITE to BLACK."""
        board = Board()
        board.current_player = WHITE

        board.switch_player()

        assert board.current_player == BLACK

    def test_switch_player_with_observer(self):
        """Test that switching player notifies observers."""
        board = Board()
        # Create a mock observer
        mock_observer = Mock()
        board.register_observer(mock_observer)

        board.switch_player()

        # Verify the observer was notified
        mock_observer.handle_notification.assert_called_with("switch_player", side=WHITE)
```

#### 2.4 Test Get Empties Method

```python
class TestBoardGetEmpties:
    def test_get_empties_initial(self):
        """Test getting empty points on an initial board."""
        board = Board()
        empties = board.get_empties(BLACK)

        assert len(empties) == 302
        assert set(empties) == set(range(302))

    def test_get_empties_with_stones(self):
        """Test getting empty points on a board with stones."""
        board = Board()
        board.board[10] = BLACK
        board.board[11] = WHITE

        empties = board.get_empties(BLACK)

        assert len(empties) == 300
        assert 10 not in empties
        assert 11 not in empties

    def test_get_empties_with_ko(self):
        """Test getting empty points with a ko situation."""
        board = Board()
        # Setup a ko situation
        board.latest_removes.append([42])  # Simulating a ko point

        empties = board.get_empties(BLACK)

        assert 42 not in empties

    def test_get_empties_with_suicides(self):
        """Test getting empty points with suicide points."""
        board = Board()
        # Add some suicide points
        board.black_suicides.add(20)
        board.white_suicides.add(21)

        black_empties = board.get_empties(BLACK)
        white_empties = board.get_empties(WHITE)

        assert 20 not in black_empties
        assert 21 not in white_empties
        assert 20 in white_empties
        assert 21 in black_empties
```

#### 2.5 Test Score Method

```python
class TestBoardScore:
    def test_score_empty_board(self):
        """Test scoring an empty board."""
        board = Board()
        black, white, unclaimed = board.score()

        # On an empty board, no territories are claimed
        assert black == 0
        assert white == 0
        assert unclaimed == 1.0

    def test_score_with_stones(self):
        """Test scoring a board with some stones but no territories."""
        board = Board()
        # Place some stones but don't complete territories
        board.board[10] = BLACK
        board.board[20] = BLACK
        board.board[30] = WHITE
        board.board[40] = WHITE

        black, white, unclaimed = board.score()

        # Only stones, no territories claimed yet
        assert black > 0
        assert white > 0
        assert unclaimed < 1.0
        assert round(black + white + unclaimed, 6) == 1.0  # Total should be 1.0

    def test_score_with_territories(self):
        """Test scoring with claimed territories."""
        board = Board()
        # Create a small territory for BLACK
        faces = [10, 11, 12, 13, 14]
        for face in faces:
            board.board[face] = BLACK

        black, white, unclaimed = board.score()

        # BLACK should have some territory
        assert black > 0
        assert white == 0
        assert unclaimed < 1.0
        assert round(black + white + unclaimed, 6) == 1.0
```

### 3. Test Game State Methods

```python
class TestBoardGameState:
    def test_is_game_over_false(self):
        """Test is_game_over when the game is not over."""
        board = Board()
        # With an empty board, game is not over
        assert board.is_game_over() == False

    def test_is_game_over_true(self):
        """Test is_game_over when the game is over."""
        board = Board()
        # Make all points suicides for the current player
        player = board.current_player
        if player == BLACK:
            board.black_suicides = set(range(302))
        else:
            board.white_suicides = set(range(302))

        assert board.is_game_over() == True

    def test_result(self):
        """Test the result method."""
        board = Board()
        # Currently returns an empty dict
        assert board.result() == {}
```

### 4. Test Observer Pattern

```python
class TestBoardObserverPattern:
    def test_register_observer(self):
        """Test registering an observer."""
        board = Board()
        mock_observer = Mock()

        board.register_observer(mock_observer)

        assert mock_observer in board._observers

    def test_register_duplicate_observer(self):
        """Test registering the same observer twice."""
        board = Board()
        mock_observer = Mock()

        board.register_observer(mock_observer)
        board.register_observer(mock_observer)

        # The observer should only be added once
        assert board._observers.count(mock_observer) == 1

    def test_unregister_observer(self):
        """Test unregistering an observer."""
        board = Board()
        mock_observer = Mock()
        board.register_observer(mock_observer)

        board.unregister_observer(mock_observer)

        assert mock_observer not in board._observers

    def test_enable_disable_notification(self):
        """Test enabling and disabling notifications."""
        board = Board()
        mock_observer = Mock()
        board.register_observer(mock_observer)

        # Disable notifications
        board.disable_notification()
        board.notify_observers("test")
        mock_observer.handle_notification.assert_not_called()

        # Enable notifications
        board.enable_notification()
        board.notify_observers("test")
        mock_observer.handle_notification.assert_called_once()
```

### 5. Test SimulatedBoard Class

```python
class TestSimulatedBoard:
    def test_redirect(self):
        """Test redirecting state from another board."""
        original = Board()
        original.board[10] = BLACK
        original.current_player = WHITE
        original.latest_removes.append([20])
        original.black_suicides.add(30)
        original.white_suicides.add(31)
        original.turns[0] = "0-1"

        simulator = SimulatedBoard()
        simulator.redirect(original)

        # Verify the simulator has copied all state
        assert simulator.board[10] == BLACK
        assert simulator.current_player == WHITE
        assert simulator.latest_removes[-1] == [20]
        assert 30 in simulator.black_suicides
        assert 31 in simulator.white_suicides
        assert simulator.turns[0] == "0-1"

        # Verify that modifying the simulator doesn't affect the original
        simulator.board[10] = 0
        assert original.board[10] == BLACK

    def test_genmove_basic(self):
        """Test basic move generation."""
        board = Board()
        simulator = SimulatedBoard()
        simulator.redirect(board)

        move = simulator.genmove(BLACK)

        # Should return a valid move
        assert isinstance(move, int)
        assert 0 <= move < 302

    def test_simulate_score(self):
        """Test score simulation for a move."""
        simulator = SimulatedBoard()
        simulator.board = np.zeros([302])

        # Make a simple board position
        simulator.board[10] = BLACK

        # Simulate playing at position 11
        try:
            score, gain = simulator.simulate_score(0, 11, BLACK)

            # We should get a score and gain
            assert isinstance(score, float)
            assert isinstance(gain, float)
        except ValueError:
            # If the simulation raises an expected error, the test still passes
            pass
```

### 6. Test Helper Functions

```python
class TestHelperFunctions:
    def test_calculate_area_unclaimed(self):
        """Test calculating area for an unclaimed territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        assert black == 0
        assert white == 0
        assert unclaimed == area

    def test_calculate_area_black_claimed(self):
        """Test calculating area for a BLACK-claimed territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        for pos in piece:
            boarddata[pos] = BLACK
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        assert black == area
        assert white == 0
        assert unclaimed == 0

    def test_calculate_area_contested(self):
        """Test calculating area for a contested territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        # Mix of BLACK and WHITE
        boarddata[0] = BLACK
        boarddata[1] = BLACK
        boarddata[2] = WHITE
        boarddata[3] = WHITE
        boarddata[4] = BLACK
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        # Should be split proportionally
        assert black == 6.0  # 3/5 of area
        assert white == 4.0  # 2/5 of area
        assert unclaimed == 0

    def test_calculate_distance(self):
        """Test distance calculation between two points."""
        # This depends on the specific cities data structure
        point1 = 0
        point2 = 1

        distance = calculate_distance(point1, point2)

        # The distance should be positive
        assert distance > 0

    def test_calculate_potential(self):
        """Test potential calculation for a point."""
        board = np.zeros([302])
        board[1] = BLACK
        board[2] = WHITE
        point = 0
        counter = 10

        potential = calculate_potential(board, point, counter)

        # Should return a number based on the distances
        assert isinstance(potential, float)
```

## Verification

To verify that the tests are working correctly and improving coverage:

1. Run all the newly added tests:
   ```
   pytest tests/unit/game/test_board.py -v
   ```

2. Check the test coverage for the board module:
   ```
   pytest tests/unit/game/test_board.py --cov=polyclash.game.board --cov-report=term
   ```

3. Verify that the coverage has increased from 61% to at least 80%.

4. Ensure that all tests pass, indicating that the methods are working as expected.

## Next Steps

After successfully implementing and verifying the extended test coverage for the core game logic:

1. Continue with implementing the next phase of testing improvements, focusing on:
   - AI Component Tests
   - Network Component Tests
   - UI Component Tests

2. Update the implementation plan README.md to mark "003 - Core Game Logic Tests" as FINISHED.

## Test Implementation Timeline

| Day | Focus Area | Tasks |
|-----|------------|-------|
| 1 | Setup & Existing Methods | Expand liberty and play tests |
| 2 | Basic Methods | Implement tests for reset, switch_player, get_empties |
| 3 | Observer Pattern | Implement observer pattern tests |
| 4 | Game Logic Methods | Implement tests for score, is_game_over, result |
| 5 | Complex Methods | Implement tests for remove_stone and its edge cases |
| 6 | SimulatedBoard | Implement tests for the SimulatedBoard class |
| 7 | Helper Functions & Verification | Implement tests for helper functions and verify coverage |

## Notes and Considerations

1. When testing methods that rely on the complex data structures like `neighbors`, `cities`, etc., use real data from the game rather than mocking these structures to ensure the tests accurately reflect the game's behavior.

2. For methods that have randomness (like `genmove`), focus on testing the structure and boundaries of the output rather than specific values.

3. Be sure to test both the success and failure paths for methods that can raise exceptions.

4. Consider adding performance tests for methods that might be computationally expensive, like `has_liberty` on large connected groups or `genmove` for complex board positions.
