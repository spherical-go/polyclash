# Phase 1.1: Revised Enhanced Testing Framework

This document presents a revised plan for the Enhanced Testing Framework phase, addressing the test coverage gaps identified in our recent analysis. While we've successfully reorganized the test structure and fixed the existing tests, significant coverage gaps remain that must be addressed.

## Progress Status

| Task | Status | Completion Date |
|------|--------|----------------|
| ✅ Test Structure Reorganization | **FINISHED** | March 25, 2025 |
| 🔄 GUI Component Tests | **ONGOING** | - |
| 🔄 Core Game Logic Tests | **ONGOING** | - |
| 📅 Integration Tests | **PLANNED** | - |
| 📅 Functional Tests | **PLANNED** | - |
| 📅 Performance Tests | **PLANNED** | - |
| 📅 CI/CD Enhancements | **PLANNED** | - |

**Last Updated:** March 25, 2025

## Current Coverage Analysis (2025-03-25)

The overall test coverage stands at 61%, with significant gaps in critical components:

### Coverage Gaps by Component

#### Critical Gaps (Coverage < 30%)
- **polyclash/gui/dialogs.py**: Only 11% coverage (204 out of 230 statements missing)
- **polyclash/gui/overly_map.py**: Only 21% coverage (42 out of 53 statements missing)
- **polyclash/gui/view_sphere.py**: Only 25% coverage (91 out of 121 statements missing)
- **polyclash/gui/overly_info.py**: Only 28% coverage (33 out of 46 statements missing)

#### Significant Gaps (30-60% Coverage)
- **polyclash/gui/main.py**: 42% coverage (78 out of 134 statements missing)

#### Moderate Gaps (60-80% Coverage)
- **polyclash/game/board.py**: 61% coverage (89 out of 226 statements missing)
- **polyclash/util/storage.py**: 64% coverage (105 out of 291 statements missing)
- **polyclash/game/controller.py**: 71% coverage (29 out of 99 statements missing)

#### Well-Covered (> 80%)
- **polyclash/game/player.py**: 87% coverage
- **polyclash/gui/mesh.py**: 87% coverage
- **polyclash/server.py**: 91% coverage
- **polyclash/client.py**: 96% coverage
- **polyclash/workers/ai_play.py**: 95% coverage
- **polyclash/workers/network.py**: 100% coverage
- **polyclash/util/api.py**: 100% coverage
- **polyclash/game/timer.py**: 100% coverage
- **polyclash/data/data.py**: 100% coverage

## Revised Implementation Plan

The revised plan prioritizes the components with the lowest coverage while still maintaining the original structure:

### 1. GUI Component Tests (3 weeks) ⬆️ [Priority Increased]

#### 1.1 Dialog Tests
- Create a test harness for dialog components that doesn't require user interaction
- Test dialog initialization with various parameters
- Test dialog field validation
- Test dialog response to different input patterns
- Test dialog callback functions

Example test cases:
```python
def test_network_game_dialog_initialization():
    dialog = NetworkGameDialog(None)
    assert dialog.windowTitle() == "Network Game"
    assert dialog.server_edit.text() == "localhost:5000"

def test_dialog_field_validation():
    dialog = NetworkGameDialog(None)
    dialog.server_edit.setText("")
    dialog.accept_button.click()
    assert dialog.error_label.text() != ""  # Error message should be displayed
```

#### 1.2 View Sphere Tests
- Test rendering initialization
- Test camera positioning and controls
- Test stone placement visualization
- Test interaction with the game board
- Test vertex coloring and highlighting

Example test cases:
```python
def test_view_sphere_initialization():
    view = ActiveSphereView(None)
    assert view.rotation == [0, 0]
    assert view.distance == 5.0

def test_stone_rendering():
    view = ActiveSphereView(None)
    mock_board = MagicMock()
    mock_board.board = {0: BLACK, 1: WHITE}
    view.board = mock_board
    # Test that the stones are rendered correctly
    stone_positions = view.get_stone_positions()
    assert 0 in stone_positions
    assert 1 in stone_positions
```

