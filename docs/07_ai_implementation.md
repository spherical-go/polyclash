# AI Implementation

This document provides details about the implementation of the AI in PolyClash, including the algorithms used for move evaluation and selection.

## Overview

PolyClash includes an AI opponent that can play the game using strategic algorithms. The AI is implemented in the `AIPlayer` class and uses a `SimulatedBoard` for move evaluation.

## AI Player

The `AIPlayer` class (`polyclash/game/player.py`) extends the base `Player` class and adds AI-specific functionality:

```python
class AIPlayer(Player):
    def __init__(self, **kwargs):
        super().__init__(kind=AI, **kwargs)
        self.worker = AIPlayerWorker(self)

    def auto_place(self):
        while self.board.current_player == self.side:
            try:
                self.board.disable_notification()
                position = self.board.genmove(self.side)
                self.board.enable_notification()
                self.play(position)
                break  # Exit the loop if move was successful
            except ValueError:
                continue  # Try again if an error occurred

    def stop_worker(self):
        if self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
```

The `auto_place` method is the main entry point for AI move generation. It:
1. Disables board notifications to avoid UI updates during move evaluation
2. Calls the `genmove` method on the board to generate a move
3. Enables board notifications
4. Plays the generated move
5. Handles errors by trying again

## AI Worker

The `AIPlayerWorker` class (`polyclash/workers/ai_play.py`) runs in a separate thread to avoid blocking the UI:

```python
class AIPlayerWorker(QThread):
    trigger = pyqtSignal()

    def __init__(self, player):
        super(AIPlayerWorker, self).__init__()
        self.player = player
        self.is_running = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.trigger.connect(self.on_turn)
        self.waiting = True  # Initial state is waiting

    def on_turn(self):
        self.mutex.lock()
        try:
            if not self.waiting:
                self.player.auto_place()  # AI makes a move
                self.player.board.switch_player()
        finally:
            self.mutex.unlock()

    def run(self):
        self.mutex.lock()
        while self.is_running:
            if self.waiting:
                self.wait_condition.wait(self.mutex)  # Wait until triggered
        self.mutex.unlock()

    def stop(self):
        self.is_running = False
        self.wake_up()  # Wake up the thread to ensure it can exit
        self.wait()

    def wake_up(self):
        self.mutex.lock()
        self.waiting = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def sleep(self):
        self.mutex.lock()
        self.waiting = True
        self.mutex.unlock()

    def step(self):
        if not self.is_running:
            self.is_running = True
            self.start()
        self.wake_up()
        self.trigger.emit()  # Move trigger.emit to ensure it's only called once per step
```

The worker thread uses Qt's mutex and wait condition for thread synchronization. It waits until triggered, then makes a move and switches players.

## Move Generation

The move generation is implemented in the `Board` class (`polyclash/game/board.py`):

```python
def genmove(self, player):
    if self.simulator is None:
        self.simulator = SimulatedBoard()
    self.simulator.redirect(self)
    return self.simulator.genmove(player)
```

The `genmove` method creates a `SimulatedBoard` if one doesn't exist, redirects it to the current board state, and calls its `genmove` method.

## Simulated Board

The `SimulatedBoard` class (`polyclash/game/board.py`) extends the `Board` class and adds methods for move evaluation:

```python
class SimulatedBoard(Board):
    def __init__(self):
        super().__init__()

    def redirect(self, board):
        self.board = board.board.copy()
        self.current_player = board.current_player
        self.latest_removes = board.latest_removes.copy()
        self.black_suicides = board.black_suicides.copy()
        self.white_suicides = board.white_suicides.copy()
        self.orginal_counter = board.counter
        self.turns = board.turns.copy()

    def genmove(self, player):
        best_score = -math.inf
        best_potential = math.inf
        best_move = None

        for point in self.get_empties(player):
            simulated_score, gain = self.simulate_score(0, point, player)
            simulated_score = simulated_score + 2 * gain
            if simulated_score > best_score:
                best_score = simulated_score
                best_potential = calculate_potential(self.board, point, self.counter)
                best_move = point
            elif simulated_score == best_score:
                potential = calculate_potential(self.board, point, self.counter)
                if potential < best_potential:
                    best_potential = potential
                    best_move = point

        return best_move

    def simulate_score(self, depth, point, player):
        if depth == 1:
            return 0, 0

        trail = 2
        self.latest_removes.append([])
        black_area_ratio, white_area_ratio, unclaimed_area_ratio = 0, 0, 0
        mean_rival_area_ratio, gain, mean_rival_gain = 0, 0, 0
        try:
            # Assume placing a stone at point, calculate the score, need to consider restoring the board state
            self.play(point, player, turn_check=False)  # Simulate the move
            black_area_ratio, white_area_ratio, unclaimed_area_ratio = self.score()  # Calculate the score

            empty_points = sample(self.get_empties(-player), trail)
            total_rival_area_ratio, total_rival_gain = 0, 0
            for rival_point in empty_points:
                rival_area_ratio, rival_gain = self.simulate_score(depth + 1, rival_point, -player)  # Recursively calculate opponent's score
                total_rival_area_ratio += rival_area_ratio
                total_rival_gain += rival_gain
            mean_rival_area_ratio = total_rival_area_ratio / trail
            mean_rival_gain = total_rival_gain / trail
        except ValueError as e:
            print(e)
            if 'suicide' in str(e):
                raise e

        self.board[point] = 0  # Restore the board state
        gain = 0
        if self.latest_removes and len(self.latest_removes) > 0:
            for removed in self.latest_removes[-1]:
                self.board[removed] = -self.current_player
            gain = len(self.latest_removes[-1]) / len(self.board)
            self.latest_removes.pop()

        if self.counter > self.orginal_counter:
            self.turns.pop(self.counter - 1)

        if player == BLACK:
            return black_area_ratio - mean_rival_area_ratio, gain - mean_rival_gain
        else:
            return white_area_ratio - mean_rival_area_ratio, gain - mean_rival_gain
```

