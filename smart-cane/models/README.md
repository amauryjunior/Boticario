# models/

Este diretório deve conter `obstacle_detector.tflite`, o modelo quantizado de
detecção de obstáculos usado por `src/ai/detector.py` (modo `tflite`).

Este repositório **não inclui um modelo treinado** — treinar um detector
específico para as classes definidas em `configs/config.yaml` (`ai.classes`)
está fora do escopo do firmware. Até que um modelo treinado seja adicionado
aqui, o `Detector` opera automaticamente em um dos modos de fallback (RF03):

1. **heuristic** — detecção por contornos/bordas via OpenCV: regiões de alto
   contraste dentro da ROI são tratadas como obstáculo genérico. Usado
   automaticamente quando `obstacle_detector.tflite` não existe mas OpenCV
   está disponível.
2. **simulated** — usado com `--simulation`, gera detecções fictícias para
   testes de lógica e demonstração sem hardware.

Para usar um modelo real, treine (ou converta) um detector de objetos leve
(ex.: MobileNet-SSD ou YOLO quantizado) exportado em formato TFLite e copie
o arquivo para `models/obstacle_detector.tflite`. O decodificador de
saída em `Detector._tflite_detections` deve ser adaptado ao formato de saída
do modelo escolhido (boxes/scores/classes).
