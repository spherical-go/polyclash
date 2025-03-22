import pytest
from polyclash.game.board import Board, BLACK, WHITE

class TestAIPerformance:
    def test_ai_move_generation_time(self, benchmark):
        """Benchmark AI move generation time."""
        board = Board()
        # Benchmark the AI move generation
        result = benchmark(board.genmove, BLACK)
        assert 0 <= result < 302  # Valid move index

    def test_ai_performance_empty_board(self, benchmark):
        """Test AI performance with an empty board."""
        board = Board()
        empty_result = benchmark.pedantic(board.genmove, args=(BLACK,), iterations=5, rounds=3)
        assert 0 <= empty_result < 302

    def test_ai_performance_few_stones(self, benchmark):
        """Test AI performance with a few stones on the board."""
        board = Board()
        board.play(0, BLACK)
        board.switch_player()  # Switch to WHITE
        board.play(1, WHITE)
        board.switch_player()  # Switch to BLACK
        board.play(2, BLACK)
        board.switch_player()  # Switch to WHITE
        board.play(3, WHITE)
        board.switch_player()  # Switch to BLACK
        few_stones_result = benchmark.pedantic(board.genmove, args=(BLACK,), iterations=5, rounds=3)
        assert 0 <= few_stones_result < 302
        
    def test_ai_performance_many_stones(self, benchmark):
        """Test AI performance with many stones on the board."""
        board = Board()
        for i in range(20):
            try:
                player = BLACK if i % 2 == 0 else WHITE
                if board.current_player == player:
                    board.play(i, player)
                    board.switch_player()
            except ValueError:
                pass  # Skip invalid moves
        many_stones_result = benchmark.pedantic(board.genmove, args=(BLACK,), iterations=5, rounds=3)
        assert 0 <= many_stones_result < 302

    def test_simulation_depth_performance(self, benchmark):
        """Test performance with different simulation depths."""
        board = Board()
        board.play(0, BLACK)
        board.switch_player()  # Switch to WHITE
        board.play(1, WHITE)
        board.switch_player()  # Switch to BLACK
        
        # Initialize the simulator if it's None
        if board.simulator is None:
            from polyclash.game.board import SimulatedBoard
            board.simulator = SimulatedBoard()
        
        # Create a simulator
        simulator = board.simulator
        simulator.redirect(board)
        
        # Benchmark with depth 0
        result = benchmark.pedantic(
            simulator.simulate_score, args=(0, 2, BLACK), iterations=5, rounds=3
        )
        
        # Note: This is not a strict assertion, as performance can vary
        # The main goal is to measure and track performance over time
        print(f"Simulation performance: {result}")
