"""Distance sensor abstraction — RF04. Wraps a ToF or ultrasonic backend with
moving-average filtering, invalid-reading rejection, and a hard read timeout
so a stalled sensor can never block the main loop."""
import random
import threading

from collections import deque

from src.sensors.tof_vl53l1x import ToFVL53L1X
from src.sensors.ultrasonic_hcsr04 import UltrasonicHCSR04

READ_TIMEOUT_S = 0.05


class SimulatedDistanceBackend:
    """Generates plausible distance readings for --simulation mode: a slow
    random walk between min/max, with occasional invalid samples."""

    def __init__(self, min_m=0.2, max_m=3.0):
        self.min_m = min_m
        self.max_m = max_m
        self._value = max_m

    def read(self):
        step = random.uniform(-0.15, 0.15)
        self._value = min(max(self._value + step, self.min_m - 0.05), self.max_m + 0.5)
        if random.random() < 0.03:
            return None
        return round(self._value, 3)

    def close(self):
        pass


class DistanceSensor:
    def __init__(self, config, simulate=False):
        cfg = config.section("distance_sensor")
        self.enabled = cfg.get("enabled", True)
        self.min_distance_m = cfg.get("min_distance_m", 0.2)
        self.max_distance_m = cfg.get("max_distance_m", 3.0)
        window = cfg.get("moving_average_window", 5)
        self._history = deque(maxlen=max(window, 1))
        self.simulate = simulate

        if simulate or not self.enabled:
            self.backend = SimulatedDistanceBackend(self.min_distance_m, self.max_distance_m)
        elif cfg.get("type", "vl53l1x") == "hc-sr04":
            self.backend = UltrasonicHCSR04(config)
        else:
            self.backend = ToFVL53L1X(config)

    def _is_valid(self, value):
        if value is None:
            return False
        return self.min_distance_m <= value <= (self.max_distance_m + 1.0)

    def read(self):
        """Read one filtered distance sample in meters, or None if unavailable.
        Runs the backend read in a daemon thread with a hard timeout so a
        hung I2C/GPIO call can never stall the main scanning loop (RF04)."""
        result = {"value": None}

        def _do_read():
            try:
                result["value"] = self.backend.read()
            except Exception:
                result["value"] = None

        thread = threading.Thread(target=_do_read, daemon=True)
        thread.start()
        thread.join(timeout=READ_TIMEOUT_S)
        raw = result["value"] if not thread.is_alive() else None

        if not self._is_valid(raw):
            return self._smoothed() if self._history else None

        self._history.append(raw)
        return self._smoothed()

    def _smoothed(self):
        if not self._history:
            return None
        return sum(self._history) / len(self._history)

    def close(self):
        self.backend.close()
