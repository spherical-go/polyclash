class Game:
    """
    This class specifies the base Game class. To define your own game, subclass
    this class and implement the functions below. This works when the game is
    two-player, adversarial and turn-based.

    Use 1 for player1 and -1 for player2.
    """

    def __init__(self):
        pass

    def init_board(self):
        pass

    def board_size(self):
        pass

    def action_size(self):
        pass

    def next_state(self, board, player, action):
        pass

    def valid_moves(self, board, player):
        pass

    def game_ended(self, board, player):
        pass

    def canonical_form(self, board, player):
        pass

    def symmetries(self, board, pi):
        pass

    def representation(self, board):
        pass
