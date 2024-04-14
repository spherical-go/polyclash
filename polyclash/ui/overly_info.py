from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget

from polyclash.board import BLACK
from polyclash.ui.constants import stone_black_color, stone_white_color


black = QColor(*[int(255 * elm) for elm in stone_black_color])
white = QColor(*[int(255 * elm) for elm in stone_white_color])


class OverlayInfo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def change_color(self, color):
        self.color = color
        self.update()

    def handle_notification(self, message, **kwargs):
        if message == "switch_player":
            color = black if kwargs["side"] == BLACK else white
            self.change_color(color)
