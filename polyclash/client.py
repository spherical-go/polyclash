import sys

from PyQt5.QtWidgets import QApplication

from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import SphericalGoController
from polyclash.game.player import HUMAN, AI
from polyclash.gui.main import MainWindow


def main():
    app = QApplication(sys.argv)

    controller = SphericalGoController()
    controller.add_player(BLACK, kind=HUMAN)
    controller.add_player(WHITE, kind=AI)

    window = MainWindow(controller=controller)

    screen = app.primaryScreen().geometry()
    width = screen.width() // 5 * 4
    height = screen.height() // 5 * 4
    x = (screen.width() - width) // 2
    y = (screen.height() - height) // 2
    window.move(x, y)
    window.resize(width, height)

    controller.board.reset()
    window.delayed_resize(width+1, height+1)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
