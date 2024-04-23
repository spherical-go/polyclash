from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget

from polyclash.game.board import BLACK
from polyclash.gui.constants import stone_black_color, stone_white_color


black = QColor(*[int(255 * elm) for elm in stone_black_color])
white = QColor(*[int(255 * elm) for elm in stone_white_color])


class OverlayInfo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.black_ratio = 0
        self.white_ratio = 0
        self.unknown_ratio = 1
        self.color = Qt.black  # set default color
        self.setAttribute(Qt.WA_TranslucentBackground)  # set transparent background

    def paintEvent(self, event):
        painter = QPainter(self)

        # set opacity
        painter.setOpacity(0.5)  # 50% transparent

        # draw a translucent background
        painter.setBrush(QBrush(QColor(192, 192, 192, 127)))  # light gray, semi-transparent
        painter.drawRect(self.rect())  # cover the entire widget area

        # draw a circle disk with color
        painter.setOpacity(1.0)  # 100% opaque
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(10, 10, 50, 50)  # draw a circle with (x, y, width, height)

        # draw text
        painter.setPen(Qt.black)
        painter.drawText(70, 30, f"Black: {100 * self.black_ratio:.2f}")
        painter.drawText(70, 50, f"White: {100 * self.white_ratio:.2f}")
        painter.drawText(70, 70, f"Unknown: {100 * self.unknown_ratio:.2f}")

    def change_color(self, color):
        self.color = color
        self.update()

    def change_score(self, black_ratio, white_ratio, unknown_ratio):
        self.black_ratio = black_ratio
        self.white_ratio = white_ratio
        self.unknown_ratio = unknown_ratio
        self.update()

    def handle_notification(self, message, **kwargs):
        if message == "switch_player":
            color = black if kwargs["side"] == BLACK else white
            self.change_color(color)
        if message == "reset":
            self.change_color(BLACK)
            self.change_score(0, 0, 1)
        if message == "add_stone":
            self.change_score(*kwargs['score'])
        if message == "remove_stone":
            self.change_score(*kwargs['score'])
