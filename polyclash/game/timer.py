from __future__ import annotations

import time
from typing import Optional


class Timer:
    def __init__(self, duration: float) -> None:
        self.duration: float = duration
        self.start_time: Optional[float] = None
        self.paused: bool = False
        self.remaining_time: float = duration

    def start(self) -> None:
        self.start_time = time.time()

    def pause(self) -> None:
        if self.start_time is not None:
            self.remaining_time -= time.time() - self.start_time
            self.paused = True
            self.start_time = None

    def resume(self) -> None:
        if self.paused:
            self.start_time = time.time()
            self.paused = False

    def reset(self) -> None:
        self.start_time = None
        self.remaining_time = self.duration
        self.paused = False

    def get_time(self) -> float:
        if self.start_time is not None:
            return self.duration - (time.time() - self.start_time)
        return self.remaining_time

    def is_expired(self) -> bool:
        return self.get_time() <= 0
