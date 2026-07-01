#!/usr/bin/env python3
"""Bench calibration — RF11: distance range, ROI and AI confidence threshold.
Saves the results back into configs/config.yaml."""
import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.sensors.distance_sensor import DistanceSensor


def calibrate_distance_range(config, simulate, samples):
    sensor = DistanceSensor(config, simulate=simulate)
    readings = []
    print(f"Coletando {samples} amostras de distancia... mantenha a area livre.")
    for _ in range(samples):
        value = sensor.read()
        if value is not None:
            readings.append(value)
        time.sleep(0.1)
    sensor.close()

    if not readings:
        print("Nenhuma leitura valida obtida - verifique o sensor.")
        return

    min_reading = min(readings)
    max_reading = max(readings)
    print(
        f"Leituras: min={min_reading:.2f}m max={max_reading:.2f}m "
        f"media={statistics.mean(readings):.2f}m"
    )
    config.set("distance_sensor.min_distance_m", round(max(min_reading - 0.05, 0.05), 2))
    config.set("distance_sensor.max_distance_m", round(max_reading + 0.2, 2))


def calibrate_roi(config):
    print("Ajuste da ROI (valores 0.0-1.0). Pressione Enter para manter o atual.")
    for field, label in (
        ("roi_top", "topo"),
        ("roi_bottom", "base"),
        ("roi_left", "esquerda"),
        ("roi_right", "direita"),
    ):
        current = config.get(f"camera.{field}")
        raw = input(f"  {label} [{current}]: ").strip()
        if raw:
            config.set(f"camera.{field}", float(raw))


def calibrate_confidence(config):
    current = config.get("ai.min_confidence")
    raw = input(f"Confianca minima do modelo de IA [{current}]: ").strip()
    if raw:
        config.set("ai.min_confidence", float(raw))


def main():
    parser = argparse.ArgumentParser(description="Calibracao de bancada - RF11")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--simulation", action="store_true")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--skip-roi", action="store_true")
    parser.add_argument("--skip-confidence", action="store_true")
    args = parser.parse_args()

    config = Config.load(args.config)
    calibrate_distance_range(config, args.simulation, args.samples)
    if not args.skip_roi:
        calibrate_roi(config)
    if not args.skip_confidence:
        calibrate_confidence(config)

    config.save(args.config)
    print(f"Configuracao salva em {args.config}")


if __name__ == "__main__":
    main()
