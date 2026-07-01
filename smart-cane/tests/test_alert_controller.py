from src.config import Config
from src.alerts.alert_controller import AlertController
from src.alerts.vibration import VibrationMotor
from src.alerts.buzzer import Buzzer


def make_controller(cooldown_ms=500):
    config = Config()
    config.set("risk.cooldown_ms", cooldown_ms)
    events = []

    def on_event(name, action, kwargs):
        events.append((name, action, kwargs))

    left = VibrationMotor(17, "left", simulate=True, on_event=on_event)
    right = VibrationMotor(27, "right", simulate=True, on_event=on_event)
    buzzer = Buzzer(22, simulate=True, on_event=on_event)
    controller = AlertController(left, right, buzzer, config)
    return controller, left, right, buzzer, events


def test_alert_left():
    controller, *_ = make_controller()
    alert = controller.decide(2, "esquerda")
    assert alert.vibrate_left is True
    assert alert.vibrate_right is False


def test_alert_right():
    controller, *_ = make_controller()
    alert = controller.decide(2, "direita")
    assert alert.vibrate_left is False
    assert alert.vibrate_right is True


def test_alert_center():
    controller, *_ = make_controller()
    alert = controller.decide(2, "centro")
    assert alert.vibrate_left is True
    assert alert.vibrate_right is True


def test_no_risk_stops_motors():
    controller, *_ = make_controller()
    alert = controller.decide(0, "nenhuma")
    assert alert.vibrate_left is False
    assert alert.vibrate_right is False
    assert alert.beep is False


def test_silent_mode_blocks_buzzer_not_vibration():
    controller, left, right, buzzer, events = make_controller()
    controller.toggle_silent_mode()
    alert = controller.decide(3, "centro")
    controller.execute(alert)
    try:
        beep_events = [e for e in events if e[0] == "buzzer" and e[1] == "beep"]
        assert beep_events == []
        pulse_events = [e for e in events if e[1] == "pulse_start"]
        assert len(pulse_events) == 2  # both motors still vibrate
    finally:
        left.stop()
        right.stop()


def test_cooldown_prevents_rapid_beeping():
    controller, left, right, buzzer, events = make_controller(cooldown_ms=1000)
    alert = controller.decide(3, "centro")
    controller.execute(alert)
    controller.execute(alert)  # immediate repeat, should be suppressed by cooldown
    try:
        beep_events = [e for e in events if e[0] == "buzzer" and e[1] == "beep"]
        assert len(beep_events) == 1
    finally:
        left.stop()
        right.stop()


def test_critical_risk_triggers_beep():
    controller, left, right, buzzer, events = make_controller()
    alert = controller.decide(3, "centro")
    assert alert.beep is True
    controller.execute(alert)
    try:
        beep_events = [e for e in events if e[0] == "buzzer" and e[1] == "beep"]
        assert len(beep_events) == 1
    finally:
        left.stop()
        right.stop()
