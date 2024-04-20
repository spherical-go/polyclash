from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QWidget


class OverlayMap(QWidget):
    def __init__(self, parent=None, rows=4, columns=2):
        super().__init__(parent)
        self.rows = rows
        self.columns = columns
        self.images = [[None for _ in range(columns)] for _ in range(rows)]
        self.scaled_images = [[None for _ in range(columns)] for _ in range(rows)]
        self.last_width = 0
        self.last_height = 0
        self.setAttribute(Qt.WA_TranslucentBackground)  # set transparent background
        self.setMouseTracking(True)  # Enable mouse tracking
        self.sphere_view = None

    def set_image(self, row, col, image):
        if row < self.rows and col < self.columns:
            self.images[row][col] = image
            self.scaled_images[row][col] = None  # Invalidate scaled image cache
            self.update()  # Trigger repaint

    def resizeEvent(self, event):
        # When the widget is resized, invalidate the scaled image cache
        if self.last_width != self.width() or self.last_height != self.height():
            self.last_width = self.width()
            self.last_height = self.height()
            self.scaled_images = [[None for _ in range(self.columns)] for _ in range(self.rows)]
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # set opacity
        painter.setOpacity(0.5)  # 50% transparent

        # draw a translucent background
        painter.setBrush(QBrush(QColor(192, 192, 192, 127)))  # light gray, semi-transparent
        painter.drawRect(self.rect())  # cover the entire widget area

        img_height = self.height() // self.rows
        img_width = self.width() // self.columns
        painter.setOpacity(1.0)
        for row in range(self.rows):
            for col in range(self.columns):
                if self.scaled_images[row][col] is None and self.images[row][col] is not None:
                    # only when the scaled image is not cached, scale the image
                    self.scaled_images[row][col] = self.images[row][col].scaled(img_width, img_height,
                                                                                Qt.KeepAspectRatio)
                img = self.scaled_images[row][col]
                if img:
                    x = col * img_width
                    y = row * img_height
                    painter.drawImage(x, y, img)

    def mousePressEvent(self, event):
        col = event.x() // (self.width() // self.columns)
        row = event.y() // (self.height() // self.rows)
        self.trigger_view_change(row, col)

    def set_sphere_view(self, sphere_view):
        self.sphere_view = sphere_view

    def trigger_view_change(self, row, col):
        if self.sphere_view:
            self.sphere_view.change_view(row, col)
