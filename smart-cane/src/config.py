"""Configuration loading and access for the Smart Cane firmware."""
import copy
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "camera": {
        "enabled": True,
        "width": 320,
        "height": 320,
        "fps": 10,
        "roi_top": 0.15,
        "roi_bottom": 0.85,
        "roi_left": 0.05,
        "roi_right": 0.95,
    },
    "ai": {
        "enabled": True,
        "model_path": "models/obstacle_detector.tflite",
        "min_confidence": 0.55,
        "classes": [
            "galho",
            "placa",
            "poste",
            "lixeira",
            "marquise",
            "mobiliario_urbano",
            "obstaculo_generico",
        ],
    },
    "distance_sensor": {
        "type": "vl53l1x",
        "enabled": True,
        "min_distance_m": 0.2,
        "max_distance_m": 3.0,
        "moving_average_window": 5,
        "trigger_pin": 23,
        "echo_pin": 24,
    },
    "imu": {
        "enabled": False,
        "type": "mpu6050",
        "i2c_address": 0x68,
        "movement_threshold_g": 0.05,
    },
    "risk": {
        "attention_distance_m": 3.0,
        "moderate_distance_m": 2.0,
        "critical_distance_m": 1.0,
        "persistence_frames": 3,
        "cooldown_ms": 500,
    },
    "alerts": {
        "vibration_enabled": True,
        "buzzer_enabled": True,
        "silent_mode_default": False,
        "left_motor_pin": 17,
        "right_motor_pin": 27,
        "buzzer_pin": 22,
    },
    "button": {
        "enabled": True,
        "pin": 5,
        "long_press_seconds": 2,
    },
    "logging": {
        "enabled": True,
        "path": "logs/",
        "format": "csv",
    },
    "power": {
        "low_power_mode": True,
        "idle_fps": 3,
        "movement_detection_enabled": True,
    },
}


class Config:
    """Dict-like configuration object with dotted-path access and YAML load/save."""

    def __init__(self, data=None):
        self._data = data if data is not None else copy.deepcopy(DEFAULT_CONFIG)

    @classmethod
    def load(cls, path):
        path = Path(path)
        merged = copy.deepcopy(DEFAULT_CONFIG)
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh) or {}
            _deep_merge(merged, loaded)
        return cls(merged)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(self._data, fh, allow_unicode=True, sort_keys=False)

    def get(self, dotted_key, default=None):
        node = self._data
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, dotted_key, value):
        node = self._data
        parts = dotted_key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def section(self, name):
        return self._data.get(name, {})

    def as_dict(self):
        return copy.deepcopy(self._data)

    def __getitem__(self, key):
        return self._data[key]


def _deep_merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
