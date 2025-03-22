import pytest
from polyclash.game.board import Board, BLACK, WHITE

class TestAIPerformance:
    def test_ai_move_generation_time(self, benchmark):
        """Benchmark AI move generation time."""
        board = Board()
        # Benchmark the AI move generation
        result = benchmark(board.genmove, BLACK)
        assert 0 <= result < 302  # Valid move index

    def test_ai_performance_with_different_board_states(self, benchmark):
        """Test AI performance with different board states."""
        # Empty board
        board = Board()
        empty_result = benchmark.pedantic(board.genmove, args=(BLACK,), iterations=5, rounds=3)
        assert 0 <= empty_result < 302
        
        # Board with a few stones
        board = Board()
        board.play(0, BLACK)
        board.play(1, WHITE)
        board.play(2, BLACK)
        board.play(3, WHITE)
        few_stones_result = benchmark.pedantic(board.genmove, args=(BLACK,), iterations=5, rounds=3)
        assert 0 <= few_stones_result < 302
        
        # Board with many stones
        board = Board()
        for i in range(20):
            try:
                board.play(i, BLACK if i % 2 == 0 else WHITE)
            except ValueError:
                pass  # Skip invalid moves
        many_stones_result = benchmark.pedantic(board.genmove, args=(BLACK,), iterations=5, rounds=3)
        assert 0 <= many_stones_result < 302

    def test_simulation_depth_performance(self, benchmark):
        """Test performance with different simulation depths."""
        board = Board()
        board.play(0, BLACK)
        board.play(1, WHITE)
        
        # Create a simulator
        simulator = board.simulator
        simulator.redirect(board)
        
        # Benchmark with depth 0
        depth0_result = benchmark.pedantic(
            simulator.simulate_score, args=(0, 2, BLACK), iterations=5, rounds=3
        )
        
        # Benchmark with depth 1
        depth1_result = benchmark.pedantic(
            simulator.simulate_score, args=(1, 2, BLACK), iterations=5, rounds=3
        )
        
        # Compare performance
        # Note: This is not a strict assertion, as performance can vary
        # The main goal is to measure and track performance over time
        print(f"Depth 0 performance: {depth0_result}")
        print(f"Depth 1 performance: {depth1_result}")
