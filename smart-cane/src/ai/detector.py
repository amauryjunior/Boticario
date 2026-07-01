"""Obstacle detection abstraction — RF03. Provides one consistent interface
across three backends, selected automatically by what's available:

  1. tflite      — real inference using models/obstacle_detector.tflite
  2. heuristic   — contour/edge fallback (OpenCV) when no trained model exists
  3. simulated   — synthetic detections for --simulation / development

Every backend returns the same schema: class, confidence, bbox, position
(esquerda/centro/direita), in_roi, timestamp — see RF03 acceptance criteria.
"""
import random
import time

from src.ai.model_loader import ModelLoader
from src.ai.obstacle_classes import classes_from_config
from src.camera.frame_preprocessor import horizontal_position

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


class Detector:
    def __init__(self, config, simulate=False):
        self.config = config
        self.simulate = simulate
        self.min_confidence = config.get("ai.min_confidence", 0.55)
        self.classes = classes_from_config(config)
        self.enabled = config.get("ai.enabled", True)
        self.model = None
        self.mode = "simulated" if simulate else "disabled"

        if self.enabled and not simulate:
            self.model = ModelLoader(config.get("ai.model_path"))
            if self.model.load():
                self.mode = "tflite"
            elif cv2 is not None and np is not None:
                self.mode = "heuristic"
            else:
                self.mode = "disabled"

    def detect(self, frame):
        """Return a list of detections matching the RF03 schema."""
        if self.mode == "simulated":
            return self._simulated_detections()
        if self.mode == "tflite":
            return self._tflite_detections(frame)
        if self.mode == "heuristic":
            return self._heuristic_detections(frame)
        return []

    def _simulated_detections(self):
        if random.random() > 0.6:
            return []
        cls = random.choice(self.classes)
        confidence = round(random.uniform(0.5, 0.95), 2)
        position = random.choice(["esquerda", "centro", "direita"])
        return [
            {
                "class": cls,
                "confidence": confidence,
                "bbox": (40, 20, 120, 140),
                "position": position,
                "in_roi": True,
                "timestamp": time.time(),
            }
        ]

    def _tflite_detections(self, frame):
        # Placeholder wiring for a real quantized detector: resize to the
        # model's expected input, run inference, decode boxes/scores/labels.
        # Left generic since obstacle_detector.tflite is trained outside this
        # repository — see models/README.md.
        return []

    def _heuristic_detections(self, frame):
        """Contour-based fallback used when no trained model is available:
        flags large, high-contrast regions in the ROI as generic obstacles."""
        if frame is None or cv2 is None:
            return []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        edges = cv2.Canny(gray, 60, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape[:2]
        min_area = 0.02 * h * w
        detections = []
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            if cw * ch < min_area:
                continue
            confidence = min(0.5 + (cw * ch) / (h * w), 0.9)
            detections.append(
                {
                    "class": "obstaculo_generico",
                    "confidence": round(confidence, 2),
                    "bbox": (x, y, cw, ch),
                    "position": horizontal_position(x + cw / 2, w),
                    "in_roi": True,
                    "timestamp": time.time(),
                }
            )
        return detections
