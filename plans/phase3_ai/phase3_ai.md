# Phase 3: AI Enhancement

This document outlines the detailed plan for implementing the AI Enhancement phase of the PolyClash improvement roadmap. This phase focuses on significantly improving the AI opponent by implementing more sophisticated algorithms and optimizations.

## Goals

- Implement Monte Carlo Tree Search (MCTS) algorithm
- Add position evaluation heuristics
- Create an opening book for common positions
- Implement endgame solver for final positions
- Add difficulty levels for AI
- Optimize AI performance
- Implement AI training and learning capabilities

## Current AI Implementation

The current AI implementation uses a simple algorithm:
- It evaluates each possible move by simulating the game state after the move
- It calculates a score based on territory control and captures
- It samples a few opponent responses to estimate the opponent's best reply
- It chooses the move with the highest score and lowest "potential" (a measure of distance to existing stones)

While functional, this approach has several limitations:
- Limited look-ahead capability
- Random sampling of opponent moves
- Simple evaluation function
- No opening book or endgame solver
- No learning capability

## Implementation Plan

### 1. Monte Carlo Tree Search Implementation (3 weeks)

#### 1.1 MCTS Core Algorithm
- Implement the four phases of MCTS:
  - Selection: Using UCB1 formula to balance exploration and exploitation
  - Expansion: Adding new nodes to the tree
  - Simulation: Random playouts to estimate node value
  - Backpropagation: Updating node statistics based on simulation results

```python
class MCTSNode:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = state.get_legal_moves()
        
    def select_child(self):
        # UCB1 formula: wi/ni + C * sqrt(ln(N)/ni)
        C = 1.41  # Exploration parameter
        return max(self.children, key=lambda c: c.wins/c.visits + C * math.sqrt(math.log(self.visits)/c.visits))
        
    def expand(self):
        move = self.untried_moves.pop()
        next_state = self.state.copy()
        next_state.play(move)
        child = MCTSNode(next_state, self, move)
        self.children.append(child)
        return child
        
    def update(self, result):
        self.visits += 1
        self.wins += result
        
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
        
    def is_terminal(self):
        return self.state.is_game_over()
```

#### 1.2 MCTS Integration with Board
- Create a `MCTSPlayer` class that extends `AIPlayer`
- Implement the `genmove` method using MCTS
- Add configuration options for MCTS parameters

```python
class MCTSPlayer(AIPlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.simulation_count = kwargs.get('simulation_count', 1000)
        self.time_limit = kwargs.get('time_limit', 5.0)  # seconds
        
    def genmove(self, board, player):
        root = MCTSNode(board)
        end_time = time.time() + self.time_limit
        
        # Run simulations until time limit or simulation count is reached
        for _ in range(self.simulation_count):
            if time.time() > end_time:
                break
                
            # Selection
            node = root
            while node.is_fully_expanded() and not node.is_terminal():
                node = node.select_child()
                
            # Expansion
            if not node.is_terminal():
                node = node.expand()
                
            # Simulation
            state = node.state.copy()
            while not state.is_game_over():
                move = random.choice(state.get_legal_moves())
                state.play(move)
                
            # Backpropagation
            result = 1 if state.get_winner() == player else 0
            while node is not None:
                node.update(result)
                node = node.parent
                
        # Return the move with the most visits
        return max(root.children, key=lambda c: c.visits).move
```

#### 1.3 MCTS Enhancements
- Implement RAVE (Rapid Action Value Estimation) for better move selection
- Add virtual loss to encourage thread divergence in parallel MCTS
- Implement progressive widening for large branching factors

### 2. Position Evaluation Heuristics (2 weeks)

#### 2.1 Pattern Recognition
- Implement pattern matching for common Go shapes
- Create a database of pattern templates
- Assign weights to different patterns

```python
class Pattern:
    def __init__(self, template, weight):
        self.template = template
        self.weight = weight
        
    def matches(self, board, position):
        # Check if the pattern matches at the given position
        # ...
        return match_score
```

