from src.config import Config
from src.fusion.risk_estimator import (
    RiskEstimator,
    RISK_NONE,
    RISK_ATTENTION,
    RISK_MODERATE,
    RISK_CRITICAL,
)
from src.sensors.distance_sensor import DistanceSensor
from src.ai.detector import Detector


def make_config():
    config = Config()
    config.set("risk.persistence_frames", 1)
    return config


def test_fusion_camera_and_distance_combine_to_critical():
    estimator = RiskEstimator(make_config())
    detection = {
        "class": "poste",
        "confidence": 0.9,
        "bbox": (0, 0, 5, 5),
        "position": "direita",
        "in_roi": True,
    }
    result = estimator.estimate([detection], 0.6, None)
    assert result.risk_level == RISK_CRITICAL
    assert result.position == "direita"


def test_fusion_fallback_without_camera_uses_distance_only():
    estimator = RiskEstimator(make_config())
    result = estimator.estimate([], 0.9, None)  # no vision at all
    assert result.risk_level == RISK_MODERATE
    assert result.position == "centro"


def test_fusion_fallback_without_distance_uses_vision_only():
    estimator = RiskEstimator(make_config())
    detection = {
        "class": "galho",
        "confidence": 0.8,
        "bbox": (0, 0, 5, 5),
        "position": "esquerda",
        "in_roi": True,
    }
    result = estimator.estimate([detection], None, None)
    assert result.risk_level == RISK_ATTENTION
    assert result.position == "esquerda"


def test_no_obstacle_when_both_sensors_empty():
    estimator = RiskEstimator(make_config())
    result = estimator.estimate([], None, None)
    assert result.risk_level == RISK_NONE


def test_simulated_distance_sensor_produces_readings_in_range():
    config = make_config()
    sensor = DistanceSensor(config, simulate=True)
    readings = [sensor.read() for _ in range(20)]
    valid = [r for r in readings if r is not None]
    assert len(valid) > 0
    max_allowed = config.get("distance_sensor.max_distance_m") + 1.0
    for r in valid:
        assert 0.0 <= r <= max_allowed
    sensor.close()


def test_simulated_detector_returns_valid_schema():
    config = make_config()
    detector = Detector(config, simulate=True)
    found_any = False
    for _ in range(30):
        for d in detector.detect(None):
            found_any = True
            assert {"class", "confidence", "bbox", "position", "in_roi", "timestamp"} <= d.keys()
            assert d["position"] in ("esquerda", "centro", "direita")
    assert found_any