#### 1.3 Overlay Tests
- Test overlay positioning
- Test information display
- Test map interaction
- Test overlay visibility controls
- Test overlay updates on game state changes

Example test cases:
```python
def test_overlay_info_display():
    overlay = OverlayInfo(None)
    overlay.update_score(5, 3)
    assert "Black: 5" in overlay.score_label.text()
    assert "White: 3" in overlay.score_label.text()

def test_overlay_map_interaction():
    overlay = OverlayMap(None)
    # Test map clicking behavior
    with patch.object(overlay, 'on_click') as mock_on_click:
        # Simulate clicking on the map
        event = QMouseEvent(QEvent.MouseButtonPress, QPointF(10, 10),
                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        overlay.mousePressEvent(event)
        mock_on_click.assert_called_once()
```

#### 1.4 Main Window Tests
- Test menu action handlers
- Test window layout and component integration
- Test window resize behavior
- Test game state synchronization with UI
- Test network notification handling

### 2. Core Game Logic Tests (2 weeks) [Priority Maintained]

#### 2.1 Advanced Board State Tests
- Test more complex game scenarios
- Test edge cases in the rules implementation
- Test rare game situations
- Test board with different configurations

Example test cases:
```python
def test_complex_capture_scenario():
    board = Board()
    # Set up a complex capture situation
    # ... detailed setup code with multiple interacting groups
    board.play(capture_move, BLACK)
    # Verify correct captures
    assert board.board[expected_capture1] == 0
    assert board.board[expected_capture2] == 0

def test_nearly_surrounded_group_survival():
    board = Board()
    # Set up a group that is nearly surrounded but has one liberty
    # ... setup code
    # Try to play the last liberty
    with pytest.raises(ValueError, match="Suicide move"):
        board.play(last_liberty, WHITE)
```

#### 2.2 Storage Path Tests
- Test edge cases in storage operations
- Test error recovery paths
- Test concurrent access scenarios
- Test data migration paths

Example test cases:
```python
def test_storage_race_condition_handling():
    storage = MemoryStorage()
    # Simulate concurrent access
    storage.create_room("test_room")
    # Simulate a race condition
    with patch.object(storage, 'games') as mock_games:
        mock_games.__getitem__.side_effect = KeyError
        # Test that the code handles the KeyError gracefully
        with pytest.raises(Exception) as e:
            storage.get_key("test_room", "black")
        assert "not found" in str(e.value)

def test_storage_data_integrity():
    storage = MemoryStorage()
    # Create a room and make some changes
    result = storage.create_room("test_room")
    # Verify data integrity
    storage.join_room("test_room", "black", result["black_key"])
    status = storage.joined_status("test_room")
    assert status["black"] is True
    assert status["white"] is False
```

#### 2.3 Controller Edge Cases
- Test controller state transitions
- Test player management edge cases
- Test game flow control in unusual scenarios

Example test cases:
```python
def test_controller_player_replacement():
    controller = SphericalGoController()
    controller.add_player(BLACK, kind=HUMAN)
    # Test replacing a player
    controller.add_player(BLACK, kind=AI)
    # Verify the player was replaced
    assert controller.players[0].kind == AI

def test_controller_game_restart():
    controller = SphericalGoController()
    controller.add_player(BLACK, kind=HUMAN)
    controller.add_player(WHITE, kind=AI)
    controller.start()
    # Play some moves
    controller.play(0)
    controller.play(1)
    # Restart the game
    controller.restart()
    # Verify the game state was reset
    assert controller.board.counter == 0
    assert controller.board.board[0] == 0
    assert controller.board.board[1] == 0
```

### 3. Integration Tests (2 weeks) [Priority Maintained]

#### 3.1 Enhanced Client-Server Integration
- Test comprehensive game flow between client and server
- Test error handling and recovery
- Test network instability scenarios

