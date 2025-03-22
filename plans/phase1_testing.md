# Phase 1.1: Enhanced Testing Framework

This document outlines the detailed plan for implementing the Enhanced Testing Framework phase of the PolyClash improvement roadmap. This is the first phase of our improvement efforts, focusing on strengthening the foundation of the project through comprehensive testing.

## Goals

- Increase test coverage across all components
- Implement different types of tests (unit, integration, functional)
- Set up performance benchmarks
- Establish CI/CD pipeline for automated testing
- Create a sustainable testing culture

## Current Testing Status

The project currently has some tests in the `tests/` directory:
- `test_ai.py`: Tests for the AI implementation
- `test_board.py`: Tests for the game board logic
- `test_data.py`: Tests for the data structures
- `test_server.py`: Tests for the server functionality
- `test_storage.py`: Tests for the storage mechanisms

While this provides a foundation, we need to expand the test coverage significantly and implement a more structured testing approach.

## Implementation Plan

### 1. Test Structure Reorganization (1 week)

#### 1.1 Create a Hierarchical Test Structure
```
tests/
├── unit/
│   ├── game/
│   │   ├── test_board.py
│   │   ├── test_controller.py
│   │   ├── test_player.py
│   │   └── test_timer.py
│   ├── gui/
│   │   ├── test_main.py
│   │   ├── test_view_sphere.py
│   │   └── ...
│   ├── util/
│   │   ├── test_api.py
│   │   ├── test_storage.py
│   │   └── ...
│   └── workers/
│       ├── test_ai_play.py
│       └── test_network.py
├── integration/
│   ├── test_client_server.py
│   ├── test_ui_logic.py
│   └── ...
├── functional/
│   ├── test_game_scenarios.py
│   ├── test_network_play.py
│   └── ...
└── performance/
    ├── test_ai_performance.py
    ├── test_server_performance.py
    └── ...
```

#### 1.2 Set Up Test Configuration
- Create `conftest.py` files for shared fixtures
- Set up pytest configuration in `pytest.ini`
- Configure test coverage reporting

#### 1.3 Migrate Existing Tests
- Move existing tests to the new structure
- Update imports and dependencies
- Ensure all existing tests pass in the new structure

### 2. Core Game Logic Tests (2 weeks)

#### 2.1 Board State Management
- Test board initialization with different configurations
- Test stone placement in various scenarios
- Test liberty counting in different configurations
- Test group detection and management

Example test cases:
```python
def test_board_initialization():
    board = Board()
    assert len(board.board) == 60  # 60 vertices in a snub dodecahedron
    assert board.current_player == BLACK

def test_stone_placement():
    board = Board()
    board.play(0, BLACK)
    assert board.board[0] == BLACK
    assert board.current_player == WHITE
```

#### 2.2 Move Validation
- Test valid move detection
- Test invalid move rejection
- Test ko rule enforcement
- Test suicide move prevention

Example test cases:
```python
def test_invalid_move_occupied_vertex():
    board = Board()
    board.play(0, BLACK)
    with pytest.raises(ValueError):
        board.play(0, WHITE)

def test_ko_rule():
    # Set up a ko situation
    board = Board()
    # ... (setup code)
    with pytest.raises(ValueError, match="Ko rule violation"):
        board.play(ko_position, BLACK)
```

#### 2.3 Capture Mechanics
- Test single stone capture
- Test group capture
- Test complex capture scenarios
- Test capture counting and tracking

Example test cases:
```python
def test_single_stone_capture():
    board = Board()
    # Place a white stone
    board.play(0, WHITE)
    # Surround it with black stones
    # ... (setup code)
    # The white stone should be captured
    assert board.board[0] == 0
    assert len(board.latest_removes[-1]) == 1
```

#### 2.4 Scoring Algorithm
- Test territory calculation
- Test score computation in various end-game scenarios
- Test score updates during gameplay
- Test final score determination

Example test cases:
```python
def test_scoring_empty_board():
    board = Board()
    black_score, white_score, _ = board.score()
    assert black_score == white_score  # Equal scores on empty board

def test_scoring_with_territories():
    board = Board()
    # Set up a board with clear territories
    # ... (setup code)
    black_score, white_score, _ = board.score()
    assert black_score > white_score  # Black has more territory
```

### 3. AI Component Tests (1 week)

#### 3.1 Move Generation
- Test AI move selection in various board states
- Test move prioritization
- Test response to different game situations

Example test cases:
```python
def test_ai_move_generation():
    board = Board()
    # Set up a specific board state
    # ... (setup code)
    move = board.genmove(BLACK)
    assert 0 <= move < 60  # Valid move index

def test_ai_capture_prioritization():
    board = Board()
    # Set up a board where capture is possible
    # ... (setup code)
    move = board.genmove(BLACK)
    assert move == capture_move  # AI should prioritize capture
```

#### 3.2 Board Evaluation
- Test position evaluation accuracy
- Test territory assessment
- Test threat detection

