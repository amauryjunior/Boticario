"""Timing helpers used for latency measurement and loop pacing."""
import time


def now_ms():
    return time.monotonic() * 1000.0


class Timer:
    """Context manager that records elapsed wall-clock time in milliseconds."""

    def __init__(self):
        self.elapsed_ms = 0.0

    def __enter__(self):
        self._start = now_ms()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = now_ms() - self._start
        return False
