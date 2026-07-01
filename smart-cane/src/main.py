"""Smart Cane Gralha Azul — main entry point.

Orchestrates the RF01-RF14 state machine: sensor/camera initialization,
the scan-detect-fuse-alert loop, the physical button, and safe shutdown.
The cane's physical shaft is never disabled by software — see section 17
(fail-safe) of the project requirements: on any electronic failure the
device simply stops alerting, it never blocks normal cane use.
"""
import argparse
import signal
import sys
import time
from pathlib import Path

# `python src/main.py` puts src/ (not the project root) on sys.path, so add
# the project root explicitly to make `from src...` absolute imports work.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.camera.camera_reader import CameraReader
from src.camera.frame_preprocessor import preprocess
from src.ai.detector import Detector
from src.sensors.distance_sensor import DistanceSensor
from src.sensors.imu_sensor import IMUSensor
from src.fusion.risk_estimator import RiskEstimator
from src.alerts.vibration import VibrationMotor
from src.alerts.buzzer import Buzzer
from src.alerts.alert_controller import AlertController
from src.power.power_manager import PowerManager
from src.logging.event_logger import EventLogger
from src.utils.timing import Timer, now_ms
from src.utils.health_check import HealthReport

try:
    from gpiozero import Button
except Exception:  # pragma: no cover
    Button = None

STATE_BOOT = "BOOT"
STATE_SELF_TEST = "SELF_TEST"
STATE_READY = "READY"
STATE_SCANNING = "SCANNING"
STATE_ALERT_ATTENTION = "ALERT_ATTENTION"
STATE_ALERT_MODERATE = "ALERT_MODERATE"
STATE_ALERT_CRITICAL = "ALERT_CRITICAL"
STATE_LOW_BATTERY = "LOW_BATTERY"
STATE_ERROR = "ERROR"
STATE_SHUTDOWN = "SHUTDOWN"