#### 2.2 Influence Maps
- Implement influence maps to visualize territorial control
- Use influence maps for position evaluation
- Combine influence with other heuristics

```python
def calculate_influence(board, player):
    influence = np.zeros(len(board.board))
    for i, stone in enumerate(board.board):
        if stone == 0:
            continue
        stone_influence = stone * INFLUENCE_FACTOR
        for j, _ in enumerate(board.board):
            if i == j:
                continue
            distance = board.calculate_distance(i, j)
            if distance > 0:
                influence[j] += stone_influence / distance
    return influence
```

#### 2.3 Strategic Features
- Implement evaluation of strategic features:
  - Territory control
  - Connectivity
  - Influence
  - Safety of groups
  - Potential for growth

```python
def evaluate_position(board, player):
    score = 0
    
    # Territory
    black_score, white_score, _ = board.score()
    territory_score = black_score - white_score if player == BLACK else white_score - black_score
    score += TERRITORY_WEIGHT * territory_score
    
    # Connectivity
    connectivity = calculate_connectivity(board, player)
    score += CONNECTIVITY_WEIGHT * connectivity
    
    # Influence
    influence = calculate_influence(board, player)
    score += INFLUENCE_WEIGHT * sum(influence)
    
    # Group safety
    safety = calculate_group_safety(board, player)
    score += SAFETY_WEIGHT * safety
    
    # Potential
    potential = calculate_potential(board, player)
    score += POTENTIAL_WEIGHT * potential
    
    return score
```

### 3. Opening Book (1 week)

#### 3.1 Opening Database
- Create a database of strong opening moves
- Implement a mechanism to select openings based on board state
- Add variations for different playing styles

```python
class OpeningBook:
    def __init__(self, filename):
        self.openings = {}
        self.load(filename)
        
    def load(self, filename):
        # Load openings from file
        # ...
        
    def get_move(self, board):
        # Find a matching opening position
        board_hash = self.hash_board(board)
        if board_hash in self.openings:
            return self.openings[board_hash]
        return None
        
    def hash_board(self, board):
        # Create a hash of the board state
        # ...
        return board_hash
```

#### 3.2 Opening Integration
- Integrate the opening book with the MCTS algorithm
- Use opening book for the first N moves
- Gradually transition to MCTS as the game progresses

```python
def genmove(self, board, player):
    # Check opening book first
    if board.counter < 10:  # First 10 moves
        move = self.opening_book.get_move(board)
        if move is not None:
            return move
            
    # Fall back to MCTS
    return self.mcts_genmove(board, player)
```

### 4. Endgame Solver (2 weeks)

#### 4.1 Exact Solver
- Implement minimax algorithm for endgame positions
- Use alpha-beta pruning for efficiency
- Add transposition tables to avoid redundant calculations

```python
def solve_endgame(board, player, alpha, beta, depth):
    # Check if game is over
    if board.is_game_over():
        return board.score()
        
    # Check transposition table
    board_hash = hash_board(board)
    if board_hash in transposition_table:
        return transposition_table[board_hash]
        
    # Get legal moves
    moves = board.get_legal_moves()
    
    # If no moves, pass
    if not moves:
        new_board = board.copy()
        new_board.pass_move()
        return -solve_endgame(new_board, -player, -beta, -alpha, depth + 1)
        
    # Try each move
    best_score = -float('inf')
    for move in moves:
        new_board = board.copy()
        new_board.play(move, player)
        score = -solve_endgame(new_board, -player, -beta, -alpha, depth + 1)
        best_score = max(best_score, score)
        alpha = max(alpha, best_score)
        if alpha >= beta:
            break
            
    # Store result in transposition table
    transposition_table[board_hash] = best_score
    return best_score
```

#### 4.2 Endgame Integration
- Detect when the game enters the endgame phase
- Switch from MCTS to endgame solver
- Implement a smooth transition between the two algorithms

