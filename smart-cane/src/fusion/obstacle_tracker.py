"""Tracks obstacle risk across frames to provide persistence — RF06/RF07.

Keeps a short rolling history of per-frame risk observations so a minimum
number of consistent frames is required before an alert is considered valid,
avoiding false alarms from single-frame sensor/vision noise.
"""
from collections import deque


class ObstacleTracker:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self._history = deque(maxlen=window_size)

    def update(self, risk_level, position):
        self._history.append((risk_level, position))

    def reset(self):
        self._history.clear()

    def persistent_risk(self, persistence_frames):
        """Return (risk_level, position) only if that risk level has held
        for at least `persistence_frames` consecutive observations, else
        (0, "nenhuma")."""
        if len(self._history) < persistence_frames:
            return 0, "nenhuma"
        recent = list(self._history)[-persistence_frames:]
        levels = [level for level, _ in recent]
        if min(levels) == 0:
            return 0, "nenhuma"
        risk_level = min(levels)
        position = recent[-1][1]
        return risk_level, position
