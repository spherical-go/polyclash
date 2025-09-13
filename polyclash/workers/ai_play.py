from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QMutex, QThread, QWaitCondition, pyqtSignal


class AIPlayerWorker(QThread):
    trigger = pyqtSignal()

    def __init__(self, player: Any) -> None:
        super(AIPlayerWorker, self).__init__()
        self.player: Any = player
        self.is_running: bool = False
        self.mutex: QMutex = QMutex()
        self.wait_condition: QWaitCondition = QWaitCondition()
        self.trigger.connect(self.on_turn)
        self.waiting: bool = True  # 初始状态为等待

    def on_turn(self) -> None:
        self.mutex.lock()
        try:
            if not self.waiting:
                self.player.auto_place()  # AI makes a move
                self.player.board.switch_player()
        finally:
            self.mutex.unlock()
            # self.sleep()  # Ensures the thread goes back to waiting after action

    def run(self) -> None:
        self.mutex.lock()
        while self.is_running:
            if self.waiting:
                self.wait_condition.wait(self.mutex)  # Wait until triggered
        self.mutex.unlock()

    def stop(self) -> None:
        self.is_running = False
        self.wake_up()  # Wake up the thread to ensure it can exit
        self.wait()

    def wake_up(self) -> None:
        self.mutex.lock()
        self.waiting = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def sleep(self) -> None:
        self.mutex.lock()
        self.waiting = True
        self.mutex.unlock()

    def step(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.start()
        self.wake_up()
        self.trigger.emit()  # Move trigger.emit to ensure it's only called once per step