Example test cases:
```python
def test_position_evaluation():
    board = Board()
    # Set up a board with a clear advantage for black
    # ... (setup code)
    simulator = SimulatedBoard()
    simulator.redirect(board)
    score, _ = simulator.simulate_score(0, test_move, BLACK)
    assert score > 0  # Positive score for black
```

#### 3.3 Simulation
- Test look-ahead accuracy
- Test simulation depth management
- Test performance with different parameters

Example test cases:
```python
def test_simulation_depth():
    board = Board()
    # ... (setup code)
    simulator = SimulatedBoard()
    simulator.redirect(board)
    # Test with different depths
    score1, _ = simulator.simulate_score(0, test_move, BLACK)
    score2, _ = simulator.simulate_score(1, test_move, BLACK)
    assert score1 != score2  # Different depths should give different scores
```

### 4. Network Component Tests (1 week)

#### 4.1 API Endpoints
- Test all REST endpoints
- Test request validation
- Test response formatting
- Test error handling

Example test cases:
```python
def test_new_game_endpoint(client):
    response = client.post('/sphgo/new', json={'token': 'test_token'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'game_id' in data
    assert 'black_key' in data
    assert 'white_key' in data
    assert 'viewer_key' in data
```

#### 4.2 Socket.IO Events
- Test event emission and reception
- Test real-time updates
- Test connection management

Example test cases:
```python
def test_socket_join_event(socket_client):
    socket_client.emit('join', {'key': 'test_key'})
    received = socket_client.get_received()
    assert len(received) > 0
    assert received[0]['name'] == 'joined'
```

#### 4.3 Authentication
- Test token generation and validation
- Test session management
- Test permission enforcement

Example test cases:
```python
def test_invalid_token():
    response = client.post('/sphgo/play', json={'token': 'invalid_token'})
    assert response.status_code == 401
```

### 5. UI Component Tests (1 week)

#### 5.1 Main Window
- Test menu actions
- Test status bar updates
- Test window resizing

#### 5.2 Game View
- Test 3D rendering
- Test mouse interaction
- Test keyboard shortcuts

#### 5.3 Overlays
- Test overlay info display
- Test overlay map functionality
- Test dialog interactions

### 6. Integration Tests (1 week)

#### 6.1 Client-Server Integration
- Test client-server communication
- Test game state synchronization
- Test error handling and recovery

#### 6.2 UI-Logic Integration
- Test UI updates in response to game state changes
- Test user interaction flow
- Test error message display

#### 6.3 Storage-Server Integration
- Test data persistence across server restarts
- Test concurrent access patterns
- Test data migration scenarios

### 7. Functional Tests (1 week)

#### 7.1 Complete Game Scenarios
- Test playing a complete game against AI
- Test network game setup and play
- Test game ending conditions

#### 7.2 Error Scenarios
- Test network disconnection handling
- Test invalid move recovery
- Test server error recovery

### 8. Performance Tests (1 week)

#### 8.1 AI Performance
- Benchmark AI move generation time
- Test AI performance with different board states
- Identify performance bottlenecks

#### 8.2 Network Performance
- Test server performance under load
- Measure latency in different network conditions
- Test concurrent game handling

#### 8.3 UI Performance
- Test rendering performance
- Measure UI responsiveness
- Identify UI bottlenecks

### 9. CI/CD Setup (1 week)

#### 9.1 GitHub Actions Configuration
- Set up workflow for running tests on pull requests
- Configure test coverage reporting
- Set up performance benchmark tracking

#### 9.2 Quality Gates
- Define minimum test coverage requirements
- Set up linting and code quality checks
- Configure automated code review

## Testing Tools

We will use the following tools for testing:

- **pytest**: Main testing framework
- **pytest-cov**: For measuring test coverage
- **pytest-mock**: For mocking dependencies
- **pytest-benchmark**: For performance testing
- **pytest-asyncio**: For testing asynchronous code
- **pytest-qt**: For testing PyQt applications

## Dependencies

```
pytest==7.4.0
pytest-cov==4.1.0
pytest-mock==3.11.1
pytest-benchmark==4.0.0
pytest-asyncio==0.21.1
pytest-qt==4.2.0
```

## Success Criteria

- Unit test coverage of at least 80% for core game logic
- Integration test coverage of at least 70% for component interactions
- Functional tests covering all main user workflows
- Performance benchmarks established for critical operations
- CI/CD pipeline successfully running tests on all pull requests
- All existing and new tests passing

## Timeline

| Week | Tasks |
|------|-------|
| 1 | Test Structure Reorganization |
| 2-3 | Core Game Logic Tests |
| 4 | AI Component Tests |
| 5 | Network Component Tests |
| 6 | UI Component Tests |
| 7 | Integration Tests |
| 8 | Functional Tests |
| 9 | Performance Tests |
| 10 | CI/CD Setup |

## Next Steps

After completing the Enhanced Testing Framework phase, we will move on to the Code Refactoring phase, which will build upon the improved testing infrastructure to safely refactor the codebase.
