"""HC-SR04 ultrasonic distance sensor driver (trigger/echo GPIO) — alternative
to the VL53L1X ToF sensor, selected via distance_sensor.type in config.yaml."""
try:
    from gpiozero import DistanceSensor as _GPIOZeroDistanceSensor
except Exception:  # pragma: no cover
    _GPIOZeroDistanceSensor = None


class UltrasonicHCSR04:
    def __init__(self, config):
        if _GPIOZeroDistanceSensor is None:
            raise RuntimeError(
                "gpiozero not available; run with --simulation or install "
                "gpiozero on the Raspberry Pi."
            )
        cfg = config.section("distance_sensor")
        trigger_pin = cfg.get("trigger_pin", 23)
        echo_pin = cfg.get("echo_pin", 24)
        max_distance = cfg.get("max_distance_m", 3.0)
        self._sensor = _GPIOZeroDistanceSensor(
            echo=echo_pin, trigger=trigger_pin, max_distance=max_distance
        )

    def read(self):
        return self._sensor.distance

    def close(self):
        self._sensor.close()
