"""Event logging for bench/field validation — RF12. Writes one row per
processing cycle to a session-scoped CSV or JSON-Lines file."""
import csv
import json
import time
from datetime import datetime
from pathlib import Path

FIELDS = [
    "timestamp",
    "distance_m",
    "detected_class",
    "confidence",
    "bbox",
    "risk_level",
    "alert_type",
    "latency_ms",
    "battery_status",
    "mode",
]


class EventLogger:
    def __init__(self, config):
        cfg = config.section("logging")
        self.enabled = cfg.get("enabled", True)
        self.format = cfg.get("format", "csv")
        self.base_path = Path(cfg.get("path", "logs/"))
        self._file = None
        self._writer = None
        self.session_file = None

        if self.enabled:
            self.base_path.mkdir(parents=True, exist_ok=True)
            session_name = datetime.now().strftime("session_%Y%m%d_%H%M%S")
            suffix = "csv" if self.format == "csv" else "jsonl"
            self.session_file = self.base_path / f"{session_name}.{suffix}"
            self._file = open(self.session_file, "w", newline="", encoding="utf-8")
            if self.format == "csv":
                self._writer = csv.DictWriter(self._file, fieldnames=FIELDS)
                self._writer.writeheader()

    def log(self, **fields):
        if not self.enabled or self._file is None:
            return
        row = {key: fields.get(key, "") for key in FIELDS}
        row["timestamp"] = row["timestamp"] or time.time()
        if self.format == "csv":
            self._writer.writerow(row)
        else:
            self._file.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._file.flush()

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None
