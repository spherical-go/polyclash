import sys

from PyQt5.QtWidgets import QApplication

from polyclash.board import board
from polyclash.ui.main import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    screen = app.primaryScreen().geometry()
    width = screen.width() // 5 * 4
    height = screen.height() // 5 * 4
    window.resize(width, height)
    board.register_observer(window.sphere_view)
    board.register_observer(window.overlay_info)

    x = (screen.width() - width) // 2
    y = (screen.height() - height) // 2
    window.move(x, y)

    window.show()
    sys.exit(app.exec_())
