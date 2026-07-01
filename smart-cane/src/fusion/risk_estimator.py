"""Risk fusion — combines AI detections, distance sensor and IMU state — RF06.

Risk levels: 0 = sem risco, 1 = atenção, 2 = risco moderado, 3 = risco crítico.
"""
from dataclasses import dataclass

from src.fusion.obstacle_tracker import ObstacleTracker

RISK_NONE = 0
RISK_ATTENTION = 1
RISK_MODERATE = 2
RISK_CRITICAL = 3


@dataclass
class RiskResult:
    risk_level: int
    position: str


def _select_primary_detection(detections, min_confidence):
    """Pick the most relevant in-ROI detection above the confidence threshold."""
    valid = [
        d
        for d in detections
        if d.get("confidence", 0) >= min_confidence and d.get("in_roi", True)
    ]
    if not valid:
        return None
    return max(valid, key=lambda d: d["confidence"])


class RiskEstimator:
    """Stateful risk fusion engine implementing RF06 rules plus RF07
    persistence/hysteresis so alerts don't flicker on/off."""

    def __init__(self, config):
        self.min_confidence = config.get("ai.min_confidence", 0.55)
        self.attention_m = config.get("risk.attention_distance_m", 3.0)
        self.moderate_m = config.get("risk.moderate_distance_m", 2.0)
        self.critical_m = config.get("risk.critical_distance_m", 1.0)
        self.persistence_frames = config.get("risk.persistence_frames", 3)
        self.tracker = ObstacleTracker(window_size=max(self.persistence_frames * 2, 5))

    def _instant_risk(self, detections, distance_m):
        """Single-frame risk estimate, before persistence/hysteresis (RF06 rules)."""
        detection = _select_primary_detection(detections or [], self.min_confidence)
        valid_distance = (
            distance_m is not None and distance_m > 0 and distance_m <= self.attention_m
        )

        if detection is None and not valid_distance:
            return RISK_NONE, "nenhuma"

        # Rule 1: no visual detection, but the distance sensor sees something close.
        if detection is None:
            if distance_m <= self.critical_m:
                return RISK_MODERATE, "centro"
            if distance_m <= self.moderate_m:
                return RISK_ATTENTION, "centro"
            return RISK_NONE, "nenhuma"

        position = detection.get("position", "centro")

        # Rule 3: persistent visual detection with distance below critical threshold.
        if valid_distance and distance_m <= self.critical_m:
            return RISK_CRITICAL, position

        # Rule 2: visual detection with distance below moderate threshold.
        if valid_distance and distance_m <= self.moderate_m:
            return RISK_MODERATE, position

        if valid_distance and distance_m <= self.attention_m:
            return RISK_ATTENTION, position

        # Vision only, no usable distance reading (e.g. sensor timeout).
        return RISK_ATTENTION, position

    def estimate(self, detections, distance_m, imu_state=None):
        """Combine one frame of sensor data into a debounced risk level+position."""
        instant_risk, instant_position = self._instant_risk(detections, distance_m)
        self.tracker.update(instant_risk, instant_position)
        stable_risk, stable_position = self.tracker.persistent_risk(self.persistence_frames)
        return RiskResult(risk_level=stable_risk, position=stable_position or "nenhuma")

    def reset(self):
        self.tracker.reset()


def estimate_risk(detections, distance_m, imu_state, config):
    """Stateless convenience wrapper around RF06's rules. Prefer RiskEstimator
    directly in the main loop, since it carries persistence state across frames."""
    return RiskEstimator(config).estimate(detections, distance_m, imu_state)
