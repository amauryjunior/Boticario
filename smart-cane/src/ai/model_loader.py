"""Loads the TFLite obstacle-detection model, if present and supported."""
from pathlib import Path

try:
    import tflite_runtime.interpreter as tflite
except Exception:  # pragma: no cover
    try:
        from tensorflow import lite as tflite  # dev-machine fallback
    except Exception:
        tflite = None


class ModelLoader:
    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.interpreter = None
        self.available = False

    def load(self):
        if tflite is None or not self.model_path.exists():
            return False
        try:
            self.interpreter = tflite.Interpreter(model_path=str(self.model_path))
            self.interpreter.allocate_tensors()
            self.available = True
        except Exception:
            self.interpreter = None
            self.available = False
        return self.available

    def input_details(self):
        return self.interpreter.get_input_details() if self.interpreter else []

    def output_details(self):
        return self.interpreter.get_output_details() if self.interpreter else []
