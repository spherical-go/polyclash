import time


class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.start_time = None
        self.paused = False
        self.remaining_time = duration

    def start(self):
        self.start_time = time.time()

    def pause(self):
        if self.start_time is not None:
            self.remaining_time -= time.time() - self.start_time
            self.paused = True
            self.start_time = None

    def resume(self):
        if self.paused:
            self.start_time = time.time()
            self.paused = False

    def reset(self):
        self.start_time = None
        self.remaining_time = self.duration
        self.paused = False

    def get_time(self):
        if self.start_time is not None:
            return self.duration - (time.time() - self.start_time)
        return self.remaining_time

    def is_expired(self):
        return self.get_time() <= 0

