"""Camera frame acquisition — RF02. Wraps Picamera2/OpenCV with graceful
degradation and a simulated frame source for --simulation mode."""
import time

try:
    from picamera2 import Picamera2
except Exception:  # pragma: no cover - only available on the Raspberry Pi
    Picamera2 = None

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


class CameraReader:
    def __init__(self, config, simulate=False):
        cfg = config.section("camera")
        self.enabled = cfg.get("enabled", True)
        self.width = cfg.get("width", 320)
        self.height = cfg.get("height", 320)
        self.fps = cfg.get("fps", 10)
        self.simulate = simulate or not self.enabled
        self._picam = None
        self._cv_cap = None
        self._last_frame_time = 0.0
        self.available = False

        if self.simulate:
            self.available = True
            return

        if Picamera2 is not None:
            try:
                self._picam = Picamera2()
                video_config = self._picam.create_video_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"}
                )
                self._picam.configure(video_config)
                self._picam.start()
                self.available = True
                return
            except Exception:
                self._picam = None

        if cv2 is not None:
            try:
                self._cv_cap = cv2.VideoCapture(0)
                self._cv_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._cv_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.available = self._cv_cap.isOpened()
            except Exception:
                self._cv_cap = None
                self.available = False

    def read_frame(self):
        """Return the newest frame, dropping stale ones so the pipeline never
        processes backlog (RF02 acceptance criterion)."""
        min_interval = 1.0 / max(self.fps, 1)
        now = time.monotonic()
        if now - self._last_frame_time < min_interval:
            return None
        self._last_frame_time = now

        if self.simulate:
            return self._simulated_frame()

        if self._picam is not None:
            try:
                return self._picam.capture_array()
            except Exception:
                return None

        if self._cv_cap is not None:
            # Discard any buffered frame so we always process the latest one.
            self._cv_cap.grab()
            ok, frame = self._cv_cap.retrieve()
            return frame if ok else None

        return None

    def _simulated_frame(self):
        if np is None:
            return None
        return np.zeros((self.height, self.width, 3), dtype="uint8")

    def restart(self):
        """Attempt to recover the camera after a failure (RNF03 robustness)."""
        self.close()
        time.sleep(0.5)
        if Picamera2 is not None and not self.simulate:
            try:
                self._picam = Picamera2()
                self._picam.start()
                self.available = True
                return True
            except Exception:
                self.available = False
                return False
        return self.available

    def close(self):
        if self._picam is not None:
            try:
                self._picam.stop()
            except Exception:
                pass
        if self._cv_cap is not None:
            try:
                self._cv_cap.release()
            except Exception:
                pass
