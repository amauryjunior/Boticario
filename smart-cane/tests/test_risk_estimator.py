from src.config import Config
from src.fusion.risk_estimator import (
    RiskEstimator,
    RISK_NONE,
    RISK_ATTENTION,
    RISK_MODERATE,
    RISK_CRITICAL,
)


def make_estimator(persistence_frames=1):
    config = Config()
    config.set("risk.persistence_frames", persistence_frames)
    return RiskEstimator(config)


def detection(confidence=0.8, position="centro", in_roi=True, cls="obstaculo_generico"):
    return {
        "class": cls,
        "confidence": confidence,
        "bbox": (0, 0, 10, 10),
        "position": position,
        "in_roi": in_roi,
    }


def test_no_obstacle():
    estimator = make_estimator()
    result = estimator.estimate([], None, None)
    assert result.risk_level == RISK_NONE


def test_obstacle_far_attention():
    estimator = make_estimator()
    result = estimator.estimate([detection()], 2.8, None)
    assert result.risk_level == RISK_ATTENTION


def test_obstacle_moderate():
    estimator = make_estimator()
    result = estimator.estimate([detection()], 1.5, None)
    assert result.risk_level == RISK_MODERATE


def test_obstacle_critical():
    estimator = make_estimator()
    result = estimator.estimate([detection(position="direita")], 0.8, None)
    assert result.risk_level == RISK_CRITICAL
    assert result.position == "direita"


def test_low_confidence_ignored():
    estimator = make_estimator()
    estimator.min_confidence = 0.9
    result = estimator.estimate([detection(confidence=0.3)], 0.8, None)
    # Vision discarded (below threshold); falls back to sensor-only rule.
    assert result.risk_level == RISK_MODERATE
    assert result.position == "centro"


def test_detection_outside_roi_ignored():
    estimator = make_estimator()
    result = estimator.estimate([detection(position="esquerda", in_roi=False)], 1.5, None)
    # Vision discarded (outside ROI); falls back to sensor-only rule -> centro.
    assert result.risk_level == RISK_ATTENTION
    assert result.position == "centro"


def test_invalid_distance_uses_vision_only():
    estimator = make_estimator()
    result = estimator.estimate([detection(position="esquerda")], None, None)
    assert result.risk_level == RISK_ATTENTION
    assert result.position == "esquerda"


def test_no_risk_when_distance_far_and_no_vision():
    estimator = make_estimator()
    result = estimator.estimate([], 2.8, None)
    assert result.risk_level == RISK_NONE


def test_persistence_requires_multiple_frames():
    estimator = make_estimator()
    estimator.persistence_frames = 3

    result1 = estimator.estimate([detection()], 0.8, None)
    assert result1.risk_level == RISK_NONE  # not persistent yet

    result2 = estimator.estimate([detection()], 0.8, None)
    assert result2.risk_level == RISK_NONE

    result3 = estimator.estimate([detection()], 0.8, None)
    assert result3.risk_level == RISK_CRITICAL
