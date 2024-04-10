import numpy as np


class Board:
    def __init__(self):
        self.grid = np.zeros([302])
        self.current_player = "blue"

    def place_stone(self, position):
        if self.grid[position] != 0:
            raise ValueError("Position already occupied")
        if self.current_player == "blue":
            self.grid[position] = -1
        else:
            self.grid[position] = 1

    def check_capture(self, position):
        pass

    def switch_player(self):
        if self.current_player == "blue":
            self.current_player = "red"
        else:
            self.current_player = "blue"

    def calculate_score(self):
        pass

    def play(self, position):
        self.place_stone(position)
        self.check_capture(position)
        self.calculate_score()
        self.switch_player()


