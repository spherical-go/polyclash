from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget

from polyclash.board import BLACK


class OverlayInfo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = Qt.black  # set default color
        self.setAttribute(Qt.WA_TranslucentBackground)  # set transparent background

    def paintEvent(self, event):
        painter = QPainter(self)

        # set opacity
        painter.setOpacity(0.5)  # 50% transparent

        # 绘制半透明背景
        painter.setBrush(QBrush(QColor(192, 192, 192, 127)))  # 浅灰色，半透明
        painter.drawRect(self.rect())  # 覆盖整个Widget区域

        # 绘制小圆盘，不透明
        painter.setOpacity(1.0)  # 重置为不透明
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(10, 10, 50, 50)  # 绘制小圆盘

    def change_color(self, color):
        self.color = color
        self.update()

    def handle_notification(self, message, **kwargs):
        if message == "switch_player":
            color = Qt.black if kwargs["side"] == BLACK else Qt.white
            self.change_color(color)
