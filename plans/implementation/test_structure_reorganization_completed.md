# Test Structure Reorganization Implementation Plan - COMPLETED

**Status: COMPLETED (March 25, 2025)**

This implementation plan has been fully executed and completed. The test structure has been successfully reorganized according to this plan, and all tests are now passing.

## Implementation Summary

- ✅ Created the hierarchical test structure as specified
- ✅ Set up test configuration files (conftest.py, pytest.ini)
- ✅ Migrated existing tests to the new structure 
- ✅ Added new test files for previously untested components
- ✅ Fixed test failures in the reorganized structure
- ✅ Achieved 61% overall test coverage with the new structure

## Remaining Coverage Gaps

While the test structure reorganization is complete, significant coverage gaps remain that should be addressed in subsequent phases. See `plans/phase1_testing_revised.md` for a detailed analysis of current coverage and planned improvements.

---

# Original Implementation Plan

This document provides a detailed implementation plan for the first step of the Enhanced Testing Framework phase: Test Structure Reorganization. This plan includes specific code examples and commands to execute.

## Goals

- Create a hierarchical test structure
- Set up test configuration files
- Migrate existing tests to the new structure
- Ensure all existing tests pass in the new structure

## Implementation Steps

### 1. Create the New Test Directory Structure

First, create the new directory structure for the tests:

```bash
# Create the main test directories
mkdir -p tests/unit/game
mkdir -p tests/unit/gui
mkdir -p tests/unit/util
mkdir -p tests/unit/workers
mkdir -p tests/integration
mkdir -p tests/functional
mkdir -p tests/performance
```

### 2. Set Up Test Configuration

#### 2.1 Create a Root `conftest.py`

Create a root `conftest.py` file with shared fixtures:

```python
# tests/conftest.py
import pytest
from polyclash.game.board import Board
from polyclash.game.controller import SphericalGoController
from polyclash.game.player import Player, BLACK, WHITE

@pytest.fixture
def empty_board():
    """Fixture for an empty board."""
    return Board()

@pytest.fixture
def controller():
    """Fixture for a controller with an empty board."""
    return SphericalGoController()

@pytest.fixture
def black_player():
    """Fixture for a black player."""
    return Player(BLACK)

@pytest.fixture
def white_player():
    """Fixture for a white player."""
    return Player(WHITE)
```

#### 2.2 Create Module-Specific `conftest.py` Files

Create module-specific `conftest.py` files with fixtures relevant to each module:

```python
# tests/unit/game/conftest.py
import pytest
from polyclash.game.board import Board, BLACK, WHITE

@pytest.fixture
def board_with_stones():
    """Fixture for a board with some stones placed."""
    board = Board()
    # Place some stones in a typical pattern
    board.play(0, BLACK)
    board.play(1, WHITE)
    board.play(2, BLACK)
    board.play(3, WHITE)
    return board

@pytest.fixture
def board_with_capture():
    """Fixture for a board with a capture situation."""
    board = Board()
    # Set up a capture situation
    # This will depend on the specific board topology
    # ...
    return board
```

```python
# tests/unit/gui/conftest.py
import pytest
from PyQt5.QtWidgets import QApplication
from polyclash.gui.main import MainWindow
from polyclash.game.controller import SphericalGoController

@pytest.fixture(scope="session")
def qapp():
    """Fixture for a QApplication instance."""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(qapp):
    """Fixture for a MainWindow instance."""
    controller = SphericalGoController()
    window = MainWindow(controller=controller)
    yield window
    window.close()
```

```python
# tests/integration/conftest.py
import pytest
import tempfile
import os
from polyclash.server import app as flask_app

@pytest.fixture
def client():
    """Fixture for a Flask test client."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client
```

#### 2.3 Create `pytest.ini`

Create a `pytest.ini` file to configure pytest:

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=polyclash --cov-report=term --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    functional: Functional tests
    performance: Performance tests
```

### 3. Migrate Existing Tests

#### 3.1 Analyze Existing Tests

First, analyze the existing tests to understand their structure and dependencies:

```bash
# List existing test files
ls -la tests/
```

#### 3.2 Migrate Board Tests

Move and update the board tests:

```python
# tests/unit/game/test_board.py
import pytest
from polyclash.game.board import Board, BLACK, WHITE

# Import existing tests from tests/test_board.py
# Update imports and fixtures as needed

