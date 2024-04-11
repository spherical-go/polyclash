import numpy as np


class Board:
    def __init__(self):
        self.grid = np.zeros([60])
        self.current_player = "black"

    def place_stone(self, position):
        if self.grid[position] != 0:
            raise ValueError("Position already occupied")
        if self.current_player == "black":
            self.grid[position] = -1
        else:
            self.grid[position] = 1

    def check_capture(self, position):
        pass

    def switch_player(self):
        if self.current_player == "black":
            self.current_player = "white"
        else:
            self.current_player = "black"

    def calculate_score(self):
        pass

    def play(self, position):
        self.place_stone(position)
        self.check_capture(position)
        self.calculate_score()
        self.switch_player()


