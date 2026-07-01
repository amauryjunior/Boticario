#!/usr/bin/env python3
"""Measures per-stage latency — RF13: capture, inference, sensor read,
decision, and total time until an alert decision is made."""
import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.camera.camera_reader import CameraReader
from src.camera.frame_preprocessor import preprocess
from src.ai.detector import Detector
from src.sensors.distance_sensor import DistanceSensor
from src.fusion.risk_estimator import RiskEstimator
from src.alerts.alert_controller import AlertController
from src.alerts.vibration import VibrationMotor
from src.alerts.buzzer import Buzzer
from src.utils.timing import Timer, now_ms

TARGET_ACCEPTABLE_MS = 500
TARGET_IDEAL_MS = 200


def run_benchmark(config_path, simulate, iterations):
    config = Config.load(config_path)
    camera = CameraReader(config, simulate=simulate)
    detector = Detector(config, simulate=simulate)
    distance_sensor = DistanceSensor(config, simulate=simulate)
    risk_estimator = RiskEstimator(config)
    alerts_cfg = config.section("alerts")
    left = VibrationMotor(alerts_cfg.get("left_motor_pin"), "left", simulate=True)
    right = VibrationMotor(alerts_cfg.get("right_motor_pin"), "right", simulate=True)
    buzzer = Buzzer(alerts_cfg.get("buzzer_pin"), simulate=True)
    alert_controller = AlertController(left, right, buzzer, config)

    stages = {"capture": [], "inference": [], "distance": [], "decision": [], "total": []}

    for _ in range(iterations):
        loop_start = now_ms()

        with Timer() as t_capture:
            frame = camera.read_frame()
            processed = preprocess(frame, config) if frame is not None else None
        with Timer() as t_infer:
            detections = detector.detect(processed) if processed is not None else []
        with Timer() as t_dist:
            distance_m = distance_sensor.read()
        with Timer() as t_decision:
            result = risk_estimator.estimate(detections, distance_m, None)
            alert = alert_controller.decide(result.risk_level, result.position)
            alert_controller.execute(alert)

        stages["capture"].append(t_capture.elapsed_ms)
        stages["inference"].append(t_infer.elapsed_ms)
        stages["distance"].append(t_dist.elapsed_ms)
        stages["decision"].append(t_decision.elapsed_ms)
        stages["total"].append(now_ms() - loop_start)

    left.close()
    right.close()
    buzzer.close()
    camera.close()
    distance_sensor.close()
    return stages


def report(stages):
    print(f"{'Etapa':<12}{'media(ms)':>12}{'p95(ms)':>12}{'max(ms)':>12}")
    for stage, values in stages.items():
        if not values:
            continue
        values_sorted = sorted(values)
        p95 = values_sorted[int(0.95 * (len(values_sorted) - 1))]
        print(f"{stage:<12}{statistics.mean(values):>12.1f}{p95:>12.1f}{max(values):>12.1f}")

    total_mean = statistics.mean(stages["total"]) if stages["total"] else 0
    if total_mean <= TARGET_IDEAL_MS:
        verdict = "IDEAL"
    elif total_mean <= TARGET_ACCEPTABLE_MS:
        verdict = "ACEITAVEL"
    else:
        verdict = "FORA DA META"
    print(f"\nLatencia total media: {total_mean:.1f} ms -> {verdict}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark de latencia - RF13")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--simulation", action="store_true", default=True)
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()

    stages = run_benchmark(args.config, args.simulation, args.iterations)
    report(stages)


if __name__ == "__main__":
    main()
