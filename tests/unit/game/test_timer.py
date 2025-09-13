import time

from polyclash.game.timer import Timer


class TestTimer:
    def test_timer_initialization(self):
        timer = Timer(60)
        assert timer.duration == 60
        assert timer.remaining_time == 60
        assert timer.paused == False
        assert timer.start_time is None

    def test_timer_start(self):
        timer = Timer(60)
        timer.start()
        assert timer.start_time is not None
        assert timer.get_time() <= 60

    def test_timer_pause_resume(self):
        timer = Timer(60)
        timer.start()
        time.sleep(0.1)
        timer.pause()
        assert timer.paused == True
        assert timer.start_time is None
        time_after_pause = timer.get_time()
        time.sleep(0.1)
        assert (
            timer.get_time() == time_after_pause
        )  # Time should not decrease after pausing

        timer.resume()
        assert timer.paused == False
        assert timer.start_time is not None

    def test_timer_reset(self):
        timer = Timer(60)
        timer.start()
        time.sleep(0.1)
        timer.pause()
        timer.reset()
        assert timer.remaining_time == 60
        assert timer.paused == False
        assert timer.start_time is None

    def test_timer_time_decrease(self):
        timer = Timer(60)
        timer.start()
        time.sleep(1)
        assert timer.get_time() < 60

    def test_timer_expiration(self):
        timer = Timer(0.1)
        timer.start()
        time.sleep(0.2)
        assert timer.is_expired() == True
