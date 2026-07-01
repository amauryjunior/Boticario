"""Obstacle class labels used by the detector — RF03."""

OBSTACLE_CLASSES = [
    "galho",
    "placa",
    "poste",
    "lixeira",
    "marquise",
    "mobiliario_urbano",
    "caixa_suspensa",
    "obstaculo_generico",
]


def classes_from_config(config):
    configured = config.get("ai.classes")
    return configured if configured else list(OBSTACLE_CLASSES)