```python
def is_endgame(board):
    # Check if the game is in the endgame phase
    empty_count = sum(1 for stone in board.board if stone == 0)
    return empty_count <= ENDGAME_THRESHOLD
    
def genmove(self, board, player):
    if is_endgame(board):
        return self.solve_endgame(board, player)
    else:
        return self.mcts_genmove(board, player)
```

### 5. Difficulty Levels (1 week)

#### 5.1 Parameter Tuning
- Implement different parameter sets for various difficulty levels
- Adjust simulation count, time limit, and exploration parameter
- Create presets for beginner, intermediate, and advanced levels

```python
DIFFICULTY_PRESETS = {
    'beginner': {
        'simulation_count': 100,
        'time_limit': 1.0,
        'exploration_param': 2.0,  # More exploration
        'use_opening_book': False,
        'use_endgame_solver': False,
    },
    'intermediate': {
        'simulation_count': 500,
        'time_limit': 3.0,
        'exploration_param': 1.41,  # Standard UCB1
        'use_opening_book': True,
        'use_endgame_solver': False,
    },
    'advanced': {
        'simulation_count': 1000,
        'time_limit': 5.0,
        'exploration_param': 1.0,  # Less exploration
        'use_opening_book': True,
        'use_endgame_solver': True,
    },
}
```

#### 5.2 Deliberate Mistakes
- Implement a mechanism for the AI to make deliberate mistakes
- Adjust mistake probability based on difficulty level
- Ensure mistakes are plausible and not too obvious

```python
def apply_difficulty(self, moves, scores, difficulty):
    if difficulty == 'advanced':
        # Always choose the best move
        return moves[np.argmax(scores)]
        
    if difficulty == 'intermediate':
        # Sometimes choose a suboptimal move
        if random.random() < 0.2:  # 20% chance
            # Choose from the top 3 moves
            top_indices = np.argsort(scores)[-3:]
            return moves[random.choice(top_indices)]
        else:
            return moves[np.argmax(scores)]
            
    if difficulty == 'beginner':
        # Often choose a suboptimal move
        if random.random() < 0.4:  # 40% chance
            # Choose from the top 5 moves
            top_indices = np.argsort(scores)[-5:]
            return moves[random.choice(top_indices)]
        else:
            return moves[np.argmax(scores)]
```

### 6. Performance Optimization (2 weeks)

#### 6.1 Parallel Processing
- Implement parallel MCTS using multiple threads
- Use thread pool for simulation phase
- Implement lock-free tree updates

```python
def parallel_mcts(board, player, num_threads=4):
    root = MCTSNode(board)
    end_time = time.time() + TIME_LIMIT
    
    def worker():
        while time.time() < end_time:
            # Run one MCTS iteration
            # ...
            
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)
        
    for thread in threads:
        thread.join()
        
    return max(root.children, key=lambda c: c.visits).move
```

#### 6.2 Memory Optimization
- Implement more efficient board representation
- Use bitboards for faster operations
- Optimize node memory usage in MCTS tree

```python
class BitBoard:
    def __init__(self):
        self.black_stones = 0  # 64-bit integer
        self.white_stones = 0  # 64-bit integer
        
    def play(self, position, player):
        if player == BLACK:
            self.black_stones |= (1 << position)
        else:
            self.white_stones |= (1 << position)
            
    def has_stone(self, position, player):
        if player == BLACK:
            return (self.black_stones & (1 << position)) != 0
        else:
            return (self.white_stones & (1 << position)) != 0
```

#### 6.3 Algorithm Optimization
- Implement early pruning in MCTS
- Use domain knowledge to guide simulations
- Implement incremental updates for board evaluation

```python
def guided_simulation(board, player):
    # Use domain knowledge to guide the simulation
    # Instead of random playouts
    while not board.is_game_over():
        moves = board.get_legal_moves()
        if not moves:
            board.pass_move()
            continue
            
        # Choose moves with some heuristics
        capture_moves = [m for m in moves if would_capture(board, m, player)]
        if capture_moves:
            move = random.choice(capture_moves)
        else:
            # Choose a move that's close to existing stones
            move = choose_move_by_proximity(board, moves, player)
            
        board.play(move, player)
        player = -player
        
    return board.get_winner()
```

