"""VL53L1X Time-of-Flight distance sensor driver (I2C)."""
try:
    import board
    import busio
    import adafruit_vl53l1x
except Exception:  # pragma: no cover - only available on real hardware
    board = busio = adafruit_vl53l1x = None


class ToFVL53L1X:
    def __init__(self, config):
        if adafruit_vl53l1x is None:
            raise RuntimeError(
                "adafruit_vl53l1x library not available; run with --simulation "
                "or install the VL53L1X dependencies on the Raspberry Pi."
            )
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = adafruit_vl53l1x.VL53L1X(i2c)
        self._sensor.start_ranging()

    def read(self):
        if not self._sensor.data_ready:
            return None
        distance_cm = self._sensor.distance
        self._sensor.clear_interrupt()
        if distance_cm is None:
            return None
        return distance_cm / 100.0

    def close(self):
        try:
            self._sensor.stop_ranging()
        except Exception:
            pass
