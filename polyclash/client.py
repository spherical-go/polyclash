import sys

from PyQt5.QtWidgets import QApplication

from polyclash.board import board
from polyclash.ui.main import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create a board and a city manager
    window = MainWindow()
    window.resize(2000, 1200)
    board.register_observer(window.sphere_view)
    board.register_observer(window.overlay_info)

    screen = app.primaryScreen().geometry()
    x = (screen.width() - window.width()) / 2
    y = (screen.height() - window.height()) / 2
    window.move(int(x), int(y))

    window.show()
    sys.exit(app.exec_())