Example test cases:
```python
def test_full_game_client_server():
    server = create_test_server()
    client = create_test_client()
    # Setup a complete game
    game_id = server.create_game()
    client1.join(game_id, "black")
    client2.join(game_id, "white")
    client1.ready()
    client2.ready()
    # Play several moves
    client1.play(0)
    client2.play(1)
    # ... more moves
    # Test game completion
    assert client1.get_status() == "finished"
    assert client2.get_status() == "finished"
```

#### 3.2 Enhanced UI-Logic Integration
- Test UI updates for all game state changes
- Test complete user interaction flows
- Test error reporting and recovery through the UI

Example test cases:
```python
def test_ui_game_flow():
    main_window = create_test_window()
    # Test starting a local game
    main_window.localMode()
    # Verify the UI state
    assert main_window.controller.players[0].kind == HUMAN
    assert main_window.controller.players[1].kind == AI
    # Test playing a move
    main_window.sphere_view.on_click(0)
    # Verify the UI updated
    assert main_window.controller.board.board[0] == BLACK
```

### 4. Functional Tests (1 week) [Priority Maintained]

#### 4.1 Enhanced Game Scenarios
- Test more complex game scenarios end-to-end
- Test all game ending conditions
- Test score calculation in various end-game states

Example test cases:
```python
def test_game_timeout():
    # Setup a game with a short timer
    controller = create_test_controller(timer_duration=1)
    # Start the game
    controller.start()
    # Wait for the timer to expire
    time.sleep(2)
    # Verify the game ended correctly
    assert controller.game_over
    assert controller.winner == WHITE  # Assume BLACK times out first
```

### 5. Performance Tests (1 week) [Priority Maintained]

#### 5.1 Enhanced AI Performance
- More detailed benchmarks for AI performance
- Test AI with various board configurations
- Identify and optimize performance bottlenecks

Example test cases:
```python
def test_ai_benchmark(benchmark):
    board = Board()
    # Setup a mid-game scenario
    # ... setup code
    # Benchmark AI move generation
    def ai_move():
        board.genmove(BLACK)
    # Run the benchmark
    result = benchmark(ai_move)
    # Assert reasonable performance
    assert result.stats.mean < 0.5  # Less than 500ms per move
```

### 6. CI/CD Enhancements (1 week) [Priority Maintained]

#### 6.1 Coverage Enforcement
- Set up minimum coverage requirements for critical components
- Configure coverage reports for pull requests
- Implement automated coverage trend analysis

## Timeline (Revised)

| Week | Tasks | Focus |
|------|-------|-------|
| 1-3 | GUI Component Tests | Dialogs, View Sphere, Overlays |
| 4-5 | Core Game Logic Tests | Board Edge Cases, Storage, Controller |
| 6-7 | Integration Tests | Client-Server, UI-Logic |
| 8 | Functional Tests | Complete Game Scenarios |
| 9 | Performance Tests | AI Benchmarks |
| 10 | CI/CD Enhancements | Coverage Enforcement |

## Success Criteria (Revised)

- Overall test coverage increase from 61% to at least 80%
- Critical components (GUI elements) coverage increased to at least 70%
- All integration test coverage increased to at least 80%
- Functional tests covering all main user workflows
- Performance benchmarks established for all critical operations
- CI/CD pipeline enforcing minimum coverage standards

## Key Changes from Original Plan

1. **Increased focus on GUI testing**: Allocating more time and priority to the components with the lowest coverage
2. **More detailed test cases**: Providing more specific test scenarios for complex components
3. **Coverage-driven priorities**: Reorganizing the plan to address the most critical gaps first
4. **Specific success metrics**: Setting clear, measurable targets for coverage improvements
5. **Timeline adjustment**: Allocating more time to GUI testing (3 weeks instead of 1 week)

This revised plan maintains the overall structure and timeline of the original plan while adjusting priorities to address the identified coverage gaps more effectively.