RISK_TO_STATE = {
    0: STATE_SCANNING,
    1: STATE_ALERT_ATTENTION,
    2: STATE_ALERT_MODERATE,
    3: STATE_ALERT_CRITICAL,
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


class SmartCane:
    def __init__(self, config_path, simulate=False):
        self.simulate = simulate
        self.config = Config.load(config_path)
        self.state = STATE_BOOT
        self._running = False

        self.camera = CameraReader(self.config, simulate=simulate)
        self.detector = Detector(self.config, simulate=simulate)
        self.distance_sensor = DistanceSensor(self.config, simulate=simulate)
        self.imu = IMUSensor(self.config, simulate=simulate)
        self.risk_estimator = RiskEstimator(self.config)
        self.power_manager = PowerManager(self.config, imu_sensor=self.imu)
        self.logger = EventLogger(self.config)

        alerts_cfg = self.config.section("alerts")
        self.left_motor = VibrationMotor(alerts_cfg.get("left_motor_pin"), "left", simulate=simulate)
        self.right_motor = VibrationMotor(alerts_cfg.get("right_motor_pin"), "right", simulate=simulate)
        self.buzzer = Buzzer(alerts_cfg.get("buzzer_pin"), simulate=simulate)
        self.alert_controller = AlertController(self.left_motor, self.right_motor, self.buzzer, self.config)

        self.button = None
        self._button_press_start = None
        button_cfg = self.config.section("button")
        self.long_press_seconds = button_cfg.get("long_press_seconds", 2)
        if button_cfg.get("enabled", True) and not simulate and Button is not None:
            self.button = Button(button_cfg.get("pin", 5))
            self.button.when_pressed = self._on_button_pressed
            self.button.when_released = self._on_button_released

    # ---- RF10: physical button ------------------------------------------------
    def _on_button_pressed(self):
        self._button_press_start = time.monotonic()

    def _on_button_released(self):
        if self._button_press_start is None:
            return
        held = time.monotonic() - self._button_press_start
        self._button_press_start = None
        if held >= self.long_press_seconds:
            log("Botao: toque longo -> encerrando com seguranca")
            self._running = False
        else:
            silent = self.alert_controller.toggle_silent_mode()
            log(f"Botao: toque curto -> modo silencioso = {silent}")
            if not silent:
                self.buzzer.beep(60)

    # ---- RF01: self-test --------------------------------------------------
    def self_test(self):
        self.state = STATE_SELF_TEST
        report = HealthReport()
        report.add("camera", self.camera.available, critical=True)
        report.add("distance_sensor", self.distance_sensor.enabled or self.simulate, critical=True)
        report.add("imu", self.imu.enabled or self.simulate, critical=False)
        report.add(
            "ai_model",
            self.detector.mode in ("tflite", "heuristic", "simulated"),
            critical=False,
            message=self.detector.mode,
        )
        report.add("vibration_left", True, critical=False)
        report.add("vibration_right", True, critical=False)
        report.add("buzzer", True, critical=False)

        for line in report.summary_lines():
            log(line)

        if report.has_critical_failure:
            self.state = STATE_ERROR
            self.buzzer.error_pattern()
            log("Falha critica no autoteste - verifique camera/sensor de distancia")
            return False

        if report.degraded:
            log("Iniciando em modo degradado (sensor nao critico indisponivel)")

        self.state = STATE_READY
        return True

    # ---- Main loop -------------------------------------------------------
    def run(self):
        if not self.self_test():
            self._shutdown()
            return

        self._running = True
        self.state = STATE_SCANNING
        log("Sistema pronto - iniciando varredura (SCANNING)")

        while self._running:
            loop_start = now_ms()
            try:
                self._tick(loop_start)
            except Exception as exc:  # RNF03: one bad frame must never crash the loop
                log(f"Erro no ciclo principal (ignorado): {exc}")
            target_period_ms = 1000.0 / max(self.power_manager.current_fps(), 1)
            elapsed_ms = now_ms() - loop_start
            time.sleep(max((target_period_ms - elapsed_ms) / 1000.0, 0.0))

        self._shutdown()

    def _tick(self, loop_start):
        with Timer() as capture_timer:
            frame = self.camera.read_frame()
            processed = preprocess(frame, self.config) if frame is not None else None

        with Timer() as inference_timer:
            detections = self.detector.detect(processed) if processed is not None else []

        with Timer() as distance_timer:
            distance_m = self.distance_sensor.read()

        with Timer() as decision_timer:
            result = self.risk_estimator.estimate(detections, distance_m, None)
            alert = self.alert_controller.decide(result.risk_level, result.position)
            self.alert_controller.execute(alert)

        self.state = RISK_TO_STATE.get(result.risk_level, STATE_SCANNING)
        total_latency_ms = now_ms() - loop_start

        primary = detections[0] if detections else {}
        self.logger.log(
            timestamp=time.time(),
            distance_m=distance_m,
            detected_class=primary.get("class", ""),
            confidence=primary.get("confidence", ""),
            bbox=primary.get("bbox", ""),
            risk_level=result.risk_level,
            alert_type=alert.position,
            latency_ms=round(total_latency_ms, 1),
            battery_status=self.power_manager.battery_status(),
            mode="simulation" if self.simulate else "hardware",
        )

        if result.risk_level > 0:
            dist_txt = "N/D" if distance_m is None else f"{distance_m:.2f}m"
            log(
                f"{self.state}: risco={result.risk_level} posicao={result.position} "
                f"dist={dist_txt} lat={total_latency_ms:.1f}ms"
            )

    def _shutdown(self):
        self.state = STATE_SHUTDOWN
        log("Encerrando com seguranca (SHUTDOWN)")
        self.alert_controller.stop_all()
        self.left_motor.close()
        self.right_motor.close()
        self.buzzer.close()
        self.camera.close()
        self.distance_sensor.close()
        self.imu.close()
        self.logger.close()

    def stop(self):
        self._running = False


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bengala Inteligente Gralha Azul")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--simulation", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    cane = SmartCane(args.config, simulate=args.simulation)

    def _handle_signal(signum, frame):
        cane.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    cane.run()


if __name__ == "__main__":
    main()
