"""IMU driver (MPU-6050 family) — optional. Used for movement detection
(RNF05 power saving) and cane-motion context for risk fusion (RF06)."""
import math
import time

try:
    import smbus2
except Exception:  # pragma: no cover - only available on real hardware
    smbus2 = None

MPU6050_ADDR = 0x68
MPU6050_ACCEL_XOUT_H = 0x3B
MPU6050_PWR_MGMT_1 = 0x6B


class IMUSensor:
    def __init__(self, config, simulate=False):
        cfg = config.section("imu")
        self.enabled = cfg.get("enabled", False)
        self.movement_threshold_g = cfg.get("movement_threshold_g", 0.05)
        self.simulate = simulate or smbus2 is None
        self._bus = None
        self._address = cfg.get("i2c_address", MPU6050_ADDR)

        if self.enabled and not self.simulate:
            self._bus = smbus2.SMBus(1)
            self._bus.write_byte_data(self._address, MPU6050_PWR_MGMT_1, 0)

    def read_acceleration_g(self):
        """Return (ax, ay, az) in g, or None if the IMU is disabled."""
        if not self.enabled:
            return None
        if self.simulate:
            t = time.monotonic()
            return (0.15 * math.sin(t * 2.0), 0.05 * math.sin(t * 0.7), 1.0)
        raw = self._bus.read_i2c_block_data(self._address, MPU6050_ACCEL_XOUT_H, 6)
        ax = _to_signed16(raw[0] << 8 | raw[1]) / 16384.0
        ay = _to_signed16(raw[2] << 8 | raw[3]) / 16384.0
        az = _to_signed16(raw[4] << 8 | raw[5]) / 16384.0
        return (ax, ay, az)

    def is_moving(self):
        accel = self.read_acceleration_g()
        if accel is None:
            return True  # unknown state -> assume moving (safer default, RNF05)
        ax, ay, az = accel
        magnitude_delta = abs(math.sqrt(ax ** 2 + ay ** 2 + az ** 2) - 1.0)
        return magnitude_delta > self.movement_threshold_g

    def close(self):
        if self._bus is not None:
            self._bus.close()


def _to_signed16(value):
    if value >= 0x8000:
        value -= 0x10000
    return value
