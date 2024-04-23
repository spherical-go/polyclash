from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition


class AIPlayerWorker(QThread):
    trigger = pyqtSignal()

    def __init__(self, player):
        super(AIPlayerWorker, self).__init__()
        self.player = player
        self.is_running = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.trigger.connect(self.on_turn)
        self.waiting = True  # 初始状态为等待

    def on_turn(self):
        self.mutex.lock()
        try:
            if not self.waiting:
                self.player.auto_place()  # AI makes a move
                self.player.board.switch_player()
        finally:
            self.mutex.unlock()
            # self.sleep()  # Ensures the thread goes back to waiting after action

    def run(self):
        self.mutex.lock()
        while self.is_running:
            if self.waiting:
                self.wait_condition.wait(self.mutex)  # Wait until triggered
        self.mutex.unlock()

    def stop(self):
        self.is_running = False
        self.wake_up()  # Wake up the thread to ensure it can exit
        self.wait()

    def wake_up(self):
        self.mutex.lock()
        self.waiting = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def sleep(self):
        self.mutex.lock()
        self.waiting = True
        self.mutex.unlock()

    def step(self):
        if not self.is_running:
            self.is_running = True
            self.start()
        self.wake_up()
        self.trigger.emit()  # Move trigger.emit to ensure it's only called once per step