class TestBoardInitialization:
    def test_board_creation(self):
        board = Board()
        assert len(board.board) == 60  # 60 vertices in a snub dodecahedron
        assert board.current_player == BLACK

    # Add more initialization tests...

class TestBoardPlay:
    def test_stone_placement(self):
        board = Board()
        board.play(0, BLACK)
        assert board.board[0] == BLACK
        assert board.current_player == WHITE

    # Add more play tests...

class TestBoardCapture:
    def test_single_stone_capture(self, board_with_capture):
        # Test capture mechanics
        # ...

    # Add more capture tests...

class TestBoardScoring:
    def test_empty_board_scoring(self):
        board = Board()
        black_score, white_score, _ = board.score()
        assert black_score == white_score  # Equal scores on empty board

    # Add more scoring tests...
```

#### 3.3 Migrate AI Tests

Move and update the AI tests:

```python
# tests/unit/workers/test_ai_play.py
import pytest
from polyclash.game.board import Board, BLACK, WHITE
from polyclash.workers.ai_play import AIPlayerWorker

# Import existing tests from tests/test_ai.py
# Update imports and fixtures as needed

class TestAIMoveGeneration:
    def test_ai_generates_valid_move(self):
        board = Board()
        move = board.genmove(BLACK)
        assert 0 <= move < 60  # Valid move index

    # Add more move generation tests...

class TestAIEvaluation:
    def test_position_evaluation(self):
        board = Board()
        # Set up a specific board state
        # ...
        # Test evaluation function
        # ...

    # Add more evaluation tests...
```

#### 3.4 Migrate Server Tests

Move and update the server tests:

```python
# tests/unit/util/test_api.py
import pytest
from polyclash.util.api import connect, join, ready, play, close

# Import existing tests from tests/test_server.py
# Update imports and fixtures as needed

class TestAPIFunctions:
    def test_connect_function(self, mocker):
        # Mock the requests.post method
        mock_post = mocker.patch('requests.post')
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'black_key': 'test_black_key',
            'white_key': 'test_white_key',
            'viewer_key': 'test_viewer_key'
        }
        
        # Test the connect function
        black_key, white_key, viewer_key = connect('http://test-server.com', 'test_token')
        assert black_key == 'test_black_key'
        assert white_key == 'test_white_key'
        assert viewer_key == 'test_viewer_key'

    # Add more API function tests...
```

```python
# tests/integration/test_client_server.py
import pytest
from polyclash.util.api import connect, join, ready, play, close
from polyclash.server import app

# Import existing tests from tests/test_server.py
# Update imports and fixtures as needed

class TestServerEndpoints:
    def test_new_game_endpoint(self, client):
        response = client.post('/sphgo/new', json={'token': 'test_token'})
        assert response.status_code == 200
        data = response.json
        assert 'game_id' in data
        assert 'black_key' in data
        assert 'white_key' in data
        assert 'viewer_key' in data

    # Add more endpoint tests...
```

#### 3.5 Migrate Storage Tests

Move and update the storage tests:

```python
# tests/unit/util/test_storage.py
import pytest
from polyclash.util.storage import MemoryStorage, RedisStorage, DataStorage

# Import existing tests from tests/test_storage.py
# Update imports and fixtures as needed

class TestMemoryStorage:
    def test_create_room(self):
        storage = MemoryStorage()
        data = storage.create_room()
        assert 'game_id' in data
        assert 'black_key' in data
        assert 'white_key' in data
        assert 'viewer_key' in data

    # Add more memory storage tests...

class TestRedisStorage:
    def test_create_room(self, mocker):
        # Mock Redis
        mock_redis = mocker.patch('redis.StrictRedis')
        storage = RedisStorage()
        data = storage.create_room()
        assert 'game_id' in data
        assert 'black_key' in data
        assert 'white_key' in data
        assert 'viewer_key' in data

    # Add more Redis storage tests...
```

#### 3.6 Migrate Data Tests

Move and update the data tests:

```python
# tests/unit/data/test_data.py
import pytest
from polyclash.data.data import load_data

# Import existing tests from tests/test_data.py
# Update imports and fixtures as needed

class TestDataLoading:
    def test_load_data(self):
        data = load_data()
        assert data is not None
        # Add more specific assertions based on expected data

    # Add more data loading tests...
