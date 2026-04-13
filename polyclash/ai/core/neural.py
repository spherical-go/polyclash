class NeuralNet:
    """
    This class specifies the base NeuralNet class. To define your own neural
    network, subclass this class and implement the functions below. The neural
    network does not consider the current player, and instead only deals with
    the canonical form of the board.
    """

    def __init__(self, game):
        pass

    def train(self, examples):
        pass

    def predict(self, board):
        pass

    def save_checkpoint(self, folder, filename):
        pass

    def load_checkpoint(self, folder, filename):
        pass
