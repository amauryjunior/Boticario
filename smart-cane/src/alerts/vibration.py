"""Vibration motor control (left/right) — RF08. Drives a repeating pulse
pattern via PWM whose speed/intensity scales with the risk level."""
import threading

try:
    from gpiozero import PWMOutputDevice
except Exception:  # pragma: no cover - not available off-device
    PWMOutputDevice = None


class VibrationMotor:
    PULSE_PATTERNS = {
        1: {"period_s": 1.5, "duty": 0.4},
        2: {"period_s": 0.8, "duty": 0.7},
        3: {"period_s": 0.3, "duty": 1.0},
    }

    def __init__(self, pin, name="motor", simulate=False, on_event=None):
        self.pin = pin
        self.name = name
        self.simulate = simulate or PWMOutputDevice is None
        self.on_event = on_event
        self._device = None if self.simulate else PWMOutputDevice(pin)
        self._thread = None
        self._stop_event = threading.Event()

    def _emit(self, action, **kwargs):
        if self.on_event:
            self.on_event(self.name, action, kwargs)

    def pulse(self, risk_level):
        """Start (or restart) a repeating pulse pattern for the given risk level."""
        pattern = self.PULSE_PATTERNS.get(risk_level)
        if pattern is None:
            self.stop()
            return
        self.stop()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._pulse_loop, args=(pattern,), daemon=True)
        self._thread.start()
        self._emit("pulse_start", risk_level=risk_level)

    def _pulse_loop(self, pattern):
        period = pattern["period_s"]
        duty = pattern["duty"]
        on_time = period * 0.35
        off_time = max(period - on_time, 0.05)
        while not self._stop_event.is_set():
            self._set_value(duty)
            if self._stop_event.wait(on_time):
                break
            self._set_value(0.0)
            if self._stop_event.wait(off_time):
                break
        self._set_value(0.0)

    def _set_value(self, duty):
        if self._device is not None:
            self._device.value = duty
        self._emit("value", duty=duty)

    def stop(self):
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.0)
        self._thread = None
        self._set_value(0.0)
        self._emit("stop")

    def close(self):
        self.stop()
        if self._device is not None:
            self._device.close()