### 7. AI Training and Learning (2 weeks)

#### 7.1 Self-Play Training
- Implement a self-play training pipeline
- Generate games by having the AI play against itself
- Use the generated games to improve the AI

```python
def self_play_training(num_games=100):
    games = []
    for _ in range(num_games):
        board = Board()
        moves = []
        while not board.is_game_over():
            player = board.current_player
            move = mcts_genmove(board, player)
            board.play(move, player)
            moves.append(move)
        winner = board.get_winner()
        games.append((moves, winner))
    return games
```

#### 7.2 Pattern Learning
- Extract patterns from self-play games
- Assign weights to patterns based on win rate
- Update the pattern database with learned patterns

```python
def extract_patterns(games):
    patterns = {}
    for moves, winner in games:
        board = Board()
        for move in moves:
            player = board.current_player
            # Extract patterns around the move
            local_patterns = get_local_patterns(board, move)
            for pattern in local_patterns:
                if pattern not in patterns:
                    patterns[pattern] = {'count': 0, 'wins': 0}
                patterns[pattern]['count'] += 1
                if player == winner:
                    patterns[pattern]['wins'] += 1
            board.play(move, player)
    return patterns
```

#### 7.3 Opening Book Generation
- Use self-play games to generate an opening book
- Identify successful opening sequences
- Add variations based on win rate

```python
def generate_opening_book(games, min_frequency=5):
    openings = {}
    for moves, winner in games:
        board = Board()
        for i, move in enumerate(moves[:10]):  # Consider first 10 moves as opening
            player = board.current_player
            board_hash = hash_board(board)
            if board_hash not in openings:
                openings[board_hash] = {}
            if move not in openings[board_hash]:
                openings[board_hash][move] = {'count': 0, 'wins': 0}
            openings[board_hash][move]['count'] += 1
            if player == winner:
                openings[board_hash][move]['wins'] += 1
            board.play(move, player)
            
    # Filter out rare moves
    filtered_openings = {}
    for board_hash, moves in openings.items():
        filtered_moves = {move: data for move, data in moves.items() if data['count'] >= min_frequency}
        if filtered_moves:
            filtered_openings[board_hash] = filtered_moves
            
    return filtered_openings
```

## Testing Strategy

### Unit Tests
- Test MCTS components individually
- Verify correct behavior of selection, expansion, simulation, and backpropagation
- Test position evaluation heuristics
- Test opening book and endgame solver

### Integration Tests
- Test MCTS integration with the game board
- Test difficulty level adjustments
- Test performance optimizations

### Functional Tests
- Test AI performance against known positions
- Compare new AI against the old AI
- Measure win rate against different opponents

### Performance Tests
- Benchmark MCTS performance
- Measure nodes explored per second
- Compare parallel vs. sequential implementation

## Dependencies

```
numpy>=1.20.0
scipy>=1.7.0
numba>=0.54.0  # For performance optimization
joblib>=1.0.0  # For parallel processing
```

## Success Criteria

- New AI achieves at least 80% win rate against the old AI
- MCTS can explore at least 10,000 nodes per second on a standard machine
- Different difficulty levels provide appropriate challenge for players of different skill levels
- Opening book covers at least 100 common opening positions
- Endgame solver can solve positions with up to 15 empty vertices

## Timeline

| Week | Tasks |
|------|-------|
| 1-3 | MCTS Implementation |
| 4-5 | Position Evaluation Heuristics |
| 6 | Opening Book |
| 7-8 | Endgame Solver |
| 9 | Difficulty Levels |
| 10-11 | Performance Optimization |
| 12-13 | AI Training and Learning |

## Next Steps

After completing the AI Enhancement phase, we will move on to the Network Play Enhancement phase, which will build upon the improved AI to provide a better multiplayer experience.
