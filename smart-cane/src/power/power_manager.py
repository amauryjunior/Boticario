"""Power management — RNF05 (idle FPS scaling, movement-aware, low-power mode)."""
import time


class PowerManager:
    def __init__(self, config, imu_sensor=None):
        cfg = config.section("power")
        self.low_power_mode = cfg.get("low_power_mode", True)
        self.idle_fps = cfg.get("idle_fps", 3)
        self.active_fps = config.get("camera.fps", 10)
        self.movement_detection_enabled = cfg.get("movement_detection_enabled", True)
        self.imu = imu_sensor
        self.idle_timeout_s = 8.0
        self._idle_since = None

    def is_idle(self):
        if not self.movement_detection_enabled or self.imu is None or not self.imu.enabled:
            return False
        moving = self.imu.is_moving()
        now = time.monotonic()
        if moving:
            self._idle_since = None
            return False
        if self._idle_since is None:
            self._idle_since = now
            return False
        return (now - self._idle_since) >= self.idle_timeout_s

    def current_fps(self):
        if self.low_power_mode and self.is_idle():
            return self.idle_fps
        return self.active_fps

    def battery_status(self, voltage=None):
        """Coarse battery label from a voltage reading, if available. No ADC
        is wired in the base MVP, so this defaults to "unknown" — see RF12."""
        if voltage is None:
            return "unknown"
        if voltage < 3.5:
            return "low"
        if voltage < 3.7:
            return "medium"
        return "high"
