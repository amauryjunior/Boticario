"""Buzzer control — RF09. Used sparingly: short beeps for critical risk or
system errors only, so it never masks ambient sounds the user relies on."""
import threading

try:
    from gpiozero import DigitalOutputDevice
except Exception:  # pragma: no cover
    DigitalOutputDevice = None


class Buzzer:
    def __init__(self, pin, simulate=False, on_event=None):
        self.pin = pin
        self.simulate = simulate or DigitalOutputDevice is None
        self.on_event = on_event
        self._device = None if self.simulate else DigitalOutputDevice(pin)
        self.enabled = True

    def _emit(self, action, **kwargs):
        if self.on_event:
            self.on_event("buzzer", action, kwargs)

    def beep(self, duration_ms=120):
        if not self.enabled:
            return
        self._set(True)
        threading.Timer(duration_ms / 1000.0, self._set, args=(False,)).start()
        self._emit("beep", duration_ms=duration_ms)

    def error_pattern(self):
        """Short double-beep used for critical/error states (RF01, RF09)."""
        self.beep(80)
        threading.Timer(0.15, self.beep, args=(80,)).start()

    def _set(self, on):
        if self._device is not None:
            self._device.value = on
        self._emit("value", on=on)

    def close(self):
        self._set(False)
        if self._device is not None:
            self._device.close()
