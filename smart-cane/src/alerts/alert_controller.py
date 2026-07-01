"""Alert decision and execution — RF08 (directional vibration), RF09 (buzzer),
RF07 (cooldown so alerts don't spam the user)."""
from dataclasses import dataclass

from src.utils.timing import now_ms


@dataclass
class AlertCommand:
    risk_level: int
    position: str  # "esquerda" | "direita" | "centro" | "nenhuma"
    vibrate_left: bool = False
    vibrate_right: bool = False
    beep: bool = False


class AlertController:
    def __init__(self, left_motor, right_motor, buzzer, config):
        self.left_motor = left_motor
        self.right_motor = right_motor
        self.buzzer = buzzer
        alerts_cfg = config.section("alerts")
        self.vibration_enabled = alerts_cfg.get("vibration_enabled", True)
        self.buzzer_enabled = alerts_cfg.get("buzzer_enabled", True)
        self.silent_mode = alerts_cfg.get("silent_mode_default", False)
        self.cooldown_ms = config.get("risk.cooldown_ms", 500)
        self._last_beep_ms = 0.0

    def toggle_silent_mode(self):
        self.silent_mode = not self.silent_mode
        return self.silent_mode

    def decide(self, risk_level, position):
        """Pure decision step: map (risk, position) -> AlertCommand (RF08 rules)."""
        if risk_level <= 0:
            return AlertCommand(risk_level=0, position="nenhuma")

        vibrate_left = position in ("esquerda", "centro")
        vibrate_right = position in ("direita", "centro")
        beep = risk_level >= 3
        return AlertCommand(
            risk_level=risk_level,
            position=position,
            vibrate_left=vibrate_left,
            vibrate_right=vibrate_right,
            beep=beep,
        )

    def execute(self, alert: AlertCommand):
        """Drives the actual (or simulated) hardware based on a decision."""
        if alert.risk_level <= 0:
            self.left_motor.stop()
            self.right_motor.stop()
            return

        if self.vibration_enabled:
            if alert.vibrate_left:
                self.left_motor.pulse(alert.risk_level)
            else:
                self.left_motor.stop()
            if alert.vibrate_right:
                self.right_motor.pulse(alert.risk_level)
            else:
                self.right_motor.stop()

        if alert.beep and self.buzzer_enabled and not self.silent_mode:
            now = now_ms()
            if now - self._last_beep_ms >= self.cooldown_ms:
                self.buzzer.beep(150)
                self._last_beep_ms = now

    def stop_all(self):
        self.left_motor.stop()
        self.right_motor.stop()