```

### 4. Add New Test Files

Create new test files for components that don't have tests yet:

```python
# tests/unit/game/test_controller.py
import pytest
from polyclash.game.controller import SphericalGoController, LOCAL, NETWORK
from polyclash.game.board import BLACK, WHITE

class TestControllerInitialization:
    def test_controller_creation(self):
        controller = SphericalGoController()
        assert controller.mode == LOCAL
        assert controller.board is not None

    # Add more initialization tests...

class TestControllerGameFlow:
    def test_add_player(self):
        controller = SphericalGoController()
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        assert len(controller.players) == 2

    def test_start_game(self):
        controller = SphericalGoController()
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.start_game()
        assert controller.is_started

    # Add more game flow tests...
```

```python
# tests/unit/game/test_player.py
import pytest
from polyclash.game.player import Player, HumanPlayer, AIPlayer, RemotePlayer, BLACK, WHITE

class TestPlayerCreation:
    def test_human_player_creation(self):
        player = HumanPlayer(side=BLACK)
        assert player.side == BLACK
        assert player.kind == HUMAN

    def test_ai_player_creation(self):
        player = AIPlayer(side=WHITE)
        assert player.side == WHITE
        assert player.kind == AI

    # Add more player creation tests...

class TestPlayerInteraction:
    def test_human_player_play(self, mocker):
        board = mocker.Mock()
        player = HumanPlayer(side=BLACK)
        player.board = board
        player.play(0)
        board.play.assert_called_once_with(0, BLACK)

    # Add more player interaction tests...
```

### 5. Create Integration Tests

Create integration tests for component interactions:

```python
# tests/integration/test_ui_logic.py
import pytest
from PyQt5.QtCore import Qt
from polyclash.gui.main import MainWindow
from polyclash.game.controller import SphericalGoController

class TestUILogicIntegration:
    def test_stone_placement_updates_ui(self, qapp, main_window):
        # Simulate placing a stone
        controller = main_window.controller
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.start_game()
        
        # Mock the view_sphere's update method
        main_window.view_sphere.update = lambda: None
        
        # Place a stone
        controller.play(0)
        
        # Check that the board state is updated
        assert controller.board.board[0] == BLACK

    # Add more UI-logic integration tests...
```

### 6. Create Functional Tests

Create functional tests for complete workflows:

```python
# tests/functional/test_game_scenarios.py
import pytest
from polyclash.game.controller import SphericalGoController
from polyclash.game.board import BLACK, WHITE
from polyclash.game.player import HumanPlayer, AIPlayer

class TestCompleteGameScenarios:
    def test_human_vs_ai_game(self):
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=AI)
        controller.start_game()
        
        # Play a few moves
        controller.play(0)  # Human plays
        # AI will automatically play
        
        # Check game state
        assert controller.board.counter >= 2
        assert controller.is_started

    # Add more complete game scenarios...
```

### 7. Create Performance Tests

Create performance tests for critical operations:

```python
# tests/performance/test_ai_performance.py
import pytest
from polyclash.game.board import Board, BLACK
import time

class TestAIPerformance:
    def test_ai_move_generation_time(self, benchmark):
        board = Board()
        # Benchmark the AI move generation
        result = benchmark(board.genmove, BLACK)
        assert 0 <= result < 60  # Valid move index

    # Add more AI performance tests...
```

### 8. Update `requirements-dev.txt`

Update the development requirements to include the testing tools:

```
pytest==7.4.0
pytest-cov==4.1.0
pytest-mock==3.11.1
pytest-benchmark==4.0.0
pytest-asyncio==0.21.1
pytest-qt==4.2.0
```

### 9. Create a Test Runner Script

Create a script to run the tests:

```python
# scripts/run_tests.py
#!/usr/bin/env python
import subprocess
import sys
import os

def run_tests():
    """Run the tests with pytest."""
    # Change to the project root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run the tests
    result = subprocess.run(['pytest'], capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    # Return the exit code
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())
```

Make the script executable:

```bash
chmod +x scripts/run_tests.py
```

## Verification

After implementing these changes, verify that the tests are working correctly:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run with coverage report
pytest --cov=polyclash --cov-report=term --cov-report=html
```

## Next Steps

After completing the test structure reorganization, proceed to the next step of the Enhanced Testing Framework phase: implementing Core Game Logic Tests.