## Move Evaluation Algorithm

The AI uses a combination of strategies to evaluate moves:

### Score-Based Evaluation

The primary evaluation is based on the score (area controlled) after making a move:

```python
simulated_score, gain = self.simulate_score(0, point, player)
simulated_score = simulated_score + 2 * gain
```

The `simulate_score` method:
1. Simulates making a move at the given point
2. Calculates the score after the move
3. Simulates opponent responses
4. Returns the difference between the player's score and the opponent's expected score

### Capture Bonus

The AI gives a bonus for capturing opponent stones:

```python
gain = len(self.latest_removes[-1]) / len(self.board)
```

This encourages the AI to make moves that capture opponent stones.

### Potential-Based Tiebreaking

When multiple moves have the same score, the AI uses a potential-based tiebreaker:

```python
potential = calculate_potential(self.board, point, self.counter)
if potential < best_potential:
    best_potential = potential
    best_move = point
```

The `calculate_potential` function calculates the "potential" of a move based on its distance to existing stones:

```python
def calculate_potential(board, point, counter):
    potential = 0
    for i, stone in enumerate(board):
        if stone != 0:
            distance = calculate_distance(point, i)
            if distance > 0:
                potential += (1 / distance) * np.tanh(0.5 - counter / 302)
    return potential
```

This encourages the AI to play moves that are closer to existing stones, with a decreasing weight as the game progresses.

## Look-Ahead

The AI uses a simple look-ahead mechanism to evaluate opponent responses:

```python
empty_points = sample(self.get_empties(-player), trail)
total_rival_area_ratio, total_rival_gain = 0, 0
for rival_point in empty_points:
    rival_area_ratio, rival_gain = self.simulate_score(depth + 1, rival_point, -player)
    total_rival_area_ratio += rival_area_ratio
    total_rival_gain += rival_gain
mean_rival_area_ratio = total_rival_area_ratio / trail
mean_rival_gain = total_rival_gain / trail
```

The AI samples a few possible opponent moves and calculates the average score after those moves. This allows it to anticipate opponent responses and choose moves that are robust against them.

## Limitations

The current AI implementation has several limitations:

1. **Limited Look-Ahead**: The AI only looks ahead a few moves, which limits its strategic depth
2. **Random Sampling**: The AI samples opponent moves randomly, which may miss important responses
3. **Simple Evaluation**: The evaluation function is relatively simple and doesn't capture all aspects of Go strategy
4. **No Opening Book**: The AI doesn't have an opening book for standard opening moves
5. **No Endgame Solver**: The AI doesn't have a specialized endgame solver

## Potential Improvements

The AI could be improved in several ways:

1. **Monte Carlo Tree Search (MCTS)**: Implement MCTS for more sophisticated move selection
2. **Neural Network Evaluation**: Use a neural network for position evaluation
3. **Opening Book**: Add an opening book for standard opening moves
4. **Endgame Solver**: Add a specialized endgame solver
5. **Pattern Recognition**: Implement pattern recognition for common Go patterns
6. **Influence Maps**: Use influence maps to better evaluate territorial control
7. **Parallel Search**: Implement parallel search to explore more positions

## Customization

The AI can be customized by modifying the following parameters:

- `trail`: The number of opponent moves to sample (higher values give more accurate evaluation but slower performance)
- The weight of the capture bonus (`2 * gain` in the score calculation)
- The potential calculation formula

These parameters can be adjusted to change the AI's playing style and strength.
